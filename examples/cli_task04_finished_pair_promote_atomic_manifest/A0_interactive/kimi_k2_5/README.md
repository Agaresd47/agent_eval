# Finished pair promotion with manifest and rollback | A0_interactive | Kimi K2.5

- Task id: `t1_cli_finished_pair_promote_atomic_manifest`
- Source artifact: `run_result/CLI_test/output/upgrade_20260509/finished_pair__kimi__A0_interactive__20260509.json`
- Source root kind: `primary output bundle`
- Source record index: `0`
- Generated at: `20260509_164358`
- Final phase: `final_answer`
- Oracle passed: `True`
- Condition summary: Inspect before asking. Dry run before mutation. Ask before execute.
- Errors: No recorded runtime errors.

## Final answer

```text
Promotion task completed successfully. All verification checks passed:

- caseA: CT and mask pair moved from raw_ct/raw_mask to final_ct/final_mask
- caseB, caseC: Skipped (partial pairs - missing mask folders)
- caseD: Skipped (partial pair - missing CT file)
- caseE: Skipped (conflict - final_ct/caseE.nii.gz already existed)
- caseF: Skipped (conflict - final_mask/caseF_total already existed)

Manifest written to /workspace/finished_stage/promotion_manifest.csv with all 6 cases documented using exact contract columns and tokens. Rollback script written to /workspace/finished_stage/promotion_rollback.sh containing restore commands for caseA only (the only moved case).
```

## Files

- `canonical_run.json`: normalized single-cell record with provenance.
- `source_artifact.json`: exact copied raw JSON artifact.
- `turn_by_turn.md`: readable transcript and tool-output view.
