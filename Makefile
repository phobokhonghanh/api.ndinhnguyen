.PHONY: help install run dev deploy test db-migrate-local db-migrate-remote secret-put-admin-token

WRANGLER ?= $(shell if command -v wrangler >/dev/null 2>&1; then echo wrangler; elif command -v npx >/dev/null 2>&1; then echo "npx wrangler"; else echo wrangler; fi)
PYWRANGLER ?= $(shell if [ -x ./.venv/bin/pywrangler ]; then echo ./.venv/bin/pywrangler; elif command -v pywrangler >/dev/null 2>&1; then echo pywrangler; else echo pywrangler; fi)
DB_NAME ?= ndinhnguyen
PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

help:
	@printf "%s\n" \
		"make install            Install the project and dev dependencies" \
		"make run                Start local Python Worker preview" \
		"make dev                Start local Python Worker preview" \
		"make deploy             Deploy the Python Worker" \
		"make test               Run pytest" \
		"make db-migrate-local   Apply D1 migrations to local DB" \
		"make db-migrate-remote  Apply D1 migrations to remote DB" \
		"make secret-put-admin-token  Set ADMIN_TOKEN in Cloudflare"

install:
	$(PIP) install -e ".[dev]"

run: dev

dev:
	$(PYWRANGLER) dev

deploy:
	$(PYWRANGLER) deploy

test:
	$(PYTHON) -m pytest

db-migrate-local:
	$(WRANGLER) d1 migrations apply $(DB_NAME) --local

db-migrate-remote:
	$(WRANGLER) d1 migrations apply $(DB_NAME) --remote

secret-put-admin-token:
	$(WRANGLER) secret put ADMIN_TOKEN
