# agent_eval

一个面向中国大厂 `Agent Dev / Agent Eval` 岗位的轻量评测项目。

这个仓库的目标不是做完整产品，而是提供一套面试官可以直接拉起、快速理解的评测原型，用来展示你是否能把 Agent 能力拆成可验证、可复现、可扩展的评测结构。

当前公开版重点覆盖两类问题：

- `T1`：高风险文件操作任务里，模型什么时候该追问，什么时候该检查，什么时候才应该执行
- `T2`：planner 写给 worker 的任务说明，是否能在多轮交接后变得更清晰、更安全

## 这个仓库适合展示什么

- 能否把模糊的 Agent 行为问题，落成结构化评测任务
- 能否把 `clarification / inspection / execution` 三段行为拆开建模
- 能否设计 planner-worker handoff 的评测口径
- 能否把 `task / judge / fixture / runner` 解耦，而不是把逻辑都堆进 prompt

## 仓库结构

- `TASKS.md`
  - 面试题背景和讨论方向
- `configs/public/`
  - 对外展示用的最小配置
- `data/t1_chat/`
  - `T1` 对话式评测任务与 judge
- `data/t1_cli/`
  - `T1` CLI/sandbox 评测任务与 judge
- `data/t2_episodes/`
  - `T2` planner-worker episodes 与 judge
- `fixtures/`
  - 任务依赖的样例文件和目录
- `rules/`
  - 评测规则、rubric 与共享定义
- `scripts/task/task1/t1_matrix_runner.py`
  - `T1` read-only runner
- `scripts/task/task1/run_sandbox_eval.py`
  - `T1` CLI sandbox runner
- `scripts/task/task2/t2_matrix_runner.py`
  - `T2` planner-worker runner
- `tests/run_tests.py`
  - 对外 smoke cases

## 快速开始

```bash
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
make smoke
```

如果你不使用 `make`：

```bash
python tests/run_tests.py
python -m unittest discover -s tests -p "test_*.py"
```

## 环境变量

仅跑 `smoke / dry-run` 不需要模型 key。

真正跑 `live matrix` 时，默认需要：

- `OPENAI_API_KEY`
  - 用于 judge 调用
- `EVAL_API_KEY`
- `EVAL_BASE_URL`
- `EVAL_MODEL_NAME`
  - 用于默认公开 runner `provider_stub_chat`

最简单的接法是接一个 OpenAI-compatible 接口，例如：

```env
EVAL_BASE_URL=https://api.openai.com/v1
EVAL_MODEL_NAME=gpt-4.1-mini
EVAL_API_KEY=your_api_key
```

如果你想切到别的 provider，可以改 [configs/models.yaml](</C:/Users/agares/OneDrive/0 求职/面试/agent_eval/configs/models.yaml>)。

## 常用命令

- `make smoke`
  - 跑公开样例和单测，不需要 key
- `make t1-dry`
  - 跑 `T1` read-only dry-run
- `make t1-live`
  - 跑默认 `T1 Chat` 演示配置
- `make t1-cli-mock`
  - 跑 `T1 CLI` mock-agent 路径，不需要 key
- `make t1-cli-live`
  - 跑 `T1 CLI` live 路径
- `make t2-dry`
  - 跑 `T2` dry-run
- `make t2-live`
  - 跑默认 `T2` 演示配置

输出会写到 `run_result/`。

## 默认公开配置

这个仓库故意把公开配置做得很小，方便面试官上手：

- [configs/public/t1_chat_demo.yaml](</C:/Users/agares/OneDrive/0 求职/面试/agent_eval/configs/public/t1_chat_demo.yaml>)
  - 两个 `T1 Chat` 任务
- [configs/public/t1_cli_demo.yaml](</C:/Users/agares/OneDrive/0 求职/面试/agent_eval/configs/public/t1_cli_demo.yaml>)
  - 两个 `T1 CLI` 任务
- [configs/public/t2_demo.yaml](</C:/Users/agares/OneDrive/0 求职/面试/agent_eval/configs/public/t2_demo.yaml>)
  - 两个 `T2` episode

如果你想扩成更大的矩阵，直接复制这些配置，再加 task / episode / model pair 即可。

## 面试时可以怎么讲

- `T1` 的重点不是“模型会不会答”，而是“模型会不会在信息不足时克制地问和查”
- `T1 Chat` 和 `T1 CLI` 分开，是因为二者的风险面、工具约束和 judge 口径本质不同
- `T2` 的重点不是“worker 最后能不能写出代码”，而是“planner 传递的信息边界是否稳定”
- 这个仓库的核心设计点，是把 `task`、`judge`、`fixture`、`runner` 分开，方便后续扩成 hidden eval
