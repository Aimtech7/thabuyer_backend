.PHONY: help install migrate run test lint clean docker-up docker-down seed

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install --upgrade pip
	pip install -r requirements.txt

migrate: ## Run database migrations
	python manage.py makemigrations
	python manage.py migrate

run: ## Start Django dev server
	python manage.py runserver

test: ## Run test suite with coverage
	pytest --cov=. --cov-report=term-missing --cov-report=html -v

lint: ## Run linting checks
	flake8 .
	python manage.py check --deploy

seed: ## Create demo data
	python manage.py seed_demo_data

superuser: ## Create superuser
	python manage.py createsuperuser

collectstatic: ## Collect static files
	python manage.py collectstatic --noinput

celery-worker: ## Start Celery worker
	celery -A core worker --loglevel=info --concurrency=4

celery-beat: ## Start Celery beat scheduler
	celery -A core beat --loglevel=info

docker-up: ## Build and start Docker containers
	docker compose up -d --build

docker-down: ## Stop Docker containers
	docker compose down

docker-logs: ## Tail Docker logs
	docker compose logs -f api celery_worker

clean: ## Remove compiled Python files and cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage
