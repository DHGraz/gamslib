# make test, coverage, documentation, etc
SHELL := /bin/bash

.PHONY: all test coverage clean

docs:
	@echo "Generating documentation..."
	@pdoc3 --html --output-dir reference --force gamslib
	@echo "Documentation generated in the 'reference' directory."


test:
	@uv run pytest tests 

coverage:
	@uv run pytest tests --cov-report term-missing --cov=gamslib 

build:
	@uv build	
