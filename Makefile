#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = t2v-sign-language
PYTHON_VERSION = 3.12.7
PYTHON_INTERPRETER = python

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Create a Python virtual environment using rye
.PHONY: create_environment
create_environment:
	rye init --py=$(PYTHON_VERSION) --requirements=requirements.lock --dev-requirements=requirements-dev.lock

## Install Python Dependencies
.PHONY: requirements
requirements:
	rye sync


## Delete all compiled Python files
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using flake8 and black (use `make format` to do formatting)
.PHONY: lint
lint:
	rye run flake8 t2v_sign_language
	rye run isort --check --diff --profile black t2v_sign_language
	rye run black --check --config pyproject.toml t2v_sign_language

## Format source code with black
.PHONY: format
format:
	rye run black --config pyproject.toml t2v_sign_language


## Download Data from storage system
.PHONY: sync_data_down
sync_data_down:
	gsutil -m rsync -r gs://t2v-sign-language/data/ data/


## Upload Data to storage system
.PHONY: sync_data_up
sync_data_up:
	gsutil -m rsync -r data/ gs://t2v-sign-language/data/






#################################################################################
# PROJECT RULES                                                                 #
#################################################################################



#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = '\n'.join([line for line in sys.stdin]); \
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n([a-zA-Z_-]+):', lines); \
print('Available rules:\n'); \
print('\n'.join(['{:25}{}'.format(*reversed(match)) for match in matches]))
endef
export PRINT_HELP_PYSCRIPT

help:
	@$(PYTHON_INTERPRETER) -c "${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)
