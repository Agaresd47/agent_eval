# Exact whitelist split | B1 | DeepSeek V4 Flash

- Condition: `B1`
- Episode: `ep003_totalseg_whitelist_split`
- Pair: `deepseek_x_qwen`
- Source run: `run_result/T2_fill/output/t2_matrix_20260508_205201`
- Generated at: `20260508_205201`
- Source record index: `0`
- Canonical selection basis: latest real run for this exact condition + promoted episode + pair
- Raw judge verdict: `spec_strong`
- Displayed verdict: `spec_acceptable`
- Handoff score: `8`
- Worker score: `6`

## Judge read

Planner_v1 correctly preserved the core exact-whitelist, move-not-delete, mirrored-archive, and log-and-continue semantics, and worker_v1 reflected that safely while keeping the whitelist artifact missing. Planner_v2 then introduced an explicitly wrong category-based interpretation, causing worker_v2 to drift. Overall this is a strong handoff with a bad revision, so the main signal quality remains high.

## Manual Review Override

- Reviewer: `gpt-5.4 manual review`
- Reviewed on: `2026-05-09`
- Override status: `approved_override`
- Reviewed verdict: `spec_acceptable`
- Reason: planner_v1/worker_v1 preserved much of the core boundary, but planner_v2 introduced the forbidden category/pattern whitelist rule and worker_v2 adopted it. The raw judge output is internally inconsistent with the judge yaml cap for forbidden-assumption cases.

## Files

- `canonical_run.json`: normalized single-cell record with provenance metadata.
- `source_record.json`: exact raw record for this cell.
- `source_matrix.json`: full source matrix artifact from the selected run.
- `source_execution_note.md`: run-level execution note.
- `handoff_trace.md`: readable planner/worker/judge trace.
- `source_prompts/`: copied prompt previews for planner, worker, and judge when available.
- `manual_review_override.json`: reviewed verdict metadata when this cell has an approved manual override.
