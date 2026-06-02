# Source runs and notes

These are the concrete run artifacts behind this folder summary.

- `run_result/T2_fill/output/t2_matrix_20260508_205201`
  - deepseek_x_qwen=reviewed:spec_acceptable (raw:spec_strong)
- `run_result/T2_fill/output/t2_matrix_20260508_205311`
  - haiku_x_qwen=spec_weak, qwen_x_qwen=spec_strong, glm_x_qwen=spec_weak, kimi_x_qwen=spec_acceptable, mimo_x_qwen=spec_acceptable

## Reading note

- This browser keeps the condition boundary strict: `B1` and `B1_guardrailed` are not mixed.
- Historical `B0_guardrailed` pilot runs remain in `artifact_inventory.json`, but they are not used as `B1G` substitutes here.
