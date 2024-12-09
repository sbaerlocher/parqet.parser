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
