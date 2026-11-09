"""
Stage 3 – Validate
===================
Runs all validation checks against normalised data.
Issues are classified as ERROR, WARNING, or INFO.
The pipeline exits with a non-zero status when any ERROR is found.

Checks implemented
------------------
1.  Missing course codes.
2.  Duplicate course codes.
3.  Missing course titles.
4.  Invalid / non-numeric credits.
5.  Invalid semester labels.
6.  Prerequisites referencing nonexistent courses.
7.  Prerequisite cycles (DFS-based).
8.  Missing source URLs (courses, rules, resources).
9.  Missing retrieval dates (courses, rules, resources).
10. Missing source types (courses, rules, resources).
11. Invalid course-skill references (course or skill not in catalogue).
12. Invalid resource-skill references (resource or skill not in catalogue).
13. Duplicate IDs (courses, skills, rules, resources).
14. External resources missing licence information.
15. Invalid or missing resource URLs.
16. Academic rules without source evidence (source_url).
17. Chunks without valid parent IDs  (checked after chunking; stub here).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ValidationIssue:
    severity: Severity
    check_id: str
    entity_type: str
    entity_id: str
    message: str


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    @property
    def has_critical_errors(self) -> bool:
        return bool(self.errors)

    def add(self, severity: Severity, check_id: str, entity_type: str,
            entity_id: str, message: str) -> None:
        self.issues.append(ValidationIssue(severity, check_id, entity_type, entity_id, message))


# ---------------------------------------------------------------------------
# Prerequisite cycle detection (DFS)
# ---------------------------------------------------------------------------

def _detect_cycles(edges: dict[str, list[str]]) -> list[list[str]]:
    """
    Detect cycles in a directed graph using DFS.

    Parameters
    ----------
    edges : dict mapping course_code -> list of courses it requires

    Returns
    -------
    list of cycles, each cycle is a list of node labels forming the cycle.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {}
    parent: dict[str, str | None] = {}
    cycles: list[list[str]] = []

    def dfs(node: str) -> None:
        color[node] = GRAY
        for neighbour in edges.get(node, []):
            if color.get(neighbour) == GRAY:
                # Found a cycle; reconstruct it
                cycle = [neighbour, node]
                cur = node
                while parent.get(cur) and parent[cur] != neighbour:
                    cur = parent[cur]  # type: ignore[assignment]
                    cycle.append(cur)
                cycle.append(neighbour)
                cycles.append(list(reversed(cycle)))
            elif color.get(neighbour, WHITE) == WHITE:
                parent[neighbour] = node
                dfs(neighbour)
        color[node] = BLACK

    for node in list(edges.keys()):
        if color.get(node, WHITE) == WHITE:
            dfs(node)

    return cycles


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

def _check_courses(result: ValidationResult, courses: list) -> set[str]:
    """Checks 1–5. Returns set of valid course codes for downstream checks."""
    valid_codes: set[str] = set()
    seen_ids: dict[str, int] = {}

    for course in courses:
        cid = course.course_id
        code = course.code

        # Check 13 – duplicate IDs
        seen_ids[cid] = seen_ids.get(cid, 0) + 1
        if seen_ids[cid] > 1:
            result.add(Severity.ERROR, "CHK_013", "course", cid,
                       f"Duplicate course_id '{cid}'.")

        # Check 1 – missing course code
        if not code:
            result.add(Severity.ERROR, "CHK_001", "course", cid,
                       "Course has an empty or missing course code.")
            continue

        # Check 3 – missing title
        if not course.title:
            result.add(Severity.ERROR, "CHK_003", "course", code,
                       "Course is missing a title.")

        # Check 4 – credits
        if course.credits is None:
            result.add(Severity.ERROR, "CHK_004", "course", code,
                       f"Credits field is invalid or non-numeric (original value: {course.credits_original!r}).")
        elif course.credits <= 0:
            result.add(Severity.WARNING, "CHK_004", "course", code,
                       f"Credits value is non-positive: {course.credits}.")

        # Check 5 – semester
        if course.semester is None:
            result.add(Severity.ERROR, "CHK_005", "course", code,
                       f"Invalid semester label (original value: {course.semester_original!r}).")

        # Check 8 – source URL
        if not course.source_url:
            result.add(Severity.ERROR, "CHK_008", "course", code,
                       "Course is missing source_url.")

        # Check 9 – retrieval date
        if not course.retrieved_on:
            result.add(Severity.WARNING, "CHK_009", "course", code,
                       "Course is missing retrieved_on date.")

        # Check 10 – source type
        if course.source_type == "not_stated":
            result.add(Severity.WARNING, "CHK_010", "course", code,
                       "Course source_type is not_stated.")

        valid_codes.add(code)

    # Check 2 – duplicate course codes (codes, not IDs)
    code_counts: dict[str, int] = {}
    for course in courses:
        code_counts[course.code] = code_counts.get(course.code, 0) + 1
    for code, count in code_counts.items():
        if count > 1:
            result.add(Severity.ERROR, "CHK_002", "course", code,
                       f"Duplicate course code '{code}' appears {count} times.")

    return valid_codes


def _check_prerequisites(result: ValidationResult, prerequisites: list,
                          valid_codes: set[str]) -> None:
    """Checks 6–7: missing prerequisite courses and prerequisite cycles."""
    # Build adjacency: course -> courses it requires
    edges: dict[str, list[str]] = {}
    for prereq in prerequisites:
        cc = prereq.course_code
        req = prereq.requires_course_code

        # Check 6 – prerequisite references nonexistent course
        if req and req not in valid_codes:
            result.add(Severity.ERROR, "CHK_006", "prerequisite", prereq.prerequisite_id,
                       f"Prerequisite '{req}' for course '{cc}' does not exist in the course catalogue.")

        edges.setdefault(cc, []).append(req)

    # Check 7 – prerequisite cycles
    cycles = _detect_cycles(edges)
    for cycle in cycles:
        cycle_str = " -> ".join(cycle)
        result.add(Severity.ERROR, "CHK_007", "prerequisite", "CYCLE",
                   f"Prerequisite cycle detected: {cycle_str}")


def _check_skills(result: ValidationResult, skills: list) -> set[str]:
    """Check 13 (duplicate skill IDs). Returns set of valid skill IDs."""
    valid_ids: set[str] = set()
    seen: dict[str, int] = {}
    for skill in skills:
        sid = skill.skill_id
        seen[sid] = seen.get(sid, 0) + 1
        if seen[sid] > 1:
            result.add(Severity.ERROR, "CHK_013", "skill", sid,
                       f"Duplicate skill_id '{sid}'.")
        valid_ids.add(sid)
    return valid_ids


def _check_course_skill_links(result: ValidationResult, links: list,
                               valid_codes: set[str], valid_skill_ids: set[str]) -> None:
    """Check 11: invalid course-skill references."""
    for link in links:
        if link.course_code not in valid_codes:
            result.add(Severity.ERROR, "CHK_011", "course_skill_link",
                       f"{link.course_code}:{link.skill_id}",
                       f"Course code '{link.course_code}' in course-skill link does not exist.")
        if link.skill_id not in valid_skill_ids:
            result.add(Severity.ERROR, "CHK_011", "course_skill_link",
                       f"{link.course_code}:{link.skill_id}",
                       f"Skill ID '{link.skill_id}' in course-skill link does not exist.")


def _check_rules(result: ValidationResult, rules: list) -> None:
    """Checks 8–10 for rules, check 16 (rules without source), check 13."""
    seen: dict[str, int] = {}
    for rule in rules:
        rid = rule.rule_id
        seen[rid] = seen.get(rid, 0) + 1
        if seen[rid] > 1:
            result.add(Severity.ERROR, "CHK_013", "rule", rid,
                       f"Duplicate rule_id '{rid}'.")

        # Check 16 – rules without source evidence
        if not rule.source_url:
            result.add(Severity.ERROR, "CHK_016", "rule", rid,
                       "Academic rule is missing source_url (no source evidence).")

        if not rule.retrieved_on:
            result.add(Severity.WARNING, "CHK_009", "rule", rid,
                       "Academic rule is missing retrieved_on date.")

        if rule.source_type == "not_stated":
            result.add(Severity.WARNING, "CHK_010", "rule", rid,
                       "Academic rule source_type is not_stated.")


def _check_resources(result: ValidationResult, resources: list,
                     valid_skill_ids: set[str], resource_skill_links: list) -> set[str]:
    """Checks 14–15, check 8–10 for resources, check 13. Returns valid resource IDs."""
    valid_ids: set[str] = set()
    seen: dict[str, int] = {}

    for res in resources:
        rid = res.resource_id
        seen[rid] = seen.get(rid, 0) + 1
        if seen[rid] > 1:
            result.add(Severity.ERROR, "CHK_013", "resource", rid,
                       f"Duplicate resource_id '{rid}'.")

        # Check 14 – missing licence
        if not res.licence or res.licence.strip().lower() in {"", "none", "unknown"}:
            result.add(Severity.WARNING, "CHK_014", "resource", rid,
                       "Resource is missing licence information.")

        # Check 15 – missing URL
        if not res.url:
            result.add(Severity.ERROR, "CHK_015", "resource", rid,
                       "Resource is missing URL.")

        # Check 8 – source URL
        if not res.source_url:
            result.add(Severity.WARNING, "CHK_008", "resource", rid,
                       "Resource is missing source_url.")

        # Check 9 – retrieval date
        if not res.retrieved_on:
            result.add(Severity.WARNING, "CHK_009", "resource", rid,
                       "Resource is missing retrieved_on date.")

        # Check 10 – source type
        if res.source_type == "not_stated":
            result.add(Severity.WARNING, "CHK_010", "resource", rid,
                       "Resource source_type is not_stated.")

        valid_ids.add(rid)

    # Check 12 – resource-skill references
    for link in resource_skill_links:
        if link.resource_id not in valid_ids:
            result.add(Severity.ERROR, "CHK_012", "resource_skill_link",
                       f"{link.resource_id}:{link.skill_id}",
                       f"Resource ID '{link.resource_id}' in resource-skill link does not exist.")
        if link.skill_id not in valid_skill_ids:
            result.add(Severity.ERROR, "CHK_012", "resource_skill_link",
                       f"{link.resource_id}:{link.skill_id}",
                       f"Skill ID '{link.skill_id}' in resource-skill link does not exist.")

    return valid_ids


def _check_chunks(result: ValidationResult, chunks: list,
                  valid_parent_ids: set[str]) -> None:
    """Check 17: chunks without valid parent IDs."""
    for chunk in chunks:
        pid = chunk.get("parent_id", "")
        if not pid or pid not in valid_parent_ids:
            result.add(Severity.ERROR, "CHK_017", "chunk", chunk.get("chunk_id", "unknown"),
                       f"Chunk has invalid or missing parent_id: '{pid}'.")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_validate(normalise_result, chunks: list | None = None) -> ValidationResult:
    """
    Execute Stage 3: validate all normalised entities.

    Parameters
    ----------
    normalise_result : NormaliseResult from stage 2.
    chunks           : Optional list of chunk dicts from stage 4 (for check 17).

    Returns
    -------
    ValidationResult with all issues.  Caller should exit(1) if has_critical_errors.
    """
    logger.info("=== Stage 3: Validate ===")
    result = ValidationResult()

    valid_codes = _check_courses(result, normalise_result.courses)
    _check_prerequisites(result, normalise_result.prerequisites, valid_codes)
    valid_skill_ids = _check_skills(result, normalise_result.skills)
    _check_course_skill_links(result, normalise_result.course_skill_links,
                              valid_codes, valid_skill_ids)
    _check_rules(result, normalise_result.rules)
    valid_resource_ids = _check_resources(result, normalise_result.resources,
                                           valid_skill_ids, normalise_result.resource_skill_links)

    if chunks is not None:
        # Build valid parent IDs from courses, rules, resources
        valid_parent_ids = (
            {f"COURSE_{c.code}" for c in normalise_result.courses}
            | {r.rule_id for r in normalise_result.rules}
            | {res.resource_id for res in normalise_result.resources}
        )
        _check_chunks(result, chunks, valid_parent_ids)

    # Summary
    n_errors = len(result.errors)
    n_warnings = len(result.warnings)
    n_info = len([i for i in result.issues if i.severity == Severity.INFO])
    logger.info(
        "Validation complete: %d errors, %d warnings, %d info",
        n_errors, n_warnings, n_info,
    )

    for issue in result.issues:
        log_fn = logger.error if issue.severity == Severity.ERROR else (
            logger.warning if issue.severity == Severity.WARNING else logger.info
        )
        log_fn("[%s] %s (%s / %s): %s",
               issue.severity.value, issue.check_id,
               issue.entity_type, issue.entity_id, issue.message)

    return result

