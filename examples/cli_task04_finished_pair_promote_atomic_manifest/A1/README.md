# Finished pair promotion with manifest and rollback | A1

- Condition summary: Policy is resolved. Pair inventory, conflict checks, manifest scope, and verification still require inspection.
- Condition rules source: `data/t1_tasks/test_ground/t1_cli_finished_pair_promote_atomic_manifest_A1.yaml`

| Model | Cell status | Oracle passed | Final phase | Has errors |
| --- | --- | --- | --- | --- |
| Claude Haiku 4.5 | present | True | final_answer | no |
| Qwen3 Coder 30B | present | False | need_dry_run | yes |
| GLM 4.7 Flash | present | True | final_answer | no |
| Kimi K2.5 | present | True | final_answer | no |
| DeepSeek V4 Flash | present | True | final_answer | no |
| MiMo V2.5 Pro | present | True | final_answer | no |

Each model folder contains the standalone artifact bundle for that cell.
