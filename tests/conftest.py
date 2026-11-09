"""
Shared pytest fixtures for the pipeline test suite.
Provides small, clearly synthetic test datasets.
These fixtures do NOT represent real institutional records.
"""
from __future__ import annotations

import pytest
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Synthetic fixture data (NOT real institutional records)
# ---------------------------------------------------------------------------

VALID_COURSES_RAW = [
    {
        "course_code": "TST101",
        "title": "Test Course Alpha",
        "department": "Test Department",
        "credits": 4,
        "semester": 1,
        "course_type_original": "Core",
        "original_category": "Programme Core",
        "mode": "not_stated",
        "objectives": "Learn test objective A. Understand test concept B.",
        "syllabus": "Unit 1: Topic A. Unit 2: Topic B.",
        "hard_prerequisites": [],
        "recommended_prerequisites": [],
        "source_url": "https://example.test/course",
        "retrieved_on": "2026-01-01",
        "source_type": "official",
        "verification_status": "verified",
    },
    {
        "course_code": "TST201",
        "title": "Test Course Beta",
        "department": "Test Department",
        "credits": 3,
        "semester": 2,
        "course_type_original": "Elective",
        "original_category": "Programme Elective",
        "mode": "not_stated",
        "objectives": "Apply test methods to solve problems.",
        "syllabus": "Unit 1: Method X. Unit 2: Method Y.",
        "hard_prerequisites": ["TST101"],
        "recommended_prerequisites": [],
        "source_url": "https://example.test/course",
        "retrieved_on": "2026-01-01",
        "source_type": "official",
        "verification_status": "verified",
    },
]

VALID_RULES_RAW = [
    {
        "rule_id": "RULE_TEST_001",
        "category": "credit_limits",
        "text": "Students must not register for more than 24 credits per semester.",
        "numeric_limit": 24,
        "applies_to": "All students",
        "conditions": "None",
        "source_url": "https://example.test/manual",
        "document_name": "Test Manual",
        "page_or_section": "Section 3",
        "retrieved_on": "2026-01-01",
        "source_type": "official",
        "verification_status": "verified",
    },
]

VALID_RESOURCES_RAW = [
    {
        "resource_id": "RES_TEST_001",
        "title": "Test Learning Resource",
        "provider": "Test Provider",
        "url": "https://example.test/resource",
        "licence": "CC BY 4.0",
        "licence_verification_status": "verified",
        "format": "video_lectures",
        "duration": "4 weeks",
        "duration_type": "published",
        "associated_course_codes": ["TST101"],
        "associated_skills": ["SKILL_TEST_001"],
        "description": "A synthetic test resource covering basic concepts for TST101.",
        "source_url": "https://example.test/resource",
        "retrieved_on": "2026-01-01",
        "source_type": "open_licence",
    },
]

VALID_SKILLS_RAW = [
    {
        "skill_id": "SKILL_TEST_001",
        "name": "Test Skill Alpha",
        "description": "A synthetic test skill.",
        "proficiency_level": "foundational",
        "parent_skill_id": None,
        "source_url": "https://example.test/skill",
        "retrieved_on": "2026-01-01",
        "source_type": "manual",
        "verification_status": "curated",
    },
]

VALID_COURSE_SKILL_LINKS_RAW = [
    {
        "course_code": "TST101",
        "skill_id": "SKILL_TEST_001",
        "depth": "working",
        "mapping_rationale": "TST101 teaches this skill directly.",
        "evidence": "Syllabus covers test skill content.",
        "source_url": "https://example.test/course",
        "source_type": "official",
        "verification_status": "verified",
    },
]

VALID_RESOURCE_SKILL_LINKS_RAW = [
    {
        "resource_id": "RES_TEST_001",
        "skill_id": "SKILL_TEST_001",
        "level": "working",
        "mapping_rationale": "Resource directly teaches skill.",
    },
]

