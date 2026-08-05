"""Weather interface and synthetic generation tests (categories 3, 9)."""
from __future__ import annotations

import pytest

from najm3000 import SYNTHETIC_DISCLAIMER
from najm3000.aggregation.aggregator import make_location
from najm3000.weather.interface import (
    DataSourceClassification,
    WeatherTimeSeries,
    WeatherValidationError,
)
from najm3000.weather.synthetic import build_times, generate_clearsky_weather

TEST_DAY = "2025-06-21"


@pytest.fixture(scope="module")
def weather(project_config, data_sources_config):
    location = make_location(project_config)
    times = build_times(TEST_DAY, project_config.location.timezone, 30)
    return generate_clearsky_weather(
        location, times, data_sources_config.data_sources.synthetic_clearsky
    )


def test_synthetic_label_and_disclaimer(weather):
    assert (
        weather.classification
        is DataSourceClassification.SYNTHETIC_SOFTWARE_TEST
    )
    assert SYNTHETIC_DISCLAIMER in weather.disclaimer
    assert weather.is_validated


def test_output_timestamps_have_tz(weather):
    assert weather.data.index.tz is not None
    assert str(weather.data.index.tz) == "Asia/Riyadh"


def test_irradiance_non_negative(weather):
    for column in ("ghi", "dni", "dhi"):
        assert (weather.data[column] >= 0.0).all()


def test_night_irradiance_zero(weather):
    midnight = weather.data.between_time("00:00", "03:00")
    assert (midnight["ghi"] == 0.0).all()


def test_naive_index_rejected(weather):
    naive = weather.data.copy()
    naive.index = naive.index.tz_localize(None)
    bad = WeatherTimeSeries(
        classification=DataSourceClassification.SYNTHETIC_SOFTWARE_TEST,
        data=naive,
        disclaimer=SYNTHETIC_DISCLAIMER,
    )
    with pytest.raises(WeatherValidationError, match="timezone-aware"):
        bad.validate()


def test_missing_column_rejected(weather):
    bad = WeatherTimeSeries(
        classification=DataSourceClassification.SYNTHETIC_SOFTWARE_TEST,
        data=weather.data.drop(columns=["wind_speed"]),
        disclaimer=SYNTHETIC_DISCLAIMER,
    )
    with pytest.raises(WeatherValidationError, match="wind_speed"):
        bad.validate()


def test_synthetic_cannot_become_measured(weather):
    with pytest.raises(WeatherValidationError, match="never"):
        weather.relabel(DataSourceClassification.MEASURED_SITE)


def test_missing_disclaimer_rejected(weather):
    bad = WeatherTimeSeries(
        classification=DataSourceClassification.SYNTHETIC_SOFTWARE_TEST,
        data=weather.data,
        disclaimer="",
    )
    with pytest.raises(WeatherValidationError, match="disclaimer"):
        bad.validate()
