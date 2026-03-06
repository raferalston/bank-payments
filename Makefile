.PHONY: help install up down restart logs app bank db migrate lint format test pre-commit clean

help: ## Показать список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Зависимости ---

install: ## Установить зависимости через uv
	uv sync --all-groups

pre-commit: ## Установить pre-commit хуки
	uv run pre-commit install

# --- Docker ---

up: ## Запустить все сервисы (docker compose)
	docker compose up -d

down: ## Остановить все сервисы
	docker compose down

restart: ## Перезапустить все сервисы
	docker compose restart

logs: ## Показать логи всех сервисов
	docker compose logs -f

# --- Локальный запуск ---

app: ## Запустить основное приложение локально
	uv run uvicorn src.main:app --reload --port 8000

bank: ## Запустить bank mock локально
	uv run uvicorn bank_mock.main:app --reload --port 8001

db: ## Запустить БД, Redis и создать тестовую БД
	docker compose up -d db redis
	@echo "Waiting for PostgreSQL to be ready..."
	@until docker exec it-guru_postgres pg_isready -U it-guru -d it-guru > /dev/null 2>&1; do sleep 1; done
	@docker exec it-guru_postgres psql -U it-guru -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'it-guru_test'" | grep -q 1 \
		|| docker exec it-guru_postgres psql -U it-guru -d postgres -c "CREATE DATABASE \"it-guru_test\";"

celery: ## Запустить Celery worker
	uv run celery -A src.celery_app worker --loglevel=info

flower: ## Запустить Flower (мониторинг Celery)
	uv run celery -A src.celery_app flower --port=5555

# --- Миграции ---

migrate-init: ## Инициализировать aerich
	uv run aerich init-db

migrate: ## Применить миграции (aerich)
	uv run aerich upgrade

migrate-new: ## Создать новую миграцию (usage: make migrate-new name="add_field")
	uv run aerich migrate --name $(name)

# --- Качество кода ---

lint: ## Запустить линтер (ruff check)
	uv run ruff check src/ bank_mock/

lint-fix: ## Запустить линтер с автоисправлением (импорты I001 и др.)
	uv run ruff check --fix src/ bank_mock/

format: ## Отформатировать код (ruff format)
	uv run ruff format src/ bank_mock/

# --- Тесты ---

test: ## Запустить тесты
	uv run pytest

test-v: ## Запустить тесты с подробным выводом
	uv run pytest -v
