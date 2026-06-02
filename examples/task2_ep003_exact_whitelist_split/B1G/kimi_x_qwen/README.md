# Exact whitelist split | B1G | Kimi K2.5

- Condition: `B1_guardrailed`
- Episode: `ep003_totalseg_whitelist_split`
- Pair: `kimi_x_qwen`
- Source run: `run_result/T2_four_planner_probe/output/t2_matrix_20260505_104641`
- Generated at: `20260505_104641`
- Source record index: `1`
- Canonical selection basis: latest real run for this exact condition + promoted episode + pair
- Raw judge verdict: `spec_weak`
- Displayed verdict: `spec_weak`
- Handoff score: `4`
- Worker score: `4`

## Judge read

The planner preserved the broad move-to-archive triage shape, but it did not robustly lock the worker onto exact filename membership. It introduced unsafe pattern-language, then planner_v2 incorrectly changed missing-file behavior and added extra machinery. The worker followed those weaker directions and did not keep the missing exact whitelist artifact as the central unresolved item.

## Files

- `canonical_run.json`: normalized single-cell record with provenance metadata.
- `source_record.json`: exact raw record for this cell.
- `source_matrix.json`: full source matrix artifact from the selected run.
- `source_execution_note.md`: run-level execution note.
- `handoff_trace.md`: readable planner/worker/judge trace.
- `source_prompts/`: copied prompt previews for planner, worker, and judge when available.
- `manual_review_override.json`: reviewed verdict metadata when this cell has an approved manual override.
