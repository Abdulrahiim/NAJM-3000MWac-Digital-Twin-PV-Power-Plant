"""Tests for the plant model backing the dashboard overview (Sprint 5).

The plant view shows many blocks. Blocks of identical configuration produce
identical model output, so an illustrative deterministic spread (ASMP-023) is
applied for presentation. These tests hold that spread to its declared bounds
and to reproducibility.
"""

from __future__ import annotations

import pytest

from najm3000.dashboard.plant import (
    BLOCK_SPREAD_ASSUMPTION_ID,
    BLOCK_SPREAD_FRACTION,
    build_plant,
    variation_factor,
)


@pytest.fixture
def plant(blocks_config):
    return build_plant(blocks_config)


# --- structure --------------------------------------------------------------


def test_block_count_comes_from_configuration(plant, blocks_config):
    assert plant.block_count == blocks_config.plant_scaling_scenario.block_count
    assert len(plant.blocks) == plant.block_count


def test_plant_reports_where_its_block_count_came_from(plant):
    """GAP-019 is unresolved; the figure used must be attributable."""
    assert plant.block_count_source
    assert "GAP-019" in plant.block_count_note


def test_plant_carries_the_scaling_label(plant, blocks_config):
    assert plant.label == blocks_config.plant_scaling_scenario.label


def test_block_ids_are_unique_and_sanitized(plant):
    import re

    ids = [b.block_id for b in plant.blocks]
    assert len(set(ids)) == len(ids)
    assert all(re.fullmatch(r"[A-Z0-9_]+", i) for i in ids)


def test_every_block_references_a_configured_block(plant, blocks_config):
    assert all(b.config_name in blocks_config.blocks for b in plant.blocks)


def test_both_equipment_configurations_appear_in_the_plant(plant, blocks_config):
    used = {b.config_name for b in plant.blocks}
    assert used == set(blocks_config.blocks)


def test_grid_positions_are_unique(plant):
    positions = [(b.row, b.column) for b in plant.blocks]
    assert len(set(positions)) == len(positions)


# --- illustrative spread (ASMP-023) ----------------------------------------


def test_spread_is_declared_against_an_assumption_id():
    assert BLOCK_SPREAD_ASSUMPTION_ID == "ASMP-023"


def test_variation_stays_within_the_declared_bounds(plant):
    for block in plant.blocks:
        assert abs(block.variation - 1.0) <= BLOCK_SPREAD_FRACTION + 1e-12


def test_variation_is_deterministic():
    """Same index must always give the same factor, so runs are reproducible."""
    assert variation_factor(17) == variation_factor(17)
    assert variation_factor(17) != variation_factor(18)


def test_variation_has_no_systematic_bias(plant):
    """The spread must not quietly inflate or deflate plant totals."""
    mean = sum(b.variation for b in plant.blocks) / len(plant.blocks)
    assert mean == pytest.approx(1.0, abs=0.005)


def test_rebuilding_the_plant_reproduces_the_same_variations(blocks_config):
    first = build_plant(blocks_config)
    second = build_plant(blocks_config)
    assert [b.variation for b in first.blocks] == [
        b.variation for b in second.blocks
    ]


# --- scaling ----------------------------------------------------------------


def test_scaling_applies_each_block_variation(plant):
    per_config = {name: 1000.0 for name in {b.config_name for b in plant.blocks}}
    scaled = plant.scale(per_config)
    assert len(scaled) == plant.block_count
    for block in plant.blocks:
        assert scaled[block.block_id] == pytest.approx(1000.0 * block.variation)


def test_plant_total_equals_the_sum_of_its_blocks(plant):
    per_config = {name: 1000.0 for name in {b.config_name for b in plant.blocks}}
    scaled = plant.scale(per_config)
    assert plant.total(per_config) == pytest.approx(sum(scaled.values()))


def test_scaling_rejects_a_missing_configuration_value(plant):
    with pytest.raises(KeyError):
        plant.scale({})
