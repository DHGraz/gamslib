# make test, coverage, documentation, etc
SHELL := /bin/bash

docs:
	@echo "Generating documentation..."
	@pdoc3 --html --output-dir reference --force gamslib
	@echo "Documentation generated in the 'reference' directory."


test:
	uv run pytest tests --cov=gamslib --cov-report=term-missing

build:
	uv build	