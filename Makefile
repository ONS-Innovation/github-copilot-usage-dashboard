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

.PHONY: format
format:  ## Format the code.
	poetry run black .
	poetry run ruff check . --fix

.PHONY: black
black: ## Run black.
	poetry run black src --check
	poetry run black aws_lambda_scripts --check

.PHONY: ruff
ruff: ## Run ruff without fixing.
	poetry run ruff check src
	poetry run ruff check aws_lambda_scripts

.PHONY: pylint
pylint: ## Run pylint.
	poetry run pylint src
	poetry run pylint aws_lambda_scripts

.PHONY: lint
lint:  ## Run Python linter
	make black
	make ruff || true
	make pylint || true

.PHONY: mypy
mypy:  ## Run mypy.
	poetry run mypy src
	poetry run mypy aws_lambda_scripts

.PHONY: install
install:  ## Install the dependencies excluding dev.
	poetry install --only main --no-root

.PHONY: install-dev
install-dev:  ## Install the dependencies including dev.
	poetry install --no-root

.PHONY: run-local
run-local:  ## Install the dependencies including dev.
	poetry run streamlit run src/app.py --server.port 8502