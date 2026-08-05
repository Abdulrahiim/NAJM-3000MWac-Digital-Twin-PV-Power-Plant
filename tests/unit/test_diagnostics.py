"""Tests for the deviation diagnostic engine (Sprint 9).

The engine attributes a measured-vs-expected gap to a cause. It reads only
signals — never the fault registry — so identifying an injected fault is a
genuine inference rather than a lookup. The first test in this file enforces
that, because it is the whole reason the feature is worth showing.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd

from najm3000.dashboard.diagnostics import (
    Diagnosis,
    StationSignals,
    diagnose,
)

SOURCE = (
    Path(__file__).parent.parent.parent
    / "src" / "najm3000" / "dashboard" / "diagnostics.py"
)


def _signals(
    expected_kw: list[float],
    measured_kw: list[float],
    poa: list[float] | None = None,
    temp_module: list[float] | None = None,
    inverters_kw: dict[str, list[float]] | None = None,
) -> StationSignals:
    n = len(expected_kw)
    index = pd.date_range("2025-06-21 05:00", periods=n, freq="1h", tz="Asia/Riyadh")
    series = lambda v: pd.Series(v, index=index)  # noqa: E731
    return StationSignals(
        block_id="BLK_0001",
        expected_kw=series(expected_kw),
        measured_kw=series(measured_kw),
        poa_w_m2=series(poa if poa is not None else [900.0] * n),
        temp_module_c=series(
            temp_module if temp_module is not None else [55.0] * n
        ),
        inverters_kw={k: series(v) for k, v in (inverters_kw or {}).items()},
        rated_kw=8800.0,
    )


# --- the engine must infer, not recall --------------------------------------


def test_the_engine_does_not_import_the_fault_registry():
    """Printing back an injected fault would demonstrate nothing."""
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    assert "najm3000.dashboard.faults" not in imported
    assert not any("fault" in module for module in imported)


# --- healthy operation ------------------------------------------------------


def test_a_healthy_station_reports_no_finding():
    signals = _signals([1000.0] * 8, [995.0] * 8)
    assert diagnose(signals) is None


def test_night_time_is_not_a_fault():
    signals = _signals([0.0] * 8, [0.0] * 8, poa=[0.0] * 8)
    assert diagnose(signals) is None


def test_inverter_clipping_is_reported_as_normal_not_as_a_fault():
    """Flat AC while irradiance climbs is design behaviour, not a defect."""
    signals = _signals(
        expected_kw=[8800.0] * 8,
        measured_kw=[8790.0] * 8,
        poa=[700, 800, 900, 1000, 1050, 1050, 1000, 900],
    )
    finding = diagnose(signals)
    assert finding is None or finding.severity == "normal"


# --- fault attribution ------------------------------------------------------


def test_total_outage_is_attributed_to_the_inverter_being_offline():
    signals = _signals(
        expected_kw=[1000.0] * 8,
        measured_kw=[0.0] * 8,
        poa=[900.0] * 8,
    )
    finding = diagnose(signals)
    assert finding is not None
    assert finding.cause == "inverter_offline"
    assert finding.severity == "critical"


def test_a_halved_station_is_attributed_to_one_inverter_lost():
    """Two inverters, one at zero: the station runs at half capacity."""
    signals = _signals(
        expected_kw=[1000.0] * 8,
        measured_kw=[500.0] * 8,
        inverters_kw={"inverter_01": [500.0] * 8, "inverter_02": [0.0] * 8},
    )
    finding = diagnose(signals)
    assert finding is not None
    assert finding.cause == "single_inverter_outage"
    assert "inverter_02" in finding.explanation


def test_a_proportional_shortfall_is_attributed_to_soiling_or_degradation():
    """A deficit that scales with irradiance points at optical loss."""
    poa = [200, 400, 600, 800, 900, 800, 600, 300]
    expected = [p * 10.0 for p in poa]
    measured = [e * 0.90 for e in expected]
    finding = diagnose(_signals(expected, measured, poa=poa))
    assert finding is not None
    assert finding.cause == "optical_loss"


def test_a_shortfall_only_at_high_temperature_is_attributed_to_thermal():
    temps = [30, 35, 45, 62, 70, 68, 45, 32]
    expected = [1000.0] * 8
    measured = [1000.0 if t < 60 else 880.0 for t in temps]
    finding = diagnose(_signals(expected, measured, temp_module=temps))
    assert finding is not None
    assert finding.cause == "thermal_derating"


def test_an_intermittent_dropout_is_attributed_to_communications():
    expected = [1000.0] * 10
    measured = [1000, 0, 1000, 1000, 0, 1000, 0, 1000, 1000, 1000]
    finding = diagnose(_signals(expected, [float(v) for v in measured]))
    assert finding is not None
    assert finding.cause == "intermittent_reporting"


# --- every finding must be explainable --------------------------------------


def test_every_finding_carries_evidence_and_a_confidence():
    signals = _signals([1000.0] * 8, [0.0] * 8)
    finding = diagnose(signals)
    assert isinstance(finding, Diagnosis)
    assert finding.evidence, "a finding with no evidence is an assertion"
    assert finding.confidence in {"High", "Medium", "Low"}
    assert finding.explanation.strip()


def test_findings_state_the_deviation_they_are_explaining():
    finding = diagnose(_signals([1000.0] * 8, [600.0] * 8))
    assert finding is not None
    assert finding.deviation_percent is not None
    assert finding.deviation_percent < 0


def test_a_finding_is_labelled_as_derived_from_simulated_signals():
    finding = diagnose(_signals([1000.0] * 8, [0.0] * 8))
    assert finding is not None
    assert "SIMULATED" in finding.basis.upper()


def test_diagnosis_is_serialisable_for_the_api():
    finding = diagnose(_signals([1000.0] * 8, [0.0] * 8))
    assert finding is not None
    payload = finding.as_dict()
    for key in ("block_id", "cause", "severity", "confidence", "explanation",
                "evidence", "deviation_percent", "basis"):
        assert key in payload


# --- determinism ------------------------------------------------------------


def test_the_same_signals_always_give_the_same_finding():
    signals = _signals([1000.0] * 8, [500.0] * 8)
    first, second = diagnose(signals), diagnose(signals)
    assert first is not None
    assert second is not None
    assert first.cause == second.cause
    assert first.explanation == second.explanation
