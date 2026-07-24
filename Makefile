.PHONY: validate test schemas architecture policy docs compile format-check lint typecheck optional-tools

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

docs:
	python3 -m pytest tests/architecture/test_docs.py

format-check:
	python3 -m ruff format --check .

lint:
	python3 -m ruff check .

typecheck:
	python3 -m mypy src

optional-tools:
	@python3 scripts/check_optional_tools.py
