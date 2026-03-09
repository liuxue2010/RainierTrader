.PHONY: install test lint run run-paper check-config

install:
	pip install -e ".[dev]"

test:
	pytest tests/

test-cov:
	pytest --cov=rainier_trader tests/

lint:
	ruff check rainier_trader/ tests/

run:
	rainier run

run-paper:
	rainier run --paper

check-config:
	rainier check-config
