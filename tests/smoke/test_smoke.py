"""Reproducibility smoke test: fixed synthetic day -> identical output."""

from __future__ import annotations

import pandas as pd

from najm3000.aggregation.aggregator import run_block_simulation
from najm3000.weather.provider import SyntheticClearskyProvider

REFERENCE_DATE = "2025-06-21"


def test_clearsky_chain_reproducible(
    project_config, equipment_config, blocks_config, data_sources_config
):
    def run():
        return run_block_simulation(
            project=project_config,
            equipment=equipment_config,
            blocks=blocks_config,
            weather_provider=SyntheticClearskyProvider(
            config=data_sources_config.data_sources.synthetic_clearsky
        ),
            block_name="test_block_a",
            day=REFERENCE_DATE,
        )

    first = run()
    second = run()
    pd.testing.assert_frame_equal(first.timeseries, second.timeseries)
    assert first.ledger.as_dict() == second.ledger.as_dict()
    assert first.block_energy_wh() == second.block_energy_wh()
