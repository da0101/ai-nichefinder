DOCKER_COMPOSE := docker compose -f infra/docker-compose.yml

.PHONY: up down status db-init lint

up:
	$(DOCKER_COMPOSE) up -d

down:
	$(DOCKER_COMPOSE) down

status:
	uv run --package nichefinder-cli nichefinder status

db-init:
	uv run --package nichefinder-cli nichefinder db init

lint:
	uv run ruff check .

