# Tests for the scenario comparison engine (Sprint 4).
from __future__ import annotations

import pytest

from najm3000.reporting.scenarios import (
    Scenario,
    ScenarioError,
    ScenarioOverride,
    albedo_sensitivity,
    apply_overrides,
    gcr_sensitivity,
    run_scenario_comparison,
)
from najm3000.weather.provider import SyntheticClearskyProvider

BLOCK = "test_block_a"
DAY = "2025-06-21"


# --- override application ---------------------------------------------------


def test_apply_overrides_replaces_value_and_keeps_unit(blocks_config):
    block = blocks_config.blocks[BLOCK]
    modified = apply_overrides(
        block, [ScenarioOverride("albedo", 0.40, "ASMP-005")]
    )
    assert modified.albedo.value == pytest.approx(0.40)
    assert modified.albedo.unit == block.albedo.unit


def test_apply_overrides_marks_the_value_as_assumed(blocks_config):
    modified = apply_overrides(
        blocks_config.blocks[BLOCK],
        [ScenarioOverride("gcr", 0.45, "ASMP-013")],
    )
    assert modified.gcr.provenance.data_quality_status == "Assumed"
    assert modified.gcr.provenance.assumption_id == "ASMP-013"


def test_apply_overrides_leaves_the_original_block_untouched(blocks_config):
    block = blocks_config.blocks[BLOCK]
    original = block.albedo.value
    apply_overrides(block, [ScenarioOverride("albedo", 0.99, "ASMP-005")])
    assert block.albedo.value == pytest.approx(original)


def test_apply_overrides_rejects_an_unknown_field(blocks_config):
    with pytest.raises(ScenarioError, match="not a configurable"):
        apply_overrides(
            blocks_config.blocks[BLOCK],
            [ScenarioOverride("not_a_field", 1.0, "ASMP-005")],
        )


def test_apply_overrides_rejects_a_non_parameter_field(blocks_config):
    """Counts and aliases are structural, not sensitivity parameters."""
    with pytest.raises(ScenarioError, match="not a configurable"):
        apply_overrides(
            blocks_config.blocks[BLOCK],
            [ScenarioOverride("modules_per_string", 30, "ASMP-017")],
        )


def test_apply_overrides_still_enforces_schema_validation(blocks_config):
    """An out-of-range override must fail validation, not run silently."""
    with pytest.raises(ScenarioError):
        apply_overrides(
            blocks_config.blocks[BLOCK],
            [ScenarioOverride("gcr", 1.5, "ASMP-013")],
        )


# --- comparison -------------------------------------------------------------


def test_comparison_runs_every_scenario(
    project_config, equipment_config, blocks_config, data_sources_config
):
    comparison = run_scenario_comparison(
        project=project_config,
        equipment=equipment_config,
        blocks=blocks_config,
        weather_provider=SyntheticClearskyProvider(
            config=data_sources_config.data_sources.synthetic_clearsky
        ),
        scenarios=[
            Scenario("baseline", BLOCK),
            Scenario(
                "high_albedo",
                BLOCK,
                (ScenarioOverride("albedo", 0.40, "ASMP-005"),),
            ),
        ],
        day=DAY,
    )
    assert set(comparison.energy_wh) == {"baseline", "high_albedo"}


def test_higher_albedo_increases_bifacial_energy(
    project_config, equipment_config, blocks_config, data_sources_config
):
    """Physical requirement: more ground reflection means more rear irradiance."""
    comparison = run_scenario_comparison(
        project=project_config,
        equipment=equipment_config,
        blocks=blocks_config,
        weather_provider=SyntheticClearskyProvider(
            config=data_sources_config.data_sources.synthetic_clearsky
        ),
        scenarios=[
            Scenario("low", BLOCK, (ScenarioOverride("albedo", 0.15, "ASMP-005"),)),
            Scenario("high", BLOCK, (ScenarioOverride("albedo", 0.45, "ASMP-005"),)),
        ],
        day=DAY,
    )
    assert comparison.energy_wh["high"] > comparison.energy_wh["low"]


def test_comparison_reports_delta_against_the_named_baseline(
    project_config, equipment_config, blocks_config, data_sources_config
):
    comparison = run_scenario_comparison(
        project=project_config,
        equipment=equipment_config,
        blocks=blocks_config,
        weather_provider=SyntheticClearskyProvider(
            config=data_sources_config.data_sources.synthetic_clearsky
        ),
        scenarios=[
            Scenario("baseline", BLOCK),
            Scenario(
                "high_albedo",
                BLOCK,
                (ScenarioOverride("albedo", 0.40, "ASMP-005"),),
            ),
        ],
        day=DAY,
        baseline="baseline",
    )
    frame = comparison.to_dataframe()
    baseline_row = frame.loc[frame["scenario"] == "baseline"].iloc[0]
    assert baseline_row["delta_wh"] == pytest.approx(0.0)
    assert baseline_row["delta_percent"] == pytest.approx(0.0)


def test_comparison_rejects_an_unknown_baseline_name(
    project_config, equipment_config, blocks_config, data_sources_config
):
    with pytest.raises(ScenarioError, match="baseline"):
        run_scenario_comparison(
            project=project_config,
            equipment=equipment_config,
            blocks=blocks_config,
            weather_provider=SyntheticClearskyProvider(
            config=data_sources_config.data_sources.synthetic_clearsky
        ),
            scenarios=[Scenario("only", BLOCK)],
            day=DAY,
            baseline="missing",
        )


def test_comparison_rejects_duplicate_scenario_names(
    project_config, equipment_config, blocks_config, data_sources_config
):
    with pytest.raises(ScenarioError, match="duplicate"):
        run_scenario_comparison(
            project=project_config,
            equipment=equipment_config,
            blocks=blocks_config,
            weather_provider=SyntheticClearskyProvider(
            config=data_sources_config.data_sources.synthetic_clearsky
        ),
            scenarios=[Scenario("same", BLOCK), Scenario("same", BLOCK)],
            day=DAY,
        )


def test_every_scenario_keeps_its_energy_balance_closed(
    project_config, equipment_config, blocks_config, data_sources_config
):
    comparison = run_scenario_comparison(
        project=project_config,
        equipment=equipment_config,
        blocks=blocks_config,
        weather_provider=SyntheticClearskyProvider(
            config=data_sources_config.data_sources.synthetic_clearsky
        ),
        scenarios=albedo_sensitivity(BLOCK, (0.15, 0.25)),
        day=DAY,
    )
    for result in comparison.results.values():
        # check_closure raises EnergyBalanceError if the ledger does not close.
        result.ledger.check_closure(result.block_energy_wh())


def test_comparison_markdown_refuses_to_claim_a_yield_prediction(
    project_config, equipment_config, blocks_config, data_sources_config
):
    comparison = run_scenario_comparison(
        project=project_config,
        equipment=equipment_config,
        blocks=blocks_config,
        weather_provider=SyntheticClearskyProvider(
            config=data_sources_config.data_sources.synthetic_clearsky
        ),
        scenarios=[Scenario("baseline", BLOCK)],
        day=DAY,
    )
    markdown = comparison.to_markdown()
    assert "SYNTHETIC DEMONSTRATION — NOT PRODUCTION VALIDATION" in markdown
    assert "not a yield prediction" in markdown.lower()


# --- sensitivity builders ---------------------------------------------------


def test_albedo_sensitivity_builds_one_scenario_per_value():
    scenarios = albedo_sensitivity(BLOCK, (0.15, 0.20, 0.30))
    assert len(scenarios) == 3
    assert all(s.overrides[0].field == "albedo" for s in scenarios)


def test_gcr_sensitivity_names_scenarios_by_value():
    scenarios = gcr_sensitivity(BLOCK, (0.30, 0.40))
    assert [s.name for s in scenarios] == ["gcr_0.30", "gcr_0.40"]


def test_sensitivity_builders_reject_an_empty_value_list():
    with pytest.raises(ScenarioError, match="at least one"):
        albedo_sensitivity(BLOCK, ())
