.PHONY: up down restart build dev logs status seed clean help \
       logs-backend logs-frontend logs-db \
       seed-force shell-backend shell-db test migrate

# Detect container runtime: use podman if available, otherwise docker
CONTAINER_RUNTIME := $(shell command -v podman >/dev/null 2>&1 && echo podman || echo docker)
COMPOSE_CMD := $(if $(findstring podman,$(CONTAINER_RUNTIME)),podman compose,docker-compose)

help: ## Show available commands
	@echo ''
	@echo '  Ondo — Dataset Readiness Platform'
	@echo '  Container runtime: $(CONTAINER_RUNTIME)'
	@echo ''
	@echo '  Quick start:  make up'
	@echo '  Stop:         make down'
	@echo ''
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ''

# ── Lifecycle ──────────────────────────────────────────────────

up: ## Start the app (build images if needed)
	$(COMPOSE_CMD) up -d --build
	@echo ''
	@echo '  Starting Ondo...'
	@echo '  Frontend:  http://localhost:3000'
	@echo '  Backend:   http://localhost:8000'
	@echo '  API docs:  http://localhost:8000/docs'
	@echo ''
	@echo '  Migrations and demo data seed run automatically on startup.'
	@echo '  Run "make logs" to follow startup progress'

down: ## Stop the app
	$(COMPOSE_CMD) down

restart: ## Restart the app (rebuild images)
	$(COMPOSE_CMD) down
	$(COMPOSE_CMD) up -d --build
	@echo ''
	@echo '  Restarting Ondo...'
	@echo '  Run "make logs" to follow startup progress'

dev: ## Start in development mode (hot-reload, mounted volumes)
	$(COMPOSE_CMD) -f docker-compose.yml -f docker-compose.dev.yml up --build

build: ## Build all container images without starting
	$(COMPOSE_CMD) build

# ── Observe ────────────────────────────────────────────────────

status: ## Show running containers and health
	$(COMPOSE_CMD) ps

logs: ## Follow logs from all services
	$(COMPOSE_CMD) logs -f

logs-backend: ## Follow backend logs
	$(COMPOSE_CMD) logs -f backend

logs-frontend: ## Follow frontend logs
	$(COMPOSE_CMD) logs -f frontend

logs-db: ## Follow database logs
	$(COMPOSE_CMD) logs -f db

# ── Data ───────────────────────────────────────────────────────

seed: ## Re-run demo data seed manually (runs automatically on startup)
	@echo 'Seeding demo data...'
	$(COMPOSE_CMD) exec backend python scripts/seed_demo_data.py
	@echo 'Done! Visit http://localhost:3000'

seed-force: ## Clear all data and re-seed from scratch
	@echo 'Force re-seeding demo data...'
	$(COMPOSE_CMD) exec backend python scripts/seed_demo_data.py --force
	@echo 'Done! Visit http://localhost:3000'

migrate: ## Run database migrations
	$(COMPOSE_CMD) exec backend alembic upgrade head

# ── Debug ──────────────────────────────────────────────────────

shell-backend: ## Open a shell in the backend container
	$(COMPOSE_CMD) exec backend /bin/bash

shell-db: ## Open a PostgreSQL shell
	$(COMPOSE_CMD) exec db psql -U postgres -d ondo

test: ## Run backend tests
	$(COMPOSE_CMD) exec backend pytest tests/ -v

# ── Cleanup ────────────────────────────────────────────────────

clean: ## Stop the app and delete all data (volumes)
	$(COMPOSE_CMD) down -v
	@echo 'Containers stopped and volumes removed'
