"""Tests for the SCADA adapter interface — which must remain INACTIVE.

NAJM-3000's SCADA is not commissioned and no operational data exists. These
tests hold the interface to two promises: it is structurally defined, and it
refuses to pretend it has data.
"""

from __future__ import annotations

import pandas as pd
import pytest

from najm3000.scada.adapter_interface import (
    HistorianAdapter,
    InactiveHistorianAdapter,
    ScadaInactiveError,
)
from najm3000.scada.canonical import (
    CANONICAL_COLUMNS,
    CanonicalSchemaError,
    empty_canonical_frame,
    validate_canonical_frame,
)
from najm3000.scada.tag_mapping import (
    TagMappingError,
    parse_tag_mappings,
)

TZ = "Asia/Riyadh"


def _frame(**overrides) -> pd.DataFrame:
    index = pd.date_range("2026-01-01", periods=3, freq="1h", tz=TZ)
    base = {
        "timestamp": index,
        "tag_id": ["BLOCK_A_INV_01_PAC"] * 3,
        "asset_id": ["representative_block_a.inverter_01"] * 3,
        "value_raw": [1.0, 2.0, 3.0],
        "value_qc": [1.0, 2.0, 3.0],
        "quality_flag": ["OK"] * 3,
        "source_classification": ["MEASURED_SITE"] * 3,
        "unit": ["W"] * 3,
        "processing_version": ["qc-0.1.0"] * 3,
    }
    base.update(overrides)
    return pd.DataFrame(base)


# --- canonical schema -------------------------------------------------------


def test_empty_canonical_frame_has_every_required_column():
    frame = empty_canonical_frame()
    assert list(frame.columns) == list(CANONICAL_COLUMNS)
    assert frame.empty


def test_validation_accepts_a_conforming_frame():
    validate_canonical_frame(_frame())


def test_validation_rejects_a_missing_required_column():
    with pytest.raises(CanonicalSchemaError, match="value_raw"):
        validate_canonical_frame(_frame().drop(columns=["value_raw"]))


def test_validation_rejects_naive_timestamps():
    naive = pd.date_range("2026-01-01", periods=3, freq="1h")
    with pytest.raises(CanonicalSchemaError, match="timezone-aware"):
        validate_canonical_frame(_frame(timestamp=naive))


def test_validation_rejects_an_unknown_source_classification():
    with pytest.raises(CanonicalSchemaError, match="classification"):
        validate_canonical_frame(
            _frame(source_classification=["INVENTED_LABEL"] * 3)
        )


def test_validation_rejects_a_missing_processing_version():
    """Untraceable QC output must not enter the comparison layer."""
    with pytest.raises(CanonicalSchemaError, match="processing_version"):
        validate_canonical_frame(_frame(processing_version=[None] * 3))


def test_validation_allows_a_null_value_when_it_is_explained():
    """Real historians have gaps; an explained gap is valid data."""
    frame = _frame(
        value_raw=[1.0, None, 3.0],
        value_qc=[1.0, None, 3.0],
        quality_flag=["OK", "NO_DATA", "OK"],
        exclusion_reason=[None, "sensor offline", None],
    )
    validate_canonical_frame(frame)


def test_validation_rejects_an_unexplained_null_value():
    """A silent gap is indistinguishable from a modelling error."""
    with pytest.raises(CanonicalSchemaError, match="unexplained"):
        validate_canonical_frame(
            _frame(value_raw=[1.0, None, 3.0], value_qc=[1.0, None, 3.0])
        )


def test_validation_rejects_a_null_flagged_but_not_given_a_reason():
    with pytest.raises(CanonicalSchemaError, match="exclusion_reason"):
        validate_canonical_frame(
            _frame(
                value_raw=[1.0, None, 3.0],
                value_qc=[1.0, None, 3.0],
                quality_flag=["OK", "NO_DATA", "OK"],
            )
        )


def test_validation_preserves_the_raw_value_alongside_the_corrected_value():
    """Raw values are never overwritten by QC — both columns are required."""
    assert "value_raw" in CANONICAL_COLUMNS
    assert "value_qc" in CANONICAL_COLUMNS


# --- adapter interface ------------------------------------------------------


def test_historian_adapter_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        HistorianAdapter()  # type: ignore[abstract]


def test_inactive_adapter_refuses_to_fetch():
    adapter = InactiveHistorianAdapter()
    with pytest.raises(ScadaInactiveError, match="not commissioned"):
        adapter.fetch(
            ["BLOCK_A_INV_01_PAC"],
            pd.Timestamp("2026-01-01", tz=TZ),
            pd.Timestamp("2026-01-02", tz=TZ),
        )


def test_inactive_adapter_reports_no_available_tags():
    """It must not invent a tag list; an empty list is the honest answer."""
    assert InactiveHistorianAdapter().list_available_tags() == []


def test_inactive_adapter_reports_itself_as_inactive():
    assert InactiveHistorianAdapter().is_active is False


def test_inactive_adapter_declares_no_classification():
    """No data exists, so no source classification can apply."""
    adapter = InactiveHistorianAdapter()
    assert adapter.classification == "NOT_AVAILABLE"
    assert "NOT COMMISSIONED" in adapter.disclaimer.upper()


def test_the_interface_requires_a_classification_and_disclaimer():
    """Consumers must be able to state provenance without knowing the adapter."""

    class Incomplete(HistorianAdapter):
        def fetch(self, tag_ids, start, end):
            return _frame()

        def list_available_tags(self):
            return []

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


def test_a_concrete_adapter_satisfies_the_interface():
    """Proves the interface is implementable without any live connection."""

    class InMemoryAdapter(HistorianAdapter):
        is_active = True

        @property
        def classification(self):
            return "MEASURED_SITE"

        @property
        def disclaimer(self):
            return "test double"

        def fetch(self, tag_ids, start, end):
            return _frame()

        def list_available_tags(self):
            return ["BLOCK_A_INV_01_PAC"]

    adapter = InMemoryAdapter()
    frame = adapter.fetch(
        ["BLOCK_A_INV_01_PAC"],
        pd.Timestamp("2026-01-01", tz=TZ),
        pd.Timestamp("2026-01-02", tz=TZ),
    )
    validate_canonical_frame(frame)
    assert adapter.list_available_tags() == ["BLOCK_A_INV_01_PAC"]


# --- tag mapping and confidentiality ---------------------------------------


def _mapping(**overrides) -> dict:
    base = {
        "tag_id": "BLOCK_A_INV_01_PAC",
        "description": "Inverter 01, Block A, AC active power",
        "asset_id": "representative_block_a.inverter_01",
        "asset_class": "Inverter",
        "physical_quantity": "ac_power",
        "unit": "W",
        "expected_range": [0.0, 5.0e6],
    }
    base.update(overrides)
    return base


def test_tag_mapping_parses_a_sanitized_entry():
    mappings = parse_tag_mappings({"tag_mappings": [_mapping()]})
    assert mappings[0].tag_id == "BLOCK_A_INV_01_PAC"
    assert mappings[0].unit == "W"


def test_tag_mapping_rejects_an_inverted_expected_range():
    with pytest.raises(TagMappingError, match="range"):
        parse_tag_mappings(
            {"tag_mappings": [_mapping(expected_range=[100.0, 0.0])]}
        )


def test_tag_mapping_rejects_duplicate_tag_ids():
    with pytest.raises(TagMappingError, match="duplicate"):
        parse_tag_mappings({"tag_mappings": [_mapping(), _mapping()]})


@pytest.mark.parametrize(
    "leak",
    [
        "192.168.1.50",
        "scada-historian.internal",
        "modbus register 40001",
        "password=hunter2",
    ],
)
def test_tag_mapping_rejects_network_or_credential_details(leak):
    """CONFIDENTIALITY.md forbids addresses and credentials in this repo."""
    with pytest.raises(TagMappingError, match="restricted"):
        parse_tag_mappings({"tag_mappings": [_mapping(description=leak)]})


def test_tag_mapping_rejects_a_tag_id_containing_an_address():
    with pytest.raises(TagMappingError, match="restricted"):
        parse_tag_mappings({"tag_mappings": [_mapping(tag_id="10.0.0.1_PAC")]})
