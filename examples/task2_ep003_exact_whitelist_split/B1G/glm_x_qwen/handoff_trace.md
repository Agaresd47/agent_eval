# Handoff trace

- Condition: `B1_guardrailed`
- Episode: `ep003_totalseg_whitelist_split`
- Pair: `glm_x_qwen`
- Source run: `run_result/T2_four_planner_probe/output/t2_matrix_20260505_104641`
- Verdict: `spec_weak`
- Handoff score: `5`
- Worker score: `7`

## Planner v1

```text
# Implementation Spec: TotalSeg Mask Whitelist Filtering

## 1. Objective
Process patient directories in `<dataset_root>/totalseg_output/` to retain only masks belonging to a specific anatomical whitelist. All other masks must be moved to a mirrored archive directory at `<archive_root>/<patient_id>/`.

## 2. Input & Context
*   **Source Root:** `<dataset_root>/totalseg_output/`
*   **Target Root:** `<archive_root>/`
*   **Whitelist Reference:** `<workspace>/whitelist_notes.md`
*   **File Format:** `.nii.gz` files only.
*   **Directory Structure:** Flat structure per patient (e.g., `<dataset_root>/totalseg_output/<patient_id>/*.nii.gz`).

## 3. Operational Logic

### 3.1. Whitelist Matching Strategy
*   **Matching Unit:** Exact filename matching.
*   **Reference:** The worker must read `<workspace>/whitelist_notes.md` to determine the valid filenames.
*   **Constraint:** Do not infer patterns (e.g., "rib_left_1" to "rib_left_10") from the notes. Only accept filenames explicitly listed or implied as valid by the notes.
*   **Specific Anatomical Rule:** The whitelist explicitly includes `vertebrae_T2` through `vertebrae_T12`. It excludes `vertebrae_C3` (cervical) and any other non-T vertebrae.

### 3.2. File Action
*   **Action:** `move` (cut and paste).
*   **Destination:** Create directory `<archive_root>/<patient_id>/` if it does not exist, then move non-whitelist files there.

### 3.3. Target Directory Mirroring
*   The directory `<archive_root>/<patient_id>/` must mirror the structure of the source directory relative to the patient ID.
*   Since the source is flat, the archive will also be flat.

### 3.4. Error Handling & Resilience
*   **Missing Files:** If a file listed in the notes is missing in the source, log a warning but do not fail the process for that patient.
*   **Interrupt:** Do not interrupt the global process if a single patient directory is empty or contains no non-whitelist files.
*   **Logging:** Record the count of files moved and the count of files skipped (whitelist) for each patient.

## 4. Safety & Constraints
*   **Destructive Write Policy:** The source directory will be modified. The worker must ensure it does not delete the whitelist files.
*   **Overwrite Policy:** If a file with the same name exists in the archive directory (e.g., from a previous run), the behavior is undefined. The worker should assume a clean state or handle collisions by logging an error.
*   **Parallelism:** The worker is designed to run per-patient. Ensure file locking is not required if running strictly sequentially per patient, or handle concurrent access if running in parallel (spec does not specify parallelism constraints, assume safe sequential processing per patient).

## 5. Open Questions
*   **Whitelist Completeness:** Does `<workspace>/whitelist_notes.md` contain the *complete* list of valid filenames, or is it a subset of examples? If it is a subset, what is the source of the full list?
*   **Archive Overwrite:** What is the desired behavior if `<archive_root>/<patient_id>/` already contains files from a previous run?
*   **File Extension:** Are there any non-`.nii.gz` files in the source directory that should be ignored or treated as non-whitelist?

---

```json
{
  "assumptions": [
    "The source directory structure is flat (all .nii.gz files in one folder per patient).",
    "The whitelist is defined by exact filenames found in <workspace>/whitelist_notes.md.",
    "The 'vertebrae_T' range (T2-T12) is the only vertebrae included in the whitelist.",
    "The worker will process patients sequentially or in a way that does not conflict with itself.",
    "The 'move' action is preferred over 'copy' to free up space in the source directory."
  ],
  "risks": [
    "Inaccurate whitelist matching if the worker infers patterns (e.g., rib numbering) instead of using exact names.",
    "Accidental deletion of whitelist files if the move logic is inverted.",
    "Data loss if the archive directory is not created before moving files.",
    "Silent failures if the whitelist reference file is missing or unreadable."
  ],
  "open_questions": [
    "What is the exact content of <workspace>/whitelist_notes.md? Is it a full list or just examples?",
    "How should the worker handle collisions if <archive_root>/<patient_id>/ already exists?",
    "Are there any non-mask files (e.g., .txt, .json) in the source directory that should be ignored?",
    "Is the worker expected to run in parallel across patients, and if so, how are file system locks handled?"
  ]
}
```
```

## Worker v1

```text
{
  "understood_goal": "Process patient directories in totalseg_output to filter mask files based on a whitelist, moving non-whitelist files to an archive directory while preserving whitelist files in place.",
  "constraints_to_follow": [
    "Only .nii.gz files should be considered for filtering.",
    "Exact filename matching must be used for whitelist validation; no pattern inference is allowed.",
    "The whitelist includes vertebrae_T2 through vertebrae_T12 and excludes vertebrae_C3 and other non-T vertebrae.",
    "All non-whitelist files must be moved to a mirrored archive directory under <archive_root>/<patient_id>/.",
    "The source directory will be modified (files moved out), but whitelist files must remain untouched.",
    "If a file listed in the notes is missing in the source, log a warning but continue processing.",
    "Do not interrupt the global process if a patient directory is empty or has no non-whitelist files.",
    "Log counts of files moved and skipped for each patient.",
    "Assume sequential processing per patient unless otherwise specified."
  ],
  "information_still_missing": [
    "The exact content of <workspace>/whitelist_notes.md — specifically whether it contains the complete list or just examples.",
    "Whether the worker should overwrite existing files in the archive directory if they already exist.",
    "Confirmation that only .nii.gz files exist in the source directories (no other file types like .txt or .json).",
    "Clarification on whether the worker is expected to run in parallel across patients and how file system locks are managed."
  ],
  "first_3_concrete_actions": [
    "Read and parse the contents of <workspace>/whitelist_notes.md to extract the list of valid filenames.",
    "Verify the existence and accessibility of the source directory <dataset_root>/totalseg_output/ and the target archive root <archive_root>/.",
    "Create a function to validate each .nii.gz filename against the parsed whitelist and determine whether it should be moved or retained."
  ]
}
```

## Planner v2

```text
# Implementation Spec Revision: TotalSeg Mask Whitelist Filtering

## 1. Objective
Process patient directories in `<dataset_root>/totalseg_output/` to retain only masks belonging to a specific anatomical whitelist. All other masks must be moved to a mirrored archive directory at `<archive_root>/<patient_id>/`.

## 2. Input & Context
*   **Source Root:** `<dataset_root>/totalseg_output/`
*   **Target Root:** `<archive_root>/`
*   **Whitelist Reference:** `<workspace>/whitelist_notes.md`
*   **File Format:** `.nii.gz` files only.
*   **Directory Structure:** Flat structure per patient (e.g., `<dataset_root>/totalseg_output/<patient_id>/*.nii.gz`).

## 3. Operational Logic

### 3.1. Whitelist Matching Strategy
*   **Matching Unit:** Exact filename matching.
*   **Reference:** The worker must read `<workspace>/whitelist_notes.md` to determine the valid filenames.
*   **Constraint:** Do not infer patterns (e.g., "rib_left_1" to "rib_left_10") from the notes. Only accept filenames explicitly listed or implied as valid by the notes.
*   **Specific Anatomical Rule:** The whitelist explicitly includes `vertebrae_T2` through `vertebrae_T12`. It excludes `vertebrae_C3` (cervical) and any other non-T vertebrae.

### 3.2. File Action
*   **Action:** `move` (cut and paste).
*   **Destination:** Create directory `<archive_root>/<patient_id>/` if it does not exist, then move non-whitelist files there.

### 3.3. Target Directory Mirroring
*   The directory `<archive_root>/<patient_id>/` must mirror the structure of the source directory relative to the patient ID.
*   Since the source is flat, the archive will also be flat.

### 3.4. Error Handling & Resilience
*   **Missing Files:** If a file listed in the notes is missing in the source, log a warning but do not fail the process for that patient.
*   **Interrupt:** Do not interrupt the global process if a single patient directory is empty or contains no non-whitelist files.
*   **Logging:** Record the count of files moved and the count of files skipped (whitelist) for each patient.

## 4. Safety & Constraints
*   **Destructive Write Policy:** The source directory will be modified. The worker must ensure it does not delete the whitelist files.
*   **Overwrite Policy:** If a file with the same name exists in the archive directory (e.g., from a previous run), the behavior is undefined. The worker should assume a clean state or handle collisions by logging an error.
*   **Parallelism:** The worker is designed to run per-patient. Ensure file locking is not required if running strictly sequentially per patient, or handle concurrent access if running in parallel (spec does not specify parallelism constraints, assume safe sequential processing per patient).

## 5. Open Questions
*   **Whitelist Completeness:** Does `<workspace>/whitelist_notes.md` contain the *complete* list of valid filenames, or is it a subset of examples? If it is a subset, what is the source of the full list?
*   **Archive Overwrite:** What is the desired behavior if `<archive_root>/<patient_id>/` already contains files from a previous run?
*   **File Extension:** Are there any non-`.nii.gz` files in the source directory that should be ignored or treated as non-whitelist?

---

```json
{
  "corrected_constraints": [
    "The whitelist matching strategy is defined as 'Exact filename matching' against the content of <workspace>/whitelist_notes.md. The worker must NOT infer patterns (e.g., 'rib_left_1' to 'rib_left_10') from the notes.",
    "The whitelist includes specific anatomical structures: heart-related, lung lobes, ribs, thoracic vertebrae (T2-T12), clavicles, humeri, sternum, and aorta. It explicitly excludes vertebrae_C3 and other non-T vertebrae.",
    "The file action is 'move' (cut and paste). The destination is <archive_root>/<patient_id>/.",
    "The target directory structure must mirror the source. Since the source is flat, the archive will be flat.",
    "The worker must handle missing files by logging a warning but not interrupting the process.",
    "The worker must log the count of files moved and skipped for each patient.",
    "The worker should assume sequential processing per patient to avoid file system locking issues."
  ],
  "still_missing": [
    "The exact content of <workspace>/whitelist_notes.md — specifically whether it contains the complete list of valid filenames or just examples.",
    "The desired behavior if <archive_root>/<patient_id>/ already contains files from a previous run (overwrite, skip, or error).",
    "Confirmation that only .nii.gz files exist in the source directories (no other file types like .txt or json).",
    "Whether the worker is expected to run in parallel across patients and how file system locks are managed."
  ],
  "worker_next_focus": [
    "Read the contents of <workspace>/whitelist_notes.md to verify the exact list of valid filenames and confirm the exclusion of non-T vertebrae.",
    "Inspect the source directory <dataset_root>/totalseg_output/ to confirm the file format (only .nii.gz) and directory structure (flat).",
    "Check the target directory <archive_root>/ to understand the current state and determine the appropriate handling for existing files."
  ]
}
```
```

## Worker v2

```text
{
  "understood_goal": "Process patient directories in totalseg_output to filter mask files based on a whitelist, moving non-whitelist files to an archive directory while preserving whitelist files in place.",
  "constraints_to_follow": [
    "Only .nii.gz files should be considered for filtering.",
    "Exact filename matching must be used for whitelist validation; no pattern inference is allowed.",
    "The whitelist includes specific anatomical structures: heart-related, lung lobes, ribs, thoracic vertebrae (T2-T12), clavicles, humeri, sternum, and aorta. It explicitly excludes vertebrae_C3 and other non-T vertebrae.",
    "All non-whitelist files must be moved to a mirrored archive directory under <archive_root>/<patient_id>/.",
    "The source directory will be modified (files moved out), but whitelist files must remain untouched.",
    "If a file listed in the notes is missing in the source, log a warning but continue processing.",
    "Do not interrupt the global process if a patient directory is empty or has no non-whitelist files.",
    "Log counts of files moved and skipped for each patient.",
    "Assume sequential processing per patient to avoid file system locking issues."
  ],
  "information_still_missing": [
    "The exact content of <workspace>/whitelist_notes.md — specifically whether it contains the complete list of valid filenames or just examples.",
    "The desired behavior if <archive_root>/<patient_id>/ already contains files from a previous run (overwrite, skip, or error).",
    "Confirmation that only .nii.gz files exist in the source directories (no other file types like .txt or json).",
    "Whether the worker is expected to run in parallel across patients and how file system locks are managed."
  ],
  "first_3_concrete_actions": [
    "Read the contents of <workspace>/whitelist_notes.md to verify the exact list of valid filenames and confirm the exclusion of non-T vertebrae.",
    "Inspect the source directory <dataset_root>/totalseg_output/ to confirm the file format (only .nii.gz) and directory structure (flat).",
    "Check the target directory <archive_root>/ to understand the current state and determine the appropriate handling for existing files."
  ],
  "understanding_delta": [
    "The revised spec clarified that the whitelist includes a broader set of anatomical structures beyond just vertebrae_T2-T12, such as heart-related, lung lobes, ribs, clavicles, humeri, sternum, and aorta.",
    "It reinforced the constraint that no pattern inference is allowed when matching filenames against the whitelist.",
    "It emphasized that the worker should assume sequential processing per patient to avoid concurrency issues."
  ]
}
```

## Judge summary

- Verdict: `spec_weak`
- Handoff score: `5`
- Spec score: `5`
- Worker score: `7`

### Concise rationale

The planner got the action/mirror/missing-file mechanics right, but it also invented a concrete whitelist subset (vertebrae_T2-T12) instead of preserving the exact filename whitelist as unresolved. Worker_v1 followed that drift; worker_v2 corrected toward safer exact-match handling while still flagging missing exact list details. Overall this is a weak-to-moderate handoff, not strong.

### Covered gold constraints

- Exact filename matching was mentioned.
- Move-to-archive semantics were stated.
- Mirrored patient-level archive structure was stated.
- Missing-file logging without aborting was stated.
- The worker was prompted to read a whitelist notes artifact rather than blindly infer.

### Missed gold constraints

- Planner introduced a false concrete whitelist boundary by asserting vertebrae_T2-T12 as the explicit whitelist rule, which is not the safe exact-filename boundary required.
- Planner did not preserve the real unresolved whitelist artifact cleanly; it mixed exact matching with a guessed anatomical subset.
- The exact filename-membership constraint was not reinforced using the visible examples (`rib_left_1.nii.gz` vs `rib_left_10.nii.gz`, `vertebrae_T5.nii.gz` vs `vertebrae_C3.nii.gz`).
- The planner did not clearly separate grounded facts from missing whitelist material, which risks overgeneralization.

### Forbidden assumptions made

- Planner assumed the whitelist explicitly includes vertebrae_T2 through T12 as a concrete rule.
- Planner implied the whitelist notes are sufficient to derive validity, instead of treating the full whitelist as unresolved exact information.
- Worker_v1 repeated the same vertebrae_T2-T12 assumption.
