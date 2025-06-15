# Intelligent File Organizer - Makefile

.PHONY: help install run test clean dev-install lint format

# Default target
help:
	@echo "🗂️  Intelligent File Organizer"
	@echo ""
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  run         - Run the application"
	@echo "  test        - Run tests"
	@echo "  test-unit   - Run unit tests only"
	@echo "  test-int    - Run integration tests only"
	@echo "  clean       - Clean up generated files"
	@echo "  dev-install - Install development dependencies"
	@echo "  lint        - Run code linting"
	@echo "  format      - Format code"
	@echo "  setup       - Full setup (install + config)"

# Installation
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt

dev-install: install
	@echo "🔧 Installing development dependencies..."
	pip install -r requirements-dev.txt || echo "⚠️  requirements-dev.txt not found"

# Setup
setup: install
	@echo "⚙️  Setting up configuration..."
	@if [ ! -f config/config.json ]; then \
		echo "📋 Creating default config..."; \
		cp config/defaults/config.json config/config.json || echo "⚠️  Default config not found"; \
	fi
	@echo "✅ Setup complete!"

# Running
run:
	@echo "🚀 Starting Intelligent File Organizer..."
	python main.py

# Testing
test:
	@echo "🧪 Running all tests..."
	python run_tests.py

test-unit:
	@echo "🧪 Running unit tests..."
	python run_tests.py --type unit

test-int:
	@echo "🧪 Running integration tests..."
	python run_tests.py --type integration

test-fast:
	@echo "⚡ Running fast tests..."
	python run_tests.py --fast

# Code quality
lint:
	@echo "🔍 Running linting..."
	python -m flake8 src/ || echo "⚠️  flake8 not installed"
	python -m mypy src/ || echo "⚠️  mypy not installed"

format:
	@echo "✨ Formatting code..."
	python -m black src/ || echo "⚠️  black not installed"
	python -m isort src/ || echo "⚠️  isort not installed"

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage .pytest_cache/ || true
	@echo "✅ Cleanup complete!"

# Quick start
quick: clean install run