"""Integration tests for the block simulation CLI and weather selection."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from najm3000.__main__ import main

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _argv(output: Path, *extra: str) -> list[str]:
    return [
        "--config-dir",
        str(FIXTURES),
        "--block",
        "test_block_a",
        "--date",
        "2025-06-21",
        "--output",
        str(output),
        *extra,
    ]


def test_cli_runs_the_synthetic_source_by_default(tmp_path: Path):
    assert main(_argv(tmp_path)) == 0
    meta = json.loads(
        (tmp_path / "test_block_a_2025-06-21.metadata.json").read_text(
            encoding="utf-8"
        )
    )
    assert meta["data_source_classification"] == "SYNTHETIC_SOFTWARE_TEST"


def test_cli_records_the_weather_source_in_metadata(tmp_path: Path):
    main(_argv(tmp_path))
    meta = json.loads(
        (tmp_path / "test_block_a_2025-06-21.metadata.json").read_text(
            encoding="utf-8"
        )
    )
    assert meta["weather_source"] == "synthetic_clearsky"


def test_cli_timestep_override_changes_the_series_length(tmp_path: Path):
    """One config must be able to serve both hourly and sub-hourly sources."""
    assert main(_argv(tmp_path, "--timestep-minutes", "60")) == 0
    meta = json.loads(
        (tmp_path / "test_block_a_2025-06-21.metadata.json").read_text(
            encoding="utf-8"
        )
    )
    assert meta["timestep_minutes"] == "60"


def test_cli_reports_a_weather_source_error_without_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """PVGIS is hourly; a 10-minute request must fail cleanly, not crash."""
    exit_code = main(
        _argv(
            tmp_path,
            "--weather",
            "public_pvgis",
            "--date",
            "2023-06-21",
            "--timestep-minutes",
            "10",
        )
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "WEATHER SOURCE" in captured.err
    assert "Traceback" not in captured.err


def test_cli_refuses_a_public_source_that_is_not_configured(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch
):
    """Never silently fall back to synthetic data."""
    import yaml

    raw = yaml.safe_load((FIXTURES / "data_sources.yaml").read_text(encoding="utf-8"))
    del raw["data_sources"]["public_pvgis"]
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    for name in ("project.yaml", "equipment.yaml", "blocks.yaml"):
        (config_dir / name).write_text(
            (FIXTURES / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    (config_dir / "data_sources.yaml").write_text(
        yaml.safe_dump(raw), encoding="utf-8"
    )

    exit_code = main(
        [
            "--config-dir",
            str(config_dir),
            "--block",
            "test_block_a",
            "--date",
            "2023-06-21",
            "--output",
            str(tmp_path / "out"),
            "--weather",
            "public_pvgis",
        ]
    )
    assert exit_code == 1
    assert "approval" in capsys.readouterr().err.lower()


def _public_fetcher(_lat: float, _lon: float, _year: int):
    import pandas as pd

    frame = pd.read_csv(
        FIXTURES / "pvgis_neutral_2023.csv", index_col=0, parse_dates=True
    )
    frame.index = pd.DatetimeIndex(frame.index)
    return frame, {}


def _public_argv(output: Path) -> list[str]:
    return _argv(
        output,
        "--weather",
        "public_pvgis",
        "--date",
        "2023-06-21",
        "--timestep-minutes",
        "60",
    )


def test_synthetic_run_is_labeled_as_a_synthetic_demonstration(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    main(_argv(tmp_path))
    assert "SYNTHETIC DEMONSTRATION" in capsys.readouterr().out


def test_public_data_run_is_not_labeled_synthetic(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch
):
    """Real satellite data must not be described as a synthetic demonstration."""
    from najm3000.weather import pvgis

    monkeypatch.setattr(pvgis, "_fetch_from_pvgis", _public_fetcher)
    assert main(_public_argv(tmp_path)) == 0
    out = capsys.readouterr().out
    assert "SYNTHETIC DEMONSTRATION" not in out
    assert "NOT SITE-MEASURED" in out.upper()


def test_public_run_metadata_does_not_claim_synthetic_data(
    tmp_path: Path, monkeypatch
):
    from najm3000.weather import pvgis

    monkeypatch.setattr(pvgis, "_fetch_from_pvgis", _public_fetcher)
    main(_public_argv(tmp_path))
    meta = json.loads(
        (tmp_path / "test_block_a_2023-06-21.metadata.json").read_text(
            encoding="utf-8"
        )
    )
    assert meta["data_source_classification"] == "PROVISIONAL_PUBLIC"
    assert "SYNTHETIC DEMONSTRATION" not in meta["disclaimer"]
