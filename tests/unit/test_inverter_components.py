"""Component-level tests for the inverter and IDT models (categories 4, 6)."""
from __future__ import annotations

import pandas as pd
import pytest

from najm3000.inverter.idt_losses import calculate_idt_losses
from najm3000.inverter.pvwatts_inverter import calculate_inverter_output


@pytest.fixture
def index():
    return pd.date_range(
        "2025-06-21 00:00", periods=8, freq="3h", tz="Asia/Riyadh"
    )


def test_mppt_window_low_zeroes_output(equipment_config, index):
    inverter = equipment_config.inverters["inverter_vendor_a_model_1"]
    p_dc = pd.Series(1e6, index=index)
    voltage = pd.Series(500.0, index=index)  # below mppt_low = 900 V
    result = calculate_inverter_output(p_dc, voltage, inverter)
    # all DC is rejected by the MPPT window -> treated as night/standby
    assert (result.mppt_loss == 1e6).all()
    assert (result.p_ac <= 0.0).all()


def test_mppt_window_high_zeroes_output(equipment_config, index):
    inverter = equipment_config.inverters["inverter_vendor_a_model_1"]
    p_dc = pd.Series(1e6, index=index)
    voltage = pd.Series(1600.0, index=index)  # above mppt_high = 1500 V
    result = calculate_inverter_output(p_dc, voltage, inverter)
    assert (result.mppt_loss == 1e6).all()


def test_clipping_at_high_dc(equipment_config, index):
    inverter = equipment_config.inverters["inverter_vendor_a_model_1"]
    p_dc = pd.Series(10e6, index=index)  # far above pdc0
    voltage = pd.Series(1200.0, index=index)
    result = calculate_inverter_output(p_dc, voltage, inverter)
    assert (result.p_ac == inverter.paco.value).all()
    assert result.clipping_loss.sum() > 0.0


def test_night_draw(equipment_config, index):
    inverter = equipment_config.inverters["inverter_vendor_a_model_1"]
    p_dc = pd.Series(0.0, index=index)
    voltage = pd.Series(0.0, index=index)
    result = calculate_inverter_output(p_dc, voltage, inverter)
    assert (result.p_ac == -inverter.night_power.value).all()
    assert (result.night_consumption == inverter.night_power.value).all()


def test_idt_losses_increase_with_load(equipment_config, index):
    idt = equipment_config.idts["idt_vendor_a_8_932_mva"]
    low = pd.Series(1e6, index=index)
    high = pd.Series(7e6, index=index)
    loss_low = calculate_idt_losses(low, idt).p_loss.iloc[0]
    loss_high = calculate_idt_losses(high, idt).p_loss.iloc[0]
    assert loss_high > loss_low > idt.p_no_load.value - 1e-9


def test_idt_no_load_at_zero_power(equipment_config, index):
    idt = equipment_config.idts["idt_vendor_a_8_932_mva"]
    zero = pd.Series(0.0, index=index)
    result = calculate_idt_losses(zero, idt)
    assert (result.p_loss == idt.p_no_load.value).all()
    assert (result.p_out == -idt.p_no_load.value).all()
