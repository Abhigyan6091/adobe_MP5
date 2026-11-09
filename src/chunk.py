"""
Stage 4 – Chunk
================
Deterministically splits course syllabi, learning objectives,
academic rules, and resource descriptions into retrieval-sized chunks.

Configuration (all configurable; not hardcoded):
  CHUNK_MAX_WORDS  – maximum words per chunk (default 400)
  CHUNK_OVERLAP    – word overlap between adjacent long-text chunks (default 50)

Chunk IDs are deterministic and stable: based on parent ID + sequence index.
No LLM or embedding calls are made.
"""
from __future__ import annotations

import logging
import textwrap
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------
CHUNK_MAX_WORDS: int = 400
CHUNK_OVERLAP: int = 50


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _word_split(text: str) -> list[str]:
    """Split text into individual words, preserving whitespace collapsing."""
    return text.split()


def _words_to_text(words: list[str]) -> str:
    return " ".join(words)


def _split_into_chunks(text: str, max_words: int, overlap: int) -> list[str]:
    """
    Split text into chunks of at most max_words words with overlap words
    of context carried over from the previous chunk.
    Returns a list of text strings.
    """
    words = _word_split(text)
    if len(words) <= max_words:
        return [text.strip()] if text.strip() else []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunk_words = words[start:end]
        chunks.append(_words_to_text(chunk_words))
        if end >= len(words):
            break
        start = end - overlap  # overlap
    return chunks


def _make_chunk_id(parent_id: str, sequence: int) -> str:
    return f"{parent_id}_CHUNK_{sequence:03d}"


# ---------------------------------------------------------------------------
# Chunk creators per entity type
# ---------------------------------------------------------------------------

def _chunk_course(course, max_words: int, overlap: int) -> list[dict[str, Any]]:
    """
    Create chunks for a single course.
    - One chunk per syllabus section (split by 'Unit').
    - One chunk for objectives if present.
    - Long sections split further by word count.
    """
    parent_id = course.course_id
    chunks: list[dict[str, Any]] = []
    seq = 1

    base_filter = {
        "programme": "B.Tech DSAI",
        "course_code": course.code,
        "semester": course.semester,
        "course_type": course.course_type,
    }

    def emit(text: str, section: str, extra_filter: dict | None = None) -> None:
        nonlocal seq
        sub_chunks = _split_into_chunks(text, max_words, overlap)
        for sc in sub_chunks:
            if not sc.strip():
                continue
            fm = {**base_filter}
            if extra_filter:
                fm.update(extra_filter)
            chunks.append({
                "chunk_id": _make_chunk_id(parent_id, seq),
                "parent_id": parent_id,
                "parent_type": "course",
                "text": sc,
                "section_title": section,
                "source_url": course.source_url,
                "retrieved_on": course.retrieved_on,
                "source_type": course.source_type,
                "filter_metadata": fm,
            })
            seq += 1

    # Objectives
    if course.objectives:
        emit(course.objectives, "Learning Objectives")

    # Syllabus: try to split by 'Unit' headings; fall back to whole text
    if course.syllabus:
        import re
        unit_pattern = re.compile(r"(Unit\s+\d+[:\s])", re.IGNORECASE)
        parts = unit_pattern.split(course.syllabus)
        if len(parts) > 1:
            # parts alternates: prefix, unit_header, unit_content, ...
            i = 1
            while i < len(parts):
                header = parts[i].strip()
                content = parts[i + 1].strip() if i + 1 < len(parts) else ""
                if content:
                    emit(f"{header} {content}", f"Syllabus – {header}")
                i += 2
        else:
            emit(course.syllabus, "Syllabus")

    return chunks


def _chunk_rule(rule, max_words: int, overlap: int) -> list[dict[str, Any]]:
    """Each academic rule produces one (or more for long rules) chunks."""
    parent_id = rule.rule_id
    text = rule.text
    if not text.strip():
        return []

    base_filter = {
        "programme": "B.Tech DSAI",
        "rule_category": rule.category,
        "applies_to": rule.applies_to or "all",
        "verification_status": rule.verification_status,
    }

    chunks: list[dict[str, Any]] = []
    sub_chunks = _split_into_chunks(text, max_words, overlap)
    for seq, sc in enumerate(sub_chunks, start=1):
        if not sc.strip():
            continue
        chunks.append({
            "chunk_id": _make_chunk_id(parent_id, seq),
            "parent_id": parent_id,
            "parent_type": "rule",
            "text": sc,
            "section_title": f"Rule: {rule.category}",
            "source_url": rule.source_url,
            "retrieved_on": rule.retrieved_on,
            "source_type": rule.source_type,
            "filter_metadata": base_filter,
        })
    return chunks


def _chunk_resource(resource, max_words: int, overlap: int) -> list[dict[str, Any]]:
    """Resource descriptions produce one (or more) chunks."""
    parent_id = resource.resource_id
    text = resource.description or ""
    if not text.strip():
        return []

    base_filter = {
        "programme": "B.Tech DSAI",
        "provider": resource.provider or "unknown",
        "format": resource.format or "unknown",
        "licence": resource.licence or "unknown",
        "licence_verification_status": resource.licence_verification_status,
    }

    chunks: list[dict[str, Any]] = []
    sub_chunks = _split_into_chunks(text, max_words, overlap)
    for seq, sc in enumerate(sub_chunks, start=1):
        if not sc.strip():
            continue
        chunks.append({
            "chunk_id": _make_chunk_id(parent_id, seq),
            "parent_id": parent_id,
            "parent_type": "resource",
            "text": sc,
            "section_title": f"Resource: {resource.title}",
            "source_url": resource.source_url,
            "retrieved_on": resource.retrieved_on,
            "source_type": resource.source_type,
            "filter_metadata": base_filter,
        })
    return chunks


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_chunk(
    normalise_result,
    max_words: int = CHUNK_MAX_WORDS,
    overlap: int = CHUNK_OVERLAP,
) -> list[dict[str, Any]]:
    """
    Execute Stage 4: chunk all courses, rules, and resources.

    Parameters
    ----------
    normalise_result : NormaliseResult from stage 2.
    max_words        : Maximum words per chunk.
    overlap          : Word overlap between consecutive chunks.

    Returns
    -------
    List of chunk dicts ready for JSONL export.
    """
    logger.info("=== Stage 4: Chunk (max_words=%d, overlap=%d) ===", max_words, overlap)

    all_chunks: list[dict[str, Any]] = []

    for course in normalise_result.courses:
        all_chunks.extend(_chunk_course(course, max_words, overlap))

    for rule in normalise_result.rules:
        all_chunks.extend(_chunk_rule(rule, max_words, overlap))

    for resource in normalise_result.resources:
        all_chunks.extend(_chunk_resource(resource, max_words, overlap))

    logger.info(
        "Chunk complete: %d total chunks "
        "(from %d courses, %d rules, %d resources)",
        len(all_chunks),
        len(normalise_result.courses),
        len(normalise_result.rules),
        len(normalise_result.resources),
    )
    return all_chunks

