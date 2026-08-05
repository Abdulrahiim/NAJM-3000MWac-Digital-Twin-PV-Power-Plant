# Tests for the provenance report generator (Sprint 4).
from __future__ import annotations

import pytest

from najm3000.config.schemas import BlocksConfig, EquipmentConfig, ProjectConfig
from najm3000.reporting.provenance_report import (
    ProvenanceReportError,
    ProvenanceRow,
    build_provenance_report,
    check_all_rows_have_provenance,
    collect_provenance,
)


def test_collect_provenance_walks_nested_models(project_config: ProjectConfig):
    rows = collect_provenance(project_config, prefix="project")
    paths = {row.parameter_path for row in rows}
    assert "project.location.latitude" in paths
    assert "project.location.altitude" in paths


def test_collect_provenance_records_value_unit_and_ids(
    project_config: ProjectConfig,
):
    rows = {r.parameter_path: r for r in collect_provenance(project_config, "project")}
    latitude = rows["project.location.latitude"]
    assert latitude.value == pytest.approx(24.5)
    assert latitude.unit == "degrees"
    assert latitude.assumption_id == "ASMP-TEST"
    assert latitude.data_quality_status == "Assumed"


def test_collect_provenance_descends_into_dict_keyed_models(
    equipment_config: EquipmentConfig,
):
    """Equipment libraries are dicts of vendor alias -> model."""
    rows = collect_provenance(equipment_config, "equipment")
    paths = {r.parameter_path for r in rows}
    assert any(p.endswith(".gamma_pdc") for p in paths)
    assert any("pv_modules." in p for p in paths)


def test_collect_provenance_never_averages_vendors(
    equipment_config: EquipmentConfig,
):
    """Each vendor alias must appear as its own row, never merged."""
    rows = collect_provenance(equipment_config, "equipment")
    module_aliases = {
        r.parameter_path.split(".")[2]
        for r in rows
        if r.parameter_path.startswith("equipment.pv_modules.")
    }
    assert len(module_aliases) == len(equipment_config.pv_modules)


def test_report_covers_every_configured_parameter(
    project_config: ProjectConfig,
    equipment_config: EquipmentConfig,
    blocks_config: BlocksConfig,
    data_sources_config,
):
    report = build_provenance_report(
        project=project_config,
        equipment=equipment_config,
        blocks=blocks_config,
        sources=data_sources_config,
    )
    assert len(report.rows) > 50
    assert all(r.unit for r in report.rows)


def test_check_provenance_rejects_row_without_source_or_assumption():
    """A row with neither ID is a provenance failure, not a warning."""
    orphan = ProvenanceRow(
        parameter_path="block.gcr",
        value=0.35,
        unit="-",
        source_id=None,
        assumption_id=None,
        gap_id=None,
        data_quality_status="Provisional",
        confidence=None,
        notes=None,
    )
    with pytest.raises(ProvenanceReportError, match="without provenance"):
        check_all_rows_have_provenance([orphan])


def test_check_provenance_accepts_rows_with_an_assumption_id():
    documented = ProvenanceRow(
        parameter_path="block.gcr",
        value=0.35,
        unit="-",
        source_id=None,
        assumption_id="ASMP-013",
        gap_id=None,
        data_quality_status="Assumed",
        confidence="Low",
        notes=None,
    )
    check_all_rows_have_provenance([documented])


def test_report_summary_counts_by_data_quality_status(
    project_config: ProjectConfig,
    equipment_config: EquipmentConfig,
    blocks_config: BlocksConfig,
    data_sources_config,
):
    report = build_provenance_report(
        project=project_config,
        equipment=equipment_config,
        blocks=blocks_config,
        sources=data_sources_config,
    )
    summary = report.summary_by_status()
    assert sum(summary.values()) == len(report.rows)
    assert "Assumed" in summary


def test_report_markdown_carries_synthetic_disclaimer(
    project_config: ProjectConfig,
    equipment_config: EquipmentConfig,
    blocks_config: BlocksConfig,
    data_sources_config,
):
    report = build_provenance_report(
        project=project_config,
        equipment=equipment_config,
        blocks=blocks_config,
        sources=data_sources_config,
    )
    markdown = report.to_markdown()
    assert "SYNTHETIC DEMONSTRATION — NOT PRODUCTION VALIDATION" in markdown
    assert "not-calibrated" in markdown
    assert "| project.location.latitude |" in markdown


def test_report_dataframe_has_one_row_per_parameter(
    project_config: ProjectConfig,
    equipment_config: EquipmentConfig,
    blocks_config: BlocksConfig,
    data_sources_config,
):
    report = build_provenance_report(
        project=project_config,
        equipment=equipment_config,
        blocks=blocks_config,
        sources=data_sources_config,
    )
    frame = report.to_dataframe()
    assert len(frame) == len(report.rows)
    assert "source_id" in frame.columns
    assert "assumption_id" in frame.columns
