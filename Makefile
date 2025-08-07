.PHONY: all
all: ## Show the available make targets.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep

.PHONY: clean
clean: ## Clean the temporary files.
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf .pytest_cache
	rm -rf tests/__pycache__
	rm -rf .coverage

.PHONY: black-check
black-check: ## Run black for code formatting, without fixing.
	poetry run black src --check

.PHONY: black-apply
black-apply: ## Run black and fix code formatting.
	poetry run black src

.PHONY: ruff-check
ruff-check: ## Run ruff for linting and code formatting, without fixing.
	poetry run ruff check src

.PHONY: ruff-apply
ruff-apply: ## Run ruff and fix linting and code formatting.
	poetry run ruff check --fix src

.PHONY: pylint
pylint: ## Run pylint for code analysis.
	poetry run pylint src

.PHONY: lint
lint:  ## Run Python linters without fixing.
	make black-check
	make ruff-check
	make pylint

.PHONY: lint-apply
lint-apply: ## Run black and ruff with auto-fix, and Pylint.
	make black-apply
	make ruff-apply
	make pylint

.PHONY: mypy
mypy:  ## Run mypy.
	poetry run mypy src

.PHONY: install
install:  ## Install the dependencies excluding dev.
	poetry install --only main --no-root

.PHONY: install-dev
install-dev:  ## Install the dependencies including dev.
	poetry install --no-root

.PHONY: test
test: ## Run the lambda tests.
	poetry run pytest -n auto --cov=src --cov-report term-missing --cov-fail-under=95
	