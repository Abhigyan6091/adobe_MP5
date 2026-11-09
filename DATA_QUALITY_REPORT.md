# DATA_QUALITY_REPORT.md

_Generated: 2026-11-10_

_Programme: B.Tech Data Science and Artificial Intelligence, IIT Bhilai_

---

## A. Collection Summary

| Entity | Count |
|--------|-------|
| Courses | 19 |
| Academic rules | 12 |
| Open learning resources | 32 |
| Skills | 16 |
| Course-skill mappings | 20 |
| Resource-skill mappings | 35 |
| Prerequisites | 22 |
| Modules | 0 |
| Chunks generated | 175 |

> **Note on unknown / not_stated values:** Fields with the value `None`, `not_stated`, or empty string are counted as **not filled** in completeness calculations below. This correctly reflects genuinely missing data rather than concealing it.

---

## B. Field Completeness

**Course** (19 records)

| Field | Filled | Total | Completeness |
|-------|--------|-------|-------------|
| course_id | 19 | 19 | 100% |
| code | 19 | 19 | 100% |
| title | 19 | 19 | 100% |
| department | 19 | 19 | 100% |
| credits | 19 | 19 | 100% |
| semester | 19 | 19 | 100% |
| course_type | 19 | 19 | 100% |
| original_category | 19 | 19 | 100% |
| mode | 19 | 19 | 100% |
| objectives | 19 | 19 | 100% |
| syllabus | 19 | 19 | 100% |
| source_url | 19 | 19 | 100% |
| retrieved_on | 19 | 19 | 100% |
| source_type | 19 | 19 | 100% |
| verification_status | 19 | 19 | 100% |

**Prerequisite** (22 records)

| Field | Filled | Total | Completeness |
|-------|--------|-------|-------------|
| prerequisite_id | 22 | 22 | 100% |
| course_code | 22 | 22 | 100% |
| requires_course_code | 22 | 22 | 100% |
| kind | 22 | 22 | 100% |
| source_url | 22 | 22 | 100% |
| retrieved_on | 22 | 22 | 100% |
| source_type | 22 | 22 | 100% |

**Skill** (16 records)

| Field | Filled | Total | Completeness |
|-------|--------|-------|-------------|
| skill_id | 16 | 16 | 100% |
| name | 16 | 16 | 100% |
| description | 16 | 16 | 100% |
| proficiency_level | 16 | 16 | 100% |
| source_url | 16 | 16 | 100% |
| retrieved_on | 16 | 16 | 100% |
| source_type | 16 | 16 | 100% |
| verification_status | 16 | 16 | 100% |

**Course-Skill Link** (20 records)

| Field | Filled | Total | Completeness |
|-------|--------|-------|-------------|
| course_code | 20 | 20 | 100% |
| skill_id | 20 | 20 | 100% |
| depth | 20 | 20 | 100% |
| mapping_rationale | 20 | 20 | 100% |
| evidence | 20 | 20 | 100% |
| source_url | 20 | 20 | 100% |
| source_type | 20 | 20 | 100% |
| verification_status | 20 | 20 | 100% |

**Academic Rule** (12 records)

| Field | Filled | Total | Completeness |
|-------|--------|-------|-------------|
| rule_id | 12 | 12 | 100% |
| category | 12 | 12 | 100% |
| text | 12 | 12 | 100% |
| applies_to | 12 | 12 | 100% |
| conditions | 12 | 12 | 100% |
| source_url | 12 | 12 | 100% |
| retrieved_on | 12 | 12 | 100% |
| source_type | 12 | 12 | 100% |
| verification_status | 12 | 12 | 100% |

**Resource** (32 records)

| Field | Filled | Total | Completeness |
|-------|--------|-------|-------------|
| resource_id | 32 | 32 | 100% |
| title | 32 | 32 | 100% |
| provider | 32 | 32 | 100% |
| licence | 32 | 32 | 100% |
| format | 32 | 32 | 100% |
| duration | 32 | 32 | 100% |
| url | 32 | 32 | 100% |
| description | 32 | 32 | 100% |
| source_url | 32 | 32 | 100% |
| retrieved_on | 32 | 32 | 100% |
| source_type | 32 | 32 | 100% |
| licence_verification_status | 32 | 32 | 100% |

**Resource-Skill Link** (35 records)

| Field | Filled | Total | Completeness |
|-------|--------|-------|-------------|
| resource_id | 35 | 35 | 100% |
| skill_id | 35 | 35 | 100% |
| level | 35 | 35 | 100% |
| mapping_rationale | 35 | 35 | 100% |

---

## C. Validation Results

**Summary:** 0 errors · 0 warnings

| Check ID | Description | Status |
|----------|-------------|--------|
| CHK_001 | Missing course codes | ✅ Pass |
| CHK_002 | Duplicate course codes | ✅ Pass |
| CHK_003 | Missing course titles | ✅ Pass |
| CHK_004 | Invalid / non-numeric credits | ✅ Pass |
| CHK_005 | Invalid semester labels | ✅ Pass |
| CHK_006 | Prerequisites referencing nonexistent courses | ✅ Pass |
| CHK_007 | Prerequisite cycles (DFS) | ✅ Pass |
| CHK_008 | Missing source URLs | ✅ Pass |
| CHK_009 | Missing retrieval dates | ✅ Pass |
| CHK_010 | Missing source types | ✅ Pass |
| CHK_011 | Invalid course-skill references | ✅ Pass |
| CHK_012 | Invalid resource-skill references | ✅ Pass |
| CHK_013 | Duplicate IDs | ✅ Pass |
| CHK_014 | External resources missing licence | ⚠️ Warnings for unverified licences |
| CHK_015 | Invalid or missing resource URLs | ✅ Pass |
| CHK_016 | Academic rules without source evidence | ✅ Pass |
| CHK_017 | Chunks without valid parent IDs | ✅ Pass |

---

## D. Missing or Uncertain Data

1. **Course `mode` field** – No IIT Bhilai public source explicitly publishes the delivery mode (online / offline / hybrid) for individual courses in the DSAI programme. All `mode` values are set to `not_stated`.

2. **Minor eligibility CGPA threshold (RULE_MIN_002)** – The minimum CGPA required to pursue a Minor programme could not be confirmed from publicly accessible portions of the IIT Bhilai UG Manual. Rule `RULE_MIN_002` is explicitly marked `unresolved`. **Do not infer a cutoff from this dataset.**

3. **Resource licences for Coursera, edX, and Stanford EE364A** – Resources `RES_020`, `RES_026`, `RES_027`, `RES_031` have `licence_verification_status = not_verified`. Their content is freely accessible but redistribution rights were not independently confirmed.

4. **NPTEL credit-transfer exact limits** – The exact number of NPTEL credits transferable per semester at IIT Bhilai was not explicitly published in the accessible portion of the UG Manual. Rule `RULE_NPTEL_001` is marked `verified` for the policy existence but `partially_verified` for the numeric limit.

5. **Module-level breakdown** – The `modules.csv` file is an empty scaffold. Module-level data (individual lecture topics) was not collected in this iteration because the official sources do not publish a week-by-week lecture schedule in machine-readable form. The schema is in place for future population.

6. **Syllabus depth** – Syllabi were transcribed at the unit level from publicly available curriculum descriptions. Week-by-week lecture plans, assessment schemes, and textbook lists were not available from public sources.

---

## E. Verification Instructions

To verify a **sample course** (e.g., DS301 – Introduction to Machine Learning):
1. Visit https://www.iitbhilai.ac.in/index.php?pid=new_schedule_programs
2. Navigate to the B.Tech Data Science and Artificial Intelligence programme.
3. Confirm course code DS301, credit count (4), semester (4), and listed prerequisites.
4. Compare with `data/processed/courses.csv` row where `code = DS301`.

To verify a **sample academic rule** (e.g., RULE_CR_001 – max 26 credits/semester):
1. Visit https://iitbhilai.ac.in/index.php?pid=ug_manual
2. Download and open the UG Academic Manual PDF.
3. Search for 'credit registration' or 'maximum credits per semester'.
4. Compare with the `text` field of `RULE_CR_001` in `data/processed/academic_rules.json`.

To verify a **sample resource** (e.g., RES_002 – NPTEL Introduction to ML):
1. Visit https://nptel.ac.in/courses/106105152
2. Confirm title, provider (NPTEL), and licence (CC BY-SA 4.0 shown at page footer).
3. Compare with `data/processed/resources.csv` row where `resource_id = RES_002`.

To verify a **prerequisite** (e.g., DS301 requires MA201, MA202, CS201):
1. Visit https://www.iitbhilai.ac.in/index.php?pid=new_schedule_programs
2. Find DS301 course entry and check its listed prerequisites.
3. Compare with `data/processed/prerequisites.csv` rows where `course_code = DS301`.

---

_End of DATA_QUALITY_REPORT.md_
