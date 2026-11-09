"""
Stage 1 – Ingest
================
Reads raw structured JSON source files and the source manifest from data/raw/.
Preserves original files untouched.
Generates SHA-256 hashes for each raw structured file.
Returns an IngestResult dataclass consumed by downstream stages.
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")
STRUCTURED_DIR = RAW_DIR / "structured"
DOCUMENTS_DIR = RAW_DIR / "documents"
MANIFEST_PATH = RAW_DIR / "source_manifest.json"


@dataclass
class IngestResult:
    """Holds all ingested raw records and provenance information."""
    courses_raw: list[dict[str, Any]] = field(default_factory=list)
    rules_raw: list[dict[str, Any]] = field(default_factory=list)
    resources_raw: list[dict[str, Any]] = field(default_factory=list)
    skills_raw: list[dict[str, Any]] = field(default_factory=list)
    course_skill_links_raw: list[dict[str, Any]] = field(default_factory=list)
    resource_skill_links_raw: list[dict[str, Any]] = field(default_factory=list)
    exercises_raw: list[dict[str, Any]] = field(default_factory=list)
    manifest: dict[str, Any] = field(default_factory=dict)
    file_hashes: dict[str, str] = field(default_factory=dict)
    ingested_at: str = field(default_factory=lambda: datetime.now().isoformat())


def _sha256(path: Path) -> str:
    """Return the SHA-256 hex digest of a file without loading it all into memory."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path, label: str) -> list[dict[str, Any]] | dict[str, Any]:
    """Load a JSON file and return its parsed contents.  Raises on parse error."""
    if not path.exists():
        raise FileNotFoundError(f"Required source file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {label} ({path}): {exc}") from exc
    logger.info("Loaded %s (%d records)", label, len(data) if isinstance(data, list) else 1)
    return data


def run_ingest() -> IngestResult:
    """
    Execute Stage 1: load all raw structured source files, record hashes,
    and return an IngestResult.

    Raw documents (PDFs, etc.) in data/raw/documents/ are listed and hashed
    but never modified or parsed here.
    """
    logger.info("=== Stage 1: Ingest ===")

    result = IngestResult()

    # -----------------------------------------------------------------
    # Load source manifest
    # -----------------------------------------------------------------
    if MANIFEST_PATH.exists():
        result.manifest = _load_json(MANIFEST_PATH, "source_manifest")
        result.file_hashes[str(MANIFEST_PATH)] = _sha256(MANIFEST_PATH)
    else:
        logger.warning("source_manifest.json not found at %s", MANIFEST_PATH)

    # -----------------------------------------------------------------
    # Load structured source files
    # -----------------------------------------------------------------
    file_map = {
        "courses_raw.json": "courses_raw",
        "academic_rules_raw.json": "rules_raw",
        "resources_raw.json": "resources_raw",
        "skills_raw.json": "skills_raw",
        "course_skill_links_raw.json": "course_skill_links_raw",
        "resource_skill_links_raw.json": "resource_skill_links_raw",
        "exercises_raw.json": "exercises_raw",
    }

    for filename, attr in file_map.items():
        path = STRUCTURED_DIR / filename
        data = _load_json(path, filename)
        setattr(result, attr, data)
        result.file_hashes[str(path)] = _sha256(path)

    # -----------------------------------------------------------------
    # Enumerate raw documents (read-only; not parsed)
    # -----------------------------------------------------------------
    if DOCUMENTS_DIR.exists():
        for doc_path in sorted(DOCUMENTS_DIR.iterdir()):
            if doc_path.is_file():
                result.file_hashes[str(doc_path)] = _sha256(doc_path)
                logger.info("Catalogued document: %s", doc_path.name)
    else:
        logger.info("No documents directory found at %s", DOCUMENTS_DIR)

    logger.info(
        "Ingest complete: %d courses, %d rules, %d resources, "
        "%d skills, %d course-skill links, %d resource-skill links, %d exercises",
        len(result.courses_raw),
        len(result.rules_raw),
        len(result.resources_raw),
        len(result.skills_raw),
        len(result.course_skill_links_raw),
        len(result.resource_skill_links_raw),
        len(result.exercises_raw),
    )
    return result

