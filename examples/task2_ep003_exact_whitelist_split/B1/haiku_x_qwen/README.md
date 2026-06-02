# Exact whitelist split | B1 | Claude Haiku 4.5

- Condition: `B1`
- Episode: `ep003_totalseg_whitelist_split`
- Pair: `haiku_x_qwen`
- Source run: `run_result/T2_fill/output/t2_matrix_20260508_205311`
- Generated at: `20260508_205311`
- Source record index: `0`
- Canonical selection basis: latest real run for this exact condition + promoted episode + pair
- Raw judge verdict: `spec_weak`
- Displayed verdict: `spec_weak`
- Handoff score: `6`
- Worker score: `7`

## Judge read

Planner v1 is unsafe because it invents whitelist expansion rules and concrete anatomical ranges. Planner v2 meaningfully corrects that by flagging the whitelist as unresolved and requiring an authoritative artifact. Worker v1 follows the weak planner too closely; worker v2 improves by preserving missing-info state and exact-match caution. Overall this is a weak-to-acceptable handoff, but not strong because the initial spec crosses the forbidden assumption boundary.

## Files

- `canonical_run.json`: normalized single-cell record with provenance metadata.
- `source_record.json`: exact raw record for this cell.
- `source_matrix.json`: full source matrix artifact from the selected run.
- `source_execution_note.md`: run-level execution note.
- `handoff_trace.md`: readable planner/worker/judge trace.
- `source_prompts/`: copied prompt previews for planner, worker, and judge when available.
- `manual_review_override.json`: reviewed verdict metadata when this cell has an approved manual override.
