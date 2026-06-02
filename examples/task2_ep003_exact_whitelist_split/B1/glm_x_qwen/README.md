# Exact whitelist split | B1 | GLM 4.7 Flash

- Condition: `B1`
- Episode: `ep003_totalseg_whitelist_split`
- Pair: `glm_x_qwen`
- Source run: `run_result/T2_fill/output/t2_matrix_20260508_205311`
- Generated at: `20260508_205311`
- Source record index: `2`
- Canonical selection basis: latest real run for this exact condition + promoted episode + pair
- Raw judge verdict: `spec_weak`
- Displayed verdict: `spec_weak`
- Handoff score: `4`
- Worker score: `5`

## Judge read

Planner v1 is clearly unsafe: it invents category/prefix logic and hardcodes vertebra ranges. Planner v2 corrects the source-of-truth confusion and preserves move/mirror/log semantics, but still over-commits to a category-based matching model instead of keeping exact whitelist membership unresolved. Worker v1 and v2 are cautious about missing mapping details, but they also carry forward an unsupported T2-T12 assumption, so the final handoff remains only weak-to-moderate quality.

## Files

- `canonical_run.json`: normalized single-cell record with provenance metadata.
- `source_record.json`: exact raw record for this cell.
- `source_matrix.json`: full source matrix artifact from the selected run.
- `source_execution_note.md`: run-level execution note.
- `handoff_trace.md`: readable planner/worker/judge trace.
- `source_prompts/`: copied prompt previews for planner, worker, and judge when available.
- `manual_review_override.json`: reviewed verdict metadata when this cell has an approved manual override.
