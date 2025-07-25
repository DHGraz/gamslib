#!/bin/bash
uv run pytest --cov --cov-report term-missing --cov=gamslib tests
