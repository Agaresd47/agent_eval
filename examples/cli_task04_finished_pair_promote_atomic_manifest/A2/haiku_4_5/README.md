# Finished pair promotion with manifest and rollback | A2 | Claude Haiku 4.5

- Task id: `t1_cli_finished_pair_promote_atomic_manifest_A2`
- Source artifact: `run_result/CLI_test/output/upgrade_20260509_supplemental_finished_pair/finished_pair_haiku_A1_A2_20260509_rerun.json`
- Source root kind: `primary output bundle`
- Source record index: `1`
- Generated at: `20260509_173032`
- Final phase: `final_answer`
- Oracle passed: `True`
- Condition summary: Policy is resolved and a grounding guide is provided. Inspect only what is needed for case-level dry-run rows, safe execution, rollback scope, and verification.
- Errors: No recorded runtime errors.

## Final answer

```text
Task completed successfully. All 6 cases have been processed:

**Moved (1 case):**
- caseA: Complete pair moved to final_ct/caseA.nii.gz and final_mask/caseA_total

**Skipped Partial (3 cases):**
- caseB: Missing mask folder
- caseC: Missing mask folder
- caseD: Missing CT file

**Skipped Conflict (2 cases):**
- caseE: final_ct/caseE.nii.gz already exists
- caseF: final_mask/caseF_total already exists

**Artifacts created:**
- promotion_manifest.csv: Records all 6 cases with action, reason, and source/target paths
- promotion_rollback.sh: Contains restore commands for caseA only (moved case)

**Verification passed:**
- Moved targets exist in final_ct and final_mask
- Moved sources removed from raw_ct and raw_mask
- Skipped sources preserved in raw directories
- Manifest contains exact tokens (moved, skip_partial, skip_conflict, complete_non_conflicting_pair, missing_mask_folder, missing_ct_file, final_ct_exists, final_mask_exists)
- Rollback script excludes all skipped cases (caseB, caseC, caseD, caseE, caseF)

Oracle verification: PASSED (all 40 checks passed).
```

## Files

- `canonical_run.json`: normalized single-cell record with provenance.
- `source_artifact.json`: exact copied raw JSON artifact.
- `turn_by_turn.md`: readable transcript and tool-output view.
