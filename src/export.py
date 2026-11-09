"""
Stage 5 – Export
=================
Writes all normalised entities and chunks to data/processed/.

Output files
------------
  courses.csv
  prerequisites.csv
  skills.csv
  course_skill_links.csv
  academic_rules.json
  resources.csv
  resource_skill_links.csv
  modules.csv           (empty scaffold – no module-level data collected yet)
  chunks.jsonl          (one valid JSON object per line)

All files are UTF-8 encoded.
"""
from __future__ import annotations

import csv
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROCESSED_DIR = Path("data/processed")


def _ensure_dir() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Wrote %d rows to %s", len(rows), path)


def _write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    logger.info("Wrote JSON to %s", path)


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    logger.info("Wrote %d JSONL records to %s", len(records), path)


# ---------------------------------------------------------------------------
# Field name definitions
# ---------------------------------------------------------------------------

COURSE_FIELDS = [
    "course_id", "code", "title", "department", "credits", "semester",
    "course_type", "original_category", "mode", "objectives", "syllabus",
    "hard_prerequisites", "recommended_prerequisites",
    "source_url", "retrieved_on", "source_type", "verification_status",
]

PREREQ_FIELDS = [
    "prerequisite_id", "course_code", "requires_course_code", "kind",
    "source_url", "retrieved_on", "source_type",
]

SKILL_FIELDS = [
    "skill_id", "name", "description", "proficiency_level", "parent_skill_id",
    "source_url", "retrieved_on", "source_type", "verification_status",
]

COURSE_SKILL_FIELDS = [
    "course_code", "skill_id", "depth", "mapping_rationale", "evidence",
    "source_url", "source_type", "verification_status",
]

RESOURCE_FIELDS = [
    "resource_id", "title", "provider", "licence", "format", "duration",
    "duration_type", "url", "description", "source_url", "retrieved_on",
    "source_type", "licence_verification_status",
]

RESOURCE_SKILL_FIELDS = [
    "resource_id", "skill_id", "level", "mapping_rationale",
]

MODULE_FIELDS = [
    "module_id", "parent_id", "parent_type", "sequence", "title",
    "summary", "associated_skills", "source_url", "retrieved_on", "source_type",
]

EXERCISE_FIELDS = [
    "exercise_id", "skill_id", "difficulty", "question", "answer_key",
    "source_url", "retrieved_on", "source_type", "verification_status",
]


# ---------------------------------------------------------------------------
# Export functions
# ---------------------------------------------------------------------------

def _course_to_dict(course) -> dict:
    d = {
        "course_id": course.course_id,
        "code": course.code,
        "title": course.title,
        "department": course.department,
        "credits": course.credits,
        "semester": course.semester,
        "course_type": course.course_type,
        "original_category": course.original_category,
        "mode": course.mode,
        "objectives": course.objectives,
        "syllabus": course.syllabus,
        "hard_prerequisites": "|".join(course.hard_prerequisites),
        "recommended_prerequisites": "|".join(course.recommended_prerequisites),
        "source_url": course.source_url,
        "retrieved_on": course.retrieved_on,
        "source_type": course.source_type,
        "verification_status": course.verification_status,
    }
    return d


def run_export(normalise_result, chunks: list[dict[str, Any]]) -> None:
    """Execute Stage 5: write all processed data to data/processed/."""
    logger.info("=== Stage 5: Export ===")
    _ensure_dir()

    # --- courses.csv ---
    course_rows = [_course_to_dict(c) for c in normalise_result.courses]
    _write_csv(PROCESSED_DIR / "courses.csv", course_rows, COURSE_FIELDS)

    # --- prerequisites.csv ---
    prereq_rows = [
        {
            "prerequisite_id": p.prerequisite_id,
            "course_code": p.course_code,
            "requires_course_code": p.requires_course_code,
            "kind": p.kind,
            "source_url": p.source_url,
            "retrieved_on": p.retrieved_on,
            "source_type": p.source_type,
        }
        for p in normalise_result.prerequisites
    ]
    _write_csv(PROCESSED_DIR / "prerequisites.csv", prereq_rows, PREREQ_FIELDS)

    # --- skills.csv ---
    skill_rows = [
        {
            "skill_id": s.skill_id,
            "name": s.name,
            "description": s.description,
            "proficiency_level": s.proficiency_level,
            "parent_skill_id": s.parent_skill_id,
            "source_url": s.source_url,
            "retrieved_on": s.retrieved_on,
            "source_type": s.source_type,
            "verification_status": s.verification_status,
        }
        for s in normalise_result.skills
    ]
    _write_csv(PROCESSED_DIR / "skills.csv", skill_rows, SKILL_FIELDS)

    # --- course_skill_links.csv ---
    csl_rows = [
        {
            "course_code": lnk.course_code,
            "skill_id": lnk.skill_id,
            "depth": lnk.depth,
            "mapping_rationale": lnk.mapping_rationale,
            "evidence": lnk.evidence,
            "source_url": lnk.source_url,
            "source_type": lnk.source_type,
            "verification_status": lnk.verification_status,
        }
        for lnk in normalise_result.course_skill_links
    ]
    _write_csv(PROCESSED_DIR / "course_skill_links.csv", csl_rows, COURSE_SKILL_FIELDS)

    # --- academic_rules.json ---
    rule_records = [
        {
            "rule_id": r.rule_id,
            "category": r.category,
            "text": r.text,
            "numeric_limit": r.numeric_limit,
            "applies_to": r.applies_to,
            "conditions": r.conditions,
            "source_url": r.source_url,
            "retrieved_on": r.retrieved_on,
            "source_type": r.source_type,
            "page_or_section": r.page_or_section,
            "verification_status": r.verification_status,
        }
        for r in normalise_result.rules
    ]
    _write_json(PROCESSED_DIR / "academic_rules.json", rule_records)

    # --- resources.csv ---
    resource_rows = [
        {
            "resource_id": r.resource_id,
            "title": r.title,
            "provider": r.provider,
            "licence": r.licence,
            "format": r.format,
            "duration": r.duration,
            "duration_type": r.duration_type,
            "url": r.url,
            "description": r.description,
            "source_url": r.source_url,
            "retrieved_on": r.retrieved_on,
            "source_type": r.source_type,
            "licence_verification_status": r.licence_verification_status,
        }
        for r in normalise_result.resources
    ]
    _write_csv(PROCESSED_DIR / "resources.csv", resource_rows, RESOURCE_FIELDS)

    # --- resource_skill_links.csv ---
    rsl_rows = [
        {
            "resource_id": lnk.resource_id,
            "skill_id": lnk.skill_id,
            "level": lnk.level,
            "mapping_rationale": lnk.mapping_rationale,
        }
        for lnk in normalise_result.resource_skill_links
    ]
    _write_csv(PROCESSED_DIR / "resource_skill_links.csv", rsl_rows, RESOURCE_SKILL_FIELDS)

    # --- modules.csv ---
    module_rows = [
        {
            "module_id": m.module_id,
            "parent_id": m.parent_id,
            "parent_type": m.parent_type,
            "sequence": m.sequence,
            "title": m.title,
            "summary": m.summary,
            "associated_skills": m.associated_skills,
            "source_url": m.source_url,
            "retrieved_on": m.retrieved_on,
            "source_type": m.source_type,
        }
        for m in getattr(normalise_result, "modules", [])
    ]
    _write_csv(PROCESSED_DIR / "modules.csv", module_rows, MODULE_FIELDS)

    # --- exercises.csv (bonus) ---
    exercise_rows = [
        {
            "exercise_id": ex.exercise_id,
            "skill_id": ex.skill_id,
            "difficulty": ex.difficulty,
            "question": ex.question,
            "answer_key": ex.answer_key,
            "source_url": ex.source_url,
            "retrieved_on": ex.retrieved_on,
            "source_type": ex.source_type,
            "verification_status": ex.verification_status,
        }
        for ex in getattr(normalise_result, "exercises", [])
    ]
    _write_csv(PROCESSED_DIR / "exercises.csv", exercise_rows, EXERCISE_FIELDS)

    # --- chunks.jsonl ---
    _write_jsonl(PROCESSED_DIR / "chunks.jsonl", chunks)

    logger.info(
        "Export complete: %d courses, %d prerequisites, %d skills, "
        "%d course-skill links, %d rules, %d resources, "
        "%d resource-skill links, %d modules, %d exercises, %d chunks",
        len(normalise_result.courses),
        len(normalise_result.prerequisites),
        len(normalise_result.skills),
        len(normalise_result.course_skill_links),
        len(normalise_result.rules),
        len(normalise_result.resources),
        len(normalise_result.resource_skill_links),
        len(getattr(normalise_result, "modules", [])),
        len(getattr(normalise_result, "exercises", [])),
        len(chunks),
    )

