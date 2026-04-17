COMPOSE := docker compose
DEV := $(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml

.PHONY: help up down restart logs build migrate revision test smoke dev dev-down shell psql redis-cli fmt lint

help:
	@echo "Market Insights — make targets"
	@echo "  up          Start prod stack (detached)"
	@echo "  down        Stop & remove containers (volumes kept)"
	@echo "  restart     Restart api container"
	@echo "  logs        Tail api logs"
	@echo "  build       Rebuild api image"
	@echo "  migrate     Run Alembic upgrade head"
	@echo "  revision m=\"msg\"  Autogenerate a new migration"
	@echo "  test        Run pytest inside api container"
	@echo "  smoke       Run end-to-end smoke script"
	@echo "  dev         Start stack with dev overrides (reload, DB ports exposed)"
	@echo "  shell       Open a shell in the api container"
	@echo "  psql        Open psql in the postgres container"

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart api

logs:
	$(COMPOSE) logs -f api

build:
	$(COMPOSE) build api

migrate:
	$(COMPOSE) exec api alembic upgrade head

revision:
	$(COMPOSE) exec api alembic revision --autogenerate -m "$(m)"

test:
	$(COMPOSE) exec api pytest -q

smoke:
	$(COMPOSE) exec api python -m app.cli smoke

dev:
	$(DEV) up -d

dev-down:
	$(DEV) down

shell:
	$(COMPOSE) exec api /bin/sh

psql:
	$(COMPOSE) exec postgres psql -U mi -d market_insights

redis-cli:
	$(COMPOSE) exec redis redis-cli
