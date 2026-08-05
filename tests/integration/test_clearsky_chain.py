"""End-to-end integration test: config -> full chain -> labeled outputs."""
from __future__ import annotations

import json
from pathlib import Path

from najm3000.__main__ import main

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_clearsky_chain_produces_valid_output(block_a_result):
    ts = block_a_result.timeseries
    assert ts.index.tz is not None
    assert (ts["poa_front"] >= 0.0).all()
    assert (ts["poa_effective"] >= 0.0).all()
    assert ts["p_block"].max() > 0.0
    # midday block power below IDT rating
    assert ts["p_block"].max() < 8.0e6


def test_cli_end_to_end(tmp_path):
    exit_code = main(
        [
            "--config-dir",
            str(FIXTURES),
            "--block",
            "test_block_a",
            "--date",
            "2025-06-21",
            "--output",
            str(tmp_path),
            "--scale-plant",
        ]
    )
    assert exit_code == 0
    parquet = tmp_path / "test_block_a_2025-06-21.parquet"
    metadata_file = tmp_path / "test_block_a_2025-06-21.metadata.json"
    assert parquet.exists()
    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    assert (
        metadata["data_source_classification"] == "SYNTHETIC_SOFTWARE_TEST"
    )
    assert "NOT PRODUCTION VALIDATION" in metadata["disclaimer"]
    assert metadata["calibration_status"] == "not-calibrated"


def test_config_validate_cli():
    from najm3000.config.validate import main as validate_main

    assert validate_main(["--config-dir", str(FIXTURES)]) == 0
