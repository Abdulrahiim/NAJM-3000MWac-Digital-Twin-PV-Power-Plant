# Tests for the assumption report generator (Sprint 4).
from __future__ import annotations

from pathlib import Path

import pytest

from najm3000.reporting.assumption_report import (
    UNREGISTERED_RISK,
    build_assumption_report,
    parse_assumptions_register,
    parse_gap_register,
)
from najm3000.reporting.provenance_report import (
    ProvenanceRow,
    build_provenance_report,
)

FIXTURES = Path(__file__).parent.parent / "fixtures"
REPO_ROOT = Path(__file__).parent.parent.parent


def _row(
    path: str,
    status: str,
    assumption_id: str | None = None,
    gap_id: str | None = None,
    source_id: str | None = None,
) -> ProvenanceRow:
    return ProvenanceRow(
        parameter_path=path,
        value=1.0,
        unit="-",
        source_id=source_id,
        assumption_id=assumption_id,
        gap_id=gap_id,
        data_quality_status=status,
        confidence="Low",
        notes=None,
    )


# --- register parsing -------------------------------------------------------


def test_parse_assumptions_register_reads_risk_level():
    entries = parse_assumptions_register(FIXTURES / "assumptions_register.md")
    assert entries["ASMP-HIGH"].risk == "High"
    assert entries["ASMP-TEST"].risk == "Low"


def test_parse_assumptions_register_reads_resolution_status():
    entries = parse_assumptions_register(FIXTURES / "assumptions_register.md")
    assert entries["ASMP-MED"].status.startswith("Resolved")
    assert entries["ASMP-TEST"].status == "Open"


def test_parse_assumptions_register_skips_header_and_separator_rows():
    entries = parse_assumptions_register(FIXTURES / "assumptions_register.md")
    assert set(entries) == {"ASMP-TEST", "ASMP-HIGH", "ASMP-MED"}


def test_parse_gap_register_reads_priority():
    gaps = parse_gap_register(FIXTURES / "data_gap_register.md")
    assert gaps["GAP-CRIT"].priority.startswith("P1")
    assert gaps["GAP-TEST"].priority.startswith("P3")


def test_parse_register_rejects_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        parse_assumptions_register(tmp_path / "nope.md")


def test_project_registers_parse_and_are_non_empty():
    """The committed project registers must remain machine-readable."""
    entries = parse_assumptions_register(REPO_ROOT / "ASSUMPTIONS_REGISTER.md")
    gaps = parse_gap_register(REPO_ROOT / "DATA_GAP_REGISTER.md")
    assert len(entries) >= 19
    assert all(e.risk in {"High", "Medium", "Low"} for e in entries.values())
    assert len(gaps) >= 7


# --- report construction ----------------------------------------------------


def test_report_flags_assumed_parameters():
    report = build_assumption_report(
        rows=[_row("a.b", "Assumed", assumption_id="ASMP-TEST")],
        assumptions=parse_assumptions_register(
            FIXTURES / "assumptions_register.md"
        ),
        gaps=parse_gap_register(FIXTURES / "data_gap_register.md"),
    )
    assert len(report.flagged) == 1
    assert report.flagged[0].risk == "Low"


def test_report_ignores_confirmed_source_backed_parameters():
    report = build_assumption_report(
        rows=[_row("a.b", "Confirmed", source_id="SRC-001")],
        assumptions=parse_assumptions_register(
            FIXTURES / "assumptions_register.md"
        ),
        gaps=parse_gap_register(FIXTURES / "data_gap_register.md"),
    )
    assert report.flagged == []


def test_report_flags_conflicting_and_missing_parameters():
    report = build_assumption_report(
        rows=[
            _row("a.conflicting", "Conflicting", assumption_id="ASMP-HIGH"),
            _row("a.missing", "Missing", assumption_id="ASMP-MED"),
        ],
        assumptions=parse_assumptions_register(
            FIXTURES / "assumptions_register.md"
        ),
        gaps=parse_gap_register(FIXTURES / "data_gap_register.md"),
    )
    assert {f.parameter_path for f in report.flagged} == {
        "a.conflicting",
        "a.missing",
    }


def test_report_marks_unregistered_assumption_ids():
    """An ASMP id absent from the register is a governance failure, not silence."""
    report = build_assumption_report(
        rows=[_row("a.b", "Assumed", assumption_id="ASMP-999")],
        assumptions=parse_assumptions_register(
            FIXTURES / "assumptions_register.md"
        ),
        gaps=parse_gap_register(FIXTURES / "data_gap_register.md"),
    )
    assert report.flagged[0].risk == UNREGISTERED_RISK
    assert report.unregistered_ids == ["ASMP-999"]


def test_report_attaches_gap_priority_when_row_cites_a_gap():
    report = build_assumption_report(
        rows=[_row("a.b", "Conflicting", assumption_id="ASMP-HIGH", gap_id="GAP-CRIT")],
        assumptions=parse_assumptions_register(
            FIXTURES / "assumptions_register.md"
        ),
        gaps=parse_gap_register(FIXTURES / "data_gap_register.md"),
    )
    assert report.flagged[0].gap_priority == "P1 — Critical"


def test_every_flagged_parameter_carries_a_risk_level():
    report = build_assumption_report(
        rows=[
            _row("a.one", "Assumed", assumption_id="ASMP-TEST"),
            _row("a.two", "Assumed", assumption_id="ASMP-HIGH"),
            _row("a.three", "Missing", assumption_id="ASMP-404"),
        ],
        assumptions=parse_assumptions_register(
            FIXTURES / "assumptions_register.md"
        ),
        gaps=parse_gap_register(FIXTURES / "data_gap_register.md"),
    )
    assert all(f.risk for f in report.flagged)


def test_high_risk_filter_returns_only_high_risk_entries():
    report = build_assumption_report(
        rows=[
            _row("a.low", "Assumed", assumption_id="ASMP-TEST"),
            _row("a.high", "Assumed", assumption_id="ASMP-HIGH"),
        ],
        assumptions=parse_assumptions_register(
            FIXTURES / "assumptions_register.md"
        ),
        gaps=parse_gap_register(FIXTURES / "data_gap_register.md"),
    )
    assert [f.parameter_path for f in report.high_risk()] == ["a.high"]


def test_report_markdown_carries_disclaimer_and_risk_counts():
    report = build_assumption_report(
        rows=[_row("a.high", "Assumed", assumption_id="ASMP-HIGH")],
        assumptions=parse_assumptions_register(
            FIXTURES / "assumptions_register.md"
        ),
        gaps=parse_gap_register(FIXTURES / "data_gap_register.md"),
    )
    markdown = report.to_markdown()
    assert "SYNTHETIC DEMONSTRATION — NOT PRODUCTION VALIDATION" in markdown
    assert "| a.high |" in markdown
    assert "High" in markdown


def test_report_over_real_config_flags_the_assumed_parameters(
    project_config, equipment_config, blocks_config, data_sources_config
):
    provenance = build_provenance_report(
        project=project_config,
        equipment=equipment_config,
        blocks=blocks_config,
        sources=data_sources_config,
    )
    report = build_assumption_report(
        rows=provenance.rows,
        assumptions=parse_assumptions_register(
            FIXTURES / "assumptions_register.md"
        ),
        gaps=parse_gap_register(FIXTURES / "data_gap_register.md"),
    )
    assumed = [r for r in provenance.rows if r.data_quality_status == "Assumed"]
    assert len(report.flagged) == len(assumed)
