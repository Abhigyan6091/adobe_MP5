"""
run_pipeline.py
===============
Single entry point.  Run with:

    python run_pipeline.py

Executes all five stages:
  1. Ingest
  2. Normalise
  3. Validate
  4. Chunk
  5. Export

Then generates the DATA_QUALITY_REPORT.md.

Returns exit code 0 on success, 1 if critical validation errors are found.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configure logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("run_pipeline")

# ---------------------------------------------------------------------------
# Ensure src/ is importable when running from project root
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))

from src.ingest import run_ingest
from src.normalize import run_normalise
from src.validate import run_validate
from src.chunk import run_chunk, CHUNK_MAX_WORDS, CHUNK_OVERLAP
from src.export import run_export
from src.report import run_report


def main() -> int:
    logger.info("=" * 60)
    logger.info("Adobe Personalised Learning Buddy – Data Foundation Pipeline")
    logger.info("Programme: B.Tech DSAI at IIT Bhilai")
    logger.info("=" * 60)

    # Stage 1 – Ingest
    try:
        ingest_result = run_ingest()
    except (FileNotFoundError, ValueError) as exc:
        logger.error("Ingest failed: %s", exc)
        return 1

    # Stage 2 – Normalise
    try:
        norm_result = run_normalise(ingest_result)
    except Exception as exc:
        logger.error("Normalise failed: %s", exc)
        return 1

    # Stage 4 – Chunk (before final validate so we can check chunk parent IDs)
    try:
        chunks = run_chunk(norm_result, max_words=CHUNK_MAX_WORDS, overlap=CHUNK_OVERLAP)
    except Exception as exc:
        logger.error("Chunk failed: %s", exc)
        return 1

    # Stage 3 – Validate (includes chunk parent-ID check)
    try:
        validation_result = run_validate(norm_result, chunks=chunks)
    except Exception as exc:
        logger.error("Validate failed unexpectedly: %s", exc)
        return 1

    if validation_result.has_critical_errors:
        logger.error(
            "Pipeline stopping: %d critical validation error(s) found. "
            "Review the issues above and correct the source data.",
            len(validation_result.errors),
        )
        # Still write report so the user can see what failed
        run_report(validation_result, chunks)
        return 1

    # Stage 5 – Export
    try:
        run_export(norm_result, chunks)
    except Exception as exc:
        logger.error("Export failed: %s", exc)
        return 1

    # Data quality report
    try:
        run_report(validation_result, chunks)
    except Exception as exc:
        logger.warning("Report generation failed (non-fatal): %s", exc)

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully.")
    logger.info(
        "Outputs in data/processed/   Report: DATA_QUALITY_REPORT.md"
    )
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

