"""
tests/test_chunking.py
Tests for the deterministic chunking module.
Verifies chunk creation, metadata preservation, and JSONL validity.
All test data is synthetic and does NOT represent real institutional records.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest import IngestResult
from src.normalize import run_normalise
from src.chunk import run_chunk, _split_into_chunks, _make_chunk_id
from src.validate import run_validate
from tests.conftest import (
    VALID_COURSES_RAW, VALID_RULES_RAW, VALID_RESOURCES_RAW,
    VALID_SKILLS_RAW, VALID_COURSE_SKILL_LINKS_RAW, VALID_RESOURCE_SKILL_LINKS_RAW,
)


def _make_norm():
    ingest = IngestResult()
    ingest.courses_raw = VALID_COURSES_RAW
    ingest.rules_raw = VALID_RULES_RAW
    ingest.resources_raw = VALID_RESOURCES_RAW
    ingest.skills_raw = VALID_SKILLS_RAW
    ingest.course_skill_links_raw = VALID_COURSE_SKILL_LINKS_RAW
    ingest.resource_skill_links_raw = VALID_RESOURCE_SKILL_LINKS_RAW
    return run_normalise(ingest)


# ---------------------------------------------------------------------------
# Unit tests for split helper
# ---------------------------------------------------------------------------

class TestSplitIntoChunks:
    def test_short_text_returns_one_chunk(self):
        text = "Short text that is well under the limit."
        result = _split_into_chunks(text, max_words=100, overlap=10)
        assert len(result) == 1
        assert result[0] == text.strip()

    def test_long_text_splits(self):
        words = ["word"] * 500
        text = " ".join(words)
        result = _split_into_chunks(text, max_words=100, overlap=10)
        assert len(result) > 1

    def test_overlap_carries_words_forward(self):
        words = ["word"] * 220
        text = " ".join(words)
        result = _split_into_chunks(text, max_words=100, overlap=20)
        # First chunk has 100 words; second chunk should start 80 words in
        first_words = result[0].split()
        second_words = result[1].split()
        assert len(first_words) == 100
        # Second chunk should start where (100 - 20) = 80 into first chunk
        assert second_words[:20] == first_words[-20:]

    def test_empty_text_returns_empty(self):
        assert _split_into_chunks("", 100, 10) == []

    def test_whitespace_only_returns_empty(self):
        assert _split_into_chunks("   \n  ", 100, 10) == []


class TestChunkIdGeneration:
    def test_chunk_id_format(self):
        cid = _make_chunk_id("COURSE_TST101", 1)
        assert cid == "COURSE_TST101_CHUNK_001"

    def test_chunk_id_sequence_padding(self):
        cid = _make_chunk_id("COURSE_TST101", 42)
        assert cid == "COURSE_TST101_CHUNK_042"


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

class TestChunkIntegration:
    def setup_method(self):
        norm = _make_norm()
        self.chunks = run_chunk(norm, max_words=400, overlap=50)

    def test_chunks_produced(self):
        assert len(self.chunks) > 0

    def test_all_chunks_have_required_fields(self):
        required = {
            "chunk_id", "parent_id", "parent_type", "text",
            "section_title", "source_url", "retrieved_on",
            "source_type", "filter_metadata",
        }
        for chunk in self.chunks:
            missing = required - set(chunk.keys())
            assert not missing, f"Chunk {chunk.get('chunk_id')} missing fields: {missing}"

    def test_all_chunks_have_non_empty_text(self):
        for chunk in self.chunks:
            assert chunk["text"].strip(), f"Chunk {chunk.get('chunk_id')} has empty text."

    def test_chunk_parent_ids_valid(self):
        # Parent IDs must reference known course IDs, rule IDs, or resource IDs
        norm = _make_norm()
        valid_parents = (
            {f"COURSE_{c.code}" for c in norm.courses}
            | {r.rule_id for r in norm.rules}
            | {res.resource_id for res in norm.resources}
        )
        for chunk in self.chunks:
            pid = chunk["parent_id"]
            assert pid in valid_parents, f"Chunk {chunk['chunk_id']} has invalid parent_id '{pid}'."

    def test_filter_metadata_is_dict(self):
        for chunk in self.chunks:
            assert isinstance(chunk["filter_metadata"], dict), (
                f"Chunk {chunk.get('chunk_id')} filter_metadata is not a dict."
            )

    def test_course_chunks_have_programme_in_filter(self):
        course_chunks = [c for c in self.chunks if c["parent_type"] == "course"]
        for chunk in course_chunks:
            assert "programme" in chunk["filter_metadata"], (
                f"Course chunk {chunk['chunk_id']} missing 'programme' in filter_metadata."
            )
            assert chunk["filter_metadata"]["programme"] == "B.Tech DSAI"
            assert "skills" in chunk["filter_metadata"], (
                f"Course chunk {chunk['chunk_id']} missing 'skills' in filter_metadata."
            )
            assert isinstance(chunk["filter_metadata"]["skills"], list)

    def test_rule_chunks_present(self):
        rule_chunks = [c for c in self.chunks if c["parent_type"] == "rule"]
        assert len(rule_chunks) > 0, "Expected at least one rule chunk."

    def test_resource_chunks_present(self):
        resource_chunks = [c for c in self.chunks if c["parent_type"] == "resource"]
        assert len(resource_chunks) > 0, "Expected at least one resource chunk."


# ---------------------------------------------------------------------------
# JSONL validity test
# ---------------------------------------------------------------------------

class TestJSONLValidity:
    def test_chunks_serialisable_to_jsonl(self):
        """Every chunk must be serialisable to a single valid JSON line."""
        norm = _make_norm()
        chunks = run_chunk(norm, max_words=400, overlap=50)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl",
                                         delete=False, encoding="utf-8") as fh:
            path = Path(fh.name)
            for chunk in chunks:
                fh.write(json.dumps(chunk, ensure_ascii=False) + "\n")

        # Re-read and parse every line
        with path.open("r", encoding="utf-8") as fh:
            lines = fh.readlines()

        assert len(lines) == len(chunks)
        for i, line in enumerate(lines):
            parsed = json.loads(line)   # raises if invalid JSON
            assert "chunk_id" in parsed, f"Line {i+1} missing chunk_id."

        path.unlink()   # clean up temp file


# ---------------------------------------------------------------------------
# Validation of chunks after chunking
# ---------------------------------------------------------------------------

class TestChunkValidation:
    def test_no_chunk_parent_id_errors_on_valid_data(self):
        """
        After chunking valid data, the validator should report no CHK_017 errors.
        """
        norm = _make_norm()
        chunks = run_chunk(norm, max_words=400, overlap=50)
        val = run_validate(norm, chunks=chunks)
        chk17_errors = [e for e in val.errors if e.check_id == "CHK_017"]
        assert chk17_errors == [], f"Unexpected CHK_017 errors: {chk17_errors}"

