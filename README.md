# Agent 边界纪律评测

一套面向「文件 / CLI / 委派类 Agent」的边界纪律评测脚手架。

评测想回答的问题：模型在信息不完整、边界未确认时的工程判断力——会不会先主动澄清和查证，而不是把空白补成默认事实往下做。

代码层面把 `task / judge / fixture / runner` 拆开，方便扩成更大的 hidden eval；rubric、condition、judge 都在 yaml 里，加任务不动 Python。

## 评测覆盖

三条线沿一条递进展开：先看纯问答下能不能识别信息缺口，再看拿到真实执行权限时能不能守纪律，最后看任务交给下游 worker 时边界能不能完整传递。

- **T1 Chat（信息缺口处理）**
  模型拿到信息留有缺口的任务时，会不会先把边界问清楚、查清楚，再决定继续执行。任务覆盖目录重组、批量去重、导出清理等高风险文件操作。

- **T1 CLI（执行纪律）**
  模型有真实 shell 执行权限时，会不会守住 `inspect → dry-run → approve → execute → verify` 闭环。每个变更操作要落 manifest 和 rollback，verify 是闭环收尾。

- **T2 Episodes（任务委派）**
  planner-worker 交接里，边界会不会被写坏或在复核里修回来。每题跑 `planner_v1 → worker_v1 → planner_v2 → worker_v2` 四步，由 judge 分别给两次 worker 输出打分。

每条线都设了多个任务条件（A0_strict / A0_interactive / A1 / A2 或 B1 / B1G），同一道题在不同信息暴露和约束下重测，差异本身就是 finding。

## 仓库结构

```
agent/         ReAct loop 与工具表（demo agent 用，会自己搭 pipeline）
configs/       judge / 模型 / 公开 demo 配置
data/
  t1_chat/         T1 Chat 任务与 judge
  t1_cli/          T1 CLI 任务与 judge
  t2_episodes/     T2 planner-worker episodes 与 judge
engine/        Pipeline DSL + 执行节点；smoke 测试与 demo agent 用这一套跑单步
examples/      三道展示题的完整 run 结果（不用配 key 也能看）
fixtures/      任务依赖的样例目录和文件
rules/         评分规则、rubric 与共享定义
scripts/task/  跑大矩阵实测用的 runner（T1/T2，端到端 LLM 调用、判分、写盘）
tests/         smoke cases 与单元测试
```

`engine/` 和 `scripts/task/` 是两条执行路径：前者把任务封成 DSL 步骤，给 demo agent 和 smoke 测试用；后者是 production runner，直接驱动模型跑全量矩阵并落盘。两边共用 `data/` 里的任务和 judge 定义。

不想跑也想看实际效果，直接看 [examples/](examples/)——三条评测线各一道展示题，含全部 condition × 全部模型 × 多次重复的 run，以及 judge 误判已知 case 的 audit log。

## 快速开始

```bash
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
make smoke
```

不用 `make` 直接跑：

```bash
python tests/run_tests.py
python -m unittest discover -s tests -p "test_*.py"
```

## 环境变量

`smoke` 和 `dry-run` 不需要任何 key。

跑 live matrix 需要：

- `OPENAI_API_KEY` —— judge 调用
- `EVAL_API_KEY` / `EVAL_BASE_URL` / `EVAL_MODEL_NAME` —— 被测模型，走 OpenAI-compatible 接口

最简一份 `.env`：

```env
EVAL_BASE_URL=https://api.openai.com/v1
EVAL_MODEL_NAME=gpt-4.1-mini
EVAL_API_KEY=your_api_key
```

切到别的 provider 改 [configs/models.yaml](configs/models.yaml)。

## 常用命令

| 命令 | 说明 | 需要 key |
| --- | --- | --- |
| `make smoke` | 公开样例 + 单测 | 否 |
| `make t1-dry` | T1 Chat read-only dry-run | 否 |
| `make t1-cli-mock` | T1 CLI mock-agent 路径 | 否 |
| `make t1-live` | T1 Chat 默认演示配置 | 是 |
| `make t1-cli-live` | T1 CLI 默认演示配置 | 是 |
| `make t2-dry` | T2 dry-run | 否 |
| `make t2-live` | T2 默认演示配置 | 是 |

输出落到 `run_result/`。

## 默认公开配置

公开配置故意做小，方便上手：

- [configs/public/t1_chat_demo.yaml](configs/public/t1_chat_demo.yaml) —— 两个 T1 Chat 任务
- [configs/public/t1_cli_demo.yaml](configs/public/t1_cli_demo.yaml) —— 两个 T1 CLI 任务
- [configs/public/t2_demo.yaml](configs/public/t2_demo.yaml) —— 两个 T2 episode

要扩成大矩阵，复制这些配置、加 task / episode / model pair 即可。

## 设计取舍

- **task / judge / fixture / runner 解耦**：rubric 和 condition 都在 yaml 里，加任务和加模型不动 Python；同一道题换条件就是改一行。
- **condition 是一等公民**：A0_strict、A0_interactive、A1、A2 不是不同的题，是同一道题在不同信息暴露和约束下重测，差异本身就是评测信号。
- **闭环判分而不是终态判分**：T1 CLI 看 `inspect / dry-run / execute / verify` 各环节的合分，终态文件系统对了但纪律环节失败仍会扣分。
- **judge 是 LLM + rubric**，不是字符串匹配；rubric 在 [rules/](rules/) 与各 `data/*/judges/` 下，可以替换或加多 judge 投票。

## 当前局限

- 公开仓库不包含完整 run result。任务规模、N、模型清单与解读见配套展示页。
- LLM judge 存在已知偏差，当前打分流程包含作者人工复核与少量 manual adjustment；下一版计划补多 judge 投票、人工盲审、逐步评分降噪。
- 任务原型来自作者本人在医学影像 ML 方向的真实数据流水线（nnU-Net 训练布局、metadata 子集切分等），领域偏窄但任务形态在文件 / CLI / 委派类 agent 上具有代表性。
