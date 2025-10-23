.PHONY: help build up down logs shell test clean dev install
.DEFAULT_GOAL := help

# Variables
# Use 'docker compose' (v2) instead of 'docker-compose' (v1)
COMPOSE = docker compose
COMPOSE_DEV = docker compose --profile dev
SERVICE = parser
SERVICE_DEV = parser-dev

# Test if 'dde' alias is defined (legacy support)
DDE_CMD=$(shell grep '^alias dde[[:space:]]*=' ${HOME}/.bashrc ${HOME}/.zshrc 2>/dev/null | awk -F= '{gsub(/^[[:space:]]*alias dde[[:space:]]*=[[:space:]]*/, "", $$2); gsub(/^[\"\047]|[\"\047]$$/, "", $$2); print $$2}' | head -n 1)

# Override commands if DDE is available
ifneq ($(DDE_CMD),)
	COMPOSE := $(DDE_CMD)
	COMPOSE_DEV := $(DDE_CMD) --profile dev
endif

help: ## Show this help message
	@echo "Parqet Parser - Makefile Commands"
	@echo "=================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Docker Operations
build: ## Build the Docker image
	$(COMPOSE) build

rebuild: ## Rebuild the Docker image without cache
	$(COMPOSE) build --no-cache

# File Operations
process: ## Process all files in data/ directory
	@echo "Processing files..."
	$(COMPOSE) up $(SERVICE)
	@echo "\nResults in output/ directory"

process-debug: ## Process files with DEBUG logging
	PARQET_LOG_LEVEL=DEBUG $(COMPOSE) up $(SERVICE)

# Legacy DDE support
parser: process ## Execute parser (legacy command)
up: process ## Alias for process

# Development
dev: ## Start development shell
	$(COMPOSE_DEV) run --rm $(SERVICE_DEV)

dev-python: ## Start Python REPL in dev container
	$(COMPOSE_DEV) run --rm $(SERVICE_DEV) python

shell: ## Open bash shell in dev container
	$(COMPOSE_DEV) run --rm $(SERVICE_DEV) /bin/bash

# Testing
test: ## Run tests in container
	$(COMPOSE_DEV) run --rm $(SERVICE_DEV) pytest

test-cov: ## Run tests with coverage
	$(COMPOSE_DEV) run --rm $(SERVICE_DEV) pytest --cov=app --cov-report=html

test-verbose: ## Run tests with verbose output
	$(COMPOSE_DEV) run --rm $(SERVICE_DEV) pytest -v

mypy: ## Run type checking
	$(COMPOSE_DEV) run --rm $(SERVICE_DEV) mypy app/

lint: ## Run all checks (tests + mypy)
	@echo "Running tests..."
	@$(MAKE) test
	@echo "\nRunning type checking..."
	@$(MAKE) mypy

# File Operations
process: ## Process all files in data/ directory
	@echo "Processing files..."
	$(COMPOSE) up $(SERVICE)
	@echo "\nResults in output/ directory"

process-debug: ## Process files with DEBUG logging
	PARQET_LOG_LEVEL=DEBUG $(COMPOSE) up $(SERVICE)

# Setup
setup: ## Initial setup (create directories and config)
	@echo "Creating directories..."
	@mkdir -p data output logs
	@if [ ! -f config.json ]; then \
		echo "Creating config.json template..."; \
		echo '{}' > config.json; \
		echo "⚠️  Please edit config.json with your IBAN mappings"; \
	fi
	@if [ ! -f .env ]; then \
		echo "Creating .env from template..."; \
		cp .env.example .env; \
		echo "✓ .env created"; \
	fi
	@echo "\n✓ Setup complete!"
	@echo "\nNext steps:"
	@echo "1. Edit config.json with your IBAN mappings"
	@echo "2. Place PDF/CSV files in data/"
	@echo "3. Run 'make process'"

install: setup build ## Complete installation (setup + build)
	@echo "\n✓ Installation complete!"
	@echo "\nReady to process files. Run:"
	@echo "  make process"

# Cleanup
clean: ## Remove output and log files
	@echo "Cleaning output and logs..."
	@rm -rf output/* logs/*
	@echo "✓ Cleaned"

clean-all: clean down ## Remove containers, output, and logs
	@echo "Removing Docker images..."
	$(COMPOSE) down --rmi local -v
	@echo "✓ Full cleanup complete"

# Docker Debug
docker-inspect: ## Inspect the parser container
	docker inspect parqet-parser

docker-stats: ## Show container resource usage
	docker stats parqet-parser --no-stream

health: ## Check container health
	@docker inspect parqet-parser | grep -A 10 '"Health"' || echo "Container not running"

# Utility targets
watch-logs: ## Watch log files in real-time
	tail -f logs/general.log

archive: ## Archive processed files by month
	@mkdir -p archive/$$(date +%Y-%m)
	@mv data/*.pdf archive/$$(date +%Y-%m)/ 2>/dev/null || true
	@mv data/*.csv archive/$$(date +%Y-%m)/ 2>/dev/null || true
	@echo "✓ Files archived to archive/$$(date +%Y-%m)/"

list-brokers: ## List all available brokers
	$(COMPOSE_DEV) run --rm $(SERVICE_DEV) python -c "\
from app.lib.brokers import *; \
print('Available Brokers:'); \
for broker in __all__: \
    if 'Broker' in broker and broker != 'BaseBroker': \
        print(f'  - {broker}');"

version: ## Show version information
	@echo "Parqet Parser"
	@echo "============="
	@echo "Python version:"
	@$(COMPOSE_DEV) run --rm $(SERVICE_DEV) python --version
	@echo "\nInstalled packages:"
	@$(COMPOSE_DEV) run --rm $(SERVICE_DEV) pip list | grep -E "(pandas|pdfplumber|pydantic|pytest)"

# Quick actions
quick-process: clean process ## Clean and process in one command

quick-test: build test ## Build and test

# Info
info: ## Show project information
	@echo "Parqet Parser Information"
	@echo "========================="
	@echo "Data directory:    ./data"
	@echo "Output directory:  ./output"
	@echo "Logs directory:    ./logs"
	@echo "Config file:       ./config.json"
	@echo ""
	@echo "File counts:"
	@echo "  Input files:  $$(ls -1 data/ 2>/dev/null | wc -l)"
	@echo "  Output CSVs:  $$(ls -1 output/*.csv 2>/dev/null | wc -l)"
	@echo "  Log files:    $$(ls -1 logs/*.log 2>/dev/null | wc -l)"

# run-megalinter:
# Run Megalinter locally to check code quality across multiple languages.
run-megalinter:
	@docker run --rm --name megalint -v $(shell pwd):/tmp/lint busybox rm -rf /tmp/lint/megalinter-reports /tmp/lint/packages/firewallguard/assets/static/js/cdn.min.js /tmp/lint/assets/abuild/6696f7cf.rsa
	@docker run --rm --name megalint -v $(shell pwd):/tmp/lint -e MARKDOWN_SUMMARY_REPORTER=true oxsecurity/megalinter:v8.4.2

# format-code: ## Format code files (using Prettier, isort, and black).
format-python:
	@docker run --rm --name isort -v $(shell pwd):/app python:3.9-slim bash -c "pip install isort && isort /app"
	@docker run --rm --name black -v $(shell pwd):/app python:3.9-slim bash -c "pip install black && black /app"


# format-eclint:
# Run ECLint using Docker to fix code style issues in JavaScript files.
format-eclint:
	@docker run --rm --name eclint -v $(shell pwd):$(shell pwd) -w /$(shell pwd) node:alpine npx eclint fix "**/*.{js,jsx}"

# format-code:
# Format code files using Prettier via Docker.
format-code:
	@docker run --rm --name prettier -v $(shell pwd):$(shell pwd) -w /$(shell pwd) node:alpine npx prettier . --write

format-all: format-python format-code format-eclint
	@echo "Formatting completed."

# run-megalinter: ## Run Megalinter l
