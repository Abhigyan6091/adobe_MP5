"""
tests/test_prerequisites.py
Tests for prerequisite validation: missing courses and cycle detection.
All test data is synthetic and does NOT represent real institutional records.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest import IngestResult
from src.normalize import run_normalise
from src.validate import run_validate, _detect_cycles
from tests.conftest import (
    VALID_RULES_RAW, VALID_RESOURCES_RAW, VALID_SKILLS_RAW,
    VALID_COURSE_SKILL_LINKS_RAW, VALID_RESOURCE_SKILL_LINKS_RAW,
)


def _make_ingest_with_courses(courses_raw) -> IngestResult:
    result = IngestResult()
    result.courses_raw = courses_raw
    result.rules_raw = VALID_RULES_RAW
    result.resources_raw = VALID_RESOURCES_RAW
    result.skills_raw = VALID_SKILLS_RAW
    result.course_skill_links_raw = VALID_COURSE_SKILL_LINKS_RAW
    result.resource_skill_links_raw = VALID_RESOURCE_SKILL_LINKS_RAW
    return result


# ---------------------------------------------------------------------------
# Cycle detection unit tests
# ---------------------------------------------------------------------------

class TestCycleDetection:
    def test_no_cycle(self):
        edges = {"A": ["B"], "B": ["C"]}
        assert _detect_cycles(edges) == []

    def test_simple_cycle(self):
        edges = {"A": ["B"], "B": ["A"]}
        cycles = _detect_cycles(edges)
        assert len(cycles) >= 1

    def test_self_loop(self):
        edges = {"A": ["A"]}
        cycles = _detect_cycles(edges)
        assert len(cycles) >= 1

    def test_triangle_cycle(self):
        edges = {"A": ["B"], "B": ["C"], "C": ["A"]}
        cycles = _detect_cycles(edges)
        assert len(cycles) >= 1

    def test_no_cycle_with_multiple_paths(self):
        edges = {"A": ["B", "C"], "B": ["D"], "C": ["D"]}
        assert _detect_cycles(edges) == []


# ---------------------------------------------------------------------------
# Integration: missing prerequisite
# ---------------------------------------------------------------------------

class TestMissingPrerequisite:
    def test_missing_prereq_raises_error(self):
        """
        SYNTHETIC TEST: TST_B requires TST_A, but TST_A is not in the catalogue.
        """
        courses_raw = [
            {
                "course_code": "TSTB",
                "title": "Synthetic Course B",
                "department": "Test",
                "credits": 3,
                "semester": 2,
                "course_type_original": "Core",
                "original_category": "Programme Core",
                "mode": "not_stated",
                "objectives": "Synthetic objective.",
                "syllabus": "Synthetic syllabus.",
                "hard_prerequisites": ["TSTA"],   # TSTA does not exist!
                "recommended_prerequisites": [],
                "source_url": "https://example.test",
                "retrieved_on": "2026-01-01",
                "source_type": "official",
                "verification_status": "verified",
            }
        ]
        ingest = _make_ingest_with_courses(courses_raw)
        norm = run_normalise(ingest)
        val = run_validate(norm)
        errors = [e for e in val.errors if e.check_id == "CHK_006"]
        assert len(errors) >= 1, "Expected CHK_006 error for missing prerequisite TSTA"

    def test_valid_prereq_no_error(self):
        """
        SYNTHETIC TEST: Both courses present; no CHK_006 error expected.
        """
        courses_raw = [
            {
                "course_code": "TSTA",
                "title": "Synthetic Course A",
                "department": "Test",
                "credits": 4,
                "semester": 1,
                "course_type_original": "Core",
                "original_category": "Programme Core",
                "mode": "not_stated",
                "objectives": "Synthetic objective A.",
                "syllabus": "Synthetic syllabus A.",
                "hard_prerequisites": [],
                "recommended_prerequisites": [],
                "source_url": "https://example.test",
                "retrieved_on": "2026-01-01",
                "source_type": "official",
                "verification_status": "verified",
            },
            {
                "course_code": "TSTB",
                "title": "Synthetic Course B",
                "department": "Test",
                "credits": 3,
                "semester": 2,
                "course_type_original": "Core",
                "original_category": "Programme Core",
                "mode": "not_stated",
                "objectives": "Synthetic objective B.",
                "syllabus": "Synthetic syllabus B.",
                "hard_prerequisites": ["TSTA"],
                "recommended_prerequisites": [],
                "source_url": "https://example.test",
                "retrieved_on": "2026-01-01",
                "source_type": "official",
                "verification_status": "verified",
            },
        ]
        ingest = _make_ingest_with_courses(courses_raw)
        norm = run_normalise(ingest)
        val = run_validate(norm)
        errors = [e for e in val.errors if e.check_id == "CHK_006"]
        assert errors == [], f"Unexpected CHK_006 errors: {errors}"


# ---------------------------------------------------------------------------
# Integration: prerequisite cycle
# ---------------------------------------------------------------------------

class TestPrerequisiteCycle:
    def test_cycle_detected(self):
        """
        SYNTHETIC TEST: TST_X requires TST_Y and TST_Y requires TST_X → cycle.
        """
        courses_raw = [
            {
                "course_code": "TSTX",
                "title": "Synthetic Course X",
                "department": "Test",
                "credits": 4,
                "semester": 1,
                "course_type_original": "Core",
                "original_category": "Programme Core",
                "mode": "not_stated",
                "objectives": "Synthetic.",
                "syllabus": "Synthetic.",
                "hard_prerequisites": ["TSTY"],
                "recommended_prerequisites": [],
                "source_url": "https://example.test",
                "retrieved_on": "2026-01-01",
                "source_type": "official",
                "verification_status": "verified",
            },
            {
                "course_code": "TSTY",
                "title": "Synthetic Course Y",
                "department": "Test",
                "credits": 4,
                "semester": 2,
                "course_type_original": "Core",
                "original_category": "Programme Core",
                "mode": "not_stated",
                "objectives": "Synthetic.",
                "syllabus": "Synthetic.",
                "hard_prerequisites": ["TSTX"],
                "recommended_prerequisites": [],
                "source_url": "https://example.test",
                "retrieved_on": "2026-01-01",
                "source_type": "official",
                "verification_status": "verified",
            },
        ]
        ingest = _make_ingest_with_courses(courses_raw)
        norm = run_normalise(ingest)
        val = run_validate(norm)
        cycle_errors = [e for e in val.errors if e.check_id == "CHK_007"]
        assert len(cycle_errors) >= 1, "Expected CHK_007 error for prerequisite cycle"

