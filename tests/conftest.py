# conftest.py — NAJM-3000 Digital Twin shared test fixtures.
from __future__ import annotations

from pathlib import Path

import pytest

from najm3000.aggregation.aggregator import (
    BlockSimulationResult,
    run_block_simulation,
)
from najm3000.config.loader import (
    load_blocks_config,
    load_data_sources_config,
    load_equipment_config,
    load_project_config,
)
from najm3000.config.schemas import (
    BlocksConfig,
    DataSourcesFile,
    EquipmentConfig,
    ProjectConfig,
    PublicWeatherConfig,
)
from najm3000.weather.provider import SyntheticClearskyProvider

FIXTURES = Path(__file__).parent / "fixtures"
TEST_DAY = "2025-06-21"


@pytest.fixture(scope="session")
def project_config() -> ProjectConfig:
    return load_project_config(FIXTURES / "project.yaml")


@pytest.fixture(scope="session")
def equipment_config() -> EquipmentConfig:
    return load_equipment_config(FIXTURES / "equipment.yaml")


@pytest.fixture(scope="session")
def blocks_config() -> BlocksConfig:
    return load_blocks_config(FIXTURES / "blocks.yaml")


@pytest.fixture(scope="session")
def data_sources_config() -> DataSourcesFile:
    return load_data_sources_config(FIXTURES / "data_sources.yaml")


@pytest.fixture(scope="session")
def public_weather_config(
    data_sources_config: DataSourcesFile,
) -> PublicWeatherConfig:
    """PROVISIONAL_PUBLIC (PVGIS) source configuration from the fixture file."""
    config = data_sources_config.data_sources.public_pvgis
    assert config is not None, "fixture must define a public_pvgis source"
    return config


@pytest.fixture(scope="session")
def block_a_result(
    project_config: ProjectConfig,
    equipment_config: EquipmentConfig,
    blocks_config: BlocksConfig,
    data_sources_config: DataSourcesFile,
) -> BlockSimulationResult:
    """One full simulation of the vendor-A test block, shared across tests."""
    return run_block_simulation(
        project=project_config,
        equipment=equipment_config,
        blocks=blocks_config,
        weather_provider=SyntheticClearskyProvider(
            config=data_sources_config.data_sources.synthetic_clearsky
        ),
        block_name="test_block_a",
        day=TEST_DAY,
    )


@pytest.fixture(scope="session")
def block_b_result(
    project_config: ProjectConfig,
    equipment_config: EquipmentConfig,
    blocks_config: BlocksConfig,
    data_sources_config: DataSourcesFile,
) -> BlockSimulationResult:
    """One full simulation of the vendor-B test block."""
    return run_block_simulation(
        project=project_config,
        equipment=equipment_config,
        blocks=blocks_config,
        weather_provider=SyntheticClearskyProvider(
            config=data_sources_config.data_sources.synthetic_clearsky
        ),
        block_name="test_block_b",
        day=TEST_DAY,
    )
