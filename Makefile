.PHONY: help check test format lint typecheck mdformat fix clean all

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

all: check ## Run all checks and tests (default CI workflow)

check: format-check lint typecheck mdformat-check test ## Run all checks without modifying files

test: ## Run tests with coverage
	pytest tests/ --cov=src --cov-report=term-missing

format: ## Format code with ruff
	ruff format

format-check: ## Check code formatting without modifying files
	ruff format --check

lint: ## Check linting issues
	ruff check

lint-fix: ## Auto-fix linting issues
	ruff check --fix

typecheck: ## Run type checking with ty
	uvx ty check

mdformat: ## Format markdown files
	uvx mdformat *.md docs/ src/

mdformat-check: ## Check markdown formatting without modifying files
	uvx mdformat --check *.md docs/ src/

fix: format lint-fix mdformat ## Auto-fix all formatting and linting issues

clean: ## Clean up Python cache files and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build dist .coverage htmlcov/

install: ## Install dependencies with uv
	uv sync

dev: install ## Set up development environment
	@echo "Development environment ready!"
	@echo "Run 'make check' to verify everything works"
