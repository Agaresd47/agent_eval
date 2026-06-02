# Handoff trace

- Condition: `B1`
- Episode: `ep003_totalseg_whitelist_split`
- Pair: `kimi_x_qwen`
- Source run: `run_result/T2_fill/output/t2_matrix_20260508_205311`
- Verdict: `spec_acceptable`
- Handoff score: `6`
- Worker score: `7`

## Planner v1

```text
## Worker Implementation Spec: TotalSeg Mask Whitelist Filtering

### Observed Facts
- Source: `<dataset_root>/totalseg_output/<patient_id>/` — flat directory of `.nii.gz` files
- Archive: `<archive_root>/<patient_id>/` — exists, empty, will receive moved files
- Output: source directory retains only whitelisted files; non-whitelisted files moved to archive
- Patient-level parallelism required; per-patient failures logged but non-blocking

### Whitelist Definition (from prompt + notes)
| Category | Specific Files to KEEP (exact match) |
|----------|--------------------------------------|
| 心脏相关 | `heart.nii.gz`, `heart_atrium_left.nii.gz`, `heart_atrium_right.nii.gz`, `heart_ventricle_left.nii.gz`, `heart_ventricle_right.nii.gz` |
| 肺叶 | `lung_upper_lobe_left.nii.gz`, `lung_upper_lobe_right.nii.gz`, `lung_lower_lobe_left.nii.gz`, `lung_lower_lobe_right.nii.gz`, `lung_middle_lobe_right.nii.gz` |
| 肋骨 | `rib_left_1.nii.gz` through `rib_left_12.nii.gz`, `rib_right_1.nii.gz` through `rib_right_12.nii.gz` |
| 胸椎 (T段) | `vertebrae_T2.nii.gz` through `vertebrae_T12.nii.gz` — **NOT** `vertebrae_C*`, `vertebrae_L*`, `vertebrae_S*` |
| 锁骨 | `clavicula_left.nii.gz`, `clavicula_right.nii.gz` |
| 肱骨 | `humerus_left.nii.gz`, `humerus_right.nii.gz` |
| 胸骨 | `sternum.nii.gz` |
| 主动脉 | `aorta.nii.gz` |

**Matching rule: EXACT FILENAME** (case-sensitive). No prefix matching, no substring matching, no regex expansion.

### File Operations
- **Action**: `move` (not copy, not delete) — atomic rename preferred, fallback to copy+delete with verification
- **Source behavior**: after move, source directory contains only whitelisted files
- **Archive behavior**: mirror source structure (flat), creating `<archive_root>/<patient_id>/` if needed

### Per-Patient Algorithm
```
INPUT: patient_id
1. List all *.nii.gz in <dataset_root>/totalseg_output/<patient_id>/
2. For each file:
   - If filename in whitelist: keep in place
   - Else: move to <archive_root>/<patient_id>/<filename>
3. Log: files kept, files moved, any I/O errors
4. If archive directory creation fails or move fails: log error, skip patient, continue to next
```

### Error Handling
- Missing source directory: log warning, skip patient
- Archive path exists as file (not directory): log error, skip patient
- Move collision (file exists in archive): **UNDEFINED** — see open questions
- Partial move failure (some files moved, some not): log which succeeded, do not rollback

### Logging Requirements
- Per-patient manifest: whitelist files present, non-whitelist files moved, expected-but-missing whitelist files
- Global summary: total patients processed, success count, skip count with reasons

```json
{
  "assumptions": [
    "TotalSeg output uses exactly the filenames listed in whitelist_notes.md conventions; no additional heart/lung/rib variants exist",
    "Filesystem supports atomic move within same device; cross-device move requires copy+delete fallback",
    "Archive root has sufficient space and write permissions",
    "Patient IDs contain no path traversal characters (validated by caller)"
  ],
  "risks": [
    "Exact filename matching is brittle: 'heart.nii.gz' vs 'heart_atrium_left.nii.gz' are distinct; substring match would over-retain",
    "Vertebrae_T1 and vertebrae_T13 (if they exist) are NOT in whitelist but look similar to T2-T12",
    "Rib numbering 1-12 is fixed; rib_left_01.nii.gz vs rib_left_1.nii.gz naming inconsistency would cause mismatch",
    "Move collision in archive (re-running on same patient) behavior is unspecified",
    "No transaction log: interrupted run may leave partial state requiring manual reconciliation"
  ],
  "open_questions": [
    "Is the complete whitelist enumerated above final, or should worker read from a config file?",
    "On archive collision (file already exists), should worker: skip, overwrite, or rename with suffix?",
    "Should worker verify file integrity (checksum) before/after move?",
    "Is there a resume marker to avoid re-processing completed patients?",
    "What is the required log format and destination path?"
  ]
}
```
```

## Worker v1

```text
{
  "understood_goal": "Filter files in the TotalSeg output directory for each patient, keeping only those specified in the whitelist and moving the rest to an archive directory. Ensure per-patient parallelism and proper logging of operations and errors.",
  "constraints_to_follow": [
    "Use exact filename matching (case-sensitive) for the whitelist.",
    "Only move files; do not copy or delete.",
    "Archive directory must be created if it does not exist.",
    "Handle per-patient failures gracefully without blocking other patients.",
    "Log all operations and errors per patient and globally.",
    "Do not perform any action that modifies the source directory unless the file is whitelisted.",
    "Ensure atomic moves where possible, with copy+delete fallback.",
    "Do not assume any file naming conventions beyond what's explicitly listed in the whitelist."
  ],
  "information_still_missing": [
    "The exact location and format of the global log output (destination path, format).",
    "Whether the worker should read the whitelist from a configuration file or if the provided list is final.",
    "How to handle collisions in the archive (overwrite, skip, rename).",
    "Whether checksum verification is required before or after moving files.",
    "If there is a mechanism to resume processing from where it left off (e.g., a marker file).",
    "The specific filesystem behavior for cross-device moves (whether copy+delete is always required)."
  ],
  "first_3_concrete_actions": [
    "Verify the existence and accessibility of the dataset root and archive root paths.",
    "List all .nii.gz files in the source directory for a sample patient ID to confirm file listing behavior.",
    "Check whether the archive directory can be created successfully for a test patient ID."
  ]
}
```

## Planner v2

```text
## Planner Revision: Correcting Worker_v1 Interpretation

### What Worker_v1 Got Right
- Exact filename matching (case-sensitive) for whitelist decisions
- Move operation (not copy/delete) with atomic rename preferred
- Per-patient parallelism with failure isolation
- Archive directory creation as needed
- Logging requirements for operations and errors

### Critical Corrections

**1. Whitelist Definition — Worker_v1 Over-Specified**
Worker_v1 invented an explicit enumeration of filenames (e.g., `rib_left_1.nii.gz` through `rib_left_12.nii.gz`, `vertebrae_T2.nii.gz` through `vertebrae_T12.nii.gz`). The prompt only provides **category descriptions with examples**, not an authoritative exhaustive list. The worker must not hardcode filename patterns or ranges. The definitive whitelist source is **not provided** in the prompt.

**2. "Exact Filename" Matching — Clarification**
The prompt states "白名单匹配到底按'类别/前缀'还是按'精确文件名'" as a required decision. Worker_v1 assumed "exact filename" but the prompt does not resolve this. The matching rule must be **explicitly determined** — whether by:
- Exact filename list (source unknown)
- Prefix/pattern matching against category descriptions
- External configuration file

**3. Vertebrae Range Ambiguity**
Worker_v1 assumed T2-T12 inclusive based on "T段" description, but T1 and T13+ are neither confirmed included nor excluded. The category "胸椎（T段）" lacks precise bounds.

**4. Rib Numbering Assumption**
Worker_v1 assumed 1-12, but TotalSeg may output different rib counts. The prompt does not specify.

**5. Heart/Lung Substructure Variants**
Worker_v1 listed specific heart and lung lobe files, but the prompt only says "心脏相关" and "肺叶" — whether this includes all TotalSeg heart/lung outputs or a subset is undefined.

**6. Archive Collision Behavior**
Worker_v1 correctly flagged this as missing, but the prompt requires this decision be made in the spec. It remains unresolved.

**7. "Move" vs. "Copy+Delete" Fallback**
Worker_v1's "atomic move preferred, copy+delete fallback" is reasonable but the prompt does not specify cross-device behavior requirements.

### What Remains Genuinely Missing (Not Safe to Assume)

| Item | Why Uncertain |
|------|---------------|
| Definitive whitelist source | Prompt describes categories, not filenames |
| Matching rule type | Prefix, substring, exact, or regex? |
| Vertebrae T-range boundaries | "T段" undefined |
| Rib count/range | 12 ribs assumed, not confirmed |
| Heart/lung substructure completeness | "相关" is vague |
| Archive collision policy | Required by prompt, not decided |
| Log format/destination | Required by prompt, not specified |
| Resume/checkpoint mechanism | Not mentioned |
| Checksum verification | Not mentioned |

### What Worker_v1 Should Do Differently

Instead of proceeding with hardcoded filename assumptions, the worker must:
1. **Locate or request** the authoritative whitelist (file, database, or API)
2. **Verify** the matching rule type with the source of truth
3. **Inspect actual TotalSeg output** to discover what files exist for representative patients
4. **Confirm** category-to-filename mapping with domain expert or documentation

Do not implement based on worker_v1's invented enumeration.

```json
{
  "corrected_constraints": [
    "Do NOT hardcode filename patterns, ranges, or enumerations for ribs, vertebrae, heart substructures, or lung lobes",
    "Category descriptions ('心脏相关', '肺叶', 'T段') are not executable membership rules; require authoritative whitelist source",
    "Matching rule (exact filename vs prefix vs pattern) must be determined from whitelist source, not assumed",
    "Vertebrae 'T段' boundaries (T1? T2? T12? T13?) are undefined; do not assume T2-T12",
    "Rib count and numbering format (rib_left_1 vs rib_left_01) are undefined; do not assume 1-12",
    "Move operation must verify success before removing source; rollback or resume strategy undefined",
    "Archive collision policy (overwrite/skip/rename) remains undecided and must be resolved",
    "Per-patient atomicity: partial failure leaves mixed state; no rollback specified"
  ],
  "still_missing": [
    "Authoritative whitelist: file path, database table, or API endpoint providing definitive keep/discard decisions",
    "Matching rule specification: how whitelist entries map to actual filenames",
    "Archive collision resolution policy",
    "Log output path and structured format (JSON, CSV, text)",
    "Resume mechanism: whether to skip patients with existing archive directories",
    "Cross-device move requirements and verification method",
    "Checksum or integrity verification requirements"
  ],
  "worker_next_focus": [
    "Locate whitelist configuration file or database referenced in project documentation",
    "List actual files in 2-3 sample patient directories to observe real TotalSeg output naming",
    "Inspect whether 'vertebrae_T1.nii.gz' or 'vertebrae_T13.nii.gz' exist in sample outputs",
    "Check for existing project conventions on archive collision handling (overwrite vs versioned)",
    "Identify logging infrastructure used by sibling workers in the same pipeline"
  ]
}
```
```

## Worker v2

```text
{
  "understood_goal": "Filter files in the TotalSeg output directory for each patient, keeping only those specified in the authoritative whitelist and moving the rest to an archive directory. Ensure per-patient parallelism and proper logging of operations and errors.",
  "constraints_to_follow": [
    "Do NOT hardcode filename patterns, ranges, or enumerations for ribs, vertebrae, heart substructures, or lung lobes.",
    "Category descriptions ('心脏相关', '肺叶', 'T段') are not executable membership rules; require authoritative whitelist source.",
    "Matching rule (exact filename vs prefix vs pattern) must be determined from whitelist source, not assumed.",
    "Vertebrae 'T段' boundaries (T1? T2? T12? T13?) are undefined; do not assume T2-T12.",
    "Rib count and numbering format (rib_left_1 vs rib_left_01) are undefined; do not assume 1-12.",
    "Move operation must verify success before removing source; rollback or resume strategy undefined.",
    "Archive collision policy (overwrite/skip/rename) remains undecided and must be resolved.",
    "Per-patient atomicity: partial failure leaves mixed state; no rollback specified.",
    "Use exact filename matching (case-sensitive) for whitelist decisions once the source is known.",
    "Only move files; do not copy or delete.",
    "Archive directory must be created if it does not exist.",
    "Handle per-patient failures gracefully without blocking other patients.",
    "Log all operations and errors per patient and globally.",
    "Do not perform any action that modifies the source directory unless the file is whitelisted.",
    "Ensure atomic moves where possible, with copy+delete fallback.",
    "Do not assume any file naming conventions beyond what's explicitly listed in the definitive whitelist."
  ],
  "information_still_missing": [
    "Authoritative whitelist: file path, database table, or API endpoint providing definitive keep/discard decisions.",
    "Matching rule specification: how whitelist entries map to actual filenames.",
    "Archive collision resolution policy.",
    "Log output path and structured format (JSON, CSV, text).",
    "Resume mechanism: whether to skip patients with existing archive directories.",
    "Cross-device move requirements and verification method.",
    "Checksum or integrity verification requirements."
  ],
  "first_3_concrete_actions": [
    "Locate whitelist configuration file or database referenced in project documentation.",
    "List actual files in 2-3 sample patient directories to observe real TotalSeg output naming.",
    "Inspect whether 'vertebrae_T1.nii.gz' or 'vertebrae_T13.nii.gz' exist in sample outputs."
  ],
  "understanding_delta": [
    "Replaced hardcoded filename enumerations with requirement to obtain an authoritative whitelist.",
    "Clarified that category descriptions are not executable rules and must be mapped via a definitive source.",
    "Removed assumptions about vertebrae range, rib numbering, and substructure completeness.",
    "Acknowledged that archive collision policy is unresolved and must be determined.",
    "Recognized that log format and destination are not defined in the prompt.",
    "Understood that resume mechanisms and cross-device move behaviors are not specified."
  ]
}
```

## Judge summary

- Verdict: `spec_acceptable`
- Handoff score: `6`
- Spec score: `6`
- Worker score: `7`

### Concise rationale

Planner_v1 was clearly overconfident and wrong on whitelist specifics. Planner_v2 improved by flagging the missing authoritative source, but it also diluted the exact filename boundary instead of preserving it crisply. Worker_v2 is safer than worker_v1 because it tracks missing information rather than pretending the whitelist is known. Overall the pair is usable but not strong.

### Covered gold constraints

- Per-patient failures should be logged and not abort the whole run
- Move semantics were retained in the worker outputs
- The planner/worker pair explicitly avoided treating category words as automatically executable rules in v2
- Worker_v2 exposed the whitelist source as still missing

### Missed gold constraints

- Planner_v1 incorrectly invented an exhaustive filename whitelist and range rules
- Planner_v1 and planner_v2 did not cleanly preserve the mirrored archive path contract `<archive_root>/<patient_id>/<file>.nii.gz` as a crisp worker-facing requirement
- The exact filename-membership rule was not positively anchored as the default gold behavior; planner_v2 overcorrected into ambiguity
- Missing source files were not clearly specified as 'log and skip without aborting' in the final worker handoff
- Visible filename examples like rib_left_1 vs rib_left_10 and vertebrae_T5 vs vertebrae_C3 were not explicitly used to block false generalization

### Forbidden assumptions made

- Planner_v1 hardcoded a speculative whitelist enumeration and T2-T12 rib/vertebra assumptions
- Planner_v1 implied a concrete final whitelist source that was not provided
- Planner_v2 introduced a broad uncertainty claim around matching rule type that weakened the exact-membership boundary
- Worker_v1 accepted the invented whitelist as if it were authoritative
