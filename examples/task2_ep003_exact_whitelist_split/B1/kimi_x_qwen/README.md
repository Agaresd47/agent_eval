# Exact whitelist split | B1 | Kimi K2.5

- Condition: `B1`
- Episode: `ep003_totalseg_whitelist_split`
- Pair: `kimi_x_qwen`
- Source run: `run_result/T2_fill/output/t2_matrix_20260508_205311`
- Generated at: `20260508_205311`
- Source record index: `3`
- Canonical selection basis: latest real run for this exact condition + promoted episode + pair
- Raw judge verdict: `spec_acceptable`
- Displayed verdict: `spec_acceptable`
- Handoff score: `6`
- Worker score: `7`

## Judge read

Planner_v1 was clearly overconfident and wrong on whitelist specifics. Planner_v2 improved by flagging the missing authoritative source, but it also diluted the exact filename boundary instead of preserving it crisply. Worker_v2 is safer than worker_v1 because it tracks missing information rather than pretending the whitelist is known. Overall the pair is usable but not strong.

## Files

- `canonical_run.json`: normalized single-cell record with provenance metadata.
- `source_record.json`: exact raw record for this cell.
- `source_matrix.json`: full source matrix artifact from the selected run.
- `source_execution_note.md`: run-level execution note.
- `handoff_trace.md`: readable planner/worker/judge trace.
- `source_prompts/`: copied prompt previews for planner, worker, and judge when available.
- `manual_review_override.json`: reviewed verdict metadata when this cell has an approved manual override.
