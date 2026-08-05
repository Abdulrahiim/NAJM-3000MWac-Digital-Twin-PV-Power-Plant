"""Runs the optional Streamlit viewer end-to-end via Streamlit's AppTest.

Verifies the UI shell actually executes and carries the mandatory labeling.
Skipped when streamlit is not installed (it is an optional ``viewer`` extra).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from najm3000 import SYNTHETIC_DISCLAIMER

AppTest = pytest.importorskip(
    "streamlit.testing.v1", reason="streamlit not installed (optional extra)"
).AppTest

FIXTURES = Path(__file__).parent.parent / "fixtures"
VIEWER = Path(__file__).parent.parent.parent / "notebooks" / "streamlit_viewer.py"


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("NAJM3000_CONFIG_DIR", str(FIXTURES))
    monkeypatch.setenv(
        "NAJM3000_ASSUMPTIONS_REGISTER", str(FIXTURES / "assumptions_register.md")
    )
    monkeypatch.setenv(
        "NAJM3000_GAP_REGISTER", str(FIXTURES / "data_gap_register.md")
    )
    monkeypatch.setenv("NAJM3000_DAY", "2025-06-21")
    return AppTest.from_file(str(VIEWER), default_timeout=120).run()


def test_viewer_runs_without_raising(app):
    assert not app.exception


def test_viewer_shows_the_synthetic_disclaimer(app):
    banner = " ".join(element.value for element in app.error)
    assert SYNTHETIC_DISCLAIMER in banner


def test_viewer_states_not_calibrated_and_not_validated(app):
    values = {metric.value for metric in app.metric}
    assert "not-calibrated" in values
    assert "not-validated" in values


def test_viewer_labels_the_weather_source_as_synthetic(app):
    values = {metric.value for metric in app.metric}
    assert "SYNTHETIC_SOFTWARE_TEST" in values


def test_viewer_lists_every_configured_block(app):
    assert set(app.selectbox[0].options) == {"test_block_a", "test_block_b"}


def test_viewer_reports_an_invalid_configuration_instead_of_crashing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setenv("NAJM3000_CONFIG_DIR", str(tmp_path))
    result = AppTest.from_file(str(VIEWER), default_timeout=120).run()
    assert not result.exception
    assert any("Configuration invalid" in e.value for e in result.error)
