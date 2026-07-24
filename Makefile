.PHONY: validate test schemas architecture policy integration docs demo compile format-check lint typecheck optional-tools

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
