.PHONY: help install run dev deploy test db-schema-local db-migrate-local db-migrate-remote db-schema-remote db-pull secret-put-admin-token logs logs-stop


WRANGLER ?= $(shell if command -v wrangler >/dev/null 2>&1; then echo wrangler; elif command -v npx >/dev/null 2>&1; then echo "npx wrangler"; else echo wrangler; fi)
PYWRANGLER ?= $(shell if [ -x ./.venv/bin/pywrangler ]; then echo ./.venv/bin/pywrangler; elif command -v pywrangler >/dev/null 2>&1; then echo pywrangler; else echo pywrangler; fi)
DB_NAME ?= ndinhnguyen
PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

help:
	@printf "%s\n" \
		"make install            (Dev) Install the project and dev dependencies" \
		"make dev                (Dev) Start local Python Worker preview" \
		"make test               (Dev) Run pytest" \
		"make db-schema-local    (Dev) Initialize D1 schema on local DB" \
		"make db-migrate-local   (Dev) Apply D1 migrations on local DB" \
		"make db-pull            (Dev) Export prod D1 data & import to local D1" \
		"make deploy             (Prod) Deploy the Python Worker" \
		"make db-migrate-remote  (Prod) Apply D1 migrations on remote DB" \
		"make db-schema-remote   (Prod) Initialize D1 schema on remote DB (alias for migrate)" \
		"make secret-put-admin-token  (Prod) Set ADMIN_TOKEN" \
		"make logs               (Logs) Start background wrangler logs tailing to logs/ folder" \
		"make logs-stop          (Logs) Stop background wrangler logs tailing"

# For Developer
install:
	$(PIP) install -e ".[dev]"

dev:
	$(PYWRANGLER) dev

test:
	$(PYTHON) -m pytest

db-schema-local:
	$(WRANGLER) d1 execute $(DB_NAME) --local --file=schema.sql

db-migrate-local:
	$(WRANGLER) d1 migrations apply $(DB_NAME) --local

## Sync D1 database from production (remote) to local development
db-pull:
	@echo "Exporting production D1 database ($(DB_NAME))..."
	$(WRANGLER) d1 export $(DB_NAME) --remote --output=./prod_dump.sql
	@echo "Resetting local D1 database tables..."
	$(WRANGLER) d1 execute $(DB_NAME) --local --command="PRAGMA foreign_keys = OFF; DROP TABLE IF EXISTS payments; DROP TABLE IF EXISTS cashbacks; DROP TABLE IF EXISTS bookmarks; DROP TABLE IF EXISTS categories; DROP TABLE IF EXISTS users; DROP TABLE IF EXISTS d1_migrations;"
	@echo "Importing production data into local D1 database..."
	$(WRANGLER) d1 execute $(DB_NAME) --local --file=./prod_dump.sql
	@rm -f ./prod_dump.sql
	@echo "Local D1 database successfully synced with production!"


# For Deploy Cloudflare Worker
deploy:
	$(PYWRANGLER) deploy

## Apply D1 migrations on remote DB
db-migrate-remote:
	$(WRANGLER) d1 migrations apply $(DB_NAME) --remote

db-schema-remote: db-migrate-remote

## Put ADMIN_TOKEN prod
secret-put-admin-token:
	$(WRANGLER) secret put ADMIN_TOKEN

## Get log prod
logs:
	chmod +x scripts/get_logs.sh
	nohup ./scripts/get_logs.sh > /dev/null 2>&1 &

logs-stop:
	@if [ -f logs/tail.pid ]; then \
		pid=$$(cat logs/tail.pid); \
		echo "Stopping logs tail process with PID $$pid..."; \
		kill -15 $$pid 2>/dev/null || true; \
		rm -f logs/tail.pid; \
	else \
		echo "No running logs tail process found."; \
	fi