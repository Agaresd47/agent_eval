# Finished pair promotion with manifest and rollback | A0_strict

- Condition summary: One safe response only. No follow-up questions. No tool calls.
- Condition rules source: `data/t1_tasks/test_ground/t1_cli_finished_pair_promote_atomic_manifest_A0_strict.yaml`

| Model | Cell status | Oracle passed | Final phase | Has errors |
| --- | --- | --- | --- | --- |
| Claude Haiku 4.5 | present | True | final_answer | no |
| Qwen3 Coder 30B | present | True | start | yes |
| GLM 4.7 Flash | present | True | start | yes |
| Kimi K2.5 | present | True | start | yes |
| DeepSeek V4 Flash | present | True | start | yes |
| MiMo V2.5 Pro | present | True | final_answer | no |

Each model folder contains the standalone artifact bundle for that cell.
