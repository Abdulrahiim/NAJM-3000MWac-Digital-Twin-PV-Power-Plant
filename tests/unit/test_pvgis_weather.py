"""Tests for PVGIS public weather ingestion (PROVISIONAL_PUBLIC).

No test performs network I/O: the provider's fetcher is injected with a
recorded response captured at a neutral coordinate, never the site.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from pvlib.location import Location

from najm3000.weather.interface import (
    DataSourceClassification,
    WeatherValidationError,
)
from najm3000.weather.pvgis import (
    PVGIS_YEAR_MAX,
    PVGIS_YEAR_MIN,
    PVGISProvider,
    WeatherSourceError,
    convert_pvgis_frame,
)

FIXTURES = Path(__file__).parent.parent / "fixtures"
FIXTURE_DAY = "2023-06-21"
NEUTRAL = Location(latitude=40.0, longitude=0.0, tz="UTC", altitude=1.0)


def _raw() -> pd.DataFrame:
    frame = pd.read_csv(
        FIXTURES / "pvgis_neutral_2023.csv", index_col=0, parse_dates=True
    )
    frame.index = pd.DatetimeIndex(frame.index)
    return frame


def _fetcher(_lat: float, _lon: float, _year: int) -> tuple[pd.DataFrame, dict]:
    return _raw(), {"inputs": {"meteo_data": {"radiation_db": "PVGIS-SARAH3"}}}


def _provider(public_weather_config, **kwargs) -> PVGISProvider:
    return PVGISProvider(config=public_weather_config, fetcher=_fetcher, **kwargs)


# --- conversion -------------------------------------------------------------


def test_ghi_is_the_sum_of_beam_and_diffuse_on_the_horizontal_plane():
    raw = _raw()
    frame = convert_pvgis_frame(raw, timezone="UTC", albedo=0.2)
    expected = raw["poa_direct"] + raw["poa_sky_diffuse"]
    assert frame["ghi"].to_numpy() == pytest.approx(expected.to_numpy())


def test_dhi_is_the_sky_diffuse_component():
    raw = _raw()
    frame = convert_pvgis_frame(raw, timezone="UTC", albedo=0.2)
    assert frame["dhi"].to_numpy() == pytest.approx(
        raw["poa_sky_diffuse"].to_numpy()
    )


def test_dni_is_derived_and_never_diverges_at_low_sun():
    """A naive BHI/sin(elevation) blows up near sunrise; pvlib clamps it."""
    frame = convert_pvgis_frame(_raw(), timezone="UTC", albedo=0.2)
    assert frame["dni"].notna().all()
    assert (frame["dni"] >= 0.0).all()
    # Solar constant is ~1361 W/m2; nothing may exceed it at the surface.
    assert float(frame["dni"].max()) < 1361.0


def test_dni_is_zero_when_the_sun_is_below_the_horizon():
    raw = _raw()
    frame = convert_pvgis_frame(raw, timezone="UTC", albedo=0.2)
    night = raw["solar_elevation"] <= 0.0
    assert float(frame.loc[night, "dni"].abs().max()) == pytest.approx(0.0)


def test_conversion_rejects_a_non_horizontal_response():
    """Ground-reflected irradiance is only zero on the horizontal plane."""
    raw = _raw().copy()
    raw.loc[raw.index[12], "poa_ground_diffuse"] = 25.0
    with pytest.raises(WeatherSourceError, match="horizontal"):
        convert_pvgis_frame(raw, timezone="UTC", albedo=0.2)


def test_conversion_rejects_a_missing_column():
    raw = _raw().drop(columns=["temp_air"])
    with pytest.raises(WeatherSourceError, match="temp_air"):
        convert_pvgis_frame(raw, timezone="UTC", albedo=0.2)


def test_conversion_maps_the_pvgis_reconstruction_flag_to_quality_flag():
    raw = _raw().copy()
    raw.loc[raw.index[5], "Int"] = 1
    frame = convert_pvgis_frame(raw, timezone="UTC", albedo=0.2)
    assert frame.loc[frame.index[5], "quality_flag"] == "PVGIS_RECONSTRUCTED"
    assert frame.loc[frame.index[0], "quality_flag"] == "PVGIS_MEASURED_SATELLITE"


def test_conversion_converts_utc_to_the_project_timezone():
    frame = convert_pvgis_frame(_raw(), timezone="Asia/Riyadh", albedo=0.2)
    assert str(frame.index.tz) == "Asia/Riyadh"


def test_conversion_rejects_a_naive_index():
    raw = _raw()
    raw.index = raw.index.tz_localize(None)
    with pytest.raises(WeatherSourceError, match="timezone-aware"):
        convert_pvgis_frame(raw, timezone="UTC", albedo=0.2)


# --- provider ---------------------------------------------------------------


def test_provider_returns_a_validated_series_for_the_requested_day(
    public_weather_config,
):
    weather = _provider(public_weather_config).fetch(
        NEUTRAL, day=FIXTURE_DAY, timezone="UTC", timestep_minutes=60
    )
    assert weather.is_validated
    assert len(weather.data) == 24


def test_provider_labels_the_data_provisional_public(public_weather_config):
    weather = _provider(public_weather_config).fetch(
        NEUTRAL, day=FIXTURE_DAY, timezone="UTC", timestep_minutes=60
    )
    assert weather.classification is DataSourceClassification.PROVISIONAL_PUBLIC


def test_provider_output_cannot_be_relabeled_as_measured_site(
    public_weather_config,
):
    """Public data must never be promoted to site-measured data."""
    weather = _provider(public_weather_config).fetch(
        NEUTRAL, day=FIXTURE_DAY, timezone="UTC", timestep_minutes=60
    )
    with pytest.raises(WeatherValidationError):
        weather.relabel(DataSourceClassification.MEASURED_SITE)


def test_provider_carries_a_disclaimer_naming_the_data_as_not_site_measured(
    public_weather_config,
):
    weather = _provider(public_weather_config).fetch(
        NEUTRAL, day=FIXTURE_DAY, timezone="UTC", timestep_minutes=60
    )
    assert "NOT SITE-MEASURED" in weather.disclaimer.upper()


@pytest.mark.parametrize("year", [PVGIS_YEAR_MIN - 1, PVGIS_YEAR_MAX + 1, 2025])
def test_provider_rejects_a_year_outside_source_coverage(
    public_weather_config, year
):
    """2025-06-21 is the synthetic test day and is outside PVGIS coverage."""
    with pytest.raises(WeatherSourceError, match=r"2005"):
        _provider(public_weather_config).fetch(
            NEUTRAL, day=f"{year}-06-21", timezone="UTC", timestep_minutes=60
        )


@pytest.mark.parametrize("timestep", [15, 30, 5])
def test_provider_rejects_a_timestep_finer_than_the_source(
    public_weather_config, timestep
):
    """Interpolating hourly irradiance would invent data."""
    with pytest.raises(WeatherSourceError, match="hourly"):
        _provider(public_weather_config).fetch(
            NEUTRAL, day=FIXTURE_DAY, timezone="UTC", timestep_minutes=timestep
        )


def test_provider_rejects_a_day_absent_from_the_returned_series(
    public_weather_config,
):
    with pytest.raises(WeatherSourceError, match="no data"):
        _provider(public_weather_config).fetch(
            NEUTRAL, day="2023-01-15", timezone="UTC", timestep_minutes=60
        )


def test_provider_never_falls_back_to_synthetic_data_on_failure(
    public_weather_config,
):
    """A silent substitution would produce unlabeled data."""

    def _broken(_lat: float, _lon: float, _year: int):
        msg = "connection refused"
        raise OSError(msg)

    provider = PVGISProvider(config=public_weather_config, fetcher=_broken)
    with pytest.raises(WeatherSourceError, match="PVGIS"):
        provider.fetch(NEUTRAL, day=FIXTURE_DAY, timezone="UTC", timestep_minutes=60)


def test_provider_passes_the_requested_coordinates_to_the_fetcher(
    public_weather_config,
):
    seen: dict[str, float] = {}

    def _recording(lat: float, lon: float, year: int):
        seen.update(lat=lat, lon=lon, year=year)
        return _fetcher(lat, lon, year)

    provider = PVGISProvider(config=public_weather_config, fetcher=_recording)
    provider.fetch(NEUTRAL, day=FIXTURE_DAY, timezone="UTC", timestep_minutes=60)
    assert seen == {"lat": 40.0, "lon": 0.0, "year": 2023}
