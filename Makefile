# Brownie Metadata Database Makefile

.PHONY: help install test test-integration migrate clean docker-up docker-down

# Default target
help:
	@echo "Available targets:"
	@echo "  install          Install dependencies"
	@echo "  test             Run all tests"
	@echo "  test-integration Run integration tests (API compatibility)"
	@echo "  migrate          Run database migrations"
	@echo "  clean            Clean up temporary files"
	@echo "  docker-up        Start services with Docker Compose"
	@echo "  docker-down      Stop services with Docker Compose"

# Install dependencies
install:
	pip install -e .

# Run all tests
test:
	pytest tests/ -v --cov=src --cov-report=html

# Run integration tests
test-integration:
	@echo "Running integration tests to check API compatibility..."
	pytest tests/test_integration.py -v

# Run migration tests
test-migration:
	@echo "Testing migration compatibility..."
	pytest tests/test_integration.py::TestMigrationCompatibility -v

# Run database migrations
migrate:
	python -m alembic upgrade head

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/

# Docker commands
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Development setup
setup: install migrate
	@echo "Development environment setup complete!"
	@echo "Run 'make test-integration' to check API compatibility"
