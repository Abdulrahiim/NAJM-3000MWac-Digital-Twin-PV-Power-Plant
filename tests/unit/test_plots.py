# Tests for the engineering plots and automated loss waterfall (Sprint 4).
from __future__ import annotations

from pathlib import Path

import pytest

from najm3000 import SYNTHETIC_DISCLAIMER
from najm3000.aggregation.loss_ledger import EnergyBalanceError, LossLedger
from najm3000.reporting.plots import (
    plot_irradiance,
    plot_loss_waterfall,
    plot_power_chain,
    plot_scenario_comparison,
    plot_temperature,
    save_engineering_plots,
    waterfall_data,
)
from najm3000.reporting.scenarios import Scenario, run_scenario_comparison
from najm3000.weather.provider import SyntheticClearskyProvider

# --- waterfall data ---------------------------------------------------------


def test_waterfall_starts_at_gross_and_ends_at_net():
    ledger = LossLedger(gross_energy_wh=1000.0)
    ledger.add("dc_cable", 50.0)
    ledger.add("inverter_conversion", 150.0)
    frame = waterfall_data(ledger, net_energy_wh=800.0)
    assert frame.iloc[0]["stage"] == "gross_energy_wh"
    assert frame.iloc[0]["cumulative_wh"] == pytest.approx(1000.0)
    assert frame.iloc[-1]["stage"] == "net_block_energy"
    assert frame.iloc[-1]["cumulative_wh"] == pytest.approx(800.0)


def test_waterfall_accounts_for_every_ledger_loss():
    ledger = LossLedger(gross_energy_wh=1000.0)
    ledger.add("dc_cable", 50.0)
    ledger.add("idt_losses", 20.0)
    frame = waterfall_data(ledger, net_energy_wh=930.0)
    stages = set(frame["stage"])
    assert {"dc_cable", "idt_losses"} <= stages


def test_waterfall_losses_are_recorded_as_negative_deltas():
    ledger = LossLedger(gross_energy_wh=1000.0)
    ledger.add("dc_cable", 50.0)
    frame = waterfall_data(ledger, net_energy_wh=950.0)
    loss_row = frame.loc[frame["stage"] == "dc_cable"].iloc[0]
    assert loss_row["delta_wh"] == pytest.approx(-50.0)


def test_waterfall_reports_each_loss_as_a_share_of_gross():
    ledger = LossLedger(gross_energy_wh=1000.0)
    ledger.add("dc_cable", 50.0)
    frame = waterfall_data(ledger, net_energy_wh=950.0)
    loss_row = frame.loc[frame["stage"] == "dc_cable"].iloc[0]
    assert loss_row["percent_of_gross"] == pytest.approx(-5.0)


def test_waterfall_refuses_a_ledger_that_does_not_close():
    """A waterfall that hides missing energy would be misleading."""
    ledger = LossLedger(gross_energy_wh=1000.0)
    ledger.add("dc_cable", 50.0)
    with pytest.raises(EnergyBalanceError):
        waterfall_data(ledger, net_energy_wh=123.0)


def test_waterfall_from_a_real_simulation_closes(block_a_result):
    frame = waterfall_data(
        block_a_result.ledger, block_a_result.block_energy_wh()
    )
    assert frame.iloc[-1]["cumulative_wh"] == pytest.approx(
        block_a_result.block_energy_wh()
    )


# --- figures ----------------------------------------------------------------


def test_loss_waterfall_figure_carries_the_synthetic_disclaimer(block_a_result):
    figure = plot_loss_waterfall(block_a_result)
    assert SYNTHETIC_DISCLAIMER in figure.get_suptitle()


def test_loss_waterfall_annotates_each_loss_with_its_share_of_gross(
    block_a_result,
):
    """Loss bars are visually thin; the share must be readable as text."""
    figure = plot_loss_waterfall(block_a_result)
    annotations = [text.get_text() for text in figure.axes[0].texts]
    losses = block_a_result.ledger.losses
    assert len(annotations) == len(losses)
    assert all(text.endswith("%") for text in annotations)


def test_irradiance_plot_labels_si_units(block_a_result):
    figure = plot_irradiance(block_a_result)
    assert "W/m" in figure.axes[0].get_ylabel()
    assert SYNTHETIC_DISCLAIMER in figure.get_suptitle()


def test_temperature_plot_labels_si_units(block_a_result):
    figure = plot_temperature(block_a_result)
    assert "°C" in figure.axes[0].get_ylabel()
    assert SYNTHETIC_DISCLAIMER in figure.get_suptitle()


def test_power_chain_plot_shows_dc_and_ac_series(block_a_result):
    figure = plot_power_chain(block_a_result)
    labels = {line.get_label() for line in figure.axes[0].get_lines()}
    assert any("DC" in label for label in labels)
    assert any("AC" in label for label in labels)
    assert SYNTHETIC_DISCLAIMER in figure.get_suptitle()


def test_scenario_plot_carries_the_synthetic_disclaimer(
    project_config, equipment_config, blocks_config, data_sources_config
):
    comparison = run_scenario_comparison(
        project=project_config,
        equipment=equipment_config,
        blocks=blocks_config,
        weather_provider=SyntheticClearskyProvider(
            config=data_sources_config.data_sources.synthetic_clearsky
        ),
        scenarios=[Scenario("baseline", "test_block_a")],
        day="2025-06-21",
    )
    figure = plot_scenario_comparison(comparison)
    assert SYNTHETIC_DISCLAIMER in figure.get_suptitle()


# --- saving -----------------------------------------------------------------


def test_save_engineering_plots_writes_every_figure(
    block_a_result, tmp_path: Path
):
    paths = save_engineering_plots(block_a_result, tmp_path)
    assert len(paths) == 4
    assert all(path.exists() and path.stat().st_size > 0 for path in paths)


def test_save_engineering_plots_creates_the_output_directory(
    block_a_result, tmp_path: Path
):
    target = tmp_path / "nested" / "plots"
    paths = save_engineering_plots(block_a_result, target)
    assert target.is_dir()
    assert all(path.parent == target for path in paths)
