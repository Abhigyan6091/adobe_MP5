# IDEAS.md – How to Use This Data

## Three Student Questions the Buddy Could Answer Well

### 1. "What courses cover the skills I need for machine learning?"

The dataset contains **course-skill mappings** (`course_skill_links.csv`) that link each course to the skills it develops (e.g., DS301 → Machine Learning, MA201 → Linear Algebra, MA202 → Probability and Statistics). The buddy can query:

> *"Which B.Tech DSAI courses develop Machine Learning skills?"*  
> → DS301 (intro/core ML, working depth), DS401 (deep learning, advanced depth), MA301 (optimisation for ML)

It can also traverse the prerequisite graph to tell the student which courses they need to take first. This works reliably because the course-skill and prerequisite data is sourced directly from official curriculum documents.

---

### 2. "What are the prerequisites for a particular course?"

The `prerequisites.csv` file contains all hard and recommended prerequisites with their `kind` field. The buddy can traverse the full prerequisite chain, not just immediate requirements:

> *"What do I need before I can take Deep Learning (DS401)?"*  
> → Directly: DS301 (ML), MA201 (Linear Algebra).  
> → And before those: MA101 (Calculus), CS201 (DSA), MA202 (Probability).  
> → Chain: MA101 → MA201 → DS301 → DS401

The prerequisite graph is validated for cycles and missing references, so answers will be internally consistent.

---

### 3. "Which open resources can help me learn a specific skill?"

The `resource_skill_links.csv` file maps 32 open learning resources to 16 skill categories, with a `level` field (intro / working / advanced) and a `mapping_rationale`. The buddy can filter by skill and by licence verification status:

> *"I want to improve my Linear Algebra. What openly licensed resources are available?"*  
> → RES_009 (MIT OCW 18.06, CC BY-NC-SA 4.0, lecture notes + videos)  
> → RES_029 (NPTEL IIT Bombay, CC BY-SA 4.0, video lectures)

It can further prioritise by format (video vs textbook) or by level, and always provides a direct URL and licence.

---

## Questions the Buddy Cannot Yet Answer Reliably

### "What is my actual skill level in a subject?"

This requires **student-specific evidence**: quiz scores, assignment grades, or self-assessment data. The current dataset contains no student performance records (deliberately, per data ethics requirements). The buddy can only tell a student what a course *teaches*, not what they have *learned*.

### "Which course should I prioritise based on my grades?"

Personalised recommendations based on academic performance require CGPA data, completed course history, and remaining degree requirements — all student-specific information that is intentionally excluded from this dataset. The buddy could provide general prerequisite-chain guidance, but cannot personalise to an individual's academic record.

### "Am I personally eligible for a Minor programme?"

The minor eligibility rule (`RULE_MIN_001`) confirms that ~20 credits of minor courses are required, but the CGPA threshold (`RULE_MIN_002`) is marked **UNRESOLVED** — it could not be confirmed from publicly accessible official sources. Even if the threshold were known, verifying eligibility requires the student's own CGPA record, which is not in this dataset.

---

## How This Knowledge Base Supports Future Systems

### Knowledge Graph Relationships
The prerequisite graph (courses → required courses) and skill taxonomy (parent_skill_id) already form a directed acyclic graph (DAG) that a graph database or in-memory graph library could traverse. Future work: add `teaches → skill → unlocks → next_course` edges for richer traversal.

### Skill-Gap Analysis
Given a target role (e.g., "ML Engineer") and its required skill set, the system could identify which skills a student lacks, then recommend which courses or open resources most efficiently fill those gaps — using the `course_skill_links` and `resource_skill_links` depth levels.

### Course Recommendations
The prerequisite graph + skill mappings + resource mappings together support:
- "Take DS301 before DS401" (prerequisite chain)
- "Supplement DS301 with RES_002 (NPTEL ML)" (resource recommendation)
- "To reach skill level advanced in Deep Learning, complete DS401 and supplement with RES_003" (goal-driven path)

### Academic Constraint Checking
The academic rules (credit limits, prerequisite enforcement, NPTEL transfer policy) can be evaluated programmatically against a student's registration plan — without storing any personal data — to flag potential registration conflicts before they occur.

### Retrieval-Augmented Tutoring
The 175 chunks in `chunks.jsonl` are ready for a vector embedding stage. Once embedded, a retrieval-augmented generation (RAG) system could:
1. Receive a student question ("Explain what SVD is and which course covers it").
2. Retrieve the top-k syllabus chunks and skill descriptions.
3. Generate a grounded answer citing source URLs and course codes.

The `filter_metadata` on each chunk allows pre-filtering by course, semester, course type, or rule category before vector search, reducing noise and improving retrieval precision.

---

*These features are not implemented here. This note describes how the collected knowledge base lays the data foundation for them.*

