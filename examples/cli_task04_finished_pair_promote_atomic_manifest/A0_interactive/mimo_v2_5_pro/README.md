# Finished pair promotion with manifest and rollback | A0_interactive | MiMo V2.5 Pro

- Task id: `t1_cli_finished_pair_promote_atomic_manifest`
- Source artifact: `run_result/CLI_test/output/upgrade_20260508/finished_pair__mimo4800__A0_interactive__20260508.json`
- Source root kind: `primary output bundle`
- Source record index: `0`
- Generated at: `20260509_003844`
- Final phase: `can_finalize`
- Oracle passed: `True`
- Condition summary: Inspect before asking. Dry run before mutation. Ask before execute.
- Errors: No recorded runtime errors.

## Final answer

```text
Promotion task completed. CaseA was moved successfully from raw_ct and raw_mask to final_ct and final_mask. Cases B, C, D were skipped due to partial pairs (missing mask or CT files), and cases E, F were skipped due to target conflicts (existing files in final directories). The promotion_manifest.csv and promotion_rollback.sh have been written and verified, with all checks passing.
```

## Files

- `canonical_run.json`: normalized single-cell record with provenance.
- `source_artifact.json`: exact copied raw JSON artifact.
- `turn_by_turn.md`: readable transcript and tool-output view.
