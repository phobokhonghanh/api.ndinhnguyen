.PHONY: help install run dev deploy test db-schema-local db-schema-remote secret-put-admin-token logs-tail logs-stop


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
		"make deploy             (Prod) Deploy the Python Worker" \
		"make db-schema-remote   (Prod) Initialize D1 schema on remote DB" \
		"make secret-put-admin-token  (Prod) Set ADMIN_TOKEN" \
		"make logs-tail          (Logs) Start background wrangler logs tailing to logs/ folder" \
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

# For Deploy Cloudflare Worker
deploy:
	$(PYWRANGLER) deploy

## Initialize D1 schema prod
db-schema-remote:
	$(WRANGLER) d1 execute $(DB_NAME) --remote --file=schema.sql

## Put ADMIN_TOKEN prod
secret-put-admin-token:
	$(WRANGLER) secret put ADMIN_TOKEN

## Get log prod
logs-tail:
	chmod +x scripts/get_logs.sh
	nohup ./scripts/get_logs.sh > /dev/null 2>&1 &

logs-stop:
	pkill -f get_logs.sh || true