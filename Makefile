# make test, coverage, documentation, etc
SHELL := /bin/bash

.PHONY: all test coverage clean docs build test-all

docs:
	@echo "Generating documentation..."
	@pdoc3 --html --output-dir reference --force gamslib
	@echo "Documentation generated in the 'reference' directory."


test:
	@uv run pytest tests 

# Run all tests with different python versions
test-versions:
	@uv run --python 3.11 --isolated --with-editable '.[test]' pytest
	@uv run --python 3.12 --isolated --with-editable '.[test]' pytest
	@uv run --python 3.13 --isolated --with-editable '.[test]' pytest
# 3.14 depencies currently have some wheel issues: magicka require 1.20, which is rather old
	# @uv run --python 3.14 --isolated --with-editable '.[test]' pytest

coverage:
	@uv run pytest tests --cov-report term-missing --cov=gamslib 

build:
	@uv build	
