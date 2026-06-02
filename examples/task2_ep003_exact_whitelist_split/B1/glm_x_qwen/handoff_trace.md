# Handoff trace

- Condition: `B1`
- Episode: `ep003_totalseg_whitelist_split`
- Pair: `glm_x_qwen`
- Source run: `run_result/T2_fill/output/t2_matrix_20260508_205311`
- Verdict: `spec_weak`
- Handoff score: `4`
- Worker score: `5`

## Planner v1

```text
# TotalSeg Mask Whitelist Filter Worker Spec

## Objective
Process patient directories under `<dataset_root>/totalseg_output/` to retain only masks belonging to a specific anatomical whitelist and move all other masks to an archive directory. The operation must be patient-level independent and parallelizable.

## Input Context
*   **Source Root:** `<dataset_root>/totalseg_output/`
*   **Archive Root:** `<archive_root>/`
*   **Whitelist Reference:** `<workspace>/whitelist_notes.md` (Contains category descriptions and examples, not a complete executable regex list).

## Operational Logic

### 1. Whitelist Matching Strategy
*   **Mechanism:** The worker must implement a matching logic that interprets the content of `<workspace>/whitelist_notes.md`.
*   **Constraint:** Do not treat the file names in the notes as a literal whitelist. The notes describe *categories* (e.g., "heart related", "vertebrae T segment") and provide examples. The worker must map these categories to the specific file naming conventions used in the dataset (e.g., `heart.nii.gz`, `vertebrae_T5.nii.gz`).
*   **Specific Exclusion:** Explicitly exclude cervical (`vertebrae_C*`) and lumbar (`vertebrae_L*`) vertebrae. Only retain thoracic vertebrae (`vertebrae_T2` through `vertebrae_T12`).

### 2. File Action
*   **Operation:** `move` (or `rename`).
*   **Behavior:** Files matching the whitelist remain in the source directory. Files *not* matching the whitelist are moved to the archive directory.

### 3. Directory Structure Mirroring
*   **Source:** `<dataset_root>/totalseg_output/<patient_id>/` (Flat structure of `.nii.gz` files).
*   **Archive:** `<archive_root>/<patient_id>/` (Flat structure mirroring the source).
*   **Behavior:** The worker should create the `<archive_root>/<patient_id>/` directory if it does not exist.

### 4. Error Handling & Logging
*   **Missing Files:** If a file listed in the file index is missing during processing, log the event but do not interrupt the processing of the current patient or the global batch.
*   **Empty Directories:** If a patient directory contains no files, log the event and proceed to the next patient.

## Output Contract
The worker should produce a JSON block containing:
*   `assumptions`: Facts inferred from the prompt.
*   `risks`: Constraints or potential pitfalls.
*   `open_questions`: Information still required for implementation.

```json
{
  "assumptions": [
    "The worker has read access to the source directory and write access to the archive directory.",
    "The file extension is always .nii.gz.",
    "The patient IDs in the source root match the directory structure under the archive root.",
    "The whitelist logic must be derived from the descriptive text in whitelist_notes.md, not just the file names listed in the notes.",
    "The operation is destructive to the source directory (files are moved, not copied)."
  ],
  "risks": [
    "Ambiguity in mapping 'heart related' to specific file names (e.g., heart.nii.gz vs heart_atrium_left.nii.gz).",
    "The whitelist_notes.md might be incomplete, leading to false positives (whitelist items not in the dataset) or false negatives (dataset items not in the whitelist).",
    "If the worker uses a simple prefix match (e.g., 'heart_*'), it might incorrectly match non-whitelist files if the naming convention is not strictly prefix-based.",
    "Parallel execution might cause race conditions if the archive directory creation is not atomic.",
    "The worker must handle the specific exclusion of cervical/lumbar vertebrae correctly, as they might share the 'vertebrae' prefix."
  ],
  "open_questions": [
    "What is the exact mapping rule to convert the category descriptions in whitelist_notes.md into file name patterns?",
    "Is the whitelist strictly defined by the content of whitelist_notes.md, or is there an external configuration file?",
    "Should the worker handle the case where the source directory is empty or contains no .nii.gz files?",
    "What is the exact naming convention for thoracic vertebrae (e.g., T1, T2... T12)?",
    "Is the operation intended to be idempotent (safe to run multiple times)?"
  ]
}
```
```

## Worker v1

```text
{
  "understood_goal": "Process patient directories under `<dataset_root>/totalseg_output/` to filter and move mask files based on a whitelist described in `<workspace>/whitelist_notes.md`. Retain only masks that belong to specified anatomical categories, excluding cervical and lumbar vertebrae, and move all others to an archive directory while maintaining directory structure.",
  "constraints_to_follow": [
    "The operation must be patient-level independent and parallelizable.",
    "Files matching the whitelist remain in the source directory; non-matching files are moved to the archive directory.",
    "The whitelist matching logic must interpret the content of `<workspace>/whitelist_notes.md` rather than using literal filenames.",
    "Explicitly exclude cervical (`vertebrae_C*`) and lumbar (`vertebrae_L*`) vertebrae from the whitelist.",
    "Only retain thoracic vertebrae (`vertebrae_T2` through `vertebrae_T12`).",
    "Directory structure must be mirrored between source and archive: `<dataset_root>/totalseg_output/<patient_id>/` and `<archive_root>/<patient_id>/`.",
    "If a file is missing during processing, log the event but continue processing.",
    "If a patient directory is empty, log the event and proceed.",
    "The worker must have read access to the source and write access to the archive.",
    "All files are assumed to have the `.nii.gz` extension."
  ],
  "information_still_missing": [
    "Exact mapping rules from category descriptions in `whitelist_notes.md` to specific file name patterns.",
    "Whether the whitelist is fully defined by `whitelist_notes.md` or requires additional configuration.",
    "Clarification on whether the operation should be idempotent (safe to run multiple times).",
    "Exact naming convention for thoracic vertebrae (e.g., T1, T2... T12) beyond what's implied.",
    "Confirmation on handling of edge cases such as empty source directories or missing files in the context of the full batch."
  ],
  "first_3_concrete_actions": [
    "Read and parse the content of `<workspace>/whitelist_notes.md` to extract category descriptions and associated examples.",
    "Identify and validate the specific file naming patterns that correspond to each anatomical category mentioned, ensuring exclusion of cervical and lumbar vertebrae.",
    "Verify the existence of the source and archive root paths and ensure proper permissions for reading and writing."
  ]
}
```

## Planner v2

```text
# Planner V2: TotalSeg Mask Whitelist Filter

## Analysis of Worker V1
Worker V1 correctly identified the high-level goal and the need to parse `<workspace>/whitelist_notes.md`. However, it made several critical leaps that violate the instruction to "not turn category words... into exact executable membership rules unless the prompt already provides the authoritative rule."

1.  **False Assumption on Whitelist Source:** Worker V1 assumed the whitelist is defined by `<workspace>/whitelist_notes.md`. The prompt explicitly states: "TotalSeg 输出每个病人 100+ 个结构 mask... 训练只保留：心脏相关、肺叶、肋骨、胸椎（T 段）、锁骨、肱骨、胸骨、主动脉。" The prompt provides the **authoritative list of categories** directly in the text, not in a separate notes file. The notes file is likely just a reference for the human annotator, not the source of truth for the worker's logic.
2.  **Ambiguous Naming Convention:** Worker V1 assumed a naming convention like `vertebrae_T5.nii.gz` without confirmation. The prompt only says "胸椎（T 段）". The actual file names in the dataset could be `T1`, `T2`, `T3`, `T4`, `T5`, `T6`, `T7`, `T8`, `T9`, `T10`, `T11`, `T12`, or `vertebrae_T1`, etc. The worker must inspect the actual file names to determine the pattern.
3.  **Over-Interpretation of "Heart Related":** Worker V1 treated "heart related" as a category to be mapped. The prompt lists "心脏相关" as a single item. The worker should treat this as a single category name to match against, rather than trying to infer sub-categories like "heart_atrium_left" from a notes file.

## Corrected Constraints
*   **Whitelist Source of Truth:** The worker must use the **categories explicitly listed in the original request text** ("心脏相关", "肺叶", "肋骨", "胸椎（T 段）", "锁骨", "肱骨", "胸骨", "主动脉") as the definitive whitelist. It must **not** rely on `<workspace>/whitelist_notes.md` for the matching logic, as that file is not guaranteed to exist or be authoritative.
*   **Pattern Matching Strategy:** The worker must inspect the actual file names in the source directory to determine the exact naming pattern for each category. It cannot assume a prefix like `heart_` or `vertebrae_`.
*   **Thoracic Vertebrae Specifics:** The prompt specifies "胸椎（T 段）". The worker must identify which files correspond to the T-segment. It must explicitly exclude cervical (C) and lumbar (L) vertebrae if they appear in the dataset, regardless of the naming convention.
*   **Action:** The worker must perform a `move` operation. Source files matching the whitelist stay; non-matching files are moved to the archive.

## Still Missing
*   **Exact File Naming Patterns:** The worker does not know if files are named `lung_left.nii.gz` or `Lung_L.nii.gz`, or if vertebrae are named `T1` or `vertebrae_T1`. It must inspect the directory contents to reverse-engineer the pattern.
*   **"Heart Related" Scope:** The prompt lists "心脏相关" as a single category. The worker needs to know if this is a single file (e.g., `heart.nii.gz`) or a group of files (e.g., `heart`, `heart_atrium_left`, `heart_atrium_right`). It must inspect the directory to see how many files fall under this category.
*   **Archive Directory Creation:** The prompt specifies `<archive_root>/<patient_id>/`. The worker must verify if `<archive_root>` exists or if it needs to be created.

## Worker Next Focus
1.  **Inspect a Sample Directory:** Pick one patient directory from `<dataset_root>/totalseg_output/` and list all `.nii.gz` files. This is the only way to determine the exact naming convention for "肺叶", "肋骨", "胸椎", etc.
2.  **Verify "Heart Related" Files:** Check if "心脏相关" maps to a single file or multiple files in the sample.
3.  **Check for C/L Vertebrae:** Verify if the dataset contains cervical (`C*`) or lumbar (`L*`) vertebrae files that need to be excluded, even if they match the "T" pattern.

```json
{
  "corrected_constraints": [
    "The authoritative whitelist is the list of categories provided in the original request text: '心脏相关', '肺叶', '肋骨', '胸椎（T 段）', '锁骨', '肱骨', '胸骨', '主动脉'. The worker must not rely on <workspace>/whitelist_notes.md for matching logic.",
    "The worker must inspect actual file names in the source directory to determine the exact naming pattern for each category (e.g., 'lung_left' vs 'Lung_L').",
    "The worker must identify the specific files corresponding to '胸椎（T 段）' and explicitly exclude any cervical (C) or lumbar (L) vertebrae files found in the dataset.",
    "The operation is a 'move' action: files matching the whitelist remain in the source directory; non-matching files are moved to <archive_root>/<patient_id>/."
  ],
  "still_missing": [
    "The exact file naming convention for '肺叶', '肋骨', '胸椎', '锁骨', '肱骨', '胸骨', and '心脏相关' (is it a single file or multiple files?).",
    "Whether the dataset contains cervical (C) or lumbar (L) vertebrae files that need to be excluded from the 'T' segment group.",
    "The existence and structure of the <archive_root> directory."
  ],
  "worker_next_focus": [
    "Inspect the file list of a single patient directory to reverse-engineer the naming patterns for the whitelist categories.",
    "Verify if '心脏相关' maps to one or multiple files in the dataset.",
    "Check if the dataset contains any files with 'C' or 'L' in the name that should be excluded from the 'T' segment group."
  ]
}
```
```

## Worker v2

```text
{
  "understood_goal": "Process patient directories under `<dataset_root>/totalseg_output/` to filter and move mask files based on a predefined whitelist of anatomical categories extracted directly from the original prompt text. Retain only masks that belong to the specified categories ('心脏相关', '肺叶', '肋骨', '胸椎（T 段）', '锁骨', '肱骨', '胸骨', '主动脉'), explicitly excluding cervical and lumbar vertebrae, and move all others to an archive directory while maintaining directory structure.",
  "constraints_to_follow": [
    "The authoritative whitelist is the list of categories provided in the original request text: '心脏相关', '肺叶', '肋骨', '胸椎（T 段）', '锁骨', '肱骨', '胸骨', '主动脉'. The worker must not rely on <workspace>/whitelist_notes.md for matching logic.",
    "The worker must inspect actual file names in the source directory to determine the exact naming pattern for each category (e.g., 'lung_left' vs 'Lung_L').",
    "The worker must identify the specific files corresponding to '胸椎（T 段）' and explicitly exclude any cervical (C) or lumbar (L) vertebrae files found in the dataset.",
    "The operation is a 'move' action: files matching the whitelist remain in the source directory; non-matching files are moved to <archive_root>/<patient_id>/.",
    "The operation must be patient-level independent and parallelizable.",
    "Files matching the whitelist remain in the source directory; non-matching files are moved to the archive directory.",
    "Directory structure must be mirrored between source and archive: `<dataset_root>/totalseg_output/<patient_id>/` and `<archive_root>/<patient_id>/`.",
    "If a file is missing during processing, log the event but continue processing.",
    "If a patient directory is empty, log the event and proceed.",
    "The worker must have read access to the source and write access to the archive.",
    "All files are assumed to have the `.nii.gz` extension."
  ],
  "information_still_missing": [
    "The exact file naming convention for '肺叶', '肋骨', '胸椎', '锁骨', '肱骨', '胸骨', and '心脏相关' (is it a single file or multiple files?).",
    "Whether the dataset contains cervical (C) or lumbar (L) vertebrae files that need to be excluded from the 'T' segment group.",
    "The existence and structure of the <archive_root> directory."
  ],
  "first_3_concrete_actions": [
    "Inspect the file list of a single patient directory from `<dataset_root>/totalseg_output/` to reverse-engineer the naming patterns for the whitelist categories.",
    "Verify if '心脏相关' maps to one or multiple files in the dataset.",
    "Check if the dataset contains any files with 'C' or 'L' in the name that should be excluded from the 'T' segment group."
  ],
  "understanding_delta": [
    "Corrected the source of truth for the whitelist from `<workspace>/whitelist_notes.md` to the explicit list of categories in the original prompt.",
    "Recognized that the worker must inspect actual file names to determine naming conventions instead of assuming prefixes or patterns.",
    "Clarified that '胸椎（T 段）' requires identification of T-segment files and explicit exclusion of C/L vertebrae if present.",
    "Confirmed that '心脏相关' is a single category to be matched against, not a sub-category requiring further inference.",
    "Updated understanding of the need to validate the existence and structure of the archive root directory."
  ]
}
```

## Judge summary

- Verdict: `spec_weak`
- Handoff score: `4`
- Spec score: `4`
- Worker score: `5`

### Concise rationale

Planner v1 is clearly unsafe: it invents category/prefix logic and hardcodes vertebra ranges. Planner v2 corrects the source-of-truth confusion and preserves move/mirror/log semantics, but still over-commits to a category-based matching model instead of keeping exact whitelist membership unresolved. Worker v1 and v2 are cautious about missing mapping details, but they also carry forward an unsupported T2-T12 assumption, so the final handoff remains only weak-to-moderate quality.

### Covered gold constraints

- move non-whitelist files to the archive instead of deleting them
- mirror patient-level directory structure in the archive
- log missing files and skip without aborting
- treat the task as patient-independent and parallelizable
- worker preserves some uncertainty instead of fully collapsing everything into a confident implementation

### Missed gold constraints

- exact filename membership was not preserved; both planner versions drift toward category/pattern interpretation
- planner v1 explicitly introduces wrong category/prefix style reasoning
- planner v2 replaces the notes file with the prompt categories as source of truth, but still invents a concrete mapping strategy instead of leaving the exact whitelist artifact unresolved
- visible examples like distinct exact filenames are not used to block false generalization
- the unresolved exact whitelist material is not kept explicit as a required handoff artifact

### Forbidden assumptions made

- planner v1 assumes category-to-filename mapping from notes text and even narrows vertebrae to T2-T12
- planner v2 assumes the prompt categories themselves are sufficient to drive matching without preserving exact filename membership as unresolved
- worker v1 and v2 both implicitly accept a category/pattern interpretation rather than exact filename whitelist membership
- worker v1 and v2 introduce `T2` through `T12` as a concrete rule without support from the visible request
