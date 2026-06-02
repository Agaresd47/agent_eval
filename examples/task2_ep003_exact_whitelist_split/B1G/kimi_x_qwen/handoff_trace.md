# Handoff trace

- Condition: `B1_guardrailed`
- Episode: `ep003_totalseg_whitelist_split`
- Pair: `kimi_x_qwen`
- Source run: `run_result/T2_four_planner_probe/output/t2_matrix_20260505_104641`
- Verdict: `spec_weak`
- Handoff score: `4`
- Worker score: `4`

## Planner v1

```text
# Worker Implementation Spec: TotalSeg Mask Whitelist Filtering

## 1. Observed Facts

| Item | Value |
|------|-------|
| Source pattern | `<dataset_root>/totalseg_output/<patient_id>/*.nii.gz` |
| Archive pattern | `<archive_root>/<patient_id>/` (mirrors source structure for moved files) |
| File format | Flat directory per patient, all `.nii.gz` |
| Operation | **Move** (not copy/delete) — archive retains file, source loses it |
| Parallelism | Patient-level independent |
| Error handling | Log and continue; do not interrupt other patients |

## 2. Whitelist Matching Rule (To Be Finalized)

**Critical Gap**: The request describes categories ("心脏相关、肺叶、肋骨、胸椎（T段）、锁骨、肱骨、胸骨、主动脉") but **no executable matching rule** is provided.

From `whitelist_notes.md` and examples, we observe:
- Exact filenames like `aorta.nii.gz`, `heart.nii.gz`, `heart_atrium_left.nii.gz`
- Lung: `lung_lower_lobe_right.nii.gz` → pattern likely `lung_*_lobe_*.nii.gz`
- Ribs: `rib_left_1.nii.gz`, `rib_left_10.nii.gz` → pattern `rib_*.nii.gz`
- Thoracic vertebrae: `vertebrae_T5.nii.gz` → **only T2-T12**, exclude `vertebrae_C3.nii.gz`
- Explicit exclusions in examples: `kidney_left.nii.gz`, `spleen.nii.gz`

**Worker must receive**: A definitive whitelist as **exact filename list OR precise regex patterns with test cases**, not category descriptions.

## 3. Directory Structure & Mirroring

```
Source (post-operation):          Archive (receives moved files):
<dataset_root>/totalseg_output/   <archive_root>/
└── <patient_id>/                 └── <patient_id>/
    ├── aorta.nii.gz  ✓ keep          └── kidney_left.nii.gz  (moved)
    ├── heart.nii.gz  ✓ keep          └── spleen.nii.gz       (moved)
    └── ...                             └── vertebrae_C3.nii.gz (moved)
```

- Archive directory structure **mirrors source relative path**: `<archive_root>/<patient_id>/<filename>`
- Pre-create `<archive_root>/<patient_id>/` if absent

## 4. File Operations & Safety

| Aspect | Specification |
|--------|---------------|
| Action | **Move** (atomic rename across filesystems if possible; fallback copy+verify+delete) |
| Overwrite policy | **UNDEFINED** — see Open Questions |
| Verification | After move, verify source absent AND archive present with identical size |
| Partial failure | If move fails mid-batch, log affected files; do not roll back completed moves for that patient |

## 5. Logging & Missing Files

- **Per-patient log**: `<workspace>/logs/<patient_id>_filter.log`
  - Each file: `KEEP <filename>` or `MOVE <filename> -> <archive_path>` or `ERROR <filename>: <reason>`
- **Missing file handling**: If expected whitelist file absent from source, log `MISSING <expected_filename>` and continue
- **Global summary**: `<workspace>/logs/filter_summary.json` with per-patient counts (kept, moved, missing, errors)

## 6. Worker First Actions

1. **Validate inputs**: Confirm `<dataset_root>/totalseg_output/<patient_id>/` exists and readable
2. **Load whitelist**: From provided path (see Open Questions), validate all patterns compile
3. **List source files**: Enumerate all `*.nii.gz`, compare against whitelist
4. **Pre-check archive**: Ensure `<archive_root>/<patient_id>/` creatable; abort patient if not
5. **Execute moves**: For each non-whitelist file, move with verification
6. **Write logs**: Atomically write per-patient log and update global summary

## 7. Constraints & Non-Actions

- **Do NOT**: Delete files permanently, copy instead of move, or modify file contents
- **Do NOT**: Assume whitelist can be derived from category names — require explicit pattern/file list
- **Do NOT**: Halt on single-patient errors — always continue to next patient
- **Do NOT**: Create archive subdirectories beyond `<patient_id>/` level

```json
{
  "assumptions": [
    "TotalSeg output filenames are stable and lowercase with .nii.gz extension",
    "<archive_root> and <dataset_root> are on same filesystem or cross-filesystem move is acceptable",
    "Patient IDs contain no path traversal characters (validated by caller)",
    "Whitelist decision for '心脏相关' includes all heart_* variants but excludes pericardium (to be confirmed)",
    "Lung lobes are identified by 'lobe' infix, not all lung_* files"
  ],
  "risks": [
    "Irreversible data loss if move is interrupted and verification fails — archive may have partial, source may have lost original",
    "Whitelist ambiguity: 'clavicle' vs 'clavicula' vs 'claviculus' naming — wrong assumption moves keepers to archive",
    "Thoracic vertebrae boundary: T1 sometimes excluded in TotalSeg; T12 vs L1 boundary risk",
    "Concurrent workers on same patient_id would race — caller must ensure patient-level isolation",
    "Cross-filesystem move may be non-atomic; partial writes possible"
  ],
  "open_questions": [
    "EXACT_WHITELIST_SOURCE: Where does worker read the definitive whitelist? File path, env var, or hardcoded list?",
    "WHITELIST_FORMAT: Is it a JSON list of exact filenames, a regex pattern file, or a Python module with match function?",
    "OVERWRITE_POLICY: If archive already contains file with same name, overwrite, skip, or error?",
    "HEART_SCOPE: Does '心脏相关' include pericardium, coronary arteries, or only heart chambers?",
    "CLAVICLE_HUMERUS_STERNUM_PATTERNS: Exact filename patterns for these three categories not shown in examples",
    "RESUME_MARKER: Is there a completion marker to skip already-processed patients, or full re-run required?",
    "ATOMICITY_REQUIREMENT: Is copy+verify+delete acceptable, or must use atomic rename?",
    "LOG_RETENTION: Should logs append or overwrite on re-run?"
  ]
}
```
```

## Worker v1

```text
{
  "understood_goal": "Move files from a source directory structure to an archive directory structure based on a whitelist of filenames or patterns, ensuring that only specified files are kept in the source and moved to the archive, while logging operations and handling errors gracefully per patient.",
  "constraints_to_follow": [
    "Perform atomic move operations (rename) when possible, fallback to copy+verify+delete if needed.",
    "Do not delete files permanently; only move them.",
    "Do not derive whitelist from category names—require explicit filename or pattern list.",
    "Process patients independently and continue processing other patients even if one fails.",
    "Pre-create archive directories as needed, mirroring the source path structure.",
    "Log all operations per patient into a dedicated log file.",
    "Maintain a global summary JSON file tracking counts of kept, moved, missing, and error files per patient.",
    "Do not modify file contents during operation.",
    "Do not create subdirectories beyond the patient ID level in the archive."
  ],
  "information_still_missing": [
    "The exact source location of the whitelist (file path, environment variable, or hardcoded list).",
    "The format of the whitelist (list of exact filenames, regex patterns, or a callable function).",
    "The overwrite policy for existing files in the archive.",
    "Clarification on whether '心脏相关' includes pericardium, coronary arteries, or only heart chambers.",
    "Exact filename patterns for clavicle, humerus, and sternum categories.",
    "Whether there is a resume marker to avoid reprocessing completed patients.",
    "Whether atomic rename is required or if copy+verify+delete is acceptable.",
    "Whether logs should append or overwrite on re-run."
  ],
  "first_3_concrete_actions": [
    "Validate that the dataset root directory exists and is readable.",
    "Determine the source of the whitelist and confirm its format (e.g., JSON list, regex file).",
    "Check that the archive root directory is writable and pre-create the patient-specific archive directory if needed."
  ]
}
```

## Planner v2

```text
## Planner Revision: TotalSeg Mask Whitelist Filtering

### Worker_v1 Corrections

**Critical Misunderstanding #1: Direction of Move**
- Worker_v1 states: "ensuring that only specified files are kept in the source and moved to the archive"
- **Correction**: The whitelist files are **KEPT in source**; non-whitelist files are **MOVED TO archive**. Worker_v1 reversed this in their summary phrasing. The operation preserves training-relevant masks in the hot path and archives the rest.

**Critical Misunderstanding #2: "Do not delete files permanently"**
- Worker_v1 lists this as a constraint, but the spec requires **move** (which removes from source). The constraint should be: "Do not permanently delete files without archiving them first" — the source directory loses the file, but it exists in archive.

**Sharpening #3: Whitelist Matching Precision**
- Worker_v1 correctly identified ambiguity but did not commit to a verification strategy. Given TotalSeg's stable naming convention, **exact filename matching against a canonical list** is safer than regex patterns. The worker should receive a JSON file mapping: `{"exact_filenames": [...], "pattern_rules": [...]}` with priority to exact matches.

**Sharpening #4: Archive Structure**
- Worker_v1's "mirrors source relative path" is correct but imprecise. The archive receives **flat patient directories** (no `totalseg_output/` subdirectory). Clarified: `<archive_root>/<patient_id>/<filename>` directly.

**Sharpening #5: Missing File Handling**
- Worker_v1's "MISSING <expected_filename>" logging is excessive. The spec says "漏文件要记录但不要中断" — this refers to **operation failures** (files that couldn't be moved), not **expected whitelist files that don't exist**. Do not pre-validate whitelist existence; simply process what exists.

### Still Missing (Do Not Assume)

| Item | Why Unavailable |
|------|---------------|
| Exact whitelist filename list | Category descriptions ("心脏相关") map to multiple TotalSeg classes; need authoritative enumeration |
| Whether `heart.nii.gz` (whole heart) vs `heart_*` (chambers) or both | "心脏相关" scope undefined |
| Whether `trachea.nii.gz` or `bronchi.nii.gz` are included | Respiratory adjacent but not explicitly listed |
| Whether `esophagus.nii.gz` is included | Thoracic structure but not in whitelist description |
| Archive filesystem: same as source or different? | Affects atomic move feasibility |
| Existing archive content: fresh start or resume? | Affects overwrite policy necessity |

### Worker Next Focus

1. **Demand explicit whitelist artifact**: Before any file operation, verify existence of whitelist file at configurable path; fail fast with clear error if missing.
2. **Validate move direction with dry-run**: Log intended KEEP vs MOVE actions without executing; require explicit confirmation or `--dry-run=false` flag.
3. **Check cross-device move capability**: Test if source and archive are same filesystem; if different, implement copy+verify+delete with checksum verification.
4. **Establish idempotency**: Use atomic marker file `<archive_root>/<patient_id>/.filter_complete` to skip reprocessing; on re-run, verify marker integrity (checksum of processed file list).

```json
{
  "corrected_constraints": [
    "Whitelist files REMAIN in source directory; non-whitelist files are MOVED to archive (direction clarified)",
    "Move operation removes file from source — this is intended, not a violation of 'do not delete'",
    "Exact filename matching takes precedence over pattern matching; patterns are fallback only",
    "Archive path is flat: <archive_root>/<patient_id>/<filename> without totalseg_output/ subdirectory",
    "Do not log 'missing' for whitelist files that don't exist in source — only log operational failures",
    "Idempotency via atomic marker file; skip patient if .filter_complete exists and is valid",
    "Cross-device moves require checksum verification (SHA-256) before source deletion"
  ],
  "still_missing": [
    "Authoritative whitelist: exact filename list for all 8 categories (heart/lungs/ribs/T-vertebrae/clavicle/humerus/sternum/aorta)",
    "Clarification: does '心脏相关' include pericardium, coronary arteries, or only heart chambers and whole heart",
    "Clarification: are trachea/bronchi/esophagus implicitly included as thoracic structures",
    "Filesystem topology: are source and archive on same device",
    "Operational mode: fresh run or resume from partial state"
  ],
  "worker_next_focus": [
    "Implement whitelist loader that accepts JSON path via environment variable WHITELIST_JSON",
    "Add --dry-run mode that prints KEEP/MOVE decisions without executing",
    "Detect cross-device scenario using os.stat st_dev comparison; branch to checksum-verified copy+delete if different",
    "Create .filter_complete marker with JSON content: {processed_files: [...], timestamp: ..., checksum_verified: true/false}"
  ]
}
```
```

## Worker v2

```text
{
  "understood_goal": "Move files from a source directory structure to an archive directory structure based on a whitelist: whitelist files remain in the source, non-whitelist files are moved to the archive, with proper logging and error handling per patient.",
  "constraints_to_follow": [
    "Whitelist files REMAIN in source directory; non-whitelist files are MOVED to archive (direction clarified)",
    "Move operation removes file from source — this is intended, not a violation of 'do not delete'",
    "Exact filename matching takes precedence over pattern matching; patterns are fallback only",
    "Archive path is flat: <archive_root>/<patient_id>/<filename> without totalseg_output/ subdirectory",
    "Do not log 'missing' for whitelist files that don't exist in source — only log operational failures",
    "Idempotency via atomic marker file; skip patient if .filter_complete exists and is valid",
    "Cross-device moves require checksum verification (SHA-256) before source deletion"
  ],
  "information_still_missing": [
    "Authoritative whitelist: exact filename list for all 8 categories (heart/lungs/ribs/T-vertebrae/clavicle/humerus/sternum/aorta)",
    "Clarification: does '心脏相关' include pericardium, coronary arteries, or only heart chambers and whole heart",
    "Clarification: are trachea/bronchi/esophagus implicitly included as thoracic structures",
    "Filesystem topology: are source and archive on same device",
    "Operational mode: fresh run or resume from partial state"
  ],
  "first_3_concrete_actions": [
    "Implement whitelist loader that accepts JSON path via environment variable WHITELIST_JSON",
    "Add --dry-run mode that prints KEEP/MOVE decisions without executing",
    "Detect cross-device scenario using os.stat st_dev comparison; branch to checksum-verified copy+delete if different"
  ],
  "understanding_delta": [
    "Corrected the direction of file movement: whitelist files stay in source, others are moved to archive.",
    "Clarified that moving files is intentional and not a violation of 'do not delete'.",
    "Prioritized exact filename matching over regex patterns for safety and clarity.",
    "Specified that archive paths are flat, without mirroring the source subdirectory structure.",
    "Removed incorrect expectation of logging 'missing' for non-existent whitelist files.",
    "Added requirement for idempotency using a .filter_complete marker file.",
    "Added requirement for cross-device move verification using checksums."
  ]
}
```

## Judge summary

- Verdict: `spec_weak`
- Handoff score: `4`
- Spec score: `4`
- Worker score: `4`

### Concise rationale

The planner preserved the broad move-to-archive triage shape, but it did not robustly lock the worker onto exact filename membership. It introduced unsafe pattern-language, then planner_v2 incorrectly changed missing-file behavior and added extra machinery. The worker followed those weaker directions and did not keep the missing exact whitelist artifact as the central unresolved item.

### Covered gold constraints

- Move non-whitelist files into the archive mirror rather than deleting them.
- Mirror structure under <archive_root>/<patient_id>/.
- Log failures and continue without aborting the whole run.
- Keep patient-level runs independent.

### Missed gold constraints

- Treat the whitelist as exact filename membership; planner drifted toward patterns and category-based reasoning.
- Preserve the exact action boundary that non-whitelist files are moved while whitelist files remain in source without inventing a prefix/category heuristic.
- Preserve unresolved whitelist material as an explicit missing handoff artifact instead of implying a stable pattern rule.
- Missing source files should be logged and skipped without aborting; planner_v2 incorrectly downplayed missing-file logging.
- Use visible examples to prevent false generalization such as rib_left_1 vs rib_left_10 being distinct exact filenames.
- Keep the archive mirror as <archive_root>/<patient_id>/<file>.nii.gz without introducing extra policy layers like marker files or checksum-based cross-device logic.

### Forbidden assumptions made

- Planner_v1 implied pattern/rule expansion from examples and a hidden whitelist_notes.md artifact.
- Planner_v2 introduced a wrong policy by suppressing missing-file logging for absent whitelist files.
- Planner_v2 added idempotency marker and checksum-verified copy+delete behavior that were not part of the task boundary.
- Worker_v2 accepted the planner's suppression of missing-file logging instead of preserving the skip-and-log requirement.
