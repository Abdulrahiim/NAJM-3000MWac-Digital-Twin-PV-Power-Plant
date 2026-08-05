"""Tests for the expected-vs-actual comparison (Sprint 8).

The comparison is what a commissioned digital twin exists to do. Until SCADA
is live there is nothing measured to compare against, so the "actual" channel
here is the physics output with measurement effects applied — and every test
below holds it to being labeled as such.

The arithmetic is checked against hand-computed inputs, not against itself.
"""

from __future__ import annotations

import pandas as pd
import pytest

from najm3000.dashboard.performance import (
    MEASURED_LABEL,
    MeasurementModel,
    deviation_percent,
    performance_ratio,
)

BLOCK = "BLK_0001"


# --- deviation --------------------------------------------------------------


def test_deviation_is_zero_when_actual_matches_expected():
    assert deviation_percent(actual=100.0, expected=100.0) == pytest.approx(0.0)


def test_deviation_is_negative_when_underperforming():
    """980 against 1000 expected is -2%."""
    assert deviation_percent(actual=980.0, expected=1000.0) == pytest.approx(-2.0)


def test_deviation_is_positive_when_overperforming():
    assert deviation_percent(actual=1050.0, expected=1000.0) == pytest.approx(5.0)


def test_deviation_against_zero_expected_is_undefined_not_infinite():
    """Night-time expected output is zero; a percentage there is meaningless."""
    assert deviation_percent(actual=0.0, expected=0.0) is None
    assert deviation_percent(actual=5.0, expected=0.0) is None


# --- performance ratio ------------------------------------------------------


def test_performance_ratio_of_a_perfect_plant_is_one():
    """PR = E / (H_poa * P_stc / G_stc). With H=1 kWh/m2, P=1000 kW, E=1000 kWh."""
    assert performance_ratio(
        energy_kwh=1000.0, poa_kwh_per_m2=1.0, installed_kw=1000.0
    ) == pytest.approx(1.0)


def test_performance_ratio_scales_with_energy():
    assert performance_ratio(
        energy_kwh=800.0, poa_kwh_per_m2=1.0, installed_kw=1000.0
    ) == pytest.approx(0.8)


def test_performance_ratio_scales_inversely_with_irradiation():
    assert performance_ratio(
        energy_kwh=1000.0, poa_kwh_per_m2=2.0, installed_kw=1000.0
    ) == pytest.approx(0.5)


def test_performance_ratio_uses_a_realistic_worked_example():
    """5.5 kWh/m2 onto 9,825 kWp yielding 45,000 kWh gives PR 0.833."""
    assert performance_ratio(
        energy_kwh=45_000.0, poa_kwh_per_m2=5.5, installed_kw=9_825.0
    ) == pytest.approx(0.8330, abs=1e-3)


def test_performance_ratio_is_undefined_without_irradiation():
    assert performance_ratio(
        energy_kwh=0.0, poa_kwh_per_m2=0.0, installed_kw=1000.0
    ) is None


def test_performance_ratio_is_undefined_without_installed_capacity():
    assert performance_ratio(
        energy_kwh=100.0, poa_kwh_per_m2=1.0, installed_kw=0.0
    ) is None


# --- the simulated measurement channel --------------------------------------


@pytest.fixture
def model() -> MeasurementModel:
    return MeasurementModel()


def _series(values: list[float]) -> pd.Series:
    index = pd.date_range("2025-06-21 06:00", periods=len(values), freq="1h", tz="UTC")
    return pd.Series(values, index=index)


def test_measured_channel_is_labeled_as_simulated(model):
    assert "SIMULATED" in MEASURED_LABEL.upper()
    assert "MEASUR" in MEASURED_LABEL.upper()
    assert model.label == MEASURED_LABEL


def test_measured_channel_is_deterministic(model):
    expected = _series([100.0, 200.0, 300.0])
    first = model.apply(BLOCK, expected)
    second = model.apply(BLOCK, expected)
    pd.testing.assert_series_equal(first, second)


def test_two_blocks_receive_different_measurement_effects(model):
    expected = _series([100.0, 200.0, 300.0])
    a = model.apply("BLK_0001", expected)
    b = model.apply("BLK_0002", expected)
    assert not a.equals(b)


def test_measured_channel_stays_within_the_declared_envelope(model):
    """Effects must be plausible, not arbitrary."""
    expected = _series([500.0] * 24)
    actual = model.apply(BLOCK, expected)
    ratio = (actual / expected).to_numpy()
    assert ratio.min() >= 1.0 - model.max_deviation
    assert ratio.max() <= 1.0 + model.max_deviation


def test_measured_channel_is_never_negative(model):
    actual = model.apply(BLOCK, _series([0.0, 10.0, 0.0]))
    assert (actual >= 0.0).all()


def test_night_time_zero_stays_zero(model):
    """No sensor noise may invent generation at night."""
    actual = model.apply(BLOCK, _series([0.0, 0.0, 0.0]))
    assert (actual == 0.0).all()


def test_measurement_runs_slightly_below_expectation_on_average(model):
    """Real plants under-run the model; a channel that over-runs would flatter."""
    expected = _series([500.0] * 48)
    actual = model.apply(BLOCK, expected)
    assert actual.sum() < expected.sum()


def test_the_underperforming_block_is_identifiable(model):
    """One station is deliberately degraded so the comparison has something to
    show. It must be findable, not a mystery."""
    assert model.degraded_block(["BLK_0001", "BLK_0002", "BLK_0003"]) in {
        "BLK_0001",
        "BLK_0002",
        "BLK_0003",
    }


def test_the_degraded_block_underperforms_more_than_its_peers(model):
    blocks = [f"BLK_{i:04d}" for i in range(1, 8)]
    bound = model.for_plant(blocks)
    expected = _series([500.0] * 24)
    losses = {
        block: 1.0 - bound.apply(block, expected).sum() / expected.sum()
        for block in blocks
    }
    assert losses[bound.degraded_block_id] == max(losses.values())


def test_a_model_not_bound_to_a_plant_degrades_nobody(model):
    """Binding is explicit, so an unbound model cannot silently degrade one."""
    assert model.degraded_block_id is None
    assert not model.is_degraded("BLK_0001")


def test_degraded_selection_is_stable_for_the_same_plant(model):
    blocks = [f"BLK_{i:04d}" for i in range(1, 30)]
    assert model.degraded_block(blocks) == model.degraded_block(blocks)
