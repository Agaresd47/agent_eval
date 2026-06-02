# Exact whitelist split | B1 | Qwen3 Coder 30B

- Condition: `B1`
- Episode: `ep003_totalseg_whitelist_split`
- Pair: `qwen_x_qwen`
- Source run: `run_result/T2_fill/output/t2_matrix_20260508_205311`
- Generated at: `20260508_205311`
- Source record index: `1`
- Canonical selection basis: latest real run for this exact condition + promoted episode + pair
- Raw judge verdict: `spec_strong`
- Displayed verdict: `spec_strong`
- Handoff score: `8`
- Worker score: `8`

## Judge read

The planner preserved the main hidden constraint: exact filename whitelist membership with move-to-archive semantics and mirrored patient structure, while explicitly leaving the exact whitelist material unresolved. The worker responses remained aligned and safe, though they still left archive-creation behavior ambiguous.

## Files

- `canonical_run.json`: normalized single-cell record with provenance metadata.
- `source_record.json`: exact raw record for this cell.
- `source_matrix.json`: full source matrix artifact from the selected run.
- `source_execution_note.md`: run-level execution note.
- `handoff_trace.md`: readable planner/worker/judge trace.
- `source_prompts/`: copied prompt previews for planner, worker, and judge when available.
- `manual_review_override.json`: reviewed verdict metadata when this cell has an approved manual override.
