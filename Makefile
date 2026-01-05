.PHONY: build start full stop clean restart logs seed help

# Detect container runtime: use podman if available, otherwise docker
CONTAINER_RUNTIME := $(shell command -v podman >/dev/null 2>&1 && echo podman || echo docker)
# Podman uses 'podman compose' (space), Docker uses 'docker-compose' (hyphen)
COMPOSE_CMD := $(if $(findstring podman,$(CONTAINER_RUNTIME)),podman compose,docker-compose)

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo 'Container runtime: $(CONTAINER_RUNTIME)'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all container images
	$(COMPOSE_CMD) build

start: ## Start containers using latest images
	$(COMPOSE_CMD) up -d
	@echo "Services starting... Wait ~30 seconds for startup"
	@echo "Demo data will be seeded automatically if database is empty"
	@echo "Using container runtime: $(CONTAINER_RUNTIME)"

full: ## Build images and start containers
	$(COMPOSE_CMD) up -d --build
	@echo "Services starting... Wait ~30 seconds for startup"
	@echo "Demo data will be seeded automatically if database is empty"
	@echo "Using container runtime: $(CONTAINER_RUNTIME)"

stop: ## Stop containers
	$(COMPOSE_CMD) down

clean: ## Clean containers and images
	$(COMPOSE_CMD) down -v
	$(COMPOSE_CMD) rm -f

restart: ## Stop containers, build images, and start with new images
	$(COMPOSE_CMD) down
	$(COMPOSE_CMD) build
	$(COMPOSE_CMD) up -d
	@echo "Services restarted with new images... Wait ~30 seconds for startup"
	@echo "Using container runtime: $(CONTAINER_RUNTIME)"

logs: ## View logs from all services
	$(COMPOSE_CMD) logs -f

logs-backend: ## View backend logs
	$(COMPOSE_CMD) logs -f backend

logs-frontend: ## View frontend logs
	$(COMPOSE_CMD) logs -f frontend

logs-db: ## View database logs
	$(COMPOSE_CMD) logs -f db

seed: ## Seed demo data (run after 'make start', or use 'make seed-force' to re-seed)
	@echo "Seeding demo data..."
	$(COMPOSE_CMD) exec backend python scripts/seed_demo_data.py
	@echo "Demo data seeded! Visit http://localhost:3000/datasets"

seed-force: ## Force re-seed demo data (clears existing data)
	@echo "Force seeding demo data (clearing existing data)..."
	$(COMPOSE_CMD) exec backend python scripts/seed_demo_data.py --force
	@echo "Demo data re-seeded! Visit http://localhost:3000/datasets"

dev: ## Start in development mode with hot-reload
	$(COMPOSE_CMD) -f docker-compose.yml -f docker-compose.dev.yml up

ps: ## Show running containers
	$(COMPOSE_CMD) ps

shell-backend: ## Open shell in backend container
	$(COMPOSE_CMD) exec backend /bin/bash

shell-db: ## Open PostgreSQL shell
	$(COMPOSE_CMD) exec db psql -U postgres -d ondo

test: ## Run backend tests
	$(COMPOSE_CMD) exec backend pytest tests/ -v

migrate: ## Run database migrations
	$(COMPOSE_CMD) exec backend alembic upgrade head

