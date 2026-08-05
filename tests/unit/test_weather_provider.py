"""Tests for the pluggable weather provider layer.

The README definition of done claims the weather source can be replaced
without changing the physics engine. These tests hold that claim to account.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from najm3000.aggregation.aggregator import run_block_simulation
from najm3000.weather.interface import DataSourceClassification
from najm3000.weather.provider import SyntheticClearskyProvider
from najm3000.weather.pvgis import PVGISProvider

FIXTURES = Path(__file__).parent.parent / "fixtures"
BLOCK = "test_block_a"
SYNTHETIC_DAY = "2025-06-21"
PUBLIC_DAY = "2023-06-21"


def _fetcher(_lat: float, _lon: float, _year: int) -> tuple[pd.DataFrame, dict]:
    frame = pd.read_csv(
        FIXTURES / "pvgis_neutral_2023.csv", index_col=0, parse_dates=True
    )
    frame.index = pd.DatetimeIndex(frame.index)
    return frame, {}


# --- synthetic provider -----------------------------------------------------


def test_synthetic_provider_labels_output_as_software_test(
    data_sources_config, project_config
):
    from najm3000.aggregation.aggregator import make_location

    provider = SyntheticClearskyProvider(
        config=data_sources_config.data_sources.synthetic_clearsky
    )
    weather = provider.fetch(
        make_location(project_config),
        day=SYNTHETIC_DAY,
        timezone="Asia/Riyadh",
        timestep_minutes=30,
    )
    assert weather.classification is DataSourceClassification.SYNTHETIC_SOFTWARE_TEST
    assert weather.is_validated
    assert len(weather.data) == 48


def test_synthetic_provider_honours_the_configured_timestep(
    data_sources_config, project_config
):
    from najm3000.aggregation.aggregator import make_location

    provider = SyntheticClearskyProvider(
        config=data_sources_config.data_sources.synthetic_clearsky
    )
    weather = provider.fetch(
        make_location(project_config),
        day=SYNTHETIC_DAY,
        timezone="Asia/Riyadh",
        timestep_minutes=60,
    )
    assert len(weather.data) == 24


# --- provider substitution in the physics engine ----------------------------


def test_block_simulation_runs_with_the_synthetic_provider(
    project_config, equipment_config, blocks_config, data_sources_config
):
    result = run_block_simulation(
        project=project_config,
        equipment=equipment_config,
        blocks=blocks_config,
        weather_provider=SyntheticClearskyProvider(
            config=data_sources_config.data_sources.synthetic_clearsky
        ),
        block_name=BLOCK,
        day=SYNTHETIC_DAY,
    )
    assert result.metadata["weather_classification"] == "SYNTHETIC_SOFTWARE_TEST"
    assert result.block_energy_wh() > 0.0


def test_block_simulation_runs_with_the_public_provider(
    project_config, equipment_config, blocks_config, public_weather_config
):
    """Swapping the weather source must require no physics-engine change."""
    hourly_project = project_config.model_copy(
        update={
            "simulation": project_config.simulation.model_copy(
                update={"timestep_minutes": 60}
            )
        }
    )
    result = run_block_simulation(
        project=hourly_project,
        equipment=equipment_config,
        blocks=blocks_config,
        weather_provider=PVGISProvider(
            config=public_weather_config, fetcher=_fetcher
        ),
        block_name=BLOCK,
        day=PUBLIC_DAY,
    )
    assert result.metadata["weather_classification"] == "PROVISIONAL_PUBLIC"
    assert result.block_energy_wh() > 0.0


def test_public_run_metadata_states_the_data_is_not_site_measured(
    project_config, equipment_config, blocks_config, public_weather_config
):
    hourly_project = project_config.model_copy(
        update={
            "simulation": project_config.simulation.model_copy(
                update={"timestep_minutes": 60}
            )
        }
    )
    result = run_block_simulation(
        project=hourly_project,
        equipment=equipment_config,
        blocks=blocks_config,
        weather_provider=PVGISProvider(
            config=public_weather_config, fetcher=_fetcher
        ),
        block_name=BLOCK,
        day=PUBLIC_DAY,
    )
    assert "NOT SITE-MEASURED" in result.metadata["weather_disclaimer"].upper()
    assert result.metadata["calibration_status"] == "not-calibrated"
    assert result.metadata["validation_status"] == "not-validated"


def test_public_run_still_closes_its_energy_balance(
    project_config, equipment_config, blocks_config, public_weather_config
):
    """Real weather must not break the loss ledger."""
    hourly_project = project_config.model_copy(
        update={
            "simulation": project_config.simulation.model_copy(
                update={"timestep_minutes": 60}
            )
        }
    )
    result = run_block_simulation(
        project=hourly_project,
        equipment=equipment_config,
        blocks=blocks_config,
        weather_provider=PVGISProvider(
            config=public_weather_config, fetcher=_fetcher
        ),
        block_name=BLOCK,
        day=PUBLIC_DAY,
    )
    result.ledger.check_closure(result.block_energy_wh())


def test_public_run_produces_less_energy_than_the_clear_sky_idealisation(
    project_config, equipment_config, blocks_config, data_sources_config,
    public_weather_config,
):
    """Real skies include cloud; clear-sky synthetic is an upper idealisation."""
    hourly_project = project_config.model_copy(
        update={
            "simulation": project_config.simulation.model_copy(
                update={"timestep_minutes": 60}
            )
        }
    )
    public = run_block_simulation(
        project=hourly_project,
        equipment=equipment_config,
        blocks=blocks_config,
        weather_provider=PVGISProvider(
            config=public_weather_config, fetcher=_fetcher
        ),
        block_name=BLOCK,
        day=PUBLIC_DAY,
    )
    synthetic = run_block_simulation(
        project=hourly_project,
        equipment=equipment_config,
        blocks=blocks_config,
        weather_provider=SyntheticClearskyProvider(
            config=data_sources_config.data_sources.synthetic_clearsky
        ),
        block_name=BLOCK,
        day=SYNTHETIC_DAY,
    )
    assert public.block_energy_wh() < synthetic.block_energy_wh()


def test_block_simulation_rejects_an_unknown_block_regardless_of_provider(
    project_config, equipment_config, blocks_config, data_sources_config
):
    with pytest.raises(KeyError):
        run_block_simulation(
            project=project_config,
            equipment=equipment_config,
            blocks=blocks_config,
            weather_provider=SyntheticClearskyProvider(
                config=data_sources_config.data_sources.synthetic_clearsky
            ),
            block_name="ghost_block",
            day=SYNTHETIC_DAY,
        )
