UNAME := $(shell uname)
PROJECT_NAME=poker-bot

DOCKER_COMPOSE=docker compose -p $(PROJECT_NAME) -f docker-compose.yaml

all: help
up: ## Up project
	@echo "Up poker bot..."
	$(DOCKER_COMPOSE) up -d
cs-fix:
	@echo "Code style formatter..."
	$(DOCKER_COMPOSE) run python_bot_poker black ./
linter:
	@echo "Running pyright..."
	$(DOCKER_COMPOSE) run python_bot_poker pyright
