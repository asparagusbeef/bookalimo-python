# Bookalimo SDK Development Makefile

.PHONY: help install test test-fast test-all lint typecheck format security clean coverage docs build publish

# Default target
help:
	@echo "Bookalimo SDK Development Commands"
	@echo "================================="
	@echo ""
	@echo "Setup and Installation:"
	@echo "  install         Install package in development mode with all extras"
	@echo "  install-test    Install package with test dependencies only"
	@echo "  install-min     Install package with minimal dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test           Run all tests with coverage"
	@echo "  test-fast      Run tests quickly (no integration/performance tests)"
	@echo "  test-all       Run comprehensive test suite including slow tests"
	@echo "  test-unit      Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-performance  Run performance tests only"
	@echo "  test-noplaces  Run tests without Google Places integration"
	@echo "  test-real-api  Run real API integration tests (requires credentials)"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint           Run linting checks"
	@echo "  format         Auto-format code"
	@echo "  typecheck      Run type checking"
	@echo "  security       Run security scans"
	@echo ""
	@echo "Coverage and Reports:"
	@echo "  coverage       Generate coverage reports"
	@echo "  coverage-html  Generate HTML coverage report"
	@echo "  coverage-xml   Generate XML coverage report"
	@echo ""
	@echo "Documentation:"
	@echo "  docs           Build documentation"
	@echo "  docs-serve     Serve documentation locally"
	@echo ""
	@echo "Build and Release:"
	@echo "  build          Build distribution packages"
	@echo "  clean          Clean build artifacts and cache"
	@echo "  publish-test   Publish to TestPyPI"
	@echo "  publish        Publish to PyPI"

# Installation targets
install:
	pip install -e ".[dev,test,places]"

install-test:
	pip install -e ".[test,places]"

install-min:
	pip install -e .

# Testing targets
test:
	pytest -v --cov=bookalimo --cov-report=term-missing --cov-report=html

test-fast:
	pytest -v -m "not slow and not integration and not performance" --maxfail=5

test-all:
	pytest -v --cov=bookalimo --cov-report=term-missing --cov-report=html --cov-report=xml

test-unit:
	pytest -v tests/ -m "not integration and not performance and not slow" --cov=bookalimo

test-integration:
	pytest -v tests/ -m integration

test-performance:
	pytest -v tests/ -m performance --durations=10

test-noplaces:
	pytest -v tests/ -k "not test_google_places and not places" --cov=bookalimo

test-real-api:
	pytest -v tests/test_real_api_integration.py -m "integration and network"

# Code quality targets
lint:
	ruff check .
	ruff format --check .

format:
	ruff format .
	ruff check . --fix

typecheck:
	mypy src/bookalimo --config-file pyproject.toml

security:
	bandit -r src/ -f text
	safety check

# Coverage targets
coverage:
	pytest --cov=bookalimo --cov-report=term-missing --cov-report=html --cov-report=xml

coverage-html:
	pytest --cov=bookalimo --cov-report=html
	@echo "HTML coverage report generated in htmlcov/"

coverage-xml:
	pytest --cov=bookalimo --cov-report=xml
	@echo "XML coverage report generated: coverage.xml"

# Documentation targets
docs:
	mkdocs build --strict

docs-serve:
	mkdocs serve

# Build and release targets
build: clean
	python -m build

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

publish-test: build
	twine check dist/*
	twine upload --repository testpypi dist/*

publish: build
	twine check dist/*
	twine upload dist/*

# Development workflow targets
check: lint typecheck test-fast
	@echo "All checks passed! ✅"

ci: lint typecheck test-all security
	@echo "CI pipeline complete! ✅"

pre-commit: format lint typecheck test-fast
	@echo "Pre-commit checks complete! ✅"

# Benchmarking and profiling
benchmark:
	pytest -v tests/test_performance.py --benchmark-only --benchmark-sort=mean

profile:
	pytest -v tests/test_performance.py --profile

# Dependency management
deps-update:
	pip install -U pip setuptools wheel
	pip install -U -e ".[dev,test,places]"

deps-freeze:
	pip freeze > requirements-dev.txt

# Database/cache cleanup for tests
test-clean:
	rm -rf .pytest_cache/
	rm -rf .coverage
	find . -name "*.pyc" -delete
	find . -type d -name __pycache__ -exec rm -rf {} +

# Quick development iteration
dev: clean install test-fast
	@echo "Development setup complete! ✅"

# Full validation (run before PR)
validate: format lint typecheck test-all security docs
	@echo "Full validation complete! Ready for PR ✅"