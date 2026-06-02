# Finished pair promotion with manifest and rollback | A2 | Kimi K2.5

- Task id: `t1_cli_finished_pair_promote_atomic_manifest_A2`
- Source artifact: `run_result/CLI_test/output/upgrade_20260509/finished_pair__kimi__A2__20260509.json`
- Source root kind: `primary output bundle`
- Source record index: `0`
- Generated at: `20260509_182939`
- Final phase: `final_answer`
- Oracle passed: `True`
- Condition summary: Policy is resolved and a grounding guide is provided. Inspect only what is needed for case-level dry-run rows, safe execution, rollback scope, and verification.
- Errors: No recorded runtime errors.

## Final answer

```text
Task completed successfully. All verification checks passed:

- caseA: promoted (CT and mask moved to final_ct/final_mask, sources removed)
- caseB, caseC: skipped partial (missing mask folders, sources preserved)
- caseD: skipped partial (missing CT file, mask source preserved)
- caseE: skipped conflict (final_ct/caseE.nii.gz exists, sources preserved)
- caseF: skipped conflict (final_mask/caseF_total exists, sources preserved)

Manifests written:
- promotion_manifest.csv: 6 rows covering all cases with correct action/reason tokens
- promotion_rollback.sh: restore commands for caseA only (the moved case)

All 14 filesystem checks and 36 manifest semantic checks passed.
```

## Files

- `canonical_run.json`: normalized single-cell record with provenance.
- `source_artifact.json`: exact copied raw JSON artifact.
- `turn_by_turn.md`: readable transcript and tool-output view.
