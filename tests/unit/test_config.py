"""Schema validation tests (testing_strategy.md category 1, 8, 11)."""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from najm3000.config.loader import (
    ConfigError,
    check_equipment_references,
    load_project_config,
)
from najm3000.config.schemas import ProjectConfig

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _load_raw(name: str) -> dict:
    with (FIXTURES / name).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_valid_project_config(project_config):
    assert project_config.project.name == "NAJM-3000"
    assert project_config.project.status == "pre-operational"
    assert project_config.project.calibration_status == "not-calibrated"


def test_invalid_latitude():
    raw = _load_raw("project.yaml")
    raw["location"]["latitude"]["value"] = 95.0
    with pytest.raises(ValueError, match="latitude"):
        ProjectConfig.model_validate(raw)


def test_invalid_timezone():
    raw = _load_raw("project.yaml")
    raw["location"]["timezone"] = "Not/AZone"
    with pytest.raises(ValueError, match="IANA"):
        ProjectConfig.model_validate(raw)


def test_missing_provenance_rejected():
    raw = _load_raw("project.yaml")
    raw["location"]["latitude"]["provenance"] = {
        "data_quality_status": "Assumed"
    }
    with pytest.raises(ValueError, match="source_id"):
        ProjectConfig.model_validate(raw)


def test_placeholder_value_rejected(tmp_path):
    raw = _load_raw("project.yaml")
    raw["location"]["altitude"]["value"] = "PLACEHOLDER_ALTITUDE"
    bad = tmp_path / "project.yaml"
    bad.write_text(yaml.safe_dump(raw), encoding="utf-8")
    with pytest.raises(ConfigError, match="PLACEHOLDER"):
        load_project_config(bad)


def test_operational_status_rejected():
    raw = _load_raw("project.yaml")
    raw["project"]["status"] = "operational"
    with pytest.raises(ValueError, match="pre-operational"):
        ProjectConfig.model_validate(raw)


def test_unknown_equipment_alias_rejected(equipment_config):
    raw = _load_raw("blocks.yaml")
    raw = copy.deepcopy(raw)
    raw["blocks"]["test_block_a"]["pv_module"] = "nope"
    from najm3000.config.schemas import BlocksConfig

    broken = BlocksConfig.model_validate(raw)
    with pytest.raises(ConfigError, match="unknown pv_module"):
        check_equipment_references(broken, equipment_config)


def test_all_key_params_have_provenance(equipment_config):
    for module in equipment_config.pv_modules.values():
        for param in (
            module.pdc_stc,
            module.gamma_pdc,
            module.bifaciality,
        ):
            prov = param.provenance
            assert prov.source_id or prov.assumption_id
