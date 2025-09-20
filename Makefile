.PHONY: help install dev-install run fmt lint test migrate upgrade downgrade docker-build docker-up docker-down clean

help:
	@echo "Available commands:"
	@echo "  install           - Install production dependencies"
	@echo "  dev-install       - Install development dependencies"
	@echo "  run               - Run the application with uvicorn"
	@echo "  fmt               - Format code with black and ruff"
	@echo "  lint              - Lint code with ruff and mypy"
	@echo "  test              - Run tests with pytest"
	@echo ""
	@echo "Database migrations:"
	@echo "  migrate msg='...'  - Create new migration with message"
	@echo "  upgrade           - Apply database migrations"
	@echo "  downgrade         - Rollback one migration"
	@echo "  migration-history - Show migration history"
	@echo "  migration-current - Show current migration"
	@echo "  migration-show rev='...' - Show specific migration"
	@echo ""
	@echo "Docker commands:"
	@echo "  docker-build      - Build docker image"
	@echo "  docker-up         - Start all services"
	@echo "  docker-up-dev     - Start only database services"
	@echo "  docker-down       - Stop all services"
	@echo "  docker-down-dev   - Stop database services"
	@echo "  docker-logs       - View logs (all services)"
	@echo "  docker-logs-dev   - View logs (database services)"
	@echo ""
	@echo "  clean             - Clean cache and temporary files"

install:
	poetry install --only=main

dev-install:
	poetry install
	poetry run pre-commit install

run:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

fmt:
	poetry run black .
	poetry run ruff check --fix .

lint:
	poetry run ruff check .
	poetry run mypy .

test:
	poetry run pytest -v --cov=app --cov-report=term-missing

migrate:
	@if [ -z "$(msg)" ]; then echo "Usage: make migrate msg='Your migration message'"; exit 1; fi
	poetry run alembic revision --autogenerate -m "$(msg)"

upgrade:
	poetry run alembic upgrade head

downgrade:
	poetry run alembic downgrade -1

migration-history:
	poetry run alembic history

migration-current:
	poetry run alembic current

migration-show:
	@if [ -z "$(rev)" ]; then echo "Usage: make migration-show rev=revision_id"; exit 1; fi
	poetry run alembic show $(rev)

docker-build:
	docker build -t document-chat-assistant .

docker-up:
	docker-compose up -d

docker-up-dev:
	docker-compose -f docker-compose.dev.yml up -d

docker-down:
	docker-compose down

docker-down-dev:
	docker-compose -f docker-compose.dev.yml down

docker-logs:
	docker-compose logs -f

docker-logs-dev:
	docker-compose -f docker-compose.dev.yml logs -f

# Full stack (with app container)
docker-full:
	docker-compose up --build

docker-full-down:
	docker-compose down -v

# Test with Docker
docker-test:
	docker-compose exec app poetry run pytest

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
