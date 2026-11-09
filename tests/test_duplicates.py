"""
tests/test_duplicates.py
Tests for duplicate ID detection.
All test data is synthetic and does NOT represent real institutional records.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest import IngestResult
from src.normalize import run_normalise
from src.validate import run_validate
from tests.conftest import (
    VALID_RULES_RAW, VALID_RESOURCES_RAW, VALID_SKILLS_RAW,
    VALID_COURSE_SKILL_LINKS_RAW, VALID_RESOURCE_SKILL_LINKS_RAW,
)


def _base_ingest(**kwargs) -> IngestResult:
    result = IngestResult()
    result.courses_raw = kwargs.get("courses_raw", [])
    result.rules_raw = kwargs.get("rules_raw", VALID_RULES_RAW)
    result.resources_raw = kwargs.get("resources_raw", VALID_RESOURCES_RAW)
    result.skills_raw = kwargs.get("skills_raw", VALID_SKILLS_RAW)
    result.course_skill_links_raw = kwargs.get("csl_raw", VALID_COURSE_SKILL_LINKS_RAW)
    result.resource_skill_links_raw = kwargs.get("rsl_raw", VALID_RESOURCE_SKILL_LINKS_RAW)
    return result


_SYNTHETIC_COURSE = {
    "course_code": "TSTDUP",
    "title": "Synthetic Duplicate Course",
    "department": "Test",
    "credits": 3,
    "semester": 1,
    "course_type_original": "Core",
    "original_category": "Programme Core",
    "mode": "not_stated",
    "objectives": "Synthetic objective.",
    "syllabus": "Synthetic syllabus.",
    "hard_prerequisites": [],
    "recommended_prerequisites": [],
    "source_url": "https://example.test",
    "retrieved_on": "2026-01-01",
    "source_type": "official",
    "verification_status": "verified",
}


class TestDuplicateCourseCode:
    def test_duplicate_course_code_raises_error(self):
        """
        SYNTHETIC TEST: Two entries with the same course code TSTDUP.
        Expect CHK_002 error.
        """
        courses_raw = [_SYNTHETIC_COURSE.copy(), _SYNTHETIC_COURSE.copy()]
        ingest = _base_ingest(courses_raw=courses_raw)
        norm = run_normalise(ingest)
        val = run_validate(norm)
        dup_errors = [e for e in val.errors if e.check_id == "CHK_002"]
        assert len(dup_errors) >= 1, (
            f"Expected CHK_002 duplicate course code error, got: {val.errors}"
        )

    def test_unique_codes_no_duplicate_error(self):
        """
        SYNTHETIC TEST: Two entries with different course codes → no CHK_002.
        """
        course_a = {**_SYNTHETIC_COURSE, "course_code": "TSTA01"}
        course_b = {**_SYNTHETIC_COURSE, "course_code": "TSTB01"}
        ingest = _base_ingest(courses_raw=[course_a, course_b])
        norm = run_normalise(ingest)
        val = run_validate(norm)
        dup_errors = [e for e in val.errors if e.check_id == "CHK_002"]
        assert dup_errors == [], f"Unexpected duplicate errors: {dup_errors}"


class TestDuplicateRuleId:
    def test_duplicate_rule_id_raises_error(self):
        """
        SYNTHETIC TEST: Two rules with the same rule_id.
        Expect CHK_013 error.
        """
        dup_rule = {
            "rule_id": "RULE_DUP_001",
            "category": "credit_limits",
            "text": "Synthetic duplicate rule.",
            "numeric_limit": 20,
            "applies_to": "All students",
            "conditions": "None",
            "source_url": "https://example.test",
            "document_name": "Test",
            "page_or_section": "1",
            "retrieved_on": "2026-01-01",
            "source_type": "official",
            "verification_status": "verified",
        }
        ingest = _base_ingest(courses_raw=[_SYNTHETIC_COURSE], rules_raw=[dup_rule, dup_rule])
        norm = run_normalise(ingest)
        val = run_validate(norm)
        dup_errors = [e for e in val.errors if e.check_id == "CHK_013" and e.entity_type == "rule"]
        assert len(dup_errors) >= 1, f"Expected CHK_013 for duplicate rule IDs: {val.errors}"

