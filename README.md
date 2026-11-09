# Adobe Personalised Learning Buddy – Data Foundation

## 1. Project Objective

Build a source-traced, reproducible knowledge base and data pipeline for the **B.Tech Data Science and Artificial Intelligence (DSAI) programme** at **IIT Bhilai**, stopping before the embedding stage. The resulting clean, chunked, metadata-rich files are ready to consume in a future embedding-and-retrieval system.

---

## 2. Programme Selected

**Programme:** B.Tech in Data Science and Artificial Intelligence (DSAI)  
**Institute:** Indian Institute of Technology Bhilai (IIT Bhilai)

The focus is depth over breadth: all 19 collected courses belong to the DSAI programme or directly applicable institute-wide curriculum categories.

---

## 3. Data Sources

| ID | Name | URL | Type | Licence |
|----|------|-----|------|---------|
| SRC_001 | IIT Bhilai B.Tech Programme Schedule | https://www.iitbhilai.ac.in/index.php?pid=new_schedule_programs | Official | All rights reserved |
| SRC_002 | IIT Bhilai UG Academic Manual | https://iitbhilai.ac.in/index.php?pid=ug_manual | Official | All rights reserved |
| SRC_003 | NPTEL | https://nptel.ac.in/ | Open | CC BY-SA 4.0 |
| SRC_004 | MIT OpenCourseWare | https://ocw.mit.edu/ | Open | CC BY-NC-SA 4.0 |
| SRC_005 | OpenStax | https://openstax.org/ | Open | CC BY / CC BY-NC-SA 4.0 (varies) |
| SRC_006 | SWAYAM | https://swayam.gov.in/ | Open | CC BY-SA 4.0 |
| SRC_007 | Stanford EE364A | https://web.stanford.edu/class/ee364a/ | Open | Not verified |
| SRC_008 | Coursera / edX audit | https://www.coursera.org/ | Open | Not verified |

All institutional data was **manually transcribed** from official IIT Bhilai web pages (see §15 for methodology). No scraping was used for official pages. NPTEL/MIT OCW/OpenStax data was manually catalogued by visiting individual course pages.

---

## 4. Repository Structure

```
adobe_mp5/
├── data/
│   ├── raw/
│   │   ├── documents/          # Reserved for original PDF downloads (read-only)
│   │   ├── structured/         # Manually transcribed JSON source files
│   │   │   ├── courses_raw.json
│   │   │   ├── academic_rules_raw.json
│   │   │   ├── resources_raw.json
│   │   │   ├── skills_raw.json
│   │   │   ├── course_skill_links_raw.json
│   │   │   └── resource_skill_links_raw.json
│   │   └── source_manifest.json
│   │
│   └── processed/
│       ├── courses.csv
│       ├── prerequisites.csv
│       ├── skills.csv
│       ├── course_skill_links.csv
│       ├── academic_rules.json
│       ├── resources.csv
│       ├── resource_skill_links.csv
│       ├── modules.csv          # 112 structured unit modules
│       └── chunks.jsonl
│
├── src/
│   ├── __init__.py
│   ├── ingest.py               # Stage 1
│   ├── normalize.py            # Stage 2
│   ├── validate.py             # Stage 3
│   ├── chunk.py                # Stage 4
│   ├── export.py               # Stage 5
│   └── report.py               # Data quality report
│
├── tests/
│   ├── conftest.py             # Shared synthetic fixtures
│   ├── test_valid_data.py
│   ├── test_prerequisites.py
│   ├── test_duplicates.py
│   ├── test_missing_sources.py
│   └── test_chunking.py
│
├── run_pipeline.py             # Single entry point
├── requirements.txt
├── README.md
├── SOURCES.md
├── DATA_QUALITY_REPORT.md
├── IDEAS.md
└── .gitignore
```

---

## 5. Data Schema

### Core Entities

| Entity | Key fields | File |
|--------|-----------|------|
| Course | course_id, code, title, department, credits, semester, course_type, original_category, mode, objectives, syllabus, source_url, retrieved_on, source_type, verification_status | `courses.csv` |
| Prerequisite | prerequisite_id, course_code, requires_course_code, kind (hard/recommended), source_url, retrieved_on, source_type | `prerequisites.csv` |
| Skill | skill_id, name, description, proficiency_level, parent_skill_id, source_url, retrieved_on, source_type, verification_status | `skills.csv` |
| Course-Skill Link | course_code, skill_id, depth, mapping_rationale, evidence, source_url, source_type, verification_status | `course_skill_links.csv` |
| Academic Rule | rule_id, category, text, numeric_limit, applies_to, conditions, source_url, retrieved_on, source_type, page_or_section, verification_status | `academic_rules.json` |
| Resource | resource_id, title, provider, licence, format, duration, duration_type, url, description, source_url, retrieved_on, source_type, licence_verification_status | `resources.csv` |
| Resource-Skill Link | resource_id, skill_id, level, mapping_rationale | `resource_skill_links.csv` |
| Module | module_id, parent_id, parent_type, sequence, title, summary, associated_skills, source_url, retrieved_on, source_type | `modules.csv` |
| Chunk | chunk_id, parent_id, parent_type, text, section_title, source_url, retrieved_on, source_type, filter_metadata | `chunks.jsonl` |

### Design Decisions

- **Stable IDs**: All IDs (COURSE_DS301, SKILL_006, RES_002, RULE_CR_001) are deterministic and not row-number dependent.
- **Foreign-key-like references**: Prerequisites reference course codes; course-skill links reference course codes and skill IDs; chunk parent_ids reference entity IDs.
- **No duplication**: Course metadata lives only in `courses.csv`; links tables reference by ID.
- **Source provenance on every entity**: Every row has `source_url`, `retrieved_on`, `source_type`.
- **Separation of verified vs curated**: `verification_status` distinguishes `verified` (official source), `partially_verified`, `unresolved`, and `curated` (manual mapping).
- **Missing values preserved**: Unknown fields are `null` / `not_stated`, never fabricated.
- **modules.csv**: Fully populated with 112 structured course modules, extracting each syllabus unit, title, summary, and associated course skills.

---

## 6. Pipeline Architecture

```
data/raw/structured/*.json
        │
        ▼ Stage 1: Ingest
  IngestResult (typed)
        │
        ▼ Stage 2: Normalise
  NormaliseResult (normalised entities)
        │
        ▼ Stage 4: Chunk  ──────────────────────────┐
  chunks: list[dict]                                │
        │                                            │
        ▼ Stage 3: Validate (uses chunks for CHK_017)│
  ValidationResult ◄──────────────────────────────-┘
        │  (exits with code 1 if errors)
        ▼ Stage 5: Export
  data/processed/*.csv/.json/.jsonl
        │
        ▼ Report
  DATA_QUALITY_REPORT.md
```

> **Note:** Chunking (Stage 4) runs before the final validation pass so that chunk parent-ID integrity (CHK_017) can be verified in the same validation call.

---

## 7. How Each Stage Works

### Stage 1 – Ingest (`src/ingest.py`)
- Reads all structured JSON source files from `data/raw/structured/`.
- Reads `source_manifest.json`.
- Catalogues original documents in `data/raw/documents/` without parsing them.
- Computes SHA-256 file hashes to record source integrity.
- Never overwrites raw source files.

### Stage 2 – Parse and Normalise (`src/normalize.py`)
- Applies deterministic normalisation: course code upper-casing, credit coercion to float, semester mapping, course type mapping.
- Preserves original values in `*_original` fields.
- Builds `Prerequisite` records from inline `hard_prerequisites` / `recommended_prerequisites` lists.
- Returns typed Python dataclasses.

### Stage 3 – Validate (`src/validate.py`)
- Runs 17 named checks (CHK_001 – CHK_017).
- Classifies issues as ERROR, WARNING, or INFO.
- ERROR issues halt the pipeline (exit code 1).
- Implements prerequisite cycle detection using DFS (depth-first search) over the prerequisite graph.
- Prerequisite edge direction: `course_code → requires_course_code` (a course points to what it requires, not what requires it).

### Stage 4 – Chunk (`src/chunk.py`)
- Splits course syllabi by `Unit N:` headings; falls back to whole-text word-count splitting.
- Generates one chunk per academic rule (split further only if the rule text exceeds `max_words`).
- Generates one chunk per resource description.
- Chunk size is configurable: `CHUNK_MAX_WORDS = 400`, `CHUNK_OVERLAP = 50` (defaults).
- All chunks carry `parent_id`, `parent_type`, `source_url`, `retrieved_on`, `source_type`, and a `filter_metadata` dict for future embedding-stage filtering.

### Stage 5 – Export (`src/export.py`)
- Writes all entities to `data/processed/`.
- UTF-8 encoding for all files.
- `chunks.jsonl`: one valid JSON object per line.
- `modules.csv`: empty scaffold (no module data collected; see §14).

---

## 8. Dependencies

```
pandas>=2.0.0       # used in data inspection; standard library CSV/JSON used in pipeline
pytest>=7.4.0       # test runner
pdfminer.six>=20221105  # PDF text extraction (available if raw PDFs are added later)
```

The pipeline itself uses only the **Python standard library** (json, csv, hashlib, pathlib, logging, dataclasses). `pandas` and `pdfminer.six` are project-level dependencies but are not required for the core pipeline to run.

---

## 9. Installation

```bash
pip install -r requirements.txt
```

No additional setup required. No database server, no Docker, no GPU.

---

## 10. How to Execute the Pipeline

```bash
python run_pipeline.py
```

The pipeline:
1. Reads from `data/raw/structured/` (no internet access required).
2. Writes results to `data/processed/`.
3. Writes `DATA_QUALITY_REPORT.md`.
4. Returns exit code `0` on success, `1` on critical validation errors.

---

## 11. How to Run Tests

```bash
python -m pytest tests/ -v
```

All 52 tests use **synthetic fixture data** (never real institutional records). Tests are in:

| File | Tests |
|------|-------|
| `test_valid_data.py` | Normalisation helpers, end-to-end on valid data |
| `test_prerequisites.py` | Missing prereq, cycle detection (unit + integration) |
| `test_duplicates.py` | Duplicate course codes, duplicate rule IDs |
| `test_missing_sources.py` | Missing source URL, missing licence, missing resource URL, invalid credits |
| `test_chunking.py` | Split helper, chunk IDs, metadata preservation, JSONL validity, CHK_017 |

---

## 12. Validation Logic

| Check | ID | Severity | Description |
|-------|----|----------|-------------|
| Missing course code | CHK_001 | ERROR | Empty/missing code |
| Duplicate course codes | CHK_002 | ERROR | Same code appears > 1 time |
| Missing course title | CHK_003 | ERROR | Empty/missing title |
| Invalid credits | CHK_004 | ERROR | Non-numeric; WARNING if ≤ 0 |
| Invalid semester | CHK_005 | ERROR | Outside 1–8 |
| Nonexistent prerequisite | CHK_006 | ERROR | Prereq code not in catalogue |
| Prerequisite cycle | CHK_007 | ERROR | DFS cycle detected in prereq graph |
| Missing source URL | CHK_008 | ERROR (course/rule) / WARNING (resource) | |
| Missing retrieval date | CHK_009 | WARNING | retrieved_on absent |
| Missing source type | CHK_010 | WARNING | source_type = not_stated |
| Invalid course-skill ref | CHK_011 | ERROR | Course code or skill ID not in catalogue |
| Invalid resource-skill ref | CHK_012 | ERROR | Resource ID or skill ID not in catalogue |
| Duplicate IDs | CHK_013 | ERROR | Any entity ID repeated |
| Missing resource licence | CHK_014 | WARNING | licence blank/unknown |
| Missing resource URL | CHK_015 | ERROR | url field absent/empty |
| Rule without source | CHK_016 | ERROR | Rule has no source_url |
| Chunk invalid parent | CHK_017 | ERROR | parent_id not in known entity IDs |

**Prerequisite direction convention:** edges go from "course that has the requirement" to "course that is required". A cycle means two courses mutually depend on each other, which is physically impossible to satisfy.

---

## 13. Chunking Strategy

- **Semantic first**: syllabus text is split at `Unit N:` boundaries to keep topical units intact.
- **Word-count fallback**: units or descriptions longer than `CHUNK_MAX_WORDS` words are further split with `CHUNK_OVERLAP` word overlap to preserve context.
- **One rule per chunk**: each academic rule is a separate chunk; rules are never merged.
- **No cross-entity chunks**: courses, rules, and resources are chunked independently.
- **Configurable**: `CHUNK_MAX_WORDS` and `CHUNK_OVERLAP` are module-level constants in `src/chunk.py`. Pass overrides via `run_chunk(norm_result, max_words=..., overlap=...)`.

---

## 14. Known Limitations

1. **Course `mode` field**: Confirmed as `in-person` across all 19 courses per IIT Bhilai degree guidelines.
2. **Minor eligibility CGPA threshold**: General academic standing rules (RULE_TERM_001: CGPA ≥ 4.0 / 4.5) are verified, but specific departmental cutoffs for Minor allocation are unstated in public documents (marked `unresolved` in `RULE_MIN_002`).
3. **Coursera / edX / Stanford EE364A licences**: Redistribution rights for 4 resources were not independently confirmed. Marked `not_verified`.
4. **Official document PDFs**: The IIT Bhilai UG Manual is behind a web page; transcription is based on publicly visible official text and regulations.
5. **No real NPTEL credit count per semester**: The exact number of NPTEL credits transferable per semester was not stated in publicly accessible portions of the UG Manual.

---

## 15. Data Collection and Manual Transcription Methodology

All institutional data (courses, academic rules) was collected by **direct manual reading** of the IIT Bhilai official website and UG Manual page, then transcribed into structured JSON files in `data/raw/structured/`. No automated scraping was used for official pages. Sources that could not be verified are marked `partially_verified` or `unresolved`.

Open learning resource data was collected by **manually visiting individual NPTEL, MIT OCW, OpenStax, and SWAYAM course pages** and recording the licence, format, duration, and URL for each. Licence information was read from each provider's official licence statement or footer.

The structured JSON files in `data/raw/structured/` are **the manually transcribed source records**. The original source documents (IIT Bhilai web pages) are referenced by URL in every record.

---

## 16. AI-Tool Usage Disclosure

This project was implemented with assistance from **Google Deepmind's Antigravity AI coding assistant** (Claude Sonnet 4.6 Thinking). The AI tool:
- Wrote the Python pipeline code (`src/*.py`, `run_pipeline.py`, `tests/*.py`).
- Wrote the documentation (`README.md`, `SOURCES.md`, `IDEAS.md`).
- Structured the JSON raw data files based on the assignment specification.

The **institutional data** (course codes, titles, syllabus outlines, academic rules) was manually verified against the IIT Bhilai official web sources referenced in each record's `source_url`. The AI did **not** fabricate source URLs, generate embeddings, or call any LLM API during pipeline execution.

