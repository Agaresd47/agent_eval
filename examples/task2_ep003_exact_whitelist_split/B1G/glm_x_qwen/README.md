# Exact whitelist split | B1G | GLM 4.7 Flash

- Condition: `B1_guardrailed`
- Episode: `ep003_totalseg_whitelist_split`
- Pair: `glm_x_qwen`
- Source run: `run_result/T2_four_planner_probe/output/t2_matrix_20260505_104641`
- Generated at: `20260505_104641`
- Source record index: `0`
- Canonical selection basis: latest real run for this exact condition + promoted episode + pair
- Raw judge verdict: `spec_weak`
- Displayed verdict: `spec_weak`
- Handoff score: `5`
- Worker score: `7`

## Judge read

The planner got the action/mirror/missing-file mechanics right, but it also invented a concrete whitelist subset (vertebrae_T2-T12) instead of preserving the exact filename whitelist as unresolved. Worker_v1 followed that drift; worker_v2 corrected toward safer exact-match handling while still flagging missing exact list details. Overall this is a weak-to-moderate handoff, not strong.

## Files

- `canonical_run.json`: normalized single-cell record with provenance metadata.
- `source_record.json`: exact raw record for this cell.
- `source_matrix.json`: full source matrix artifact from the selected run.
- `source_execution_note.md`: run-level execution note.
- `handoff_trace.md`: readable planner/worker/judge trace.
- `source_prompts/`: copied prompt previews for planner, worker, and judge when available.
- `manual_review_override.json`: reviewed verdict metadata when this cell has an approved manual override.
