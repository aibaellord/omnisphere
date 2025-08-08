# 🌌 OMNISPHERE MAKEFILE 🌌
# Development and deployment commands

.PHONY: help setup clean install install-dev update-deps test lint format run docker-build docker-up docker-down

# Python and virtualenv settings
PYTHON := python3
VENV := venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python
PIP_COMPILE := $(VENV)/bin/pip-compile

# Docker settings
DOCKER_IMAGE := omnisphere
DOCKER_TAG := latest

help: ## Show this help message
	@echo "🌌 OmniSphere Development Commands"
	@echo "================================="
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

setup: ## Initial project setup
	@echo "🚀 Setting up OmniSphere development environment..."
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip pip-tools
	$(PIP) install -r requirements.txt
	@echo "✅ Setup complete! Run 'make run' to start the development server."

clean: ## Clean up build artifacts and cache files
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@echo "✅ Cleanup complete!"

install: ## Install production dependencies
	$(PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	$(PIP_COMPILE) requirements-dev.in
	$(PIP) install -r requirements-dev.txt

update-deps: ## Update and compile dependencies
	@echo "📦 Updating dependencies..."
	$(PIP_COMPILE) --upgrade requirements-core.in
	$(PIP_COMPILE) --upgrade requirements-dev.in
	$(PIP) install -r requirements.txt
	@echo "✅ Dependencies updated!"

test: ## Run tests
	@echo "🧪 Running tests..."
	$(PYTHON_VENV) -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint: ## Run linting tools
	@echo "🔍 Running linters..."
	$(PYTHON_VENV) -m flake8 src/ tests/
	$(PYTHON_VENV) -m mypy src/
	$(PYTHON_VENV) -m bandit -r src/

format: ## Format code with black and isort
	@echo "🎨 Formatting code..."
	$(PYTHON_VENV) -m black src/ tests/
	$(PYTHON_VENV) -m isort src/ tests/

format-check: ## Check if code is properly formatted
	$(PYTHON_VENV) -m black --check src/ tests/
	$(PYTHON_VENV) -m isort --check-only src/ tests/

run: ## Run the development server
	@echo "🚀 Starting OmniSphere development server..."
	$(PYTHON_VENV) -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

run-prod: ## Run production server
	@echo "🚀 Starting OmniSphere production server..."
	$(PYTHON_VENV) -m gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

docker-build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "✅ Docker image built: $(DOCKER_IMAGE):$(DOCKER_TAG)"

docker-build-dev: ## Build Docker image for development
	@echo "🐳 Building Docker development image..."
	docker build --target development -t $(DOCKER_IMAGE):dev .
	@echo "✅ Docker development image built: $(DOCKER_IMAGE):dev"

docker-up: ## Start all services with Docker Compose
	@echo "🐳 Starting Docker services..."
	docker-compose up -d
	@echo "✅ Services started! Check http://localhost:8000"

docker-down: ## Stop all services
	@echo "🛑 Stopping Docker services..."
	docker-compose down
	@echo "✅ Services stopped!"

docker-logs: ## Show logs from all services
	docker-compose logs -f

docker-shell: ## Open shell in the main container
	docker-compose exec omnisphere bash

migrate: ## Run database migrations
	@echo "📊 Running database migrations..."
	$(PYTHON_VENV) -c "from core.database import init_db; init_db()"
	@echo "✅ Migrations complete!"

seed: ## Seed database with sample data
	@echo "🌱 Seeding database..."
	$(PYTHON_VENV) -c "from scripts.seed_data import seed_all; seed_all()"
	@echo "✅ Database seeded!"

backup: ## Backup database
	@echo "💾 Creating database backup..."
	mkdir -p backups
	$(PYTHON_VENV) scripts/backup_db.py
	@echo "✅ Backup created!"

deploy-staging: ## Deploy to staging environment
	@echo "🚀 Deploying to staging..."
	# Add your staging deployment commands here
	@echo "✅ Deployed to staging!"

deploy-prod: ## Deploy to production environment
	@echo "🚀 Deploying to production..."
	# Add your production deployment commands here
	@echo "✅ Deployed to production!"

security-check: ## Run security checks
	@echo "🔒 Running security checks..."
	$(PYTHON_VENV) -m bandit -r src/
	$(PYTHON_VENV) -m safety check
	@echo "✅ Security check complete!"

docs: ## Generate documentation
	@echo "📖 Generating documentation..."
	$(PYTHON_VENV) -m mkdocs build
	@echo "✅ Documentation generated!"

docs-serve: ## Serve documentation locally
	@echo "📖 Serving documentation..."
	$(PYTHON_VENV) -m mkdocs serve

env-example: ## Copy .env.template to .env
	@if [ ! -f .env ]; then \
		cp .env.template .env; \
		echo "✅ Created .env file from template. Please edit it with your actual values."; \
	else \
		echo "⚠️  .env file already exists. Not overwriting."; \
	fi

status: ## Show project status
	@echo "🌌 OmniSphere Project Status"
	@echo "============================"
	@echo "Python version: $$($(PYTHON) --version)"
	@echo "Virtual env: $$(if [ -d $(VENV) ]; then echo '✅ Active'; else echo '❌ Not found'; fi)"
	@echo "Docker: $$(if command -v docker >/dev/null 2>&1; then echo '✅ Available'; else echo '❌ Not installed'; fi)"
	@echo "Git status: $$(git status --porcelain | wc -l | tr -d ' ') uncommitted changes"
	@echo "Environment file: $$(if [ -f .env ]; then echo '✅ Present'; else echo '⚠️  Missing (run make env-example)'; fi)"

init: setup env-example ## Complete initial project setup
	@echo "🎉 OmniSphere is ready for development!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Edit the .env file with your API keys"
	@echo "2. Run 'make run' to start the development server"
	@echo "3. Visit http://localhost:8000 to see your application"
