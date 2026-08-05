# Tests for the viewer data layer backing the optional Streamlit dashboard.
from __future__ import annotations

from pathlib import Path

import pytest

from najm3000 import SYNTHETIC_DISCLAIMER
from najm3000.config.loader import ConfigError
from najm3000.reporting.viewer import (
    ViewerError,
    available_blocks,
    load_viewer_context,
)

FIXTURES = Path(__file__).parent.parent / "fixtures"
DAY = "2025-06-21"


def _context(block: str = "test_block_a"):
    return load_viewer_context(
        config_dir=FIXTURES,
        assumptions_register=FIXTURES / "assumptions_register.md",
        gap_register=FIXTURES / "data_gap_register.md",
        block=block,
        day=DAY,
    )


def test_available_blocks_lists_every_configured_block():
    assert set(available_blocks(FIXTURES)) == {"test_block_a", "test_block_b"}


def test_available_blocks_rejects_an_invalid_config_directory(tmp_path: Path):
    with pytest.raises(ConfigError):
        available_blocks(tmp_path)


def test_context_bundles_the_simulation_and_both_reports():
    context = _context()
    assert context.result.block_name == "test_block_a"
    assert context.provenance.rows
    assert context.assumptions.total_parameters == len(context.provenance.rows)


def test_context_carries_the_mandatory_synthetic_label():
    context = _context()
    assert context.disclaimer == SYNTHETIC_DISCLAIMER
    assert context.weather_classification == "SYNTHETIC_SOFTWARE_TEST"


def test_context_reports_not_calibrated_and_not_validated():
    context = _context()
    assert context.calibration_status == "not-calibrated"
    assert context.validation_status == "not-validated"


def test_context_waterfall_closes_against_the_simulated_energy():
    context = _context()
    assert context.waterfall.iloc[-1]["cumulative_wh"] == pytest.approx(
        context.result.block_energy_wh()
    )


def test_context_rejects_an_unknown_block():
    with pytest.raises(ViewerError, match="unknown block"):
        _context(block="no_such_block")


def test_context_rejects_a_missing_register(tmp_path: Path):
    with pytest.raises(ViewerError, match="register"):
        load_viewer_context(
            config_dir=FIXTURES,
            assumptions_register=tmp_path / "absent.md",
            gap_register=FIXTURES / "data_gap_register.md",
            block="test_block_a",
            day=DAY,
        )
