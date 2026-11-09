"""
tests/test_valid_data.py
Tests for well-formed valid course and resource records.
Fixture data is clearly synthetic and does NOT represent real institutional records.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.normalize import run_normalise, normalise_course_code, normalise_credits, normalise_semester
from src.validate import run_validate
from src.ingest import IngestResult
from tests.conftest import (
    VALID_COURSES_RAW, VALID_RULES_RAW, VALID_RESOURCES_RAW,
    VALID_SKILLS_RAW, VALID_COURSE_SKILL_LINKS_RAW, VALID_RESOURCE_SKILL_LINKS_RAW,
    VALID_EXERCISES_RAW,
)


def _make_ingest(courses=None, rules=None, resources=None,
                  skills=None, csl=None, rsl=None, exercises=None) -> IngestResult:
    result = IngestResult()
    result.courses_raw = courses if courses is not None else VALID_COURSES_RAW
    result.rules_raw = rules if rules is not None else VALID_RULES_RAW
    result.resources_raw = resources if resources is not None else VALID_RESOURCES_RAW
    result.skills_raw = skills if skills is not None else VALID_SKILLS_RAW
    result.course_skill_links_raw = csl if csl is not None else VALID_COURSE_SKILL_LINKS_RAW
    result.resource_skill_links_raw = rsl if rsl is not None else VALID_RESOURCE_SKILL_LINKS_RAW
    result.exercises_raw = exercises if exercises is not None else VALID_EXERCISES_RAW
    return result


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

class TestNormalisationHelpers:
    def test_course_code_uppercase(self):
        assert normalise_course_code("tst101") == "TST101"

    def test_course_code_strips_spaces(self):
        assert normalise_course_code("  TST 101  ") == "TST101"

    def test_credits_integer(self):
        assert normalise_credits(4) == 4.0

    def test_credits_string_numeric(self):
        assert normalise_credits("3") == 3.0

    def test_credits_non_numeric_returns_none(self):
        assert normalise_credits("N/A") is None

    def test_credits_none_returns_none(self):
        assert normalise_credits(None) is None

    def test_semester_valid_int(self):
        assert normalise_semester(3) == 3

    def test_semester_string_digit(self):
        assert normalise_semester("5") == 5

    def test_semester_alias_roman(self):
        assert normalise_semester("iii") == 3

    def test_semester_out_of_range_returns_none(self):
        assert normalise_semester(9) is None

    def test_semester_non_numeric_string_returns_none(self):
        assert normalise_semester("spring") is None


# ---------------------------------------------------------------------------
# Full pipeline on valid data
# ---------------------------------------------------------------------------

class TestValidData:
    def setup_method(self):
        ingest = _make_ingest()
        self.norm = run_normalise(ingest)
        self.val = run_validate(self.norm)

    def test_courses_normalised(self):
        assert len(self.norm.courses) == 2

    def test_no_critical_errors_on_valid_data(self):
        assert not self.val.has_critical_errors, (
            f"Unexpected errors: {[e.message for e in self.val.errors]}"
        )

    def test_course_ids_deterministic(self):
        codes = [c.code for c in self.norm.courses]
        assert "TST101" in codes
        assert "TST201" in codes

    def test_prerequisite_created(self):
        prereqs = self.norm.prerequisites
        assert any(p.course_code == "TST201" and p.requires_course_code == "TST101"
                   for p in prereqs)

    def test_skills_normalised(self):
        assert len(self.norm.skills) == 1

    def test_resources_normalised(self):
        assert len(self.norm.resources) == 1

    def test_course_skill_link_created(self):
        assert len(self.norm.course_skill_links) == 1
        link = self.norm.course_skill_links[0]
        assert link.course_code == "TST101"
        assert link.skill_id == "SKILL_TEST_001"

    def test_resource_skill_link_created(self):
        assert len(self.norm.resource_skill_links) == 1

    def test_modules_extracted(self):
        assert hasattr(self.norm, "modules")
        assert len(self.norm.modules) == 4  # TST101 has 2 units, TST201 has 2 units
        m = self.norm.modules[0]
        assert m.module_id == "MOD_TST101_01"
        assert m.parent_id == "COURSE_TST101"
        assert m.sequence == 1
        assert m.title == "Topic A"

    def test_exercises_normalised(self):
        assert hasattr(self.norm, "exercises")
        assert len(self.norm.exercises) == 1
        ex = self.norm.exercises[0]
        assert ex.exercise_id == "EX_TEST_001"
        assert ex.skill_id == "SKILL_TEST_001"
        assert ex.difficulty == "easy"
        assert "Question" not in ex.answer_key



