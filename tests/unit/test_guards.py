"""Tests for the hard-fail guards: physical limits, schema rejection, labeling.

Every test here asserts that the model *refuses* to run on invalid input
rather than degrading silently.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml
from pvlib.location import Location

from najm3000.aggregation.aggregator import BlockSimulationResult
from najm3000.aggregation.loss_ledger import EnergyBalanceError, LossLedger
from najm3000.bifacial.infinite_sheds import calculate_bifacial_irradiance
from najm3000.config import validate as validate_cli
from najm3000.config.loader import (
    ConfigError,
    check_equipment_references,
    load_blocks_config,
    load_data_sources_config,
    load_equipment_config,
    load_project_config,
)
from najm3000.dc_model.pvwatts_dc import calculate_string_dc_power
from najm3000.electrical_losses.ac_cable import apply_ac_cable_loss
from najm3000.electrical_losses.dc_cable import apply_dc_cable_loss
from najm3000.inverter.idt_losses import calculate_idt_losses
from najm3000.soiling.soiling_factor import apply_soiling
from najm3000.temperature.cell_temperature import (
    CellTemperatureError,
    calculate_cell_temperature,
)
from najm3000.tracking import single_axis
from najm3000.tracking.poa_irradiance import calculate_poa_irradiance
from najm3000.tracking.single_axis import (
    TrackerLimitError,
    calculate_tracker_orientation,
)
from najm3000.tracking.solar_position import calculate_solar_position
from najm3000.validation.sanity_checks import (
    SanityCheckError,
    check_bifacial_gain,
    check_cell_temperature_bounds,
    check_dc_ge_ac,
    check_night_generation,
    check_no_negative_dc,
)
from najm3000.weather.interface import (
    DataSourceClassification,
    WeatherTimeSeries,
    WeatherValidationError,
)

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _times(tz: str | None = "Asia/Riyadh") -> pd.DatetimeIndex:
    return pd.date_range("2025-06-21 06:00", periods=4, freq="1h", tz=tz)


def _weather_frame(index: pd.DatetimeIndex) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ghi": [100.0] * len(index),
            "dni": [500.0] * len(index),
            "dhi": [50.0] * len(index),
            "temp_ambient": [30.0] * len(index),
            "wind_speed": [2.0] * len(index),
        },
        index=index,
    )


# --- timezone and weather labeling -----------------------------------------


def test_solar_position_rejects_a_naive_datetime_index():
    location = Location(latitude=24.5, longitude=45.0, tz="Asia/Riyadh")
    with pytest.raises(ValueError, match="timezone-aware"):
        calculate_solar_position(location, _times(tz=None))


def test_weather_validation_rejects_a_non_datetime_index():
    weather = WeatherTimeSeries(
        classification=DataSourceClassification.SYNTHETIC_SOFTWARE_TEST,
        data=pd.DataFrame({"ghi": [1.0]}, index=[0]),
    )
    with pytest.raises(WeatherValidationError, match="DatetimeIndex"):
        weather.validate()


def test_weather_validation_rejects_duplicate_timestamps():
    index = pd.DatetimeIndex(
        ["2025-06-21 06:00", "2025-06-21 06:00"], tz="Asia/Riyadh"
    )
    weather = WeatherTimeSeries(
        classification=DataSourceClassification.SYNTHETIC_SOFTWARE_TEST,
        data=_weather_frame(index),
    )
    with pytest.raises(WeatherValidationError, match="duplicate"):
        weather.validate()


def test_weather_validation_rejects_negative_irradiance():
    index = _times()
    frame = _weather_frame(index)
    frame.loc[frame.index[0], "ghi"] = -1.0
    weather = WeatherTimeSeries(
        classification=DataSourceClassification.SYNTHETIC_SOFTWARE_TEST,
        data=frame,
    )
    with pytest.raises(WeatherValidationError, match="negative irradiance"):
        weather.validate()


def test_weather_validation_rejects_negative_wind_speed():
    index = _times()
    frame = _weather_frame(index)
    frame.loc[frame.index[0], "wind_speed"] = -3.0
    weather = WeatherTimeSeries(
        classification=DataSourceClassification.SYNTHETIC_SOFTWARE_TEST,
        data=frame,
    )
    with pytest.raises(WeatherValidationError, match="negative wind speed"):
        weather.validate()


def test_synthetic_weather_cannot_be_relabeled_as_measured_site():
    weather = WeatherTimeSeries(
        classification=DataSourceClassification.SYNTHETIC_SOFTWARE_TEST,
        data=_weather_frame(_times()),
    )
    with pytest.raises(WeatherValidationError, match="never be reclassified"):
        weather.relabel(DataSourceClassification.MEASURED_SITE)


def test_relabeling_synthetic_as_provisional_public_is_allowed():
    weather = WeatherTimeSeries(
        classification=DataSourceClassification.SYNTHETIC_SOFTWARE_TEST,
        data=_weather_frame(_times()),
    )
    relabeled = weather.relabel(DataSourceClassification.PROVISIONAL_PUBLIC)
    assert relabeled.classification is DataSourceClassification.PROVISIONAL_PUBLIC


def test_physics_stages_refuse_unvalidated_weather(
    project_config, equipment_config, blocks_config
):
    weather = WeatherTimeSeries(
        classification=DataSourceClassification.SYNTHETIC_SOFTWARE_TEST,
        data=_weather_frame(_times()),
    )
    location = Location(latitude=24.5, longitude=45.0, tz="Asia/Riyadh")
    solar_position = calculate_solar_position(location, _times())
    block = blocks_config.blocks["test_block_a"]
    tracker = equipment_config.trackers[block.tracker]
    orientation = calculate_tracker_orientation(
        solar_position, tracker, gcr=block.gcr.value
    )
    with pytest.raises(ValueError, match="validated"):
        calculate_poa_irradiance(orientation, weather, solar_position)
    with pytest.raises(ValueError, match="validated"):
        calculate_bifacial_irradiance(
            orientation,
            solar_position,
            weather,
            block,
            equipment_config.pv_modules[block.pv_module],
            tracker,
        )


# --- physical limits --------------------------------------------------------


def test_tracker_guard_fires_if_the_model_exceeds_the_configured_limit(
    equipment_config, blocks_config, monkeypatch: pytest.MonkeyPatch
):
    """Defensive guard: an out-of-limit rotation must never reach the chain."""
    block = blocks_config.blocks["test_block_a"]
    tracker = equipment_config.trackers[block.tracker]
    location = Location(latitude=24.5, longitude=45.0, tz="Asia/Riyadh")
    solar_position = calculate_solar_position(location, _times())

    def _out_of_range(**_kwargs: object) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "tracker_theta": [999.0] * len(solar_position),
                "aoi": [0.0] * len(solar_position),
                "surface_tilt": [0.0] * len(solar_position),
                "surface_azimuth": [90.0] * len(solar_position),
            },
            index=solar_position.index,
        )

    monkeypatch.setattr(single_axis.tracking, "singleaxis", _out_of_range)
    with pytest.raises(TrackerLimitError, match="exceeds configured maximum"):
        calculate_tracker_orientation(
            solar_position, tracker, gcr=block.gcr.value
        )


def test_cell_temperature_guard_rejects_implausible_temperatures():
    index = _times()
    with pytest.raises(CellTemperatureError, match="outside plausible range"):
        calculate_cell_temperature(
            poa_global=pd.Series([50_000.0] * len(index), index=index),
            temp_ambient=pd.Series([45.0] * len(index), index=index),
            wind_speed=pd.Series([0.0] * len(index), index=index),
        )


def test_idt_loss_guard_rejects_loading_beyond_the_plausible_bound(
    equipment_config, blocks_config
):
    idt = equipment_config.idts[blocks_config.blocks["test_block_a"].idt]
    index = _times()
    overload = pd.Series([idt.rated_power_mva * 1e6 * 2.0] * len(index), index=index)
    with pytest.raises(RuntimeError, match="plausible bound"):
        calculate_idt_losses(overload, idt)


@pytest.mark.parametrize("fraction", [-0.01, 1.0, 1.5])
def test_dc_cable_loss_rejects_a_fraction_outside_the_unit_interval(fraction):
    series = pd.Series([1.0, 2.0], index=_times()[:2])
    with pytest.raises(ValueError, match="outside"):
        apply_dc_cable_loss(series, fraction)


@pytest.mark.parametrize("fraction", [-0.01, 1.0])
def test_ac_cable_loss_rejects_a_fraction_outside_the_unit_interval(fraction):
    series = pd.Series([1.0, 2.0], index=_times()[:2])
    with pytest.raises(ValueError, match="outside"):
        apply_ac_cable_loss(series, fraction)


@pytest.mark.parametrize("factor", [0.0, -0.1, 1.01])
def test_soiling_rejects_a_transmission_factor_outside_zero_to_one(factor):
    series = pd.Series([100.0, 200.0], index=_times()[:2])
    with pytest.raises(ValueError, match="outside"):
        apply_soiling(series, factor)


def test_dc_model_rejects_a_non_positive_string_length(equipment_config):
    module = next(iter(equipment_config.pv_modules.values()))
    index = _times()
    with pytest.raises(ValueError, match="must be positive"):
        calculate_string_dc_power(
            pd.Series([800.0] * len(index), index=index),
            pd.Series([45.0] * len(index), index=index),
            module,
            0,
        )


def test_loss_ledger_rejects_a_negative_loss_term():
    ledger = LossLedger(gross_energy_wh=100.0)
    with pytest.raises(EnergyBalanceError, match="negative"):
        ledger.add("impossible", -1.0)


# --- sanity checks ----------------------------------------------------------


def _result(frame: pd.DataFrame) -> BlockSimulationResult:
    return BlockSimulationResult(
        block_name="synthetic_guard_block",
        timeseries=frame,
        ledger=LossLedger(gross_energy_wh=0.0),
        metadata={},
    )


def test_sanity_check_catches_negative_dc_power():
    index = _times()
    frame = pd.DataFrame({"p_dc_string": [-1.0] * len(index)}, index=index)
    with pytest.raises(SanityCheckError, match="negative DC power"):
        check_no_negative_dc(_result(frame))


def test_sanity_check_catches_generation_at_night():
    index = _times()
    frame = pd.DataFrame({"p_ac_inverter": [500.0] * len(index)}, index=index)
    elevation = pd.Series([-10.0] * len(index), index=index)
    with pytest.raises(SanityCheckError, match="night"):
        check_night_generation(_result(frame), elevation)


def test_sanity_check_catches_ac_output_exceeding_dc_input():
    index = _times()
    frame = pd.DataFrame(
        {
            "p_ac_inverter": [1000.0] * len(index),
            "p_dc_inverter": [10.0] * len(index),
        },
        index=index,
    )
    with pytest.raises(SanityCheckError, match="exceeds DC input"):
        check_dc_ge_ac(_result(frame))


def test_sanity_check_catches_negative_rear_irradiance():
    index = _times()
    frame = pd.DataFrame({"poa_back": [-5.0] * len(index)}, index=index)
    with pytest.raises(SanityCheckError, match="negative rear"):
        check_bifacial_gain(_result(frame))


def test_sanity_check_catches_out_of_range_cell_temperature():
    index = _times()
    frame = pd.DataFrame({"temp_cell": [150.0] * len(index)}, index=index)
    with pytest.raises(SanityCheckError, match="outside"):
        check_cell_temperature_bounds(_result(frame))


# --- configuration loading --------------------------------------------------


def _fixture_yaml(name: str) -> dict:
    with (FIXTURES / name).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _write(path: Path, payload: object) -> Path:
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return path


def test_loader_rejects_a_missing_file(tmp_path: Path):
    with pytest.raises(ConfigError, match="not found"):
        load_project_config(tmp_path / "absent.yaml")


def test_loader_rejects_a_file_that_is_not_a_mapping(tmp_path: Path):
    path = tmp_path / "list.yaml"
    path.write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="did not parse to a mapping"):
        load_project_config(path)


def test_loader_rejects_a_placeholder_value(tmp_path: Path):
    payload = _fixture_yaml("project.yaml")
    payload["location"]["name"] = "PLACEHOLDER — fill me in"
    with pytest.raises(ConfigError, match="PLACEHOLDER"):
        load_project_config(_write(tmp_path / "project.yaml", payload))


def test_loader_finds_a_placeholder_nested_in_a_list(tmp_path: Path):
    path = tmp_path / "project.yaml"
    path.write_text("project:\n  aliases:\n    - PLACEHOLDER\n", encoding="utf-8")
    with pytest.raises(ConfigError, match=r"\[0\]"):
        load_project_config(path)


def test_loader_rejects_an_invalid_project_schema(tmp_path: Path):
    payload = _fixture_yaml("project.yaml")
    payload["project"]["status"] = "operational"
    with pytest.raises(ConfigError, match="project configuration invalid"):
        load_project_config(_write(tmp_path / "project.yaml", payload))


def test_loader_rejects_an_invalid_equipment_schema(tmp_path: Path):
    payload = _fixture_yaml("equipment.yaml")
    payload["pv_modules"] = {}
    payload["inverters"] = "not-a-mapping"
    with pytest.raises(ConfigError, match="equipment configuration invalid"):
        load_equipment_config(_write(tmp_path / "equipment.yaml", payload))


def test_loader_rejects_an_invalid_blocks_schema(tmp_path: Path):
    payload = _fixture_yaml("blocks.yaml")
    payload["blocks"]["test_block_a"]["modules_per_string"] = 0
    with pytest.raises(ConfigError, match="blocks configuration invalid"):
        load_blocks_config(_write(tmp_path / "blocks.yaml", payload))


def test_loader_rejects_an_invalid_data_sources_schema(tmp_path: Path):
    payload = _fixture_yaml("data_sources.yaml")
    payload["data_sources"]["synthetic_clearsky"]["authorized"] = False
    with pytest.raises(ConfigError, match="data sources configuration invalid"):
        load_data_sources_config(_write(tmp_path / "data_sources.yaml", payload))


def test_loader_rejects_a_scaling_scenario_naming_an_unknown_block(tmp_path: Path):
    payload = _fixture_yaml("blocks.yaml")
    payload["plant_scaling_scenario"]["representative_block"] = "ghost_block"
    with pytest.raises(ConfigError, match="is not a configured block"):
        load_blocks_config(_write(tmp_path / "blocks.yaml", payload))


def test_equipment_reference_check_rejects_an_unknown_alias(
    blocks_config, equipment_config
):
    block = blocks_config.blocks["test_block_a"]
    broken_block = block.model_copy(update={"inverter": "inverter_that_does_not_exist"})
    broken = blocks_config.model_copy(
        update={"blocks": {**blocks_config.blocks, "test_block_a": broken_block}}
    )
    with pytest.raises(ConfigError, match="unknown inverter alias"):
        check_equipment_references(broken, equipment_config)


# --- configuration validation CLI ------------------------------------------


def test_validate_cli_accepts_the_fixture_configuration(
    capsys: pytest.CaptureFixture[str],
):
    assert validate_cli.main(["--config-dir", str(FIXTURES)]) == 0
    assert "Configuration valid." in capsys.readouterr().out


def test_validate_cli_reports_an_invalid_configuration(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    assert validate_cli.main(["--config-dir", str(tmp_path)]) == 1
    assert "CONFIGURATION INVALID" in capsys.readouterr().err
