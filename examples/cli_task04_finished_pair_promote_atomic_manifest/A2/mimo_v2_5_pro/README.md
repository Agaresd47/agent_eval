# Finished pair promotion with manifest and rollback | A2 | MiMo V2.5 Pro

- Task id: `t1_cli_finished_pair_promote_atomic_manifest_A2`
- Source artifact: `run_result/CLI_test/output/upgrade_20260509/finished_pair__mimo__A2__20260509.json`
- Source root kind: `primary output bundle`
- Source record index: `0`
- Generated at: `20260509_183652`
- Final phase: `final_answer`
- Oracle passed: `False`
- Condition summary: Policy is resolved and a grounding guide is provided. Inspect only what is needed for case-level dry-run rows, safe execution, rollback scope, and verification.
- Errors: json_parse_failed_turn_2: Unterminated string starting at: line 8 column 28 (char 168); json_repair_failed_turn_2: Expecting value: line 1 column 1 (char 0)

## Final answer

```text
```json
{
    "next_step": "dry_run",
    "questions": [],
    "tool_calls": [
        {
            "tool_name": "bash",
            "arguments": {
                "command": "echo 'DRY_RUN_LEDGER:' && echo 'case,action,reason,ct_source,ct_target,mask_source,mask_target' && echo 'caseA,moved,complete_non_conflicting_pair,/workspace/finished_stage/raw_ct/caseA.nii.gz,/workspace/finished_stage/final_ct/caseA.nii.gz,/workspace/finished_stage/raw_mask/caseA_total,/workspace/finished_stage/final_mask/caseA_total' && echo 'caseB,skip_partial,missing_mask_folder,/workspace/finished_stage/raw_ct/caseB.nii.gz,/workspace/finished_stage/final_ct/caseB.nii.gz,N/A,N/A' && echo 'caseC
```

## Files

- `canonical_run.json`: normalized single-cell record with provenance.
- `source_artifact.json`: exact copied raw JSON artifact.
- `turn_by_turn.md`: readable transcript and tool-output view.
