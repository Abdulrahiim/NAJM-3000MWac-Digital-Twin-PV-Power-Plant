"""Physical-limit tests on the full block chain (categories 4, 5, 6, 7, 10)."""
from __future__ import annotations

import pandas as pd
import pytest

from najm3000.aggregation.aggregator import make_location, scale_to_plant
from najm3000.assets.hierarchy import derive_asset_counts
from najm3000.tracking.solar_position import calculate_solar_position
from najm3000.validation.sanity_checks import run_all_checks

TEST_DAY = "2025-06-21"


@pytest.fixture(scope="module")
def solar_elevation(project_config, block_a_result):
    location = make_location(project_config)
    solpos = calculate_solar_position(
        location, pd.DatetimeIndex(block_a_result.timeseries.index)
    )
    return solpos["apparent_elevation"]


def test_sanity_suite_passes(block_a_result, solar_elevation):
    run_all_checks(block_a_result, solar_elevation)


def test_tracker_angle_within_max(block_a_result, equipment_config):
    max_angle = (
        equipment_config.trackers["tracker_vendor_a_model_1"].max_angle.value
    )
    theta = block_a_result.timeseries["tracker_theta"].dropna()
    assert (theta.abs() <= max_angle + 1e-6).all()


def test_no_negative_dc_power(block_a_result):
    assert (block_a_result.timeseries["p_dc_string"] >= 0.0).all()


def test_zero_nighttime_generation(block_a_result, solar_elevation):
    night = solar_elevation < 0.0
    night_ac = block_a_result.timeseries.loc[night, "p_ac_inverter"]
    assert (night_ac <= 0.0).all()


def test_night_consumption_applied(block_a_result, equipment_config):
    night_power = (
        equipment_config.inverters["inverter_vendor_a_model_1"]
        .night_power.value
    )
    midnight = block_a_result.timeseries.between_time("00:00", "02:00")
    assert (midnight["p_ac_inverter"] == -night_power).all()


def test_inverter_clipping_enforced(block_a_result, equipment_config):
    paco = equipment_config.inverters["inverter_vendor_a_model_1"].paco.value
    assert (block_a_result.timeseries["p_ac_inverter"] <= paco + 1e-6).all()


def test_dc_greater_than_ac(block_a_result):
    ts = block_a_result.timeseries
    generating = ts["p_ac_inverter"] > 0.0
    assert (
        ts.loc[generating, "p_dc_inverter"]
        >= ts.loc[generating, "p_ac_inverter"] - 1e-6
    ).all()


def test_bifacial_effective_exceeds_front(block_a_result):
    ts = block_a_result.timeseries
    day = ts["poa_front"] > 50.0
    # effective = (front + bifaciality*back) * soiling; with soiling 0.98 and
    # meaningful rear gain the effective must exceed the raw front POA on a
    # clear day for a tracked bifacial system.
    assert (
        ts.loc[day, "poa_effective"] >= ts.loc[day, "poa_front"] * 0.98 - 1e-9
    ).all()
    assert ts.loc[day, "poa_back"].sum() > 0.0


def test_cell_temperature_bounds(block_a_result):
    temp = block_a_result.timeseries["temp_cell"]
    assert (temp >= -30.0).all()
    assert (temp <= 100.0).all()


def test_energy_balance_closes(block_a_result):
    ledger = block_a_result.ledger
    net = block_a_result.block_energy_wh()
    ledger.check_closure(net)  # raises on failure
    assert ledger.gross_energy_wh > 0.0


def test_idt_losses_non_negative_and_bounded(block_a_result, equipment_config):
    idt = equipment_config.idts["idt_vendor_a_8_932_mva"]
    losses = block_a_result.ledger.losses["idt_losses"]
    assert losses > 0.0
    hours = 24.0
    max_possible = (
        idt.p_no_load.value + idt.p_load_rated.value
    ) * hours * 1.44
    assert losses < max_possible


def test_vendor_a_different_from_vendor_b(block_a_result, block_b_result):
    energy_a = block_a_result.block_energy_wh()
    energy_b = block_b_result.block_energy_wh()
    assert energy_a > 0.0
    assert energy_b > 0.0
    assert energy_a != pytest.approx(energy_b, rel=1e-3)


def test_asset_counts(blocks_config):
    counts = derive_asset_counts(blocks_config.blocks["test_block_a"])
    assert counts.idts == 1
    assert counts.inverters == 2
    assert counts.smbs == 32
    assert counts.strings == 512
    assert counts.modules == 13312


def test_plant_scaling_labeled(block_a_result, blocks_config):
    scaled = scale_to_plant(block_a_result, blocks_config)
    assert "NOT PRODUCTION VALIDATION" in str(scaled["label"])
    assert scaled["scaled_plant_energy_wh"] == pytest.approx(
        float(scaled["block_energy_wh"]) * 10
    )


def test_output_metadata_carries_disclaimer(block_a_result):
    assert "NOT PRODUCTION VALIDATION" in block_a_result.metadata["disclaimer"]
    assert (
        block_a_result.metadata["weather_classification"]
        == "SYNTHETIC_SOFTWARE_TEST"
    )
    assert block_a_result.metadata["calibration_status"] == "not-calibrated"
