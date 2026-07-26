.PHONY: validate test schemas architecture policy integration runner range agent docs demo compile format-check lint typecheck optional-tools

validate: compile test

compile:
	python3 -m compileall -q src scripts tests

test:
	python3 -m pytest

schemas:
	python3 -m pytest tests/schemas

architecture:
	python3 -m pytest tests/architecture

policy:
	python3 -m pytest tests/policy tests/unit/test_policy_gateway.py

integration:
	python3 -m pytest tests/integration

runner:
	python3 -m pytest tests/integration/test_isolated_runner_mvp.py tests/architecture/test_phase_04_runner.py

range:
	python3 -m pytest tests/integration/test_cyber_range_mvp.py tests/architecture/test_phase_05_range.py

agent:
	python3 -m pytest tests/integration/test_agent_workflow.py tests/unit/test_agent_contracts.py tests/architecture/test_phase_06_agent.py

docs:
	python3 -m pytest tests/architecture/test_docs.py

demo:
	PYTHONPATH=src python3 -m cyber_eval.demo

format-check:
	python3 -m ruff format --check .

lint:
	python3 -m ruff check .

typecheck:
	python3 -m mypy src

optional-tools:
	@python3 scripts/check_optional_tools.py
