# Variables
DOCKER_COMPOSE = docker compose
APP_CONTAINER = app
PYTHON = $(DOCKER_COMPOSE) exec $(APP_CONTAINER) /usr/src/app/venv/bin/python
MANAGE_PY = $(PYTHON) /usr/src/app/lidar_service/manage.py

# Help
.PHONY: help
help:
	@echo "Makefile for Django project"
	@echo
	@echo "Available commands:"
	@echo "  make build           Build the Docker containers"
	@echo "  make up              Start the Docker containers"
	@echo "  make down            Stop the Docker containers"
	@echo "  make shell           Open a shell inside the app container"
	@echo "  make migrate         Apply migrations"
	@echo "  make createsuperuser Create a Django superuser"
	@echo "  make run             Run the Django development server"
	@echo "  make collectstatic   Collect static files"
	@echo "  make test            Run Django tests"
	@echo "  make makemigrations  Create new migrations"
	@echo "  make clean           Remove Docker containers, volumes, and Django's pyc files"

# Build and Run
build:
	$(DOCKER_COMPOSE) build

up:
	$(DOCKER_COMPOSE) up -d --build

down:
	$(DOCKER_COMPOSE) down

shell:
	$(DOCKER_COMPOSE) exec $(APP_CONTAINER) /bin/bash

# Django Tasks
migrate:
	$(MANAGE_PY) migrate

createsuperuser:
	$(MANAGE_PY) createsuperuser

run:
	$(MANAGE_PY) runserver 0.0.0.0:8000

collectstatic:
	$(MANAGE_PY) collectstatic --noinput

test:
	$(MANAGE_PY) test

makemigrations:
	$(MANAGE_PY) makemigrations

# Clean Up
.PHONY: clean
clean:
	$(DOCKER_COMPOSE) down --volumes --remove-orphans
	find . -name "*.pyc" -exec rm -f {} \;
	find . -name "__pycache__" -exec rm -rf {} \;

