"""Plant configuration must reconcile with the design basis.

The design basis (SRC-026 electrical, SRC-028 I&C) states plant totals. A
configuration that does not add up to them is wrong regardless of how
self-consistent it looks, so these figures are asserted directly.

This suite exists because the configuration once carried 286 MVPS (taken from
the IDT BOQ) and a half-size Vendor B station, and nothing caught either.

These are capacity figures, not restricted identifiers: no site name, no
coordinates, no owner or document codes appear here.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from najm3000.config.loader import load_blocks_config, load_equipment_config

# --- Design basis figures (SRC-026 §2 Plant Summary; SRC-028 §Plant Summary) --

#: Number of MV power stations. Both design bases state 365.
DESIGN_MVPS_COUNT = 365

#: Facility **minimum** design capacity, DC peak. SRC-026 §2 reads "Facility
#: Minimum Design Capacity (DC peak power) 3540.003 MWp" and its objective
#: states "for rated (min) 3540.003 MWp"; SRC-028 reads "Plant Minimum Design
#: Capacity ... 3540.055 MWp". The 52 kWp difference between them is immaterial.
#:
#: This is a floor, not a target. Delivering top-bin 645 Wp modules legitimately
#: exceeds it, so DC is asserted as >= this figure rather than approximately
#: equal to it.
DESIGN_DC_MWP_MINIMUM = 3540.055

#: Upper sanity bound on DC. The module bins run 620-645 Wp, so a build cannot
#: plausibly exceed the minimum design capacity by more than the bin spread.
DC_MAXIMUM_OVERSHOOT = 0.06

#: Nominal AC power at inverter level, at 50 degC and unity power factor.
DESIGN_AC_MVA = 3228.471

#: DC/AC ratio at inverter level.
DESIGN_DC_AC_RATIO = 1.096

#: Tolerance on plant totals. Per-MVPS rounding and module bin spread make an
#: exact match implausible; anything outside this is a configuration error.
TOLERANCE = 0.02

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
LIVE_CONFIG = (CONFIG_DIR / "blocks.yaml").exists()

requires_live_config = pytest.mark.skipif(
    not LIVE_CONFIG,
    reason="live configuration is gitignored; present only on the engineering machine",
)


@pytest.fixture
def live_blocks():
    return load_blocks_config(CONFIG_DIR / "blocks.yaml")


@pytest.fixture
def live_equipment():
    return load_equipment_config(CONFIG_DIR / "equipment.yaml")


def _block_ac_mva(block, equipment) -> float:
    inverter = equipment.inverters[block.inverter]
    return (
        inverter.paco.value
        * block.inverters_per_idt
        * block.idts_per_block
        / 1e6
    )


def _block_dc_mwp(block, equipment) -> float:
    modules = (
        block.modules_per_string
        * block.strings_per_smb
        * block.smbs_per_inverter
        * block.inverters_per_idt
        * block.idts_per_block
    )
    return modules * equipment.pv_modules[block.pv_module].pdc_stc.value / 1e6


# --- plant scale ------------------------------------------------------------


@requires_live_config
def test_block_count_matches_the_design_basis_mvps_count(live_blocks):
    """365 MVPS, not the 286 from the IDT BOQ (GAP-019)."""
    assert live_blocks.plant_scaling_scenario.block_count == DESIGN_MVPS_COUNT


# --- per-MVPS capacity ------------------------------------------------------


@requires_live_config
def test_every_configured_block_carries_full_mvps_ac_capacity(
    live_blocks, live_equipment
):
    """Each MVPS is ~8.845 MVA. A half-size station is a configuration error."""
    expected = DESIGN_AC_MVA / DESIGN_MVPS_COUNT
    for name, block in live_blocks.blocks.items():
        actual = _block_ac_mva(block, live_equipment)
        assert actual == pytest.approx(expected, rel=TOLERANCE), (
            f"{name}: {actual:.3f} MVA vs design-basis {expected:.3f} MVA per MVPS"
        )


#: Band that per-MVPS DC/AC must sit inside.
#:
#: The design basis states 1.096:1 "at inverter level" as a *plant* figure —
#: total DC over total AC. It does not require every MVPS to be identical, and
#: with 28-module strings on 16-string SMBs no integer SMB count puts the
#: Vendor B station at 1.096 (4 gives 1.051, 5 gives 1.314). Individual
#: stations therefore straddle the plant average; the strict assertion belongs
#: on the plant totals, which is what the document actually pins down.
DC_AC_BAND = (1.03, 1.13)

@requires_live_config
def test_the_representative_station_meets_the_minimum_dc_capacity(
    live_blocks, live_equipment
):
    """The station that drives plant totals must clear the design floor."""
    minimum = DESIGN_DC_MWP_MINIMUM / DESIGN_MVPS_COUNT
    representative = live_blocks.blocks[
        live_blocks.plant_scaling_scenario.representative_block
    ]
    actual = _block_dc_mwp(representative, live_equipment)
    assert actual >= minimum, (
        f"representative station {actual:.3f} MWp is below the design minimum "
        f"{minimum:.3f} MWp per MVPS"
    )
    assert actual <= minimum * (1 + DC_MAXIMUM_OVERSHOOT), (
        f"representative station {actual:.3f} MWp exceeds the design minimum "
        f"{minimum:.3f} MWp by more than the module bin spread allows"
    )


@requires_live_config
def test_every_block_dc_ac_ratio_sits_inside_the_design_band(
    live_blocks, live_equipment
):
    low, high = DC_AC_BAND
    for name, block in live_blocks.blocks.items():
        ratio = _block_dc_mwp(block, live_equipment) / _block_ac_mva(
            block, live_equipment
        )
        assert low <= ratio <= high, (
            f"{name}: DC/AC {ratio:.4f} outside [{low}, {high}]; design-basis "
            f"plant average is {DESIGN_DC_AC_RATIO}"
        )


@requires_live_config
def test_the_plant_average_dc_ac_ratio_matches_the_design_basis(
    live_blocks, live_equipment
):
    """This is the figure the design basis actually states."""
    representative = live_blocks.blocks[
        live_blocks.plant_scaling_scenario.representative_block
    ]
    ratio = _block_dc_mwp(representative, live_equipment) / _block_ac_mva(
        representative, live_equipment
    )
    assert ratio == pytest.approx(DESIGN_DC_AC_RATIO, rel=TOLERANCE)


# --- plant totals -----------------------------------------------------------


@requires_live_config
def test_plant_ac_total_reconciles_with_the_design_basis(
    live_blocks, live_equipment
):
    representative = live_blocks.blocks[
        live_blocks.plant_scaling_scenario.representative_block
    ]
    total = (
        _block_ac_mva(representative, live_equipment)
        * live_blocks.plant_scaling_scenario.block_count
    )
    assert total == pytest.approx(DESIGN_AC_MVA, rel=TOLERANCE)


@requires_live_config
def test_plant_dc_total_meets_the_design_minimum(live_blocks, live_equipment):
    """DC is a stated minimum, so the build must clear it, not match it."""
    representative = live_blocks.blocks[
        live_blocks.plant_scaling_scenario.representative_block
    ]
    total = (
        _block_dc_mwp(representative, live_equipment)
        * live_blocks.plant_scaling_scenario.block_count
    )
    assert total >= DESIGN_DC_MWP_MINIMUM, (
        f"plant DC {total:,.1f} MWp is below the design minimum "
        f"{DESIGN_DC_MWP_MINIMUM:,.1f} MWp"
    )
    assert total <= DESIGN_DC_MWP_MINIMUM * (1 + DC_MAXIMUM_OVERSHOOT)


# --- transformer topology ---------------------------------------------------


@requires_live_config
def test_inverter_capacity_does_not_exceed_its_transformer(
    live_blocks, live_equipment
):
    """An MVPS may not push more AC through an IDT than the IDT is rated for."""
    for name, block in live_blocks.blocks.items():
        idt = live_equipment.idts[block.idt]
        per_idt_mva = (
            live_equipment.inverters[block.inverter].paco.value
            * block.inverters_per_idt
            / 1e6
        )
        assert per_idt_mva <= idt.rated_power_mva * (1 + TOLERANCE), (
            f"{name}: {per_idt_mva:.3f} MVA of inverters on a "
            f"{idt.rated_power_mva} MVA transformer"
        )


@requires_live_config
def test_no_block_uses_an_lv_winding_rating_as_its_station_transformer(
    live_blocks, live_equipment
):
    """4.466 MVA is the LV winding rating of the 8.932 MVA dual-winding unit.

    Keeping that rating in the equipment library is fine — it is a real
    datasheet figure. Configuring an MVPS *on* it is the error, because it
    yields a half-size station (this is what ASMP-019 originally did).
    """
    half_ratings = {
        cfg.rated_power_mva / 2
        for cfg in live_equipment.idts.values()
        if cfg.lv_windings == 2
    }
    for name, block in live_blocks.blocks.items():
        rating = live_equipment.idts[block.idt].rated_power_mva
        assert rating not in half_ratings, (
            f"block '{name}' is built on a {rating} MVA transformer, which is "
            f"the LV winding rating of a dual-winding unit, not a station "
            f"transformer"
        )
