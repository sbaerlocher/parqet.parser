.PHONY: help
.DEFAULT_GOAL := help


# Test if 'dde' alias is defined
DDE_CMD=$(shell grep '^alias dde[[:space:]]*=' ${HOME}/.bashrc ${HOME}/.zshrc 2>/dev/null | awk -F= '{gsub(/^[[:space:]]*alias dde[[:space:]]*=[[:space:]]*/, "", $$2); gsub(/^[\"\047]|[\"\047]$$/, "", $$2); print $$2}' | head -n 1)

# Define the commands based on 'dde' alias
ifeq ($(DDE_CMD),)
	UP_CMD := docker compose up
	PARSER_CMD := docker compose exec parser python3 main.py
else
	UP_CMD := $(DDE_CMD) up
	PARSER_CMD := $(DDE_CMD) exec parser python3 main.py
endif

# Task to start all services
up:
	-$(UP_CMD) || true

# Task to execute the Parqet parser inside the container
parser:
	$(PARSER_CMD)

# Display help
help:
	@echo "Available commands:"
	@echo "  up        - Start all services using docker compose or dde."
	@echo "  parser    - Execute the Parqet parser inside the parser service."

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
