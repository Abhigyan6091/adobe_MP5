"""
tests/test_missing_sources.py
Tests for validation of missing source URLs, retrieval dates, licences.
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
    VALID_RULES_RAW, VALID_SKILLS_RAW,
    VALID_COURSE_SKILL_LINKS_RAW, VALID_RESOURCE_SKILL_LINKS_RAW,
)


def _make_ingest(**kwargs) -> IngestResult:
    result = IngestResult()
    result.courses_raw = kwargs.get("courses_raw", [])
    result.rules_raw = kwargs.get("rules_raw", VALID_RULES_RAW)
    result.resources_raw = kwargs.get("resources_raw", [])
    result.skills_raw = kwargs.get("skills_raw", VALID_SKILLS_RAW)
    result.course_skill_links_raw = kwargs.get("csl_raw", VALID_COURSE_SKILL_LINKS_RAW)
    result.resource_skill_links_raw = kwargs.get("rsl_raw", [])
    return result


class TestMissingSourceURL:
    def test_course_missing_source_url(self):
        """SYNTHETIC TEST: Course with no source_url → CHK_008 error."""
        course = {
            "course_code": "TSTA99",
            "title": "Synthetic No-URL Course",
            "department": "Test",
            "credits": 3,
            "semester": 1,
            "course_type_original": "Core",
            "original_category": "Programme Core",
            "mode": "not_stated",
            "objectives": "Synthetic.",
            "syllabus": "Synthetic.",
            "hard_prerequisites": [],
            "recommended_prerequisites": [],
            "source_url": "",     # <-- missing
            "retrieved_on": "2026-01-01",
            "source_type": "official",
            "verification_status": "verified",
        }
        ingest = _make_ingest(courses_raw=[course])
        norm = run_normalise(ingest)
        val = run_validate(norm)
        url_errors = [e for e in val.errors if e.check_id == "CHK_008"]
        assert len(url_errors) >= 1, f"Expected CHK_008 for missing source URL: {val.errors}"

    def test_course_with_source_url_no_error(self):
        """SYNTHETIC TEST: Course with source_url → no CHK_008 error."""
        course = {
            "course_code": "TSTB99",
            "title": "Synthetic URL Present Course",
            "department": "Test",
            "credits": 3,
            "semester": 1,
            "course_type_original": "Core",
            "original_category": "Programme Core",
            "mode": "not_stated",
            "objectives": "Synthetic.",
            "syllabus": "Synthetic.",
            "hard_prerequisites": [],
            "recommended_prerequisites": [],
            "source_url": "https://example.test",
            "retrieved_on": "2026-01-01",
            "source_type": "official",
            "verification_status": "verified",
        }
        ingest = _make_ingest(courses_raw=[course])
        norm = run_normalise(ingest)
        val = run_validate(norm)
        url_errors = [e for e in val.errors if e.check_id == "CHK_008"]
        assert url_errors == [], f"Unexpected CHK_008 errors: {url_errors}"


class TestMissingResourceLicence:
    def test_resource_missing_licence_warning(self):
        """SYNTHETIC TEST: Resource without licence → CHK_014 warning."""
        resource = {
            "resource_id": "RES_TEST_NO_LIC",
            "title": "Synthetic Resource Without Licence",
            "provider": "Test Provider",
            "url": "https://example.test/resource",
            "licence": "",       # <-- missing
            "licence_verification_status": "not_verified",
            "format": "video_lectures",
            "duration": "4 weeks",
            "duration_type": "published",
            "associated_course_codes": [],
            "associated_skills": [],
            "description": "Synthetic test resource with no licence.",
            "source_url": "https://example.test/resource",
            "retrieved_on": "2026-01-01",
            "source_type": "open_licence",
        }
        ingest = _make_ingest(resources_raw=[resource])
        norm = run_normalise(ingest)
        val = run_validate(norm)
        lic_warnings = [i for i in val.warnings if i.check_id == "CHK_014"]
        assert len(lic_warnings) >= 1, f"Expected CHK_014 warning for missing licence: {val.warnings}"


class TestMissingResourceURL:
    def test_resource_missing_url_error(self):
        """SYNTHETIC TEST: Resource without URL → CHK_015 error."""
        resource = {
            "resource_id": "RES_TEST_NO_URL",
            "title": "Synthetic Resource Without URL",
            "provider": "Test Provider",
            "url": "",           # <-- missing
            "licence": "CC BY 4.0",
            "licence_verification_status": "verified",
            "format": "video_lectures",
            "duration": "4 weeks",
            "duration_type": "published",
            "associated_course_codes": [],
            "associated_skills": [],
            "description": "Synthetic test resource with no URL.",
            "source_url": "https://example.test/resource",
            "retrieved_on": "2026-01-01",
            "source_type": "open_licence",
        }
        ingest = _make_ingest(resources_raw=[resource])
        norm = run_normalise(ingest)
        val = run_validate(norm)
        url_errors = [e for e in val.errors if e.check_id == "CHK_015"]
        assert len(url_errors) >= 1, f"Expected CHK_015 for missing resource URL: {val.errors}"


class TestInvalidCredits:
    def test_non_numeric_credits_error(self):
        """SYNTHETIC TEST: Course with non-numeric credits → CHK_004 error."""
        course = {
            "course_code": "TSTCRED",
            "title": "Synthetic Bad Credits Course",
            "department": "Test",
            "credits": "FOUR",   # <-- invalid
            "semester": 1,
            "course_type_original": "Core",
            "original_category": "Programme Core",
            "mode": "not_stated",
            "objectives": "Synthetic.",
            "syllabus": "Synthetic.",
            "hard_prerequisites": [],
            "recommended_prerequisites": [],
            "source_url": "https://example.test",
            "retrieved_on": "2026-01-01",
            "source_type": "official",
            "verification_status": "verified",
        }
        ingest = _make_ingest(courses_raw=[course])
        norm = run_normalise(ingest)
        val = run_validate(norm)
        credit_errors = [e for e in val.errors if e.check_id == "CHK_004"]
        assert len(credit_errors) >= 1, f"Expected CHK_004 for invalid credits: {val.errors}"

