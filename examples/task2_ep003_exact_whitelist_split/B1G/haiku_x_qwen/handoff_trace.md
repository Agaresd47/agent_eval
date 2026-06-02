# Handoff trace

- Condition: `B1_guardrailed`
- Episode: `ep003_totalseg_whitelist_split`
- Pair: `haiku_x_qwen`
- Source run: `run_result/T2_pilot_V1/output/t2_matrix_20260505_104505`
- Verdict: `spec_acceptable`
- Handoff score: `6`
- Worker score: `6`

## Planner v1

```text
# TotalSeg Mask Whitelist-Driven File Segregation — Worker Implementation Spec

## Overview

This worker processes patient directories from TotalSeg output, segregating mask files into two groups:
- **Retain in source**: Files matching a curated whitelist of anatomical structures
- **Move to archive**: All other files, preserved in a mirrored archive directory

The worker must operate **per-patient in parallel**, log missing/anomalous files without halting, and ensure the source directory contains only whitelisted masks after completion.

---

## Observed Facts

1. **Source structure**: `<dataset_root>/totalseg_output/<patient_id>/` contains flat `.nii.gz` files (no subdirectories)
2. **Archive structure**: `<archive_root>/<patient_id>/` is initially empty; will receive non-whitelisted files
3. **File naming**: TotalSeg uses fixed anatomical names (e.g., `rib_left_1.nii.gz`, `vertebrae_T5.nii.gz`), not arbitrary prefixes
4. **Whitelist source**: `<workspace>/whitelist_notes.md` documents *categories* (heart-related, lung lobes, ribs, thoracic vertebrae T2–T12, clavicle, humerus, sternum, aorta) with *example* filenames, not an exhaustive enumeration
5. **Scope**: Thoracic vertebrae only (T2–T12); cervical and lumbar excluded
6. **Action**: Move (not copy or delete) non-whitelisted files to archive
7. **Parallelism**: Patient-level independence allows concurrent processing
8. **Fault tolerance**: Missing or anomalous files logged but do not stop the worker

---

## Implementation Constraints

### 1. Whitelist Matching Strategy

**Decision required**: The whitelist must be **explicit and complete** before worker execution.

- **Not acceptable**: Inferring patterns from example filenames (e.g., "all files starting with `rib_`")
- **Required**: A definitive list of TotalSeg anatomical structure identifiers that map to the named categories

**Matching approach**:
- Match against the **base filename stem** (without `.nii.gz` extension)
- Use **exact string matching** or a **predefined set membership** (e.g., a JSON/YAML lookup table)
- Do not use regex or glob patterns unless the whitelist explicitly defines them

**Example structure** (to be provided by requester):
```
whitelist = {
  "heart": ["heart", "heart_atrium_left", "heart_atrium_right", ...],
  "lung_lobes": ["lung_lower_lobe_left", "lung_lower_lobe_right", ...],
  "ribs": ["rib_left_1", "rib_left_2", ..., "rib_right_12"],
  "thoracic_vertebrae": ["vertebrae_T2", "vertebrae_T3", ..., "vertebrae_T12"],
  "clavicle": ["clavicle_left", "clavicle_right"],
  "humerus": ["humerus_left", "humerus_right"],
  "sternum": ["sternum"],
  "aorta": ["aorta"]
}
```

### 2. File Movement Semantics

- **Action**: `MOVE` (not copy, not delete)
  - Source file is removed from `<dataset_root>/totalseg_output/<patient_id>/` after successful transfer
  - Destination file appears in `<archive_root>/<patient_id>/`
  - If move fails, log error and skip; do not retry or fall back to copy
  
- **Atomicity**: Move should be atomic at the filesystem level (rename if same filesystem, else copy + delete with verification)

### 3. Target Directory Structure

- **Mirror structure**: `<archive_root>/<patient_id>/` mirrors the flat structure of the source
  - Source: `<dataset_root>/totalseg_output/<patient_id>/kidney_left.nii.gz`
  - Archive: `<archive_root>/<patient_id>/kidney_left.nii.gz`
  - No subdirectories or category-based grouping in archive
  
- **Directory creation**: Ensure `<archive_root>/<patient_id>/` exists before moving files; create if absent

### 4. Missing and Anomalous File Handling

**Missing files** (expected in whitelist but absent from source):
- Log as `WARN` with patient ID and filename
- Do not fail the patient job
- Continue processing remaining files

**Unexpected files** (present in source but not in whitelist):
- Treat as non-whitelisted; move to archive
- Log as `INFO` (expected behavior)

**Malformed filenames** (e.g., missing `.nii.gz` extension, non-ASCII characters):
- Log as `WARN` with patient ID and filename
- Skip the file; do not move or delete
- Continue processing

**Unreadable/inaccessible files** (permission denied, I/O error):
- Log as `ERROR` with patient ID, filename, and error message
- Skip the file; do not halt the patient job
- Continue processing

### 5. Completion and Verification

**Per-patient completion**:
- After all files are processed, verify that `<dataset_root>/totalseg_output/<patient_id>/` contains **only** whitelisted files
- Log count of retained, moved, and skipped files
- Write a per-patient summary (e.g., JSON or TSV) with:
  - `patient_id`
  - `files_retained` (count)
  - `files_moved` (count)
  - `files_skipped` (count)
  - `errors` (list of anomalies)

**No global completion marker** is specified; assume each patient is independent.

---

## Worker First Actions

1. **Load and validate whitelist**:
   - Read the definitive whitelist (source TBD; not `whitelist_notes.md` alone)
   - Verify it is non-empty and contains only valid TotalSeg structure names
   - Fail fast if whitelist is malformed or missing

2. **Enumerate patient directories**:
   - Scan `<dataset_root>/totalseg_output/` for subdirectories matching patient ID pattern
   - For each patient, proceed independently

3. **For each patient**:
   - List all `.nii.gz` files in `<dataset_root>/totalseg_output/<patient_id>/`
   - Classify each file as whitelisted or non-whitelisted
   - Create `<archive_root>/<patient_id>/` if it does not exist
   - Move non-whitelisted files to archive
   - Log anomalies and completion summary

4. **Logging**:
   - Write structured logs (JSON or TSV) with patient ID, action, filename, status, and error details
   - Ensure logs are queryable for audit and debugging

---

## Risks and Constraints

| Risk | Mitigation |
|------|-----------|
| **Incomplete whitelist** | Requester must provide exhaustive, machine-readable whitelist before worker runs. Do not infer from examples. |
| **Filesystem atomicity** | Move operations may fail mid-transfer (disk full, permission denied). Log and skip; do not retry or corrupt state. |
| **Patient-level parallelism** | Ensure no shared state or race conditions between patient jobs. Use per-patient locks if needed. |
| **Archive directory collision** | If `<archive_root>/<patient_id>/` already contains files, decide: overwrite, skip, or error. (Open question.) |
| **Whitelist drift** | If whitelist changes mid-run, behavior is undefined. Lock whitelist before starting. |
| **Large file counts** | If a patient has 100+ files, memory and I/O may be bottlenecks. Stream processing recommended. |

---

## Open Questions

1. **Whitelist source and format**:
   - Where is the definitive, machine-readable whitelist stored?
   - Is it a JSON/YAML file, a database query, or embedded in code?
   - Does `whitelist_notes.md` need to be parsed, or is it documentation only?

2. **Patient ID pattern**:
   - What is the exact regex or naming convention for patient directories (e.g., `case_*`, `patient_*`, UUID)?
   - Are there any patient IDs to skip or filter?

3. **Archive collision policy**:
   - If `<archive_root>/<patient_id>/` already exists with files, should the worker:
     - Overwrite existing files?
     - Skip and log?
     - Fail the patient job?

4. **Whitelist validation**:
   - Should the worker verify that all whitelisted structures exist in at least one patient, or is it acceptable for some to be absent?

5. **Logging destination**:
   - Where should per-patient summaries and error logs be written?
   - What is the expected format (JSON, TSV, plain text)?

6. **Resume/idempotency**:
   - If the worker is interrupted and restarted, should it:
     - Re-process all patients?
     - Skip patients already completed (and how to detect completion)?
     - Verify archive integrity before re-processing?

7. **File extension validation**:
   - Should the worker reject files that do not end in `.nii.gz`?
   - Are there other valid extensions (e.g., `.nii`, `.gz`)?

8. **Whitelist scope for thoracic vertebrae**:
   - The request specifies T2–T12. Should the worker reject T1 or T13+ if present?
   - Or should it log them as non-whitelisted and move them?

---

```json
{
  "assumptions": [
    "Whitelist will be provided as a machine-readable, exhaustive list of TotalSeg anatomical structure identifiers (not inferred from whitelist_notes.md examples
```

## Worker v1

```text
{
  "understood_goal": "Process patient directories from TotalSeg output to segregate mask files into whitelisted (retained) and non-whitelisted (moved to archive) categories, ensuring each patient's source directory contains only whitelisted files after processing.",
  "constraints_to_follow": [
    "Operate per-patient in parallel with no shared state or race conditions.",
    "Use exact string matching against a predefined whitelist for file classification.",
    "Move non-whitelisted files atomically from source to archive directory.",
    "Log missing/anomalous files without halting execution.",
    "Ensure archive directory structure mirrors source flat structure.",
    "Only process files ending in `.nii.gz` extension.",
    "Verify that the whitelist is exhaustive and machine-readable before execution.",
    "Do not infer whitelist entries from examples in documentation like `whitelist_notes.md`.",
    "Do not make assumptions about patient ID naming conventions or filtering rules.",
    "Do not assume behavior for archive directory collisions or resume/idempotency."
  ],
  "information_still_missing": [
    "The definitive, machine-readable whitelist data structure (format and location).",
    "The exact regex or naming convention for patient directories under `<dataset_root>/totalseg_output/`.",
    "Policy for handling pre-existing files in `<archive_root>/<patient_id>/`.",
    "Location and format of per-patient summary/error logs.",
    "Whether the worker should validate that all whitelisted structures appear in at least one patient.",
    "Whether the worker needs to support resuming or idempotent operation.",
    "Clarification on whether `.nii` or other extensions are also valid (beyond `.nii.gz`).",
    "Specific handling instructions for T1 or T13+ thoracic vertebrae if present in files."
  ],
  "first_3_concrete_actions": [
    "Request the definitive whitelist in a machine-readable format (e.g., JSON/YAML) and confirm its completeness and validity.",
    "Confirm the exact naming convention or regex pattern for patient directories under the dataset root.",
    "Define the policy for handling existing files in the archive directory (overwrite, skip, or error)."
  ]
}
```

## Planner v2

```text
# Planner Revision: Corrections and Clarifications for Worker v1

## What Worker v1 Got Right

Worker v1 correctly identified:
- Per-patient parallelism with no shared state
- Exact string matching (not regex inference) for whitelist classification
- Atomic move semantics (not copy or delete)
- Flat archive directory structure mirroring source
- Logging without halting on anomalies
- The need for a machine-readable, exhaustive whitelist before execution

## Critical Corrections and Gaps

### 1. **Whitelist Matching: Filename Stem vs. Full Filename**

Worker v1 stated: "Match against the **base filename stem** (without `.nii.gz` extension)."

**Correction needed**: The prompt does not specify whether TotalSeg filenames are:
- Single-word stems (e.g., `heart`, `sternum`) that match exactly, or
- Compound stems with underscores (e.g., `heart_atrium_left`, `rib_left_1`) that require exact matching

**What must be verified**: Provide 3–5 actual example filenames from a real patient directory to confirm the exact naming scheme. Do not assume the example `rib_left_1.nii.gz` is representative of all rib files.

### 2. **Whitelist Completeness: Categories vs. Enumeration**

Worker v1 correctly flagged that the prompt lists *categories* (heart-related, lung lobes, ribs, thoracic vertebrae, etc.) but does not enumerate all member filenames.

**Critical gap**: The prompt references `<workspace>/whitelist_notes.md` as documentation, but does **not** state whether:
- That file contains the exhaustive, machine-readable whitelist, or
- It is documentation only and a separate whitelist file (JSON/YAML) exists elsewhere

**What must be verified**: Confirm the exact location and format of the definitive whitelist. If `whitelist_notes.md` is the source, provide its full content or a machine-readable export.

### 3. **Thoracic Vertebrae Scope: T2–T12 Enforcement**

Worker v1 asked: "Should the worker reject T1 or T13+ if present?"

**Clarification**: The prompt states the whitelist will "保留…胸椎（T 段）" (retain thoracic vertebrae T segment) and later specifies "T2–T12" in the spec. 

**What must be verified**: 
- Should T1 (cervical) or T13+ (lumbar) be treated as non-whitelisted and moved to archive?
- Or should they be logged as anomalies and skipped (not moved)?
- Assume: T1 and T13+ are **not** in the whitelist and will be moved to archive like any other non-whitelisted file.

### 4. **File Extension Validation**

Worker v1 asked: "Should the worker reject files that do not end in `.nii.gz`?"

**Assumption to lock in**: Only process files ending in `.nii.gz`. Files with other extensions (`.nii`, `.gz`, `.nii.bak`, etc.) are treated as malformed and skipped with a `WARN` log. Do not move them.

### 5. **Archive Directory Collision Policy**

Worker v1 flagged this as an open question. 

**What must be verified**: If `<archive_root>/<patient_id>/` already exists with files:
- Should the worker overwrite, skip, or error?
- Assume for now: **Overwrite** (move will replace existing files with the same name). If this is wrong, it must be corrected before execution.

### 6. **Resume and Idempotency**

Worker v1 asked whether the worker should support resuming after interruption.

**Assumption to lock in**: The worker is **not** required to support resume or idempotency. Each run is independent. If interrupted, the next run will re-process all patients. (If resume is needed, it must be specified separately.)

### 7. **Patient Directory Enumeration**

Worker v1 asked: "What is the exact regex or naming convention for patient directories?"

**What must be verified**: Provide the exact pattern or list of patient IDs to process. The prompt uses `<patient_id>` as a placeholder but does not define the pattern (e.g., `case_001`, `patient_uuid`, numeric ID).

### 8. **Logging Output Location and Format**

Worker v1 asked where per-patient summaries should be written.

**What must be verified**: Specify:
- Output directory for logs (e.g., `<workspace>/logs/`, `<dataset_root>/logs/`)
- Format (JSON, TSV, plain text)
- Whether a single aggregated log or per-patient files

**Assume for now**: Write per-patient JSON summaries to `<workspace>/segregation_logs/<patient_id>.json` with fields: `patient_id`, `files_retained`, `files_moved`, `files_skipped`, `errors` (list of dicts with filename and reason).

### 9. **Missing Whitelisted Files**

Worker v1 stated: "Log as `WARN` with patient ID and filename; do not fail the patient job."

**Clarification**: This is correct. However, the worker should **not** attempt to verify that all whitelisted structures exist in every patient. Some patients may legitimately lack certain structures. Only log if a file is expected (in whitelist) but absent; do not fail.

### 10. **Unexpected Files (Non-Whitelisted)**

Worker v1 stated: "Treat as non-whitelisted; move to archive; log as `INFO`."

**Correction**: Log as `INFO` only if the file is a valid `.nii.gz` file. If it is malformed or unreadable, log as `WARN` or `ERROR` and skip (do not move).

---

## Worker Next Steps (Before Implementation)

1. **Obtain the definitive whitelist** in machine-readable format (JSON/YAML). If `whitelist_notes.md` is the source, export it or provide its full content.
2. **Confirm patient directory naming pattern** and provide 3–5 example patient IDs.
3. **Provide 3–5 real example filenames** from a patient directory to confirm TotalSeg naming scheme.
4. **Lock in archive collision policy**: Overwrite, skip, or error?
5. **Confirm logging output location and format**.
6. **Verify that T1 and T13+ vertebrae (if present) should be moved to archive** as non-whitelisted files.

---

```json
{
  "corrected_constraints": [
    "Match whitelisted files using exact string comparison against a definitive, machine-readable whitelist (format and location TBD).",
    "Only process files with `.nii.gz` extension; skip or warn on other extensions without moving.",
    "Move non-whitelisted `.nii.gz` files atomically from source to archive; do not copy or delete.",
    "Archive directory structure mirrors source flat structure; no category-based subdirectories.",
    "Log missing whitelisted files as WARN but do not fail the patient job; do not verify all whitelisted structures exist in every patient.",
    "Log unexpected (non-whitelisted) files as INFO if valid `.nii.gz`; log as WARN/ERROR if malformed and skip without moving.",
    "Treat T1 and T13+ thoracic vertebrae (if present) as non-whitelisted and move to archive.",
    "Do not support resume or idempotency; each run is independent.",
    "Per-patient parallelism with no shared state or race conditions.",
    "Write per-patient summary logs (format and location TBD) with counts and error details."
  ],
  "still_missing": [
    "Definitive whitelist: exact location, format (JSON/YAML/other), and complete enumeration of whitelisted TotalSeg structure identifiers.",
    "Patient directory naming convention or regex pattern (e.g., case_001, patient_uuid, numeric ID).",
    "3–5 real example filenames from a patient directory to confirm TotalSeg naming scheme (e.g., are all ribs named rib_left_1, rib_left_2, etc., or is there variation?).",
    "Archive collision policy: if <archive_root>/<patient_id>/ already exists with files, should worker overwrite, skip, or error?",
    "Logging output location (directory path) and format (JSON, TSV, plain text).",
    "Confirmation that T1 and T13+ vertebrae should be treated as non-whitelisted and moved to archive (not skipped or errored).",
    "Whether the worker should validate whitelist completeness or just use it as-is."
  ],
  "worker_next_focus": [
    "Request the definitive whitelist in machine-readable format and confirm it is exhaustive and valid.",
    "Obtain 3–5 real example filenames from a patient directory to lock in the exact TotalSeg naming scheme.",
    "Confirm the patient directory naming pattern and provide example patient IDs.",
    "Clarify archive collision policy (overwrite, skip, or error).",
    "Specify logging output location and format.",
    "Verify that T1 and T13+ vertebrae (if present) should be moved to archive as non-whitelisted files."
  ]
}
```
```

## Worker v2

```text
{
  "understood_goal": "Process patient directories from TotalSeg output to segregate mask files into whitelisted (retained) and non-whitelisted (moved to archive) categories, ensuring each patient's source directory contains only whitelisted files after processing.",
  "constraints_to_follow": [
    "Match whitelisted files using exact string comparison against a definitive, machine-readable whitelist (format and location TBD).",
    "Only process files with `.nii.gz` extension; skip or warn on other extensions without moving.",
    "Move non-whitelisted `.nii.gz` files atomically from source to archive; do not copy or delete.",
    "Archive directory structure mirrors source flat structure; no category-based subdirectories.",
    "Log missing whitelisted files as WARN but do not fail the patient job; do not verify all whitelisted structures exist in every patient.",
    "Log unexpected (non-whitelisted) files as INFO if valid `.nii.gz`; log as WARN/ERROR if malformed and skip without moving.",
    "Treat T1 and T13+ thoracic vertebrae (if present) as non-whitelisted and move to archive.",
    "Do not support resume or idempotency; each run is independent.",
    "Per-patient parallelism with no shared state or race conditions.",
    "Write per-patient summary logs (format and location TBD) with counts and error details."
  ],
  "information_still_missing": [
    "Definitive whitelist: exact location, format (JSON/YAML/other), and complete enumeration of whitelisted TotalSeg structure identifiers.",
    "Patient directory naming convention or regex pattern (e.g., case_001, patient_uuid, numeric ID).",
    "3–5 real example filenames from a patient directory to confirm TotalSeg naming scheme (e.g., are all ribs named rib_left_1, rib_left_2, etc., or is there variation?).",
    "Archive collision policy: if <archive_root>/<patient_id>/ already exists with files, should worker overwrite, skip, or error?",
    "Logging output location (directory path) and format (JSON, TSV, plain text).",
    "Confirmation that T1 and T13+ vertebrae should be treated as non-whitelisted and moved to archive (not skipped or errored).",
    "Whether the worker should validate whitelist completeness or just use it as-is."
  ],
  "first_3_concrete_actions": [
    "Request the definitive whitelist in machine-readable format (JSON/YAML) and confirm it is exhaustive and valid.",
    "Obtain 3–5 real example filenames from a patient directory to lock in the exact TotalSeg naming scheme.",
    "Confirm the patient directory naming pattern and provide example patient IDs."
  ],
  "understanding_delta": [
    "Corrected the ambiguity around whether TotalSeg filenames are single-word or compound (with underscores) by requiring confirmation of actual examples.",
    "Clarified that the whitelist must be obtained from a definitive source (not just `whitelist_notes.md`) and validated for completeness.",
    "Confirmed that T1 and T13+ thoracic vertebrae should be treated as non-whitelisted and moved to archive.",
    "Locked in that only `.nii.gz` files should be processed, with others skipped and logged appropriately.",
    "Specified that archive collisions should result in overwriting existing files.",
    "Defined that logging should be per-patient in JSON format to a specified workspace directory.",
    "Removed assumption about resume/idempotency and clarified that each run is independent."
  ]
}
```

## Judge summary

- Verdict: `spec_acceptable`
- Handoff score: `6`
- Spec score: `5`
- Worker score: `6`

### Concise rationale

The planner captured the main triage workflow correctly, but planner v2 injected at least one unsafe concrete default (overwrite) and slightly weakened the exact-whitelist boundary. Worker v1 was appropriately cautious; worker v2 became more concrete but also absorbed the bad default. Overall this is usable but not strong.

### Covered gold constraints

- Move non-whitelist files into the archive mirror, not delete them.
- Preserve mirrored patient-level structure under <archive_root>/<patient_id>/.
- Missing source files should be logged and skipped without aborting the run.
- Do not infer whitelist entries from category words or examples alone.
- Keep exact whitelist material explicit as unresolved if not fully materialized.

### Missed gold constraints

- The planner v2 introduced an unsafe concrete default for archive collisions: overwrite.
- The exact filename-membership boundary was partially blurred by discussing stems/examples rather than cleanly anchoring the final rule as exact filename membership.
- The worker never fully resolved the exact whitelist artifact and remained stuck on missing-information requests.
- The planner did not clearly keep all hidden exact-whitelist examples separate from the operational rule, which allowed downstream ambiguity.

### Forbidden assumptions made

- Planner v2 assumed archive collisions should overwrite existing files.
- Planner v2 assumed T1 and T13+ vertebrae should be moved to archive without an explicit source of truth in the visible task.
- Worker v2 accepted the overwrite assumption instead of keeping it unresolved.
