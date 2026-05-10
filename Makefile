.DEFAULT_GOAL := help
.PHONY: help install run test clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

$(VENV)/bin/activate:
	python3 -m venv $(VENV)

install: $(VENV)/bin/activate ## Create .venv and install dependencies
	$(PIP) install -e ".[dev]"

run: ## Start MCP server
	$(PYTHON) -m src

test: ## Run tests
	$(PYTHON) -m pytest tests -v

clean: ## Remove .venv and caches
	rm -rf $(VENV) __pycache__ .pytest_cache *.egg-info
