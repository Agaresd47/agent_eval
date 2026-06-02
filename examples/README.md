# examples

三道展示题的完整 run 结果，每条评测线各一道。HM 不用配 key 也能看到这套评测真实跑出来长什么样。

## 三道题

| 目录 | 评测线 | 测什么 |
| --- | --- | --- |
| `chat_task04_code_export_zip_sanitizer/` | 信息缺口处理 | 模型要把代码导出给外部 reviewer，能不能先盘 secrets、`.gitignore`、之前的 export.zip 这些边界，再决定怎么做 |
| `cli_task04_finished_pair_promote_atomic_manifest/` | CLI 执行纪律 | 暂存目录里只有图像和分割文件夹都齐全的样本才能搬到正式目录，过程要落 manifest 和 rollback——重点看模型守不守 atomic + 配对 + rollback 这条事务链 |
| `task2_ep003_exact_whitelist_split/` | planner-worker 委派 | spec 反复强调"按精确文件名匹配，不是按前缀、不是按类别"，看 planner 会不会在交接和复核里把"exact"漂成"category-based" |

## 怎么挑这 3 道

- 每道题在自己那条线上区分度都好（6 个被测模型分层清晰）
- 失败模式直接打在该评测想测的核心上，不是副作用
- judge 误判已知 case 在 `manual_review_overrides.json`（task2）和 `manual_score_matrix.md`（chat / cli）里都留有 audit log，没有掩盖

## 30 秒看哪几个 cell

- **Chat task04**: 对比 `A0_interactive/haiku_4_5/` (9 分，5 个并列工具调用) vs `A0_interactive/glm_4_7/` (5 分，一个 `list_files` 草草了事)
- **CLI task04**: 对比 `A1/deepseek_v4_flash/` (10 分，inspect → dry-run → execute → manifest+rollback → verify 教科书闭环) vs `A1/qwen3_coder_30b/` (3 分，turn 16 JSON 解析失败，manifest 和 rollback 都断)
- **Task2 ep003**: 看 `B1/deepseek_x_qwen/` 的 planner_v1 vs planner_v2——planner_v1 明确写"exact filename, NOT a pattern"，planner_v2 自己改成"a set of categories"，worker_v2 跟着掉分（"二次漂移"教科书例子）

## 完整结果与解读

这里只放 3 道题。完整 16 任务 × 4 条件 × 6 模型 × 4 重复的结果与跨任务解读见配套展示页（链接待补）。
