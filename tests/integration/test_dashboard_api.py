"""Tests for the pre-commissioning dashboard API (Sprint 5).

The API is the boundary the dashboard is built against. Two properties matter
most: it never presents simulated output as measured data, and it depends on
the HistorianAdapter contract rather than on the physics engine, so the real
adapter can replace the simulated one at commissioning.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from najm3000.dashboard.api import build_app

FIXTURES = Path(__file__).parent.parent / "fixtures"
API_SOURCE = (
    Path(__file__).parent.parent.parent
    / "src"
    / "najm3000"
    / "dashboard"
    / "api.py"
)
DAY = "2025-06-21"


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(build_app(config_dir=FIXTURES, day=DAY))


# --- layer isolation --------------------------------------------------------


PHYSICS_MODULES = {
    "najm3000.aggregation.aggregator",
    "najm3000.tracking.solar_position",
    "najm3000.tracking.single_axis",
    "najm3000.tracking.poa_irradiance",
    "najm3000.bifacial.infinite_sheds",
    "najm3000.dc_model.pvwatts_dc",
    "najm3000.inverter.pvwatts_inverter",
    "najm3000.inverter.idt_losses",
    "najm3000.temperature.cell_temperature",
    "najm3000.reporting.scenarios",
}


def _imports_of(source: Path) -> set[str]:
    tree = ast.parse(source.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
        elif isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
    return found


def test_api_does_not_import_the_physics_engine():
    """The swap point is the deliverable; the API must go through the adapter."""
    direct = _imports_of(API_SOURCE)
    leaked = direct & PHYSICS_MODULES
    assert not leaked, f"API imports physics directly: {leaked}"


def test_api_does_not_reach_physics_transitively_either():
    """A local import inside a handler would defeat the boundary just as much."""
    src = API_SOURCE.parent.parent
    seen: set[str] = set()
    queue = [API_SOURCE]
    while queue:
        current = queue.pop()
        for module in _imports_of(current):
            if not module.startswith("najm3000.") or module in seen:
                continue
            seen.add(module)
            # The adapter interface is the permitted boundary; do not follow
            # the simulated implementation, which legitimately runs physics.
            if module == "najm3000.scada.simulated":
                continue
            candidate = src / Path(*module.split(".")[1:]).with_suffix(".py")
            if candidate.exists():
                queue.append(candidate)
    leaked = seen & PHYSICS_MODULES
    assert not leaked, f"API reaches physics through: {sorted(leaked)}"


# --- status -----------------------------------------------------------------


def test_status_reports_the_data_source_as_simulation(client):
    body = client.get("/api/status").json()
    assert body["is_live"] is False
    assert body["data_source"] == "SIMULATION (PRE-COMMISSIONING)"


def test_status_never_reports_measured_site(client):
    assert client.get("/api/status").json()["classification"] != "MEASURED_SITE"


def test_status_reports_not_calibrated_and_not_validated(client):
    body = client.get("/api/status").json()
    assert body["calibration_status"] == "not-calibrated"
    assert body["validation_status"] == "not-validated"


def test_status_carries_a_disclaimer_naming_it_as_not_measured(client):
    assert "NOT MEASURED" in client.get("/api/status").json()["disclaimer"].upper()


def test_status_reports_the_block_count_and_its_source(client):
    body = client.get("/api/status").json()
    assert body["block_count"] > 0
    assert "GAP-019" in body["block_count_note"]


# --- plant ------------------------------------------------------------------


def test_plant_returns_one_entry_per_block(client):
    body = client.get(f"/api/plant?t={DAY}T12:00").json()
    assert len(body["blocks"]) == body["block_count"]


def test_plant_total_equals_the_sum_of_its_blocks(client):
    body = client.get(f"/api/plant?t={DAY}T12:00").json()
    total = sum(b["ac_power_w"] for b in body["blocks"])
    assert body["plant_ac_power_w"] == pytest.approx(total)


def test_plant_produces_power_at_midday(client):
    body = client.get(f"/api/plant?t={DAY}T12:00").json()
    assert body["plant_ac_power_w"] > 0.0


def test_plant_produces_no_generation_at_night(client):
    body = client.get(f"/api/plant?t={DAY}T00:00").json()
    assert body["plant_ac_power_w"] <= 0.0


def test_plant_response_carries_classification_and_disclaimer(client):
    body = client.get(f"/api/plant?t={DAY}T12:00").json()
    assert body["classification"] != "MEASURED_SITE"
    assert body["disclaimer"]


def test_plant_labels_the_illustrative_spread(client):
    body = client.get(f"/api/plant?t={DAY}T12:00").json()
    assert body["spread_assumption_id"] == "ASMP-023"


def test_plant_rejects_a_timestamp_outside_the_simulated_day(client):
    response = client.get("/api/plant?t=2020-01-01T12:00")
    assert response.status_code == 400
    assert "available" in response.json()["detail"].lower()


# --- block detail -----------------------------------------------------------


def test_block_detail_returns_the_requested_block(client):
    body = client.get(f"/api/block/BLK_0001?t={DAY}T12:00").json()
    assert body["block_id"] == "BLK_0001"
    assert body["config_name"]


def test_block_detail_includes_the_asset_chain(client):
    body = client.get(f"/api/block/BLK_0001?t={DAY}T12:00").json()
    for key in ("poa_irradiance_w_m2", "temp_module_c", "dc_power_w", "ac_power_w"):
        assert key in body


def test_block_detail_rejects_an_unknown_block(client):
    response = client.get(f"/api/block/BLK_9999?t={DAY}T12:00")
    assert response.status_code == 404


# --- trends -----------------------------------------------------------------


def test_trends_return_a_full_day_series(client):
    body = client.get("/api/trends/BLK_0001").json()
    assert len(body["timestamps"]) > 1
    assert len(body["ac_power_w"]) == len(body["timestamps"])


def test_trends_reject_an_unknown_block(client):
    assert client.get("/api/trends/BLK_9999").status_code == 404


# --- weather ----------------------------------------------------------------


def test_weather_returns_the_panel_values(client):
    body = client.get(f"/api/weather?t={DAY}T12:00").json()
    for key in ("ghi_w_m2", "poa_w_m2", "temp_ambient_c", "wind_speed_m_s"):
        assert key in body


def test_weather_states_its_source_classification(client):
    body = client.get(f"/api/weather?t={DAY}T12:00").json()
    assert body["classification"] in {
        "SYNTHETIC_SOFTWARE_TEST",
        "PROVISIONAL_PUBLIC",
    }


# --- scenario ---------------------------------------------------------------


def test_scenario_recomputes_with_a_changed_albedo(client):
    before = client.get(f"/api/plant?t={DAY}T12:00").json()["plant_ac_power_w"]
    response = client.post("/api/scenario", json={"albedo": 0.45})
    assert response.status_code == 200
    after = client.get(f"/api/plant?t={DAY}T12:00").json()["plant_ac_power_w"]
    assert after > before
    client.post("/api/scenario", json={"albedo": 0.20})


def test_scenario_rejects_an_out_of_range_parameter(client):
    response = client.post("/api/scenario", json={"gcr": 1.5})
    assert response.status_code == 400
    assert "gcr" in response.json()["detail"].lower()


# --- 3D model and fault injection (Sprint 7) --------------------------------


def test_status_reports_the_fault_catalogue(client):
    body = client.get("/api/status").json()
    assert body["fault_catalogue"]
    assert body["injected_faults"] == 0


def test_block_model_serves_one_scene_with_tagged_groups(client):
    """One GLB holds the whole station; groups are addressed by material tag."""
    body = client.get("/api/block/BLK_0001/model").json()
    assert body["file"].startswith("/static/models/")
    assert body["file"].endswith(".glb")
    assert body["parts"]
    assert all(p["group"].startswith("NAJM_") for p in body["parts"])
    assert all(p["asset"] for p in body["parts"])


def test_block_model_states_the_model_is_representative(client):
    body = client.get("/api/block/BLK_0001/model").json()
    assert "representative" in body["note"].lower()


def test_block_model_rejects_an_unknown_block(client):
    assert client.get("/api/block/BLK_9999/model").status_code == 404


def test_injecting_a_fault_maps_it_onto_a_model_part(client):
    client.request("DELETE", "/api/fault")
    posted = client.post(
        "/api/fault",
        json={"block_id": "BLK_0001", "asset": "inverter_01",
              "fault_type": "inverter_trip"},
    )
    assert posted.status_code == 200
    body = client.get("/api/block/BLK_0001/model").json()
    faulted = [p for p in body["parts"] if p["fault"]]
    assert len(faulted) == 1
    assert faulted[0]["asset"] == "inverter_01"
    client.request("DELETE", "/api/fault")


def test_injected_fault_is_labeled_a_demonstration_over_the_api(client):
    client.request("DELETE", "/api/fault")
    body = client.post(
        "/api/fault",
        json={"block_id": "BLK_0001", "asset": "idt_01",
              "fault_type": "idt_over_temperature"},
    ).json()
    assert "INJECTED" in body["fault"]["label"].upper()
    assert body["fault"]["origin"] == "injected"
    client.request("DELETE", "/api/fault")


def test_plant_view_reports_fault_severity_per_block(client):
    client.request("DELETE", "/api/fault")
    client.post(
        "/api/fault",
        json={"block_id": "BLK_0002", "asset": "rmu",
              "fault_type": "rmu_communication_loss"},
    )
    blocks = {b["block_id"]: b for b in
              client.get(f"/api/plant?t={DAY}T12:00").json()["blocks"]}
    assert blocks["BLK_0002"]["fault_severity"] == "warning"
    assert blocks["BLK_0001"]["fault_severity"] is None
    client.request("DELETE", "/api/fault")


def test_api_rejects_an_incompatible_fault_and_asset(client):
    response = client.post(
        "/api/fault",
        json={"block_id": "BLK_0001", "asset": "idt_01",
              "fault_type": "inverter_trip"},
    )
    assert response.status_code == 400
    assert "cannot apply" in response.json()["detail"]


def test_api_rejects_a_fault_on_an_unknown_block(client):
    response = client.post(
        "/api/fault",
        json={"block_id": "BLK_9999", "asset": "inverter_01",
              "fault_type": "inverter_trip"},
    )
    assert response.status_code == 404


def test_clearing_removes_injected_faults(client):
    client.post(
        "/api/fault",
        json={"block_id": "BLK_0003", "asset": "inverter_02",
              "fault_type": "mppt_underperformance"},
    )
    assert client.request("DELETE", "/api/fault").json()["cleared"] >= 1
    assert client.get("/api/faults").json()["faults"] == []


def test_vendored_libraries_make_no_runtime_network_calls():
    """Spec-doc URLs in comments are fine; a runtime fetch is not."""
    vendor = API_SOURCE.parent / "static" / "vendor"
    if not vendor.exists():
        pytest.skip("vendor directory not present")
    for path in vendor.glob("*.js"):
        if path.name == "maplibre-gl.js":
            # The map engine performs network I/O by design: it fetches the
            # imagery tiles covered by the documented Esri exemption.
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert "XMLHttpRequest(" not in text or "loader" in path.name.lower()
        assert "importScripts(" not in text


# --- expected vs actual (Sprint 8) ------------------------------------------


def test_status_advertises_the_simulated_measurement_channel(client):
    body = client.get("/api/status").json()
    assert "SIMULATED MEASUREMENT" in body["measurement_label"].upper()
    assert body["degraded_block"]


def test_plant_view_carries_both_channels_and_a_deviation(client):
    body = client.get(f"/api/plant?t={DAY}T12:00").json()
    assert body["plant_ac_power_w"] > 0
    assert body["plant_measured_w"] > 0
    assert body["plant_deviation_percent"] is not None
    assert "SIMULATED MEASUREMENT" in body["measurement_label"].upper()


def test_measured_plant_output_runs_below_expected(client):
    """A simulated measurement that beat the physics would flatter the twin."""
    body = client.get(f"/api/plant?t={DAY}T12:00").json()
    assert body["plant_measured_w"] < body["plant_ac_power_w"]
    assert body["plant_deviation_percent"] < 0


def test_every_block_reports_its_own_deviation(client):
    blocks = client.get(f"/api/plant?t={DAY}T12:00").json()["blocks"]
    assert all("measured_w" in b for b in blocks)
    assert any(b["deviation_percent"] is not None for b in blocks)


def test_trends_include_the_measured_overlay(client):
    body = client.get("/api/trends/BLK_0001").json()
    assert len(body["measured_ac_power_w"]) == len(body["ac_power_w"])
    assert "SIMULATED MEASUREMENT" in body["measurement_label"].upper()


def test_performance_endpoint_reports_energy_deviation_and_pr(client):
    body = client.get("/api/performance/BLK_0001").json()
    assert body["expected_energy_kwh"] > 0
    assert body["measured_energy_kwh"] > 0
    assert body["deviation_percent"] < 0
    assert 0.0 < body["expected_pr"] < 1.0
    assert body["measured_pr"] < body["expected_pr"]
    assert "SIMULATED MEASUREMENT" in body["measurement_label"].upper()


def test_performance_rejects_an_unknown_block(client):
    assert client.get("/api/performance/BLK_9999").status_code == 404


def test_the_degraded_block_shows_the_worst_deviation(client):
    degraded = client.get("/api/status").json()["degraded_block"]
    blocks = client.get(f"/api/plant?t={DAY}T12:00").json()["blocks"]
    deviations = {
        b["block_id"]: b["deviation_percent"]
        for b in blocks
        if b["deviation_percent"] is not None
    }
    assert deviations[degraded] == min(deviations.values())


# --- live operations preview (Sprint 9) -------------------------------------


@pytest.fixture(scope="module")
def demo_client() -> TestClient:
    """A client with the scripted demonstration scenario enabled."""
    return TestClient(
        build_app(config_dir=FIXTURES, day=DAY, scenario_enabled=True)
    )


def test_the_scenario_is_off_unless_asked_for(client):
    assert client.get("/api/status").json()["scenario_enabled"] is False


def test_the_scenario_raises_faults_as_the_clock_advances(demo_client):
    demo_client.get(f"/api/plant?t={DAY}T00:30")
    early = demo_client.get("/api/alarms").json()["count"]
    demo_client.get(f"/api/plant?t={DAY}T20:00")
    later = demo_client.get("/api/alarms").json()["count"]
    assert later > early


def test_the_alarm_log_is_newest_first_and_labelled(demo_client):
    demo_client.get(f"/api/plant?t={DAY}T20:00")
    body = demo_client.get("/api/alarms").json()
    assert body["count"] > 0
    assert all("INJECTED" in a["label"].upper() for a in body["alarms"])
    assert all(a["origin"] == "injected" for a in body["alarms"])


def test_diagnostics_report_a_healthy_station_as_healthy(client):
    client.request("DELETE", "/api/fault")
    body = client.get("/api/diagnostics/BLK_0001").json()
    assert body["healthy"] is True
    assert body["finding"] is None


def test_diagnostics_identify_an_inverter_trip_without_being_told(client):
    """The engine sees signals only; the cause is inferred."""
    client.request("DELETE", "/api/fault")
    client.post(
        "/api/fault",
        json={"block_id": "BLK_0001", "asset": "inverter_01",
              "fault_type": "inverter_trip"},
    )
    finding = client.get("/api/diagnostics/BLK_0001").json()["finding"]
    assert finding is not None
    assert finding["cause"] in {"single_inverter_outage", "inverter_offline"}
    assert finding["evidence"]
    assert finding["confidence"] in {"High", "Medium", "Low"}
    client.request("DELETE", "/api/fault")


def test_diagnostics_identify_a_communications_dropout(client):
    client.request("DELETE", "/api/fault")
    client.post(
        "/api/fault",
        json={"block_id": "BLK_0002", "asset": "rmu",
              "fault_type": "rmu_communication_loss"},
    )
    finding = client.get("/api/diagnostics/BLK_0002").json()["finding"]
    assert finding is not None
    assert finding["cause"] == "intermittent_reporting"
    client.request("DELETE", "/api/fault")


def test_every_diagnosis_states_it_came_from_simulated_signals(client):
    client.request("DELETE", "/api/fault")
    client.post(
        "/api/fault",
        json={"block_id": "BLK_0001", "asset": "inverter_01",
              "fault_type": "inverter_trip"},
    )
    finding = client.get("/api/diagnostics/BLK_0001").json()["finding"]
    assert "SIMULATED" in finding["basis"].upper()
    assert "not ML" in finding["basis"] or "rule-based" in finding["basis"]
    client.request("DELETE", "/api/fault")


def test_diagnostics_reject_an_unknown_block(client):
    assert client.get("/api/diagnostics/BLK_9999").status_code == 404
