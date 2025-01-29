#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = t2v-sign-language
PYTHON_VERSION = 3.10
PYTHON_INTERPRETER = python

#################################################################################
# COMMANDS                                                                      #
#################################################################################


## Install Python Dependencies
.PHONY: requirements
requirements:
	$(PYTHON_INTERPRETER) -m pip install -U pip
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt
	



## Delete all compiled Python files
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using flake8 and black (use `make format` to do formatting)
.PHONY: lint
lint:
	flake8 t2v_sign_language
	isort --check --diff --profile black t2v_sign_language
	black --check --config pyproject.toml t2v_sign_language

## Format source code with black
.PHONY: format
format:
	black --config pyproject.toml t2v_sign_language


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
