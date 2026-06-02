# Handoff trace

- Condition: `B1`
- Episode: `ep003_totalseg_whitelist_split`
- Pair: `haiku_x_qwen`
- Source run: `run_result/T2_fill/output/t2_matrix_20260508_205311`
- Verdict: `spec_weak`
- Handoff score: `6`
- Worker score: `7`

## Planner v1

```text
# TotalSeg Whitelist-Driven File Triage Worker Spec

## Overview
This worker processes one patient directory at a time, identifying mask files that fall outside a curated anatomical whitelist, moving them to an archive directory, and leaving only whitelisted files in the source directory.

## Input & Output Locations

**Source:** `<dataset_root>/totalseg_output/<patient_id>/`  
**Archive (triage destination):** `<archive_root>/<patient_id>/`  
**Whitelist reference:** `<workspace>/whitelist_notes.md`

All files in source are `.nii.gz` format (TotalSeg standard naming).

## Core Task

1. **Read whitelist definition** from `whitelist_notes.md` and construct an executable whitelist (exact filename set or matching rule).
2. **Enumerate all `.nii.gz` files** in source directory for the given `<patient_id>`.
3. **Classify each file** as whitelisted or non-whitelisted.
4. **Move non-whitelisted files** to `<archive_root>/<patient_id>/` (creating the archive directory if absent).
5. **Leave whitelisted files** in source directory untouched.
6. **Log all decisions** (whitelisted, moved, missing, errors) per patient.
7. **Continue processing** even if individual files are missing or errors occur; do not halt on per-patient failures.

## Whitelist Scope (Anatomical Categories)

The following anatomical structures are whitelisted:

- **Heart-related:** heart, heart chambers (atrium, ventricle), heart valves
- **Lung lobes:** lung_lower_lobe, lung_upper_lobe (left and right variants)
- **Ribs:** rib_left, rib_right (all numbered instances, e.g., rib_left_1 through rib_left_12)
- **Thoracic vertebrae:** vertebrae_T2 through vertebrae_T12 (T-segment only; exclude cervical C* and lumbar L*)
- **Clavicle:** clavicle (left and right)
- **Humerus:** humerus (left and right)
- **Sternum:** sternum
- **Aorta:** aorta

**Non-whitelisted examples (to be moved to archive):**
- kidney_left, kidney_right, spleen (abdominal organs)
- vertebrae_C3, vertebrae_L1 (non-thoracic spine)
- Any structure not listed above

## File Matching Strategy

**Decision:** Exact filename matching is required.

- TotalSeg produces fixed, deterministic filenames (e.g., `rib_left_1.nii.gz`, `heart_atrium_left.nii.gz`).
- `whitelist_notes.md` provides category descriptions and sample filenames, but is not a complete enumeration.
- **Worker must construct a complete, executable whitelist** by:
  - Parsing anatomical category descriptions from `whitelist_notes.md`.
  - Inferring the full set of valid TotalSeg filenames for each category (e.g., all rib_left_N, rib_right_N for N in valid range).
  - Documenting the inferred whitelist in the worker's output log.

## Triage Action

**Action:** Move (not copy, not delete).

- Non-whitelisted files are **moved** from source to archive.
- This preserves the non-whitelisted masks for future reference or retraining without duplication.
- Source directory is "slimmed down" to contain only whitelisted files after the operation.

## Directory Structure

**Archive mirroring:**
- Create `<archive_root>/<patient_id>/` if it does not exist.
- Move non-whitelisted files directly into this directory (flat structure, matching source layout).
- No subdirectories or renaming; preserve original filenames.

**Source directory:**
- Remains in place; only non-whitelisted files are removed.
- Whitelisted files stay in `<dataset_root>/totalseg_output/<patient_id>/`.

## Error Handling & Logging

**Missing files:**
- If a file listed in source inventory cannot be read or moved, log the filename and error.
- Do not halt processing; continue with remaining files.

**Logging output:**
- Per-patient log entry must include:
  - Patient ID
  - Count of whitelisted files (kept in source)
  - Count of non-whitelisted files (moved to archive)
  - List of any files that could not be processed (with reason)
  - Timestamp of operation
- Aggregate log across all patients processed in this worker invocation.

**Idempotency:**
- If a file already exists in the archive directory, document the conflict (do not overwrite without explicit policy).
- If a file has already been moved in a prior run, skip it and log as already-archived.

## Parallelization

- Worker processes one `<patient_id>` at a time.
- Multiple worker instances can run in parallel on different patient IDs.
- No shared state or locking required between patients.

## Constraints & Assumptions

- All source files are `.nii.gz`.
- Archive directory structure mirrors source (flat, one level deep).
- Whitelist is static for the duration of the worker run.
- No file renaming or transformation; only move operations.

---

```json
{
  "assumptions": [
    "All files in <dataset_root>/totalseg_output/<patient_id>/ are .nii.gz format with TotalSeg-standard filenames.",
    "whitelist_notes.md contains anatomical category descriptions and sample filenames sufficient to infer a complete executable whitelist.",
    "Archive directory <archive_root>/<patient_id>/ does not exist initially and must be created by the worker.",
    "Whitelisted files remain in source; non-whitelisted files are moved (not copied or deleted).",
    "Patient directories are independent; no cross-patient dependencies.",
    "Move operation is atomic or can be retried safely on failure."
  ],
  "risks": [
    "Incomplete whitelist inference: whitelist_notes.md may not enumerate all valid TotalSeg filenames for each category (e.g., rib numbering range, vertebrae T-segment boundaries). Worker must document assumptions about filename patterns.",
    "Filename ambiguity: similar-looking filenames (e.g., rib_left_1 vs. rib_left_10) must be matched exactly; substring or prefix matching will cause misclassification.",
    "Thoracic vertebrae boundary: vertebrae_T2–T12 must be distinguished from cervical (C*) and lumbar (L*); off-by-one errors in range will misclassify.",
    "Archive collision: if a file already exists in archive from a prior run, move operation may fail or overwrite silently depending on OS/tool behavior. Policy must be explicit.",
    "Partial failure: if a patient directory is incomplete (missing expected files), worker must log and continue, not halt.",
    "Disk space: moving large numbers of files may exhaust disk if archive and source are on the same filesystem. No pre-flight check specified."
  ],
  "open_questions": [
    "What is the exact, complete list of valid TotalSeg filenames for each whitelisted category? (e.g., rib_left_1 through rib_left_12? heart_atrium_left, heart_atrium_right, heart_ventricle_left, heart_ventricle_right, or a different set?)",
    "How should the worker infer the whitelist from whitelist_notes.md? Is there a structured format (YAML, JSON, regex patterns) or free-form markdown?",
    "What is the policy if a file already exists in the archive directory? (overwrite, skip, error, rename with timestamp?)",
    "Should the worker validate that all expected whitelisted files exist in the source, or only process files that are present?",
    "What is the resume/checkpoint mechanism if the worker is interrupted mid-patient or mid-batch? (e.g., marker file, database, or restart from scratch?)",
    "Should the worker report statistics (total files processed, total bytes moved) in addition to per-patient logs?",
    "Are there any file permission or ownership constraints when moving files between dataset_root and archive_root?"
  ]
}
```
```

## Worker v1

```text
{
  "understood_goal": "Process patient directories to identify and move non-whitelisted mask files to an archive directory, retaining only whitelisted files in the source directory. The whitelist is derived from a markdown reference file and must be fully enumerated for exact filename matching.",
  "constraints_to_follow": [
    "All source files are .nii.gz format with TotalSeg-standard filenames.",
    "Whitelist is constructed by parsing anatomical category descriptions from whitelist_notes.md and inferring complete filename sets.",
    "Exact filename matching is required; substring or prefix matching is not allowed.",
    "Only move files; do not copy or delete.",
    "Archive directory structure mirrors source (flat, one level deep).",
    "Processing is per-patient and independent; no shared state or locking required.",
    "Continue processing even if individual files are missing or errors occur.",
    "Log all decisions per patient including counts and errors.",
    "Do not halt on per-patient failures."
  ],
  "information_still_missing": [
    "The exact, complete list of valid TotalSeg filenames for each whitelisted category (e.g., rib numbering range, heart chamber variants).",
    "The structured format of whitelist_notes.md (e.g., is it YAML/JSON/regex-based or free-form markdown?).",
    "Policy for handling archive collisions (overwrite, skip, error, rename?).",
    "Whether the worker should validate presence of all expected whitelisted files or only process those present.",
    "Resume/checkpoint mechanism if worker is interrupted mid-patient or mid-batch.",
    "Whether additional statistics (e.g., total bytes moved) should be reported beyond per-patient logs.",
    "File permission or ownership constraints during file moves between dataset_root and archive_root."
  ],
  "first_3_concrete_actions": [
    "Parse whitelist_notes.md to extract anatomical category descriptions and infer complete filename sets for each category.",
    "Enumerate all .nii.gz files in the source directory for a given patient ID.",
    "Implement logic to classify each file as whitelisted or non-whitelisted based on exact filename match against the constructed whitelist."
  ]
}
```

## Planner v2

```text
# Planner Revision: Corrections & Missing Details for TotalSeg Whitelist Worker

## What Worker V1 Got Right

Worker V1 correctly understood:
- Move (not copy/delete) non-whitelisted files to archive.
- Exact filename matching is required.
- Per-patient, independent processing with no cross-patient locking.
- Continue on error; log failures without halting.
- Archive directory structure mirrors source (flat).

## Critical Misunderstandings & Gaps

### 1. **Whitelist Construction is Underspecified**

Worker V1 assumes `whitelist_notes.md` contains enough information to **infer** a complete, executable whitelist. This is unsafe.

**Reality from prompt:**
- The prompt lists anatomical *categories* (e.g., "heart-related," "ribs," "thoracic vertebrae") with English descriptions.
- It does **not** provide:
  - The exact TotalSeg filename for each structure (e.g., is it `heart` or `heart_organ` or `cardiac_chamber`?).
  - The complete enumeration of variants (e.g., how many ribs? `rib_left_1` through `rib_left_12`? Or a different range?).
  - Whether `heart_atrium_left` and `heart_atrium_right` are separate files or one file.
  - The exact vertebrae range (T2–T12? T1–T12? Inclusive?).

**Worker V1 error:** Assumes inference from markdown is sufficient. It is not.

**Correction:** The worker must **receive or load a pre-built, authoritative whitelist file** (e.g., `whitelist.json` or `whitelist.txt`) that enumerates exact filenames, not infer it from category descriptions. If such a file does not exist, the worker must **fail fast and report that the whitelist artifact is missing**, not guess.

---

### 2. **Whitelist Scope is Semantic, Not Syntactic**

The prompt lists categories like "heart-related" and "rib_left, rib_right (all numbered instances)." This is semantic guidance, not a regex or filename pattern.

**Worker V1 error:** Treats category descriptions as if they can be algorithmically expanded into filenames.

**Correction:** The worker must use a **pre-built, static whitelist artifact** that maps each category to its exact TotalSeg filenames. The worker does not infer or expand; it looks up.

---

### 3. **Archive Collision Policy is Unspecified**

Worker V1 notes the risk but does not resolve it.

**Correction:** The spec must state:
- If a file already exists in `<archive_root>/<patient_id>/`, should the worker:
  - Skip the move and log a warning?
  - Overwrite?
  - Rename with a timestamp suffix?
  - Treat as an error and halt the patient?

**This must be decided before implementation.** Do not assume a default.

---

### 4. **Idempotency Assumption is Incomplete**

Worker V1 says "if a file has already been moved in a prior run, skip it and log as already-archived." But how does the worker know a file was already moved?

**Correction:** The worker needs a **state tracking mechanism**:
- Option A: Check if the file exists in source. If not, assume it was moved; check archive.
- Option B: Maintain a per-patient checkpoint file (e.g., `.triage_complete` or a JSON log).
- Option C: Always re-scan and re-move (idempotent if archive collision policy is "skip").

**This must be specified.** Do not leave it to the worker to guess.

---

### 5. **Whitelist Validation is Missing**

Worker V1 does not address: what if the source directory is missing expected whitelisted files?

**Correction:** The spec must clarify:
- Should the worker validate that all expected whitelisted files exist in the source?
- Or should it only process files that are present and log missing ones as warnings?

---

## Still Missing (Not Safe to Assume)

1. **Authoritative whitelist artifact location and format.**
   - Is it `<workspace>/whitelist.json`? `<dataset_root>/whitelist.txt`? Embedded in the worker config?
   - What is the schema? (flat list of filenames, or category → filenames map?)

2. **Exact TotalSeg filenames for each whitelisted category.**
   - The prompt provides semantic categories, not filenames.
   - Worker must receive or load the definitive mapping.

3. **Archive collision policy.**
   - Overwrite, skip, error, or rename?

4. **Idempotency mechanism.**
   - How does the worker detect already-moved files?

5. **Validation scope.**
   - Should the worker check for missing expected files, or only process present files?

6. **Logging format and destination.**
   - Where should per-patient logs be written? (stdout, file, database?)
   - What is the exact schema? (JSON, CSV, plain text?)

---

## Worker Next Focus

1. **Verify the whitelist artifact:**
   - Ask: where is the authoritative whitelist stored?
   - Ask: what is its format and schema?
   - Load it and validate it contains exact TotalSeg filenames, not semantic categories.

2. **Clarify archive collision policy:**
   - Ask: if a file already exists in the archive, what should the worker do?

3. **Clarify idempotency:**
   - Ask: how should the worker detect already-moved files?
   - Ask: should it maintain a checkpoint file per patient?

4. **Clarify validation scope:**
   - Ask: should the worker validate that all expected whitelisted files exist, or only process present files?

5. **Clarify logging:**
   - Ask: where should logs be written?
   - Ask: what is the exact schema?

---

```json
{
  "corrected_constraints": [
    "The worker must use a pre-built, authoritative whitelist artifact (not infer it from markdown). This artifact must enumerate exact TotalSeg filenames, not semantic categories.",
    "Exact filename matching is required; no inference, expansion, or pattern matching.",
    "Move (not copy/delete) non-whitelisted files to archive.",
    "Archive directory structure mirrors source (flat, one level deep).",
    "Processing is per-patient and independent; no cross-patient locking.",
    "Continue processing on per-file errors; log failures without halting the patient.",
    "Archive collision policy must be explicitly defined (overwrite, skip, error, or rename). Do not assume a default.",
    "Idempotency mechanism must be explicitly defined (state tracking, checkpoint file, or re-scan logic). Do not assume a default.",
    "Validation scope must be explicitly defined (check for missing expected files, or only process present files). Do not assume a default."
  ],
  "still_missing": [
    "Location and format of the authoritative whitelist artifact (e.g., whitelist.json, whitelist.txt, embedded config).",
    "Schema of the whitelist artifact (flat list of filenames, or category → filenames map?).",
    "Exact TotalSeg filenames for each whitelisted category (the prompt provides semantic categories, not filenames).",
    "Archive collision policy (overwrite, skip, error, rename with timestamp?).",
    "Idempotency mechanism (state tracking, checkpoint file, or re-scan logic?).",
    "Validation scope (check for missing expected files, or only process present files?).",
    "Logging format and destination (stdout, file, database? JSON, CSV, plain text?).",
    "Logging schema (what fields must each log entry contain?)."
  ],
  "worker_next_focus": [
    "Verify the location and format of the authoritative whitelist artifact before attempting to parse or infer it.",
    "Load the whitelist and validate that it contains exact TotalSeg filenames, not semantic categories or patterns.",
    "Clarify the archive collision policy with the planner or spec owner.",
    "Clarify the idempotency mechanism (how to detect already-moved files, whether to maintain checkpoints).",
    "Clarify the validation scope (whether to check for missing expected files).",
    "Clarify the logging format, destination, and schema."
  ]
}
```
```

## Worker v2

```text
{
  "understood_goal": "Process patient directories to identify and move non-whitelisted mask files to an archive directory, retaining only whitelisted files in the source directory. The whitelist must be a pre-built, authoritative artifact containing exact TotalSeg filenames, not inferred from semantic descriptions.",
  "constraints_to_follow": [
    "The worker must use a pre-built, authoritative whitelist artifact (not infer it from markdown). This artifact must enumerate exact TotalSeg filenames, not semantic categories.",
    "Exact filename matching is required; no inference, expansion, or pattern matching.",
    "Move (not copy/delete) non-whitelisted files to archive.",
    "Archive directory structure mirrors source (flat, one level deep).",
    "Processing is per-patient and independent; no cross-patient locking.",
    "Continue processing on per-file errors; log failures without halting the patient.",
    "Archive collision policy must be explicitly defined (overwrite, skip, error, or rename). Do not assume a default.",
    "Idempotency mechanism must be explicitly defined (state tracking, checkpoint file, or re-scan logic). Do not assume a default.",
    "Validation scope must be explicitly defined (check for missing expected files, or only process present files). Do not assume a default."
  ],
  "information_still_missing": [
    "Location and format of the authoritative whitelist artifact (e.g., whitelist.json, whitelist.txt, embedded config).",
    "Schema of the whitelist artifact (flat list of filenames, or category → filenames map?).",
    "Exact TotalSeg filenames for each whitelisted category (the prompt provides semantic categories, not filenames).",
    "Archive collision policy (overwrite, skip, error, rename with timestamp?).",
    "Idempotency mechanism (state tracking, checkpoint file, or re-scan logic?).",
    "Validation scope (check for missing expected files, or only process present files?).",
    "Logging format and destination (stdout, file, database? JSON, CSV, plain text?).",
    "Logging schema (what fields must each log entry contain?)."
  ],
  "first_3_concrete_actions": [
    "Verify the location and format of the authoritative whitelist artifact before attempting to parse or infer it.",
    "Load the whitelist and validate that it contains exact TotalSeg filenames, not semantic categories or patterns.",
    "Clarify the archive collision policy with the planner or spec owner."
  ],
  "understanding_delta": [
    "Previously, I assumed the worker could infer a complete whitelist from the markdown description. Now I understand this is not safe and requires a pre-built artifact.",
    "I previously treated semantic category descriptions as expandable into filenames, but the revision clarifies these are just guidance and not actionable patterns.",
    "I need to explicitly define behaviors around archive collisions, idempotency, and validation scope rather than assuming defaults.",
    "The requirement for a definitive whitelist artifact means I must validate that the input data matches expectations before proceeding."
  ]
}
```

## Judge summary

- Verdict: `spec_weak`
- Handoff score: `6`
- Spec score: `6`
- Worker score: `7`

### Concise rationale

Planner v1 is unsafe because it invents whitelist expansion rules and concrete anatomical ranges. Planner v2 meaningfully corrects that by flagging the whitelist as unresolved and requiring an authoritative artifact. Worker v1 follows the weak planner too closely; worker v2 improves by preserving missing-info state and exact-match caution. Overall this is a weak-to-acceptable handoff, but not strong because the initial spec crosses the forbidden assumption boundary.

### Covered gold constraints

- Source and archive paths are identified correctly
- Move non-whitelist files to archive is preserved
- Missing files should be logged and skipped without stopping the run
- Planner_v2 explicitly rejects prefix/category expansion as a safe substitute
- Worker_v2 correctly preserves the whitelist artifact as missing information rather than inventing exact filenames
- Worker_v2 keeps archive collision and idempotency as unresolved

### Missed gold constraints

- Planner_v1 incorrectly invents semantic category expansion and complete whitelist inference
- Planner_v1 states rib_left/rib_right all numbered instances and thoracic vertebrae ranges as if known, which is a forbidden assumption
- Planner_v1 adds a complete whitelist-like mapping that is not grounded in the visible task
- Mirrored archive structure is stated, but not with the exact patient-level file mirror `<archive_root>/<patient_id>/<file>.nii.gz>` as a precise rule
- The planner does not clearly anchor the worker on exact filename membership using the visible examples `rib_left_1` vs `rib_left_10`
- The planner does not explicitly preserve the real boundary that unresolved whitelist material must remain unresolved rather than guessed

### Forbidden assumptions made

- Planner_v1 assumed the whitelist can be inferred from markdown category descriptions
- Planner_v1 assumed rib numbering ranges and thoracic vertebrae ranges without authoritative support
- Planner_v1 treated category words as executable filename rules
- Planner_v1 effectively turned an exact whitelist task into a convenient semantic expansion task
