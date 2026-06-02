# Handoff trace

- Condition: `B1`
- Episode: `ep003_totalseg_whitelist_split`
- Pair: `mimo_x_qwen`
- Source run: `run_result/T2_fill/output/t2_matrix_20260508_205311`
- Verdict: `spec_acceptable`
- Handoff score: `8`
- Worker score: `8`

## Planner v1

```text
# Worker Specification: TotalSeg Whitelist File Segregation

## Objective
For each patient directory under `<dataset_root>/totalseg_output/<patient_id>/`, move all `.nii.gz` files **not** in the provided whitelist to `<archive_root>/<patient_id>/`. The source directory retains only whitelisted files.

## Inputs
- `dataset_root`: Path to the root of TotalSeg output.
- `archive_root`: Path to the root for archived (non-whitelisted) files.
- `whitelist`: A **complete, exact set of filenames** (e.g., `{"aorta.nii.gz", "heart.nii.gz", ...}`) to retain. **Not** a set of patterns or categories.

## Processing Steps (Per Patient)
1. **Enumerate**: List all `.nii.gz` files in the source patient directory.
2. **Classify**: For each file:
   - If filename is in `whitelist`: **Keep** in source.
   - If filename is **not** in `whitelist`: **Move** to the corresponding archive directory.
3. **Archive Structure**: Mirror the patient directory structure. Create `<archive_root>/<patient_id>/` if it does not exist.
4. **Move Operation**: Use atomic move (rename) if source and archive are on the same filesystem; otherwise, copy-then-delete.
5. **Missing Files**: If a whitelisted file is absent from the source, log a warning but continue processing other files and patients.
6. **Logging**: Record each moved file and any missing whitelisted files. Do not halt on errors for individual files or patients.

## Constraints & Rules
- **Whitelist Matching**: Exact filename match only. No prefix, pattern, or category-based matching.
- **Action**: Move (not copy or delete). The goal is to segregate, not duplicate or destroy.
- **Idempotency**: Re-running should not move files already in archive or re-move whitelisted files.
- **Parallelism**: Patient directories are independent; process them in parallel.
- **Error Handling**: Log and continue. Do not let one patient's failure block others.

## Assumptions
- All mask files are `.nii.gz` and reside directly in the patient directory (no subdirectories).
- The `whitelist` is provided as a definitive, exhaustive list of filenames to keep.
- The archive root is writable and has sufficient space.
- The worker has permissions to read source and write to archive.

## Risks
- **Incomplete Whitelist**: If the whitelist is missing entries, valid files will be incorrectly moved to archive.
- **Filesystem Differences**: Moving across filesystems may be slower and non-atomic.
- **Concurrent Modification**: If other processes write to the source directory during execution, files may be missed or duplicated.
- **Large Data Volume**: Moving many files may require careful resource management (e.g., open file handles).

## Open Questions
1. **Exact Whitelist**: What is the complete, explicit list of filenames to retain? The provided `whitelist_notes.md` is insufficient.
2. **File Extensions**: Are there any non-`.nii.gz` files in the source directories that should be ignored or handled?
3. **Archive Overwrite Policy**: If a file already exists in the archive (e.g., from a previous run), should it be overwritten, skipped, or cause an error?
4. **Logging Destination**: Where should logs (moved files, missing files, errors) be written?
5. **Completion Marker**: How should the worker signal successful completion for a patient (e.g., a marker file, exit code)?

```json
{
  "assumptions": [
    "All mask files are .nii.gz and located directly in the patient directory.",
    "The whitelist is provided as a complete set of exact filenames.",
    "The archive root is on a writable filesystem with sufficient space.",
    "The worker has read permissions on source and write permissions on archive."
  ],
  "risks": [
    "An incomplete whitelist will cause incorrect file segregation.",
    "Moving files across filesystems may be slow and non-atomic.",
    "Concurrent writes to source directories could lead to missed or duplicated files.",
    "Large data volumes may require careful resource management to avoid exhaustion."
  ],
  "open_questions": [
    "What is the exact, exhaustive list of filenames in the whitelist?",
    "Are there any non-.nii.gz files in the source directories that need handling?",
    "What is the policy if a file already exists in the archive (overwrite/skip/error)?",
    "Where should operational logs be written?",
    "How should successful completion of a patient be indicated?"
  ]
}
```
```

## Worker v1

```text
{
  "understood_goal": "For each patient directory under the TotalSeg output root, move all .nii.gz files that are not in the provided whitelist to an archive directory, while keeping only the whitelisted files in the source directory.",
  "constraints_to_follow": [
    "Whitelist matching must be exact filename match only.",
    "Only .nii.gz files are considered; other extensions are ignored.",
    "Move operation must be atomic if source and archive are on the same filesystem; otherwise, use copy-then-delete.",
    "Processing of patient directories is independent and can be done in parallel.",
    "Log each moved file and any missing whitelisted files without halting on errors.",
    "Re-running the process should not re-move files already in the archive or re-keep whitelisted files.",
    "If a whitelisted file is missing from the source, log a warning but continue processing."
  ],
  "information_still_missing": [
    "The exact, exhaustive list of filenames in the whitelist.",
    "The value of `dataset_root` and `archive_root` paths.",
    "Policy for handling existing files in the archive (overwrite/skip/error).",
    "Location where operational logs should be written.",
    "Mechanism for signaling successful completion per patient (e.g., marker file, exit code)."
  ],
  "first_3_concrete_actions": [
    "Request the exact whitelist file or list of filenames to be retained.",
    "Confirm the values of `dataset_root` and `archive_root` paths.",
    "Clarify the logging destination and the mechanism for indicating successful completion per patient."
  ]
}
```

## Planner v2

```text
## Corrected Worker Specification

Your interpretation correctly identifies the core goal and several constraints, but there is a critical misunderstanding about the whitelist and several missing details that must be resolved before implementation.

### Key Correction: Whitelist Definition
The original request does **not** provide an exact list of filenames. It provides a list of **categories** (心脏相关、肺叶、肋骨、胸椎（T 段）、锁骨、肱骨、胸骨、主动脉). The worker cannot perform exact filename matching without a definitive mapping from these categories to the actual `.nii.gz` filenames produced by TotalSeg. The planner spec's assumption of a "complete, exact set of filenames" was premature.

**Therefore, the worker must not assume it has the whitelist.** The exact, exhaustive list of filenames to retain must be provided as an input artifact (e.g., a text file or a set in a configuration). The worker's logic must be built around receiving this exact list.

### Preserved Correct Understanding
- **Action**: Move (not copy or delete) non-whitelisted files.
- **Structure**: Mirror the patient directory under `<archive_root>/<patient_id>/`.
- **Parallelism**: Patient directories are independent.
- **Error Handling**: Log and continue; do not halt on individual file or patient errors.
- **Idempotency**: Re-running should not re-process files already moved.

### Clarifications on Existing Assumptions
- **File Extension**: The assumption that only `.nii.gz` files are considered is reasonable given the context of medical image masks. However, the worker should be designed to process only files with that extension, ignoring others in the directory.
- **Move Operation**: The strategy for atomic move (same filesystem) vs. copy-then-delete (cross-filesystem) is correct and should be implemented.

### Details Still Missing (Must Be Provided)
The following cannot be assumed and must be explicitly defined by the user or system configuration:

1.  **The Exact Whitelist**: The definitive list of `.nii.gz` filenames to retain in the source directory.
2.  **Parameter Values**: The actual paths for `dataset_root` and `archive_root`.
3.  **Archive Overwrite Policy**: What to do if a file already exists at the destination in `<archive_root>/<patient_id>/` (e.g., skip, overwrite, or raise an error).
4.  **Logging Destination**: Where to write operational logs (e.g., a file path, stdout, a logging service).
5.  **Completion Signal**: How to indicate successful processing of a patient directory (e.g., creating a marker file, returning a specific exit code, or simply logging success).

### Worker Next Focus
Before writing any code, the worker must:
1.  **Obtain the definitive whitelist** as an input artifact (e.g., a file path to a list).
2.  **Confirm the values** for `dataset_root` and `archive_root`.
3.  **Clarify the policy** for handling pre-existing files in the archive.
4.  **Define the logging and completion mechanisms**.

```json
{
  "corrected_constraints": [
    "Whitelist matching must be based on an exact, provided list of filenames, not inferred from categories.",
    "Only .nii.gz files are processed; other files in the patient directory are ignored.",
    "The move operation must be atomic if source and archive are on the same filesystem; otherwise, use copy-then-delete.",
    "Patient directories are processed independently and in parallel.",
    "Log each moved file and any missing whitelisted files without halting on errors.",
    "Re-running the process should not re-move files already in the archive or re-keep whitelisted files.",
    "If a whitelisted file is missing from the source, log a warning but continue processing."
  ],
  "still_missing": [
    "The exact, exhaustive list of filenames in the whitelist (must be provided as an input artifact).",
    "The values of `dataset_root` and `archive_root` paths.",
    "Policy for handling existing files in the archive (overwrite/skip/error).",
    "Location where operational logs should be written.",
    "Mechanism for signaling successful completion per patient (e.g., marker file, exit code)."
  ],
  "worker_next_focus": [
    "Request the exact whitelist file or list of filenames to be retained.",
    "Confirm the values of `dataset_root` and `archive_root` paths.",
    "Clarify the logging destination and the mechanism for indicating successful completion per patient.",
    "Clarify the policy for handling pre-existing files in the archive directory."
  ]
}
```
```

## Worker v2

```text
{
  "understood_goal": "For each patient directory under the TotalSeg output root, move all .nii.gz files that are not in the provided whitelist to an archive directory, while keeping only the whitelisted files in the source directory. The whitelist must be an exact, provided list of filenames, not inferred from categories.",
  "constraints_to_follow": [
    "Whitelist matching must be based on an exact, provided list of filenames, not inferred from categories.",
    "Only .nii.gz files are processed; other files in the patient directory are ignored.",
    "Move operation must be atomic if source and archive are on the same filesystem; otherwise, use copy-then-delete.",
    "Patient directories are processed independently and in parallel.",
    "Log each moved file and any missing whitelisted files without halting on errors.",
    "Re-running the process should not re-move files already in the archive or re-keep whitelisted files.",
    "If a whitelisted file is missing from the source, log a warning but continue processing."
  ],
  "information_still_missing": [
    "The exact, exhaustive list of filenames in the whitelist (must be provided as an input artifact).",
    "The values of `dataset_root` and `archive_root` paths.",
    "Policy for handling existing files in the archive (overwrite/skip/error).",
    "Location where operational logs should be written.",
    "Mechanism for signaling successful completion per patient (e.g., marker file, exit code)."
  ],
  "first_3_concrete_actions": [
    "Request the exact whitelist file or list of filenames to be retained.",
    "Confirm the values of `dataset_root` and `archive_root` paths.",
    "Clarify the logging destination and the mechanism for indicating successful completion per patient."
  ],
  "understanding_delta": [
    "The original interpretation mistakenly assumed that the whitelist was a complete, exact set of filenames. The revised specification clarifies that the whitelist must be explicitly provided as an input artifact because the initial description only listed categories, not actual filenames.",
    "The constraint regarding exact filename matching is now explicitly tied to the requirement of having a definitive whitelist provided as input, rather than being inferred.",
    "The need to confirm parameter values (`dataset_root`, `archive_root`) and clarify policies for archive overwrite, logging, and completion signals remains, but is now more clearly tied to the fact that the whitelist itself is not yet available."
  ]
}
```

## Judge summary

- Verdict: `spec_acceptable`
- Handoff score: `8`
- Spec score: `8`
- Worker score: `8`

### Concise rationale

Planner_v1 was too confident about having a complete whitelist, but planner_v2 repaired that by explicitly flagging the exact list as missing and preserving move/mirror/logging semantics. Worker_v1 was mostly aligned but slightly under-specified; worker_v2 was safer and more explicit about missing information. Overall the handoff is acceptable and reasonably safe, though not maximally strong because the exact whitelist artifact remains unresolved.

### Covered gold constraints

- Treat the whitelist as exact filename membership, not category words or prefix matching.
- Preserve the action boundary: move non-whitelist files into the archive mirror; do not delete them and do not copy them by default.
- Preserve mirrored patient-level structure: `<archive_root>/<patient_id>/<file>.nii.gz`.
- If the full whitelist has not been fully materialized from visible context, explicitly leave it as missing information or a required handoff artifact instead of guessing.
- Missing source files should be logged and skipped without aborting the whole run.

### Missed gold constraints

- The visible filename examples were not explicitly used to distinguish near-collisions like `rib_left_1.nii.gz` vs `rib_left_10.nii.gz`.
- The whitelist notes artifact and missing-file log paths were discussed only generically, not anchored to the episode's suggested file locations.

### Forbidden assumptions made

- Planner_v1 assumed a complete, exact whitelist set was already available.
- Worker_v1 loosely accepted an implementation detail that could be read as copy-then-delete across filesystems without separately emphasizing the move-to-archive boundary.
- Planner_v2 asserted that the original request only listed categories, which is true from the visible text but still risks overcommitting about the exact mapping availability.
