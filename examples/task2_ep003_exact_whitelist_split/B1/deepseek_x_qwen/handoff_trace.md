# Handoff trace

- Condition: `B1`
- Episode: `ep003_totalseg_whitelist_split`
- Pair: `deepseek_x_qwen`
- Source run: `run_result/T2_fill/output/t2_matrix_20260508_205201`
- Verdict: `spec_strong`
- Handoff score: `8`
- Worker score: `6`

## Planner v1

```text
## Worker-Ready Spec: TotalSeg White-List File Split

### 1. Objective
For each patient directory under `<dataset_root>/totalseg_output/<patient_id>/`, move all mask files **not in the whitelist** to a corresponding archive directory `<archive_root>/<patient_id>/`. After the operation, the source directory should contain only whitelisted files, and the archive directory should mirror the moved files.

### 2. Whitelist Matching Rule
- **Matching is by exact filename** (including extension `.nii.gz`), not by prefix, category, or pattern.
- The whitelist is a **fixed set of exact filenames** that must be provided as a complete list. The file `<workspace>/whitelist_notes.md` contains only category descriptions and a few example filenames; it is **not** a complete executable whitelist.
- The worker must **not** infer or expand the whitelist from category names (e.g., "rib", "heart", "vertebrae_T"). Only the exact filenames in the final whitelist are considered whitelisted.
- Based on the visible file index and the request, the following exact filenames are known to be whitelisted (this is a partial list; the full whitelist must be provided):
  - `aorta.nii.gz`
  - `heart.nii.gz`
  - `heart_atrium_left.nii.gz`
  - `lung_lower_lobe_right.nii.gz`
  - `rib_left_1.nii.gz`
  - `rib_left_10.nii.gz`
  - `vertebrae_T5.nii.gz`
- Known non-whitelisted files from the index (to be moved):
  - `vertebrae_C3.nii.gz`
  - `kidney_left.nii.gz`
  - `spleen.nii.gz`

### 3. Action: Move
- The operation is **move** (not copy or delete). Files are relocated from source to archive.
- After move, the source directory retains only whitelisted files; the archive directory contains the moved files.
- The archive is a retention location, not a trash bin.

### 4. Target Directory Structure
- The archive directory mirrors the source structure: `<archive_root>/<patient_id>/` is a flat directory (same as source) containing only the moved files.
- No subdirectory nesting is required beyond the patient ID level.

### 5. Missing File Handling
- If a whitelisted file is missing from the source, log a warning but **do not** stop processing that patient or the entire run.
- If a non-whitelisted file is missing, it is irrelevant (nothing to move).
- Logging should include patient ID and filename.

### 6. Parallelism
- Patients are independent. The worker may process patients in parallel.

### 7. Error Handling
- Any file move failure (e.g., permission, disk full) should be logged per file, and the worker should continue with remaining files for that patient.
- Do not halt the entire process for a single patient or file error.

### 8. Inputs Required (Not Provided in Prompt)
- **Complete whitelist**: A list of exact filenames (e.g., from a CSV or text file) that defines which files to keep. The `whitelist_notes.md` is insufficient.
- **Exact paths**: `<dataset_root>` and `<archive_root>` are placeholders; actual paths must be supplied.
- **Patient list**: The set of patient IDs to process.

```json
{
  "assumptions": [
    "The whitelist is a fixed set of exact filenames, not patterns or categories.",
    "All files are .nii.gz and reside flat in the patient directory.",
    "The archive directory for each patient already exists or can be created by the worker.",
    "The move operation is safe (no overwrite conflicts) because each file exists only once in source.",
    "The worker has read/write permissions on both source and archive directories."
  ],
  "risks": [
    "Using whitelist_notes.md as the whitelist would cause incorrect file retention (e.g., keeping kidney_left.nii.gz or missing vertebrae_T2..T12).",
    "If the whitelist is incomplete, some whitelisted files may be moved to archive by mistake.",
    "Parallel processing may cause race conditions if two patients share a file (unlikely but should be avoided by design).",
    "Disk space must be sufficient for the move (no extra copy needed, but archive must have space)."
  ],
  "open_questions": [
    "What is the exact complete whitelist of filenames?",
    "What are the actual values for <dataset_root> and <archive_root>?",
    "How should the patient list be obtained (e.g., directory listing, a file)?",
    "Should the worker create the archive patient directory if it does not exist?",
    "What is the logging format and destination?",
    "Is there a maximum number of parallel workers allowed?",
    "Should the worker verify that no files remain in source after move that are not in the whitelist?"
  ]
}
```
```

## Worker v1

```text
{
  "understood_goal": "For each patient directory under a specified dataset root, move mask files that are not in a given whitelist to a corresponding archive directory under a specified archive root, ensuring the source directory retains only whitelisted files.",
  "constraints_to_follow": [
    "Matching of whitelist entries is by exact filename including extension (.nii.gz).",
    "Only the exact filenames listed in the complete whitelist are considered whitelisted.",
    "Files must be moved, not copied or deleted.",
    "Archive directories must mirror the source structure at the patient ID level.",
    "Processing of patients is independent and may be done in parallel.",
    "Errors during file moves should be logged individually without halting the process.",
    "Missing whitelisted files should be logged as warnings but not stop processing.",
    "No overwrite conflicts are expected since each file exists only once in source."
  ],
  "information_still_missing": [
    "The complete list of exact filenames that constitute the whitelist.",
    "The actual path values for <dataset_root> and <archive_root>.",
    "The method or source for obtaining the list of patient IDs to process.",
    "Whether the worker should create the archive directory if it does not exist.",
    "The logging format and destination for warnings and errors.",
    "Any limits on the number of parallel workers allowed.",
    "Confirmation on whether post-move verification of source directory contents is required."
  ],
  "first_3_concrete_actions": [
    "Request the complete whitelist of exact filenames from the user or designated source.",
    "Confirm the actual paths for <dataset_root> and <archive_root> with the user.",
    "Determine how the list of patient IDs will be sourced (e.g., directory listing, input file)."
  ]
}
```

## Planner v2

```text
## Planner Revision: Correcting Worker_v1 Misunderstandings

Your interpretation is mostly correct, but I need to correct several critical points:

1. **Whitelist matching rule**: You correctly state "exact filename including extension (.nii.gz)" but then list `heart_atrium_left.nii.gz` as whitelisted. The original request says "心脏相关" (heart-related) — this is a **category**, not an exact filename. The whitelist is defined by **category membership**, not by a fixed list of exact filenames. The worker must determine which files belong to the categories: heart-related, lung lobes, ribs, thoracic vertebrae (T segment), clavicles, humeri, sternum, aorta. This means:
   - `heart_atrium_left.nii.gz` is whitelisted because it's heart-related
   - `vertebrae_T5.nii.gz` is whitelisted because it's thoracic (T segment)
   - `vertebrae_C3.nii.gz` is NOT whitelisted because it's cervical (C segment)
   - `kidney_left.nii.gz` is NOT whitelisted because kidney is not in the list
   - `spleen.nii.gz` is NOT whitelisted because spleen is not in the list

2. **The whitelist is NOT a fixed set of exact filenames** — it's a set of **categories** with rules for membership. The worker needs a mapping from category to filename patterns or a complete authoritative list. The `whitelist_notes.md` file contains category descriptions that should be used to derive the actual filenames, but the worker must verify the exact naming convention used by TotalSeg.

3. **Your example whitelist is misleading** — you listed specific filenames as if they were the complete whitelist, but the actual whitelist includes ALL files matching the categories (e.g., all 12 ribs on both sides, all thoracic vertebrae T1-T12, both clavicles, both humeri, etc.).

4. **Missing file handling**: You correctly note to log warnings for missing whitelisted files, but you didn't specify what constitutes "missing" — the worker should check if any expected file (based on the category rules) is absent and log that.

5. **Archive directory creation**: You assumed it "already exists or can be created" — this needs explicit specification. The worker should create the archive patient directory if it doesn't exist.

### Corrected Constraints

```json
{
  "corrected_constraints": [
    "Whitelist membership is determined by category (heart-related, lung lobes, ribs, thoracic vertebrae T, clavicles, humeri, sternum, aorta), not by a fixed list of exact filenames.",
    "The worker must derive the actual filenames from the category rules using TotalSeg's naming convention (e.g., 'rib_left_1.nii.gz' through 'rib_left_12.nii.gz', 'vertebrae_T1.nii.gz' through 'vertebrae_T12.nii.gz').",
    "The whitelist_notes.md file contains category descriptions that should be used as the authoritative source for category membership, but the worker must verify the exact filename patterns.",
    "Files matching any of the 8 categories are whitelisted and must be kept in source.",
    "All other files (e.g., cervical vertebrae, lumbar vertebrae, kidneys, spleen, etc.) must be moved to archive.",
    "The archive directory must be created by the worker if it does not exist.",
    "Missing expected whitelisted files (based on category rules) should be logged as warnings.",
    "The worker must not assume a fixed list of filenames — it must use category-based rules to determine whitelist membership."
  ],
  "still_missing": [
    "The exact filename patterns used by TotalSeg for each category (e.g., 'heart_*.nii.gz' vs 'heart.nii.gz' for heart-related structures).",
    "Whether the naming convention uses prefixes, suffixes, or exact matches for each category.",
    "The actual values for <dataset_root> and <archive_root>.",
    "How the patient list is obtained (directory listing vs. input file).",
    "The logging format and destination.",
    "Any limits on parallel workers.",
    "Whether post-move verification of source directory is required."
  ],
  "worker_next_focus": [
    "Inspect the whitelist_notes.md file to extract the exact category descriptions and any filename examples.",
    "Examine a sample patient directory to understand TotalSeg's naming convention for each category (e.g., how ribs are named, how vertebrae are named with T/C/L prefixes).",
    "Derive the complete set of whitelisted filenames from the category rules and naming convention.",
    "Confirm with the user the actual paths for <dataset_root> and <archive_root>.",
    "Determine how patient IDs will be enumerated (e.g., list subdirectories under <dataset_root>/totalseg_output/).",
    "Specify the logging mechanism (e.g., stdout, log file) and format."
  ]
}
```
```

## Worker v2

```text
{
  "understood_goal": "For each patient directory under a specified dataset root, move mask files that do not belong to predefined anatomical categories (heart-related, lung lobes, ribs, thoracic vertebrae T, clavicles, humeri, sternum, aorta) to a corresponding archive directory under a specified archive root. The source directory should retain only files matching these categories.",
  "constraints_to_follow": [
    "Whitelist membership is determined by category (heart-related, lung lobes, ribs, thoracic vertebrae T, clavicles, humeri, sternum, aorta), not by a fixed list of exact filenames.",
    "The worker must derive the actual filenames from the category rules using TotalSeg's naming convention (e.g., 'rib_left_1.nii.gz' through 'rib_left_12.nii.gz', 'vertebrae_T1.nii.gz' through 'vertebrae_T12.nii.gz').",
    "The whitelist_notes.md file contains category descriptions that should be used as the authoritative source for category membership, but the worker must verify the exact filename patterns.",
    "Files matching any of the 8 categories are whitelisted and must be kept in source.",
    "All other files (e.g., cervical vertebrae, lumbar vertebrae, kidneys, spleen, etc.) must be moved to archive.",
    "The archive directory must be created by the worker if it does not exist.",
    "Missing expected whitelisted files (based on category rules) should be logged as warnings.",
    "The worker must not assume a fixed list of filenames — it must use category-based rules to determine whitelist membership.",
    "Files must be moved, not copied or deleted.",
    "Archive directories must mirror the source structure at the patient ID level.",
    "Processing of patients is independent and may be done in parallel.",
    "Errors during file moves should be logged individually without halting the process.",
    "Missing whitelisted files should be logged as warnings but not stop processing."
  ],
  "information_still_missing": [
    "The exact filename patterns used by TotalSeg for each category (e.g., 'heart_*.nii.gz' vs 'heart.nii.gz' for heart-related structures).",
    "Whether the naming convention uses prefixes, suffixes, or exact matches for each category.",
    "The actual values for <dataset_root> and <archive_root>.",
    "How the patient list is obtained (directory listing vs. input file).",
    "The logging format and destination.",
    "Any limits on parallel workers.",
    "Whether post-move verification of source directory is required."
  ],
  "first_3_concrete_actions": [
    "Inspect the whitelist_notes.md file to extract the exact category descriptions and any filename examples.",
    "Examine a sample patient directory to understand TotalSeg's naming convention for each category (e.g., how ribs are named, how vertebrae are named with T/C/L prefixes).",
    "Confirm with the user the actual paths for <dataset_root> and <archive_root>."
  ],
  "understanding_delta": [
    "Previously, I misunderstood the whitelist as a fixed list of exact filenames. Now I understand it is based on categories defined in whitelist_notes.md, and the worker must derive the actual filenames from those category rules.",
    "I previously thought specific filenames like 'heart_atrium_left.nii.gz' were part of a static whitelist. Now I understand that such files are whitelisted because they fall under the 'heart-related' category, not because they are explicitly listed.",
    "The requirement to create the archive directory if it does not exist was not clearly stated in my initial interpretation but is now a necessary constraint.",
    "The distinction between 'missing whitelisted files' and 'non-whitelisted files' is clarified: missing expected files from categories must be logged as warnings."
  ]
}
```

## Judge summary

- Verdict: `spec_strong`
- Handoff score: `8`
- Spec score: `8`
- Worker score: `6`

### Concise rationale

Planner_v1 correctly preserved the core exact-whitelist, move-not-delete, mirrored-archive, and log-and-continue semantics, and worker_v1 reflected that safely while keeping the whitelist artifact missing. Planner_v2 then introduced an explicitly wrong category-based interpretation, causing worker_v2 to drift. Overall this is a strong handoff with a bad revision, so the main signal quality remains high.

### Covered gold constraints

- Treat the whitelist as exact filename membership, not category words or prefix matching.
- Preserve the action boundary: move non-whitelist files into the archive mirror; do not delete them and do not copy them by default.
- Preserve mirrored patient-level structure: `<archive_root>/<patient_id>/<file>.nii.gz`.
- Missing source files should be logged and skipped without aborting the whole run.
- If the full whitelist is not materialized, leave it as missing information instead of guessing.

### Missed gold constraints

- Planner v1 added speculative example filenames and a partial whitelist list, which risks overclaiming completeness.
- Planner v2 introduced a forbidden category-based rule and exact pattern derivation, which directly conflicts with the true exact-membership boundary.
- Worker_v2 adopted the planner_v2 category framing instead of preserving the exact whitelist uncertainty.

### Forbidden assumptions made

- Planner v2: category-based membership and derived filename patterns as the whitelist rule.
- Planner v1: implied a partial concrete whitelist could stand in for the full exact whitelist, even though it was labeled partial.
