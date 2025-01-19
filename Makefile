UNAME := $(shell uname)
PROJECT_NAME=poker-bot
PHP_FPM=$(DOCKER_COMPOSE) exec python_bot_poker

DOCKER_COMPOSE=docker-compose -p $(PROJECT_NAME) -f docker-compose.yaml

all: help
up: ## Up project
	@echo "Up poker bot..."
	$(DOCKER_COMPOSE) up -d
cs-fix:
	@echo "Code style formatter..."
	$(DOCKER_COMPOSE) exec python_bot_poker black ./
