"""Tests for demonstration fault injection (Sprint 7).

A highlighted 3D component is the most persuasive thing on the dashboard, so
these tests hold the fault layer to two promises: a fault is always chosen by
the presenter and labeled as such, and injecting one never alters the physics.
"""

from __future__ import annotations

import pytest

from najm3000.dashboard.faults import (
    FAULT_CATALOGUE,
    INJECTED_LABEL,
    FaultError,
    FaultRegistry,
)

BLOCK = "BLK_0001"


@pytest.fixture
def registry() -> FaultRegistry:
    return FaultRegistry()


# --- catalogue --------------------------------------------------------------


def test_catalogue_is_not_empty():
    assert FAULT_CATALOGUE


def test_every_fault_type_declares_a_severity_from_the_status_palette():
    allowed = {"warning", "serious", "critical"}
    for key, fault in FAULT_CATALOGUE.items():
        assert fault.severity in allowed, f"{key}: {fault.severity}"


def test_every_fault_type_names_the_assets_it_can_apply_to():
    for key, fault in FAULT_CATALOGUE.items():
        assert fault.asset_kinds, f"{key} applies to nothing"


# --- injection --------------------------------------------------------------


def test_injecting_records_the_fault(registry):
    fault = registry.inject(BLOCK, "inverter_01", "inverter_trip")
    assert fault.block_id == BLOCK
    assert fault.asset == "inverter_01"
    assert registry.count() == 1


def test_injected_fault_is_labeled_as_a_demonstration(registry):
    """It must never read as a detected alarm."""
    fault = registry.inject(BLOCK, "inverter_01", "inverter_trip")
    assert INJECTED_LABEL in fault.label.upper()
    assert "DETECT" not in fault.label.upper()


def test_severity_comes_from_the_catalogue_not_the_caller(registry):
    fault = registry.inject(BLOCK, "inverter_01", "inverter_trip")
    assert fault.severity == FAULT_CATALOGUE["inverter_trip"].severity


def test_injecting_an_unknown_fault_type_is_rejected(registry):
    with pytest.raises(FaultError, match="unknown fault type"):
        registry.inject(BLOCK, "inverter_01", "made_up_fault")


def test_injecting_onto_an_incompatible_asset_is_rejected(registry):
    """An inverter trip cannot sit on a transformer."""
    with pytest.raises(FaultError, match="cannot apply"):
        registry.inject(BLOCK, "idt_01", "inverter_trip")


def test_re_injecting_the_same_fault_replaces_rather_than_duplicates(registry):
    registry.inject(BLOCK, "inverter_01", "inverter_trip")
    registry.inject(BLOCK, "inverter_01", "inverter_trip")
    assert registry.count() == 1


def test_two_assets_can_carry_faults_at_once(registry):
    registry.inject(BLOCK, "inverter_01", "inverter_trip")
    registry.inject(BLOCK, "idt_01", "idt_over_temperature")
    assert registry.count() == 2


# --- retrieval --------------------------------------------------------------


def test_faults_are_retrievable_per_block(registry):
    registry.inject(BLOCK, "inverter_01", "inverter_trip")
    registry.inject("BLK_0002", "rmu", "rmu_communication_loss")
    assert len(registry.for_block(BLOCK)) == 1
    assert len(registry.for_block("BLK_0002")) == 1
    assert registry.for_block("BLK_0099") == []


def test_worst_severity_for_a_block_reports_the_most_serious(registry):
    registry.inject(BLOCK, "rmu", "rmu_communication_loss")
    registry.inject(BLOCK, "inverter_01", "inverter_trip")
    assert registry.worst_severity(BLOCK) == "critical"


def test_worst_severity_is_none_for_a_healthy_block(registry):
    assert registry.worst_severity(BLOCK) is None


# --- clearing ---------------------------------------------------------------


def test_clearing_one_asset_leaves_the_others(registry):
    registry.inject(BLOCK, "inverter_01", "inverter_trip")
    registry.inject(BLOCK, "idt_01", "idt_over_temperature")
    assert registry.clear(BLOCK, "inverter_01") == 1
    assert registry.count() == 1


def test_clearing_a_block_removes_all_of_its_faults(registry):
    registry.inject(BLOCK, "inverter_01", "inverter_trip")
    registry.inject(BLOCK, "idt_01", "idt_over_temperature")
    assert registry.clear(BLOCK) == 2
    assert registry.count() == 0


def test_clearing_everything_empties_the_registry(registry):
    registry.inject(BLOCK, "inverter_01", "inverter_trip")
    registry.inject("BLK_0002", "rmu", "rmu_communication_loss")
    assert registry.clear() == 2
    assert registry.count() == 0


# --- the physics must remain untouched --------------------------------------


def test_injecting_a_fault_does_not_change_the_simulation(
    project_config, equipment_config, blocks_config, data_sources_config
):
    """A fault is a presentation overlay, never a corruption of the model."""
    from najm3000.aggregation.aggregator import run_block_simulation
    from najm3000.weather.provider import SyntheticClearskyProvider

    def energy() -> float:
        result = run_block_simulation(
            project=project_config,
            equipment=equipment_config,
            blocks=blocks_config,
            weather_provider=SyntheticClearskyProvider(
                config=data_sources_config.data_sources.synthetic_clearsky
            ),
            block_name="test_block_a",
            day="2025-06-21",
        )
        result.ledger.check_closure(result.block_energy_wh())
        return result.block_energy_wh()

    before = energy()
    registry = FaultRegistry()
    registry.inject(BLOCK, "inverter_01", "inverter_trip")
    assert energy() == pytest.approx(before)
