# Handoff trace

- Condition: `B1_guardrailed`
- Episode: `ep003_totalseg_whitelist_split`
- Pair: `mimo_x_qwen`
- Source run: `run_result/T2_fill/output/t2_matrix_20260508_200616`
- Verdict: `spec_strong`
- Handoff score: `8`
- Worker score: `7`

## Planner v1

```text
# Worker Specification: Whitelist-Driven File Triage for TotalSeg Output

## Objective
For each patient directory under `<dataset_root>/totalseg_output/<patient_id>/`, move all mask files **not** present in a provided whitelist to a mirrored archive directory at `<archive_root>/<patient_id>/`. The source directory must retain only whitelisted files after processing.

## Inputs
1. **`dataset_root`**: Path to the root containing patient directories.
2. **`archive_root`**: Path to the root for archived (non-whitelisted) files.
3. **`whitelist_file`**: Path to a file containing the **exact, executable whitelist** of allowed file names (one per line, including extension, e.g., `aorta.nii.gz`).  
   *Note: `whitelist_notes.md` is insufficient; the worker must receive a complete, unambiguous list.*

## Processing Steps (Per Patient)
1. **Enumerate** all files in `<dataset_root>/totalseg_output/<patient_id>/`. Assume flat directory containing only `.nii.gz` files.
2. **Load** the whitelist from `whitelist_file`. Perform **exact string matching** of each file’s base name (including extension) against the whitelist.
3. **For each file**:
   - If **not in whitelist**: move it to `<archive_root>/<patient_id>/<same_filename>`.
   - If **in whitelist**: leave it in place.
4. **Create** `<archive_root>/<patient_id>/` if it does not exist.
5. **Log** per patient:
   - List of moved files.
   - List of whitelisted files retained.
   - Any errors (e.g., missing source file, permission issues).
6. **Continue** to next patient regardless of errors in current patient.

## Constraints & Safety
- **Action**: Move (not copy, not delete). Moving removes the file from source.
- **Overwrite Policy**: Not specified. Worker must not overwrite existing files in archive without explicit instruction.
- **Missing Whitelisted Files**: If a whitelisted file is absent from the source directory, log it but do not treat as error.
- **Parallelism**: Patient-level independence allows parallel execution. Ensure no cross-patient file conflicts.
- **Destructive Writes**: Moving is irreversible. Confirm with user if archive already contains files with same names.

## Assumptions
1. The whitelist file will be provided as a separate, complete list of exact file names.
2. Patient directories contain only `.nii.gz` files; no subdirectories.
3. `dataset_root` and `archive_root` exist and are writable.
4. File names are unique per patient directory.

## Risks
1. **Data Loss**: Moving files without backup could lead to irreversible loss if archive is misconfigured.
2. **Incomplete Whitelist**: If whitelist is missing entries, valid files may be incorrectly archived.
3. **Concurrency Issues**: Parallel writes to same archive directory could cause race conditions if not managed.

## Open Questions
1. **Overwrite Behavior**: Should the worker skip, overwrite, or rename if a file already exists in the archive?
2. **Whitelist Format**: Is the whitelist a simple text file with one filename per line, or another format (e.g., JSON, CSV)?
3. **Logging Destination**: Where should logs be written (stdout, file, logging system)?
4. **Resume Capability**: Should the worker support idempotent re-runs (e.g., skip already moved files)?
5. **File Permissions**: Are there specific permission requirements for created directories/files?

```json
{
  "assumptions": [
    "Whitelist is provided as a separate file with exact filenames including extension.",
    "Patient directories are flat and contain only .nii.gz files.",
    "dataset_root and archive_root exist and are writable.",
    "File names are unique per patient directory."
  ],
  "risks": [
    "Moving files without backup could cause irreversible data loss if archive is misconfigured.",
    "Incomplete whitelist may lead to incorrect archiving of valid files.",
    "Parallel execution without proper locking could cause race conditions in archive directory."
  ],
  "open_questions": [
    "What is the overwrite policy for existing files in the archive?",
    "What is the exact format and location of the whitelist file?",
    "Where should processing logs be written?",
    "Should the worker support idempotent re-runs?",
    "Are there specific file/directory permission requirements?"
  ]
}
```
```

## Worker v1

```text
{
  "understood_goal": "For each patient directory under the dataset root, move mask files that are not in a provided whitelist to an archive directory, while retaining only whitelisted files in the source directory.",
  "constraints_to_follow": [
    "Move files (not copy or delete), which is irreversible.",
    "Perform exact string matching of filenames against the whitelist.",
    "Create the archive directory for each patient if it does not exist.",
    "Process each patient independently to allow for parallel execution.",
    "Log moved files, retained files, and any errors per patient.",
    "Do not overwrite existing files in the archive unless explicitly instructed.",
    "Assume flat directory structure with only .nii.gz files per patient.",
    "Ensure dataset_root and archive_root exist and are writable."
  ],
  "information_still_missing": [
    "The exact overwrite behavior when a file already exists in the archive (skip, overwrite, or rename).",
    "The precise format and location of the whitelist file (e.g., is it a plain text file with one filename per line?).",
    "The destination for logs (e.g., stdout, a specific log file path, or a logging system).",
    "Whether the worker should support idempotent re-runs (i.e., skipping files already moved).",
    "Specific file or directory permission requirements for created items."
  ],
  "first_3_concrete_actions": [
    "Confirm the expected format of the whitelist file (e.g., plain text with one filename per line).",
    "Clarify the overwrite policy for handling existing files in the archive directory.",
    "Determine where processing logs should be written (e.g., standard output, a log file, or a logging framework)."
  ]
}
```

## Planner v2

```text
Worker v1 correctly grasped the core objective but assumed details that the original request explicitly asks to be specified. The request requires the spec to clarify: whitelist matching (category/prefix vs exact filename), triage action (move/delete/copy), target directory structure mirroring, and missing file handling. Planner v1 assumed exact filename matching and move action without confirmation, which needs verification. Additionally, worker v1 listed missing details (overwrite behavior, whitelist format, log destination, idempotent re-runs, permissions) that are not addressed in the original request and must be resolved.

For a worker-ready spec:
- **Whitelist matching**: Specify as exact filename matching (including extension) unless the user confirms a prefix/category-based approach. This is common for TotalSeg outputs, but verify.
- **Triage action**: Specify as move to archive, as it removes files from source and preserves them, but confirm if copy or delete is preferred.
- **Target structure**: Mirror the source directory structure; since source is flat with `.nii.gz` files per patient, archive should have the same flat structure under `<archive_root>/<patient_id>/`.
- **Missing files**: Log and continue processing, as per request, without interrupting the workflow.

Worker v1 should next focus on obtaining user confirmation on the unspecified points and gathering necessary inputs like the whitelist file.

```json
{
  "corrected_constraints": [
    "Whitelist matching method (exact filename vs prefix/category) must be explicitly specified in the spec.",
    "Triage action (move, copy, or delete) must be confirmed by the user.",
    "Target directory structure should mirror source; assume flat .nii.gz files per patient unless otherwise specified."
  ],
  "still_missing": [
    "Overwrite behavior for existing files in the archive directory.",
    "Exact format and location of the whitelist file (e.g., plain text with one filename per line).",
    "Destination for processing logs (e.g., stdout, file, or logging system).",
    "Whether the worker should support idempotent re-runs (e.g., skip already moved files).",
    "Specific file or directory permission requirements for created items."
  ],
  "worker_next_focus": [
    "Obtain user confirmation on whitelist matching method and triage action.",
    "Verify and receive the whitelist file in the correct format.",
    "Clarify overwrite policy, log destination, and idempotency requirements."
  ]
}
```
```

## Worker v2

```text
{
  "understood_goal": "For each patient directory under the dataset root, move mask files that are not in a provided whitelist to an archive directory, while retaining only whitelisted files in the source directory. The archive directory structure should mirror the source structure.",
  "constraints_to_follow": [
    "Whitelist matching method must be exact filename matching (including extension) unless otherwise specified.",
    "Triage action must be move to archive, as it removes files from source and preserves them.",
    "Target directory structure should mirror source; assume flat .nii.gz files per patient.",
    "Move files (not copy or delete), which is irreversible.",
    "Perform exact string matching of filenames against the whitelist.",
    "Create the archive directory for each patient if it does not exist.",
    "Process each patient independently to allow for parallel execution.",
    "Log moved files, retained files, and any errors per patient.",
    "Do not overwrite existing files in the archive unless explicitly instructed.",
    "Assume flat directory structure with only .nii.gz files per patient.",
    "Ensure dataset_root and archive_root exist and are writable."
  ],
  "information_still_missing": [
    "The exact overwrite behavior when a file already exists in the archive (skip, overwrite, or rename).",
    "The precise format and location of the whitelist file (e.g., is it a plain text file with one filename per line?).",
    "The destination for logs (e.g., stdout, a specific log file path, or a logging system).",
    "Whether the worker should support idempotent re-runs (i.e., skipping files already moved).",
    "Specific file or directory permission requirements for created items."
  ],
  "first_3_concrete_actions": [
    "Confirm with the user whether whitelist matching is exact filename matching (including extension) or based on prefix/category.",
    "Confirm with the user whether the triage action is move, copy, or delete.",
    "Request the whitelist file in the expected format (e.g., plain text with one filename per line) and verify its location."
  ],
  "understanding_delta": [
    "Previously, I assumed exact filename matching and move action without explicit confirmation. The revision clarified that these need to be explicitly specified by the user.",
    "I updated my understanding to reflect that the target directory structure must mirror the source, and that this assumption should be confirmed if not explicitly stated.",
    "I retained the list of still-missing information because the revision message indicated that some details (like overwrite policy, log destination, etc.) were not resolved and must remain as blockers."
  ]
}
```

## Judge summary

- Verdict: `spec_strong`
- Handoff score: `8`
- Spec score: `9`
- Worker score: `7`

### Concise rationale

Planner preserved the critical boundary well: exact filename whitelist, move-to-archive, mirrored patient directory, and skip/log missing files. It is slightly weaker on unresolved-artifact handling because it assumes a complete whitelist file exists, but it does not introduce a forbidden delete/prefix default. Worker v1 is mostly correct; worker v2 adds cautious clarification but also keeps an ambiguous fallback clause, so the overall handoff is strong rather than perfect.

### Covered gold constraints

- Treat whitelist as exact filename membership.
- Move non-whitelist files into mirrored archive structure.
- Do not delete or copy by default.
- Missing files should be logged and skipped without aborting.

### Missed gold constraints

- Planner does not explicitly preserve the possibility that the full whitelist is still unresolved from visible context; it assumes a complete whitelist_file exists.
- Worker v2 reintroduces ambiguity by saying exact matching applies 'unless otherwise specified,' which weakens the boundary slightly.

### Forbidden assumptions made

- None
