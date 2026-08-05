"""Tests for the simulated historian adapter (Sprint 5).

The adapter dresses the physics engine as a telemetry source so the
pre-commissioning dashboard is built against the same contract the real
historian will implement. It must never be mistakable for measured data.
"""

from __future__ import annotations

import pandas as pd
import pytest

from najm3000.scada.adapter_interface import HistorianAdapter
from najm3000.scada.canonical import validate_canonical_frame
from najm3000.scada.simulated import (
    BLOCK_TAG_SPECS,
    SimulatedHistorianAdapter,
    UnknownTagError,
)
from najm3000.weather.provider import SyntheticClearskyProvider

DAY = "2025-06-21"
TZ = "Asia/Riyadh"


@pytest.fixture
def adapter(
    project_config, equipment_config, blocks_config, data_sources_config
) -> SimulatedHistorianAdapter:
    return SimulatedHistorianAdapter(
        project=project_config,
        equipment=equipment_config,
        blocks=blocks_config,
        weather_provider=SyntheticClearskyProvider(
            config=data_sources_config.data_sources.synthetic_clearsky
        ),
        day=DAY,
    )


def _window() -> tuple[pd.Timestamp, pd.Timestamp]:
    return (
        pd.Timestamp(f"{DAY} 00:00", tz=TZ),
        pd.Timestamp(f"{DAY} 23:59", tz=TZ),
    )


# --- identity and honesty ---------------------------------------------------


def test_adapter_implements_the_historian_interface(adapter):
    assert isinstance(adapter, HistorianAdapter)


def test_adapter_reports_itself_as_not_live(adapter):
    """It is a simulation and must say so."""
    assert adapter.is_active is False


def test_adapter_classification_follows_the_synthetic_weather_source(adapter):
    assert adapter.classification == "SYNTHETIC_SOFTWARE_TEST"


def test_adapter_classification_follows_the_public_weather_source(
    project_config, equipment_config, blocks_config, public_weather_config
):
    from pathlib import Path

    from najm3000.weather.pvgis import PVGISProvider

    fixtures = Path(__file__).parent.parent / "fixtures"

    def _fetcher(_lat, _lon, _year):
        frame = pd.read_csv(
            fixtures / "pvgis_neutral_2023.csv", index_col=0, parse_dates=True
        )
        frame.index = pd.DatetimeIndex(frame.index)
        return frame, {}

    hourly = project_config.model_copy(
        update={
            "simulation": project_config.simulation.model_copy(
                update={"timestep_minutes": 60}
            )
        }
    )
    adapter = SimulatedHistorianAdapter(
        project=hourly,
        equipment=equipment_config,
        blocks=blocks_config,
        weather_provider=PVGISProvider(
            config=public_weather_config, fetcher=_fetcher
        ),
        day="2023-06-21",
    )
    assert adapter.classification == "PROVISIONAL_PUBLIC"


def test_adapter_can_never_report_measured_site(adapter):
    """The one label a simulation must never carry."""
    start, end = _window()
    frame = adapter.fetch(adapter.list_available_tags()[:2], start, end)
    assert "MEASURED_SITE" not in set(frame["source_classification"])
    assert adapter.classification != "MEASURED_SITE"


def test_adapter_disclaimer_states_it_is_not_measured_data(adapter):
    assert "NOT" in adapter.disclaimer.upper()


# --- tags -------------------------------------------------------------------


def test_available_tags_cover_every_configured_block(adapter, blocks_config):
    tags = adapter.list_available_tags()
    assert len(tags) == len(blocks_config.blocks) * len(BLOCK_TAG_SPECS)


def test_tag_ids_are_sanitized_identifiers(adapter):
    """No addresses, no punctuation beyond underscores."""
    import re

    tags = adapter.list_available_tags()
    assert all(re.fullmatch(r"[A-Z0-9_]+", tag) for tag in tags)


def test_every_tag_spec_maps_to_a_simulation_column(adapter):
    start, end = _window()
    frame = adapter.fetch(adapter.list_available_tags(), start, end)
    assert set(frame["tag_id"]) == set(adapter.list_available_tags())


def test_fetch_rejects_an_unknown_tag(adapter):
    start, end = _window()
    with pytest.raises(UnknownTagError, match="unknown tag"):
        adapter.fetch(["NOT_A_REAL_TAG"], start, end)


# --- canonical conformance --------------------------------------------------


def test_fetch_output_validates_against_the_canonical_schema(adapter):
    start, end = _window()
    validate_canonical_frame(adapter.fetch(adapter.list_available_tags(), start, end))


def test_fetch_validated_helper_also_passes(adapter):
    start, end = _window()
    frame = adapter.fetch_validated(adapter.list_available_tags()[:3], start, end)
    assert not frame.empty


def test_every_row_carries_a_processing_version(adapter):
    start, end = _window()
    frame = adapter.fetch(adapter.list_available_tags()[:1], start, end)
    assert frame["processing_version"].notna().all()


def test_raw_and_qc_values_are_both_present_and_equal_for_a_simulation(adapter):
    """A simulation applies no QC correction, so raw and qc must agree."""
    start, end = _window()
    frame = adapter.fetch(adapter.list_available_tags()[:1], start, end)
    assert (frame["value_raw"] == frame["value_qc"]).all()


# --- filtering --------------------------------------------------------------


def test_fetch_returns_only_the_requested_tags(adapter):
    start, end = _window()
    wanted = adapter.list_available_tags()[:2]
    frame = adapter.fetch(wanted, start, end)
    assert set(frame["tag_id"]) == set(wanted)


def test_fetch_respects_the_time_window(adapter):
    tags = adapter.list_available_tags()[:1]
    start = pd.Timestamp(f"{DAY} 06:00", tz=TZ)
    end = pd.Timestamp(f"{DAY} 09:00", tz=TZ)
    frame = adapter.fetch(tags, start, end)
    stamps = pd.DatetimeIndex(frame["timestamp"])
    assert stamps.min() >= start
    assert stamps.max() <= end


def test_fetch_outside_the_simulated_day_returns_no_rows(adapter):
    tags = adapter.list_available_tags()[:1]
    frame = adapter.fetch(
        tags,
        pd.Timestamp("2025-01-01", tz=TZ),
        pd.Timestamp("2025-01-02", tz=TZ),
    )
    assert frame.empty


# --- correctness against the underlying model -------------------------------


def test_values_match_the_underlying_simulation(adapter, block_a_result):
    """The adapter must report the model, not a transformation of it."""
    start, end = _window()
    spec = next(s for s in BLOCK_TAG_SPECS if s.column == "p_block")
    tag = f"TEST_BLOCK_A_{spec.suffix}"
    frame = adapter.fetch([tag], start, end)
    expected = block_a_result.timeseries["p_block"]
    assert frame["value_raw"].to_numpy() == pytest.approx(expected.to_numpy())


def test_repeated_fetches_are_reproducible(adapter):
    start, end = _window()
    tags = adapter.list_available_tags()[:2]
    first = adapter.fetch(tags, start, end)
    second = adapter.fetch(tags, start, end)
    pd.testing.assert_frame_equal(
        first.reset_index(drop=True), second.reset_index(drop=True)
    )
