"""
Stage 2 – Parse and Normalise
==============================
Applies consistent normalisation to raw ingested records and returns
typed, normalised entity lists.

Rules:
- Original values are ALWAYS preserved in `*_original` fields.
- Normalisation is deterministic (pure functions, no randomness or LLM calls).
- Unknown / missing optional fields are set to None (null) explicitly.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

VALID_COURSE_TYPES = {"core", "elective", "open", "not_stated"}
VALID_SEMESTERS = {1, 2, 3, 4, 5, 6, 7, 8}
VALID_SOURCE_TYPES = {"official", "open_licence", "manual"}
VALID_DEPTHS = {"intro", "working", "advanced"}

_SEMESTER_ALIASES: dict[str, int] = {
    "first": 1, "second": 2, "third": 3, "fourth": 4,
    "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8,
    "i": 1, "ii": 2, "iii": 3, "iv": 4,
    "v": 5, "vi": 6, "vii": 7, "viii": 8,
}

_COURSE_TYPE_MAP: dict[str, str] = {
    "core": "core",
    "programme core": "core",
    "elective": "elective",
    "programme elective": "elective",
    "open elective": "open",
    "open": "open",
    "institute elective": "open",
}


def normalise_course_code(code: str) -> str:
    """Upper-case, strip whitespace, collapse internal spaces."""
    return re.sub(r"\s+", "", code.strip().upper())


def normalise_course_title(title: str) -> str:
    """Title-case, collapse whitespace."""
    return " ".join(title.strip().split())


def normalise_department(dept: str) -> str:
    """Strip whitespace."""
    return dept.strip()


def normalise_credits(raw: Any) -> float | None:
    """Return float or None; never raises."""
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def normalise_semester(raw: Any) -> int | None:
    """Return int (1–8) or None."""
    if isinstance(raw, int) and raw in VALID_SEMESTERS:
        return raw
    if isinstance(raw, str):
        s = raw.strip().lower()
        if s.isdigit() and int(s) in VALID_SEMESTERS:
            return int(s)
        if s in _SEMESTER_ALIASES:
            return _SEMESTER_ALIASES[s]
    return None


def normalise_course_type(raw: str) -> str:
    """Map original category string to core | elective | open | not_stated."""
    key = raw.strip().lower()
    return _COURSE_TYPE_MAP.get(key, "not_stated")


def normalise_source_type(raw: str) -> str:
    """Coerce to official | open_licence | manual | not_stated."""
    s = raw.strip().lower().replace("-", "_").replace(" ", "_")
    return s if s in VALID_SOURCE_TYPES else "not_stated"


def normalise_skill_id(raw: str) -> str:
    """Upper-case, strip."""
    return raw.strip().upper()


# ---------------------------------------------------------------------------
# Normalised dataclasses
# ---------------------------------------------------------------------------

@dataclass
class NormalisedCourse:
    course_id: str
    code: str
    title: str
    department: str
    credits: float | None
    semester: int | None
    course_type: str          # normalised
    original_category: str    # preserved
    mode: str | None
    objectives: str | None
    syllabus: str | None
    source_url: str | None
    retrieved_on: str | None
    source_type: str
    verification_status: str
    hard_prerequisites: list[str]
    recommended_prerequisites: list[str]
    # Preservation
    course_type_original: str
    credits_original: Any
    semester_original: Any


@dataclass
class NormalisedPrerequisite:
    prerequisite_id: str
    course_code: str
    requires_course_code: str
    kind: str    # hard | recommended
    source_url: str | None
    retrieved_on: str | None
    source_type: str


@dataclass
class NormalisedSkill:
    skill_id: str
    name: str
    description: str | None
    proficiency_level: str | None
    parent_skill_id: str | None
    source_url: str | None
    retrieved_on: str | None
    source_type: str
    verification_status: str


@dataclass
class NormalisedCourseSkillLink:
    course_code: str
    skill_id: str
    depth: str
    mapping_rationale: str | None
    evidence: str | None
    source_url: str | None
    source_type: str
    verification_status: str


@dataclass
class NormalisedRule:
    rule_id: str
    category: str
    text: str
    numeric_limit: float | None
    applies_to: str | None
    conditions: str | None
    source_url: str | None
    retrieved_on: str | None
    source_type: str
    page_or_section: str | None
    verification_status: str


@dataclass
class NormalisedResource:
    resource_id: str
    title: str
    provider: str | None
    licence: str | None
    format: str | None
    duration: str | None
    duration_type: str | None
    url: str | None
    description: str | None
    source_url: str | None
    retrieved_on: str | None
    source_type: str
    licence_verification_status: str


@dataclass
class NormalisedResourceSkillLink:
    resource_id: str
    skill_id: str
    level: str
    mapping_rationale: str | None


@dataclass
class NormalisedModule:
    module_id: str
    parent_id: str
    parent_type: str
    sequence: int
    title: str
    summary: str
    associated_skills: str
    source_url: str | None
    retrieved_on: str | None
    source_type: str


@dataclass
class NormalisedExercise:
    exercise_id: str
    skill_id: str
    difficulty: str
    question: str
    answer_key: str
    source_url: str | None
    retrieved_on: str | None
    source_type: str
    verification_status: str


@dataclass
class NormaliseResult:
    courses: list[NormalisedCourse] = field(default_factory=list)
    prerequisites: list[NormalisedPrerequisite] = field(default_factory=list)
    skills: list[NormalisedSkill] = field(default_factory=list)
    course_skill_links: list[NormalisedCourseSkillLink] = field(default_factory=list)
    rules: list[NormalisedRule] = field(default_factory=list)
    resources: list[NormalisedResource] = field(default_factory=list)
    resource_skill_links: list[NormalisedResourceSkillLink] = field(default_factory=list)
    modules: list[NormalisedModule] = field(default_factory=list)
    exercises: list[NormalisedExercise] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Normalisation functions
# ---------------------------------------------------------------------------

def _normalise_courses(raw_courses: list[dict]) -> tuple[list[NormalisedCourse], list[NormalisedPrerequisite]]:
    courses: list[NormalisedCourse] = []
    prerequisites: list[NormalisedPrerequisite] = []
    prereq_counter: dict[str, int] = {}

    for raw in raw_courses:
        code_raw = raw.get("course_code", "")
        code = normalise_course_code(code_raw) if code_raw else ""

        credits_raw = raw.get("credits")
        semester_raw = raw.get("semester")

        course_type_orig = raw.get("course_type_original", raw.get("course_type", "not_stated"))
        course_type_norm = normalise_course_type(course_type_orig)

        hard_prereqs = [normalise_course_code(p) for p in (raw.get("hard_prerequisites") or []) if p]
        rec_prereqs = [normalise_course_code(p) for p in (raw.get("recommended_prerequisites") or []) if p]

        course = NormalisedCourse(
            course_id=f"COURSE_{code}",
            code=code,
            title=normalise_course_title(raw.get("title", "")),
            department=normalise_department(raw.get("department", "")),
            credits=normalise_credits(credits_raw),
            semester=normalise_semester(semester_raw),
            course_type=course_type_norm,
            original_category=raw.get("original_category", "not_stated"),
            mode=raw.get("mode") or None,
            objectives=raw.get("objectives") or None,
            syllabus=raw.get("syllabus") or None,
            source_url=raw.get("source_url") or None,
            retrieved_on=raw.get("retrieved_on") or None,
            source_type=normalise_source_type(raw.get("source_type", "")),
            verification_status=raw.get("verification_status", "unverified"),
            hard_prerequisites=hard_prereqs,
            recommended_prerequisites=rec_prereqs,
            course_type_original=course_type_orig,
            credits_original=credits_raw,
            semester_original=semester_raw,
        )
        courses.append(course)

        # Expand prerequisites into relationship records
        for req_code in hard_prereqs:
            n = prereq_counter.get(code, 0) + 1
            prereq_counter[code] = n
            prerequisites.append(NormalisedPrerequisite(
                prerequisite_id=f"PREREQ_{code}_{req_code}",
                course_code=code,
                requires_course_code=req_code,
                kind="hard",
                source_url=raw.get("source_url") or None,
                retrieved_on=raw.get("retrieved_on") or None,
                source_type=normalise_source_type(raw.get("source_type", "")),
            ))
        for req_code in rec_prereqs:
            prerequisites.append(NormalisedPrerequisite(
                prerequisite_id=f"PREREQ_{code}_{req_code}_REC",
                course_code=code,
                requires_course_code=req_code,
                kind="recommended",
                source_url=raw.get("source_url") or None,
                retrieved_on=raw.get("retrieved_on") or None,
                source_type=normalise_source_type(raw.get("source_type", "")),
            ))

    return courses, prerequisites


def _normalise_skills(raw_skills: list[dict]) -> list[NormalisedSkill]:
    skills = []
    for raw in raw_skills:
        skills.append(NormalisedSkill(
            skill_id=normalise_skill_id(raw.get("skill_id", "")),
            name=raw.get("name", "").strip(),
            description=raw.get("description") or None,
            proficiency_level=raw.get("proficiency_level") or None,
            parent_skill_id=normalise_skill_id(raw["parent_skill_id"]) if raw.get("parent_skill_id") else None,
            source_url=raw.get("source_url") or None,
            retrieved_on=raw.get("retrieved_on") or None,
            source_type=normalise_source_type(raw.get("source_type", "")),
            verification_status=raw.get("verification_status", "unverified"),
        ))
    return skills


def _normalise_course_skill_links(raw_links: list[dict]) -> list[NormalisedCourseSkillLink]:
    links = []
    for raw in raw_links:
        depth = raw.get("depth", "").lower()
        if depth not in VALID_DEPTHS:
            depth = "intro"
        links.append(NormalisedCourseSkillLink(
            course_code=normalise_course_code(raw.get("course_code", "")),
            skill_id=normalise_skill_id(raw.get("skill_id", "")),
            depth=depth,
            mapping_rationale=raw.get("mapping_rationale") or None,
            evidence=raw.get("evidence") or None,
            source_url=raw.get("source_url") or None,
            source_type=normalise_source_type(raw.get("source_type", "")),
            verification_status=raw.get("verification_status", "unverified"),
        ))
    return links


def _normalise_rules(raw_rules: list[dict]) -> list[NormalisedRule]:
    rules = []
    for raw in raw_rules:
        num_limit = raw.get("numeric_limit")
        try:
            num_limit = float(num_limit) if num_limit is not None else None
        except (TypeError, ValueError):
            num_limit = None

        rules.append(NormalisedRule(
            rule_id=raw.get("rule_id", "").strip(),
            category=raw.get("category", "").strip(),
            text=raw.get("text", "").strip(),
            numeric_limit=num_limit,
            applies_to=raw.get("applies_to") or None,
            conditions=raw.get("conditions") or None,
            source_url=raw.get("source_url") or None,
            retrieved_on=raw.get("retrieved_on") or None,
            source_type=normalise_source_type(raw.get("source_type", "")),
            page_or_section=raw.get("page_or_section") or None,
            verification_status=raw.get("verification_status", "unverified"),
        ))
    return rules


def _normalise_resources(raw_resources: list[dict]) -> list[NormalisedResource]:
    resources = []
    for raw in raw_resources:
        resources.append(NormalisedResource(
            resource_id=raw.get("resource_id", "").strip(),
            title=raw.get("title", "").strip(),
            provider=raw.get("provider") or None,
            licence=raw.get("licence") or None,
            format=raw.get("format") or None,
            duration=raw.get("duration") or None,
            duration_type=raw.get("duration_type") or None,
            url=raw.get("url") or None,
            description=raw.get("description") or None,
            source_url=raw.get("source_url") or None,
            retrieved_on=raw.get("retrieved_on") or None,
            source_type=normalise_source_type(raw.get("source_type", "")),
            licence_verification_status=raw.get("licence_verification_status", "not_verified"),
        ))
    return resources


def _normalise_resource_skill_links(raw_links: list[dict]) -> list[NormalisedResourceSkillLink]:
    links = []
    for raw in raw_links:
        level = raw.get("level", "").lower()
        if level not in VALID_DEPTHS:
            level = "intro"
        links.append(NormalisedResourceSkillLink(
            resource_id=raw.get("resource_id", "").strip(),
            skill_id=normalise_skill_id(raw.get("skill_id", "")),
            level=level,
            mapping_rationale=raw.get("mapping_rationale") or None,
        ))
    return links


def _extract_modules(
    courses: list[NormalisedCourse],
    course_skill_links: list[NormalisedCourseSkillLink],
) -> list[NormalisedModule]:
    """
    Extract structured course syllabus units into fine-grained module records.
    Every course's unit outline (e.g. Unit 1: Introduction...) is converted into a module.
    """
    course_skills: dict[str, list[str]] = {}
    for link in course_skill_links:
        course_skills.setdefault(link.course_code, []).append(link.skill_id)

    modules: list[NormalisedModule] = []
    for c in courses:
        syl = c.syllabus or ""
        units = re.split(r"Unit\s+(\d+)[:\.]\s*", syl)
        for i in range(1, len(units), 2):
            seq = int(units[i])
            content = units[i + 1].strip()
            if " - " in content:
                title, summary = content.split(" - ", 1)
            elif ":" in content:
                title, summary = content.split(":", 1)
            else:
                parts = content.split(". ", 1)
                title = parts[0]
                summary = parts[1] if len(parts) > 1 else content

            skills_str = "|".join(course_skills.get(c.code, []))
            modules.append(NormalisedModule(
                module_id=f"MOD_{c.code}_{seq:02d}",
                parent_id=c.course_id,
                parent_type="course",
                sequence=seq,
                title=title.strip().rstrip("."),
                summary=summary.strip().rstrip("."),
                associated_skills=skills_str,
                source_url=c.source_url,
                retrieved_on=c.retrieved_on,
                source_type=c.source_type,
            ))
    return modules


def _normalise_exercises(raw_exercises: list[dict]) -> list[NormalisedExercise]:
    """Normalise practice exercises."""
    VALID_DIFFICULTIES = {"easy", "medium", "hard"}
    exercises = []
    for raw in raw_exercises:
        diff = raw.get("difficulty", "medium").strip().lower()
        if diff not in VALID_DIFFICULTIES:
            diff = "medium"
        exercises.append(NormalisedExercise(
            exercise_id=raw.get("exercise_id", "").strip(),
            skill_id=normalise_skill_id(raw.get("skill_id", "")),
            difficulty=diff,
            question=raw.get("question", "").strip(),
            answer_key=raw.get("answer_key", "").strip(),
            source_url=raw.get("source_url") or None,
            retrieved_on=raw.get("retrieved_on") or None,
            source_type=normalise_source_type(raw.get("source_type", "")),
            verification_status=raw.get("verification_status", "unverified"),
        ))
    return exercises


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_normalise(ingest_result) -> NormaliseResult:
    """Execute Stage 2: parse and normalise all ingested records."""
    logger.info("=== Stage 2: Parse and Normalise ===")

    courses, prerequisites = _normalise_courses(ingest_result.courses_raw)
    skills = _normalise_skills(ingest_result.skills_raw)
    course_skill_links = _normalise_course_skill_links(ingest_result.course_skill_links_raw)
    rules = _normalise_rules(ingest_result.rules_raw)
    resources = _normalise_resources(ingest_result.resources_raw)
    resource_skill_links = _normalise_resource_skill_links(ingest_result.resource_skill_links_raw)
    modules = _extract_modules(courses, course_skill_links)
    exercises = _normalise_exercises(getattr(ingest_result, "exercises_raw", []))

    result = NormaliseResult(
        courses=courses,
        prerequisites=prerequisites,
        skills=skills,
        course_skill_links=course_skill_links,
        rules=rules,
        resources=resources,
        resource_skill_links=resource_skill_links,
        modules=modules,
        exercises=exercises,
    )

    logger.info(
        "Normalise complete: %d courses, %d prerequisites, %d skills, "
        "%d course-skill links, %d rules, %d resources, %d resource-skill links, %d modules, %d exercises",
        len(courses), len(prerequisites), len(skills),
        len(course_skill_links), len(rules), len(resources), len(resource_skill_links),
        len(modules), len(exercises),
    )
    return result

