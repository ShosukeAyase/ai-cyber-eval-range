.PHONY: validate test schemas architecture policy docs optional-tools

validate: test

test:
	python3 -m pytest -q

schemas:
	python3 -m pytest -q tests/schemas

architecture:
	python3 -m pytest -q tests/architecture

policy:
	python3 -m pytest -q tests/policy

docs:
	python3 -m pytest -q tests/architecture/test_docs.py

optional-tools:
	@python3 scripts/check_optional_tools.py
