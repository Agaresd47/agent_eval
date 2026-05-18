PYTHON ?= python
T1_CHAT_CONFIG ?= configs/public/t1_chat_demo.yaml
T1_CLI_CONFIG ?= configs/public/t1_cli_demo.yaml
T2_CONFIG ?= configs/public/t2_demo.yaml

.PHONY: help install smoke test unit t1-dry t1-live t1-cli-mock t1-cli-live t2-dry t2-live

help:
	@echo install
	@echo smoke
	@echo t1-dry
	@echo t1-live
	@echo t1-cli-mock
	@echo t1-cli-live
	@echo t2-dry
	@echo t2-live

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

smoke: test unit

test:
	$(PYTHON) tests/run_tests.py

unit:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"

t1-dry:
	$(PYTHON) scripts/task/task1/t1_matrix_runner.py --config $(T1_CHAT_CONFIG) --dry-run

t1-live:
	$(PYTHON) scripts/task/task1/t1_matrix_runner.py --config $(T1_CHAT_CONFIG)

t1-cli-mock:
	$(PYTHON) scripts/task/task1/run_sandbox_eval.py --config $(T1_CLI_CONFIG) --mock-agent

t1-cli-live:
	$(PYTHON) scripts/task/task1/run_sandbox_eval.py --config $(T1_CLI_CONFIG)

t2-dry:
	$(PYTHON) scripts/task/task2/t2_matrix_runner.py --config $(T2_CONFIG) --dry-run

t2-live:
	$(PYTHON) scripts/task/task2/t2_matrix_runner.py --config $(T2_CONFIG)
