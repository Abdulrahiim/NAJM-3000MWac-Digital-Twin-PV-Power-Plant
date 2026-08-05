# Integration tests for the reporting CLI (Sprint 4).
from __future__ import annotations

from pathlib import Path

import pytest

from najm3000 import SYNTHETIC_DISCLAIMER
from najm3000.reporting.__main__ import main

FIXTURES = Path(__file__).parent.parent / "fixtures"
DAY = "2025-06-21"


def _argv(output: Path, *extra: str) -> list[str]:
    return [
        "--config-dir",
        str(FIXTURES),
        "--assumptions-register",
        str(FIXTURES / "assumptions_register.md"),
        "--gap-register",
        str(FIXTURES / "data_gap_register.md"),
        "--block",
        "test_block_a",
        "--date",
        DAY,
        "--output",
        str(output),
        *extra,
    ]


def test_cli_writes_all_report_artifacts(tmp_path: Path):
    assert main(_argv(tmp_path)) == 0
    assert (tmp_path / "provenance_report.md").exists()
    assert (tmp_path / "provenance_report.csv").exists()
    assert (tmp_path / "assumption_report.md").exists()
    assert (tmp_path / "loss_waterfall.csv").exists()
    assert len(list((tmp_path / "plots").glob("*.png"))) == 4


def test_generated_reports_carry_the_synthetic_disclaimer(tmp_path: Path):
    main(_argv(tmp_path))
    for name in ("provenance_report.md", "assumption_report.md"):
        text = (tmp_path / name).read_text(encoding="utf-8")
        assert SYNTHETIC_DISCLAIMER in text


def test_reports_never_claim_calibration_or_validation(tmp_path: Path):
    main(_argv(tmp_path))
    for path in tmp_path.glob("*.md"):
        text = (tmp_path / path.name).read_text(encoding="utf-8").lower()
        assert "calibrated against" not in text
        assert "validated against measured" not in text
        assert "predicted production" not in text


def test_cli_writes_scenario_comparison_when_requested(tmp_path: Path):
    assert main(_argv(tmp_path, "--sensitivity", "albedo")) == 0
    report = tmp_path / "scenario_comparison.md"
    assert report.exists()
    assert "not a yield prediction" in report.read_text(encoding="utf-8").lower()
    assert (tmp_path / "plots" / "scenario_comparison.png").exists()


def test_cli_skips_scenario_comparison_by_default(tmp_path: Path):
    main(_argv(tmp_path))
    assert not (tmp_path / "scenario_comparison.md").exists()


def test_cli_reports_invalid_configuration_without_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    exit_code = main(
        [
            "--config-dir",
            str(tmp_path / "missing"),
            "--block",
            "test_block_a",
            "--date",
            DAY,
            "--output",
            str(tmp_path / "out"),
        ]
    )
    assert exit_code == 1
    assert "CONFIGURATION INVALID" in capsys.readouterr().err


def test_cli_rejects_an_unknown_block(tmp_path: Path):
    exit_code = main(_argv(tmp_path, "--block", "no_such_block"))
    assert exit_code == 1


def test_cli_rejects_a_missing_register_file(tmp_path: Path):
    exit_code = main(
        [
            "--config-dir",
            str(FIXTURES),
            "--assumptions-register",
            str(tmp_path / "absent.md"),
            "--block",
            "test_block_a",
            "--date",
            DAY,
            "--output",
            str(tmp_path / "out"),
        ]
    )
    assert exit_code == 1


def test_provenance_csv_lists_every_parameter(tmp_path: Path):
    main(_argv(tmp_path))
    text = (tmp_path / "provenance_report.csv").read_text(encoding="utf-8")
    assert "parameter_path" in text.splitlines()[0]
    assert "project.location.latitude" in text
