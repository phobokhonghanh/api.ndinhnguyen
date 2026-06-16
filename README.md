# api.ndinhnguyen

> _Personal API for Nguyen Dinh Nguyen_

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=flat-square&logo=fastapi&logoColor=white) ![Cloudflare Workers](https://img.shields.io/badge/Cloudflare_Workers-Python-F38020?style=flat-square&logo=cloudflareworkers&logoColor=white) ![Cloudflare D1](https://img.shields.io/badge/Cloudflare_D1-SQLite-F38020?style=flat-square&logo=cloudflare&logoColor=white) ![Make](https://img.shields.io/badge/Make-Workflow-427819?style=flat-square&logo=gnu&logoColor=white)

---

## Routes

| Route                        | Type        | Description                                                                       |
| ---------------------------- | ----------- | --------------------------------------------------------------------------------- |
| `/health`                    | Public GET  | Health check endpoint returning API status metadata.                              |
| `/api/bookmarks`             | Auth GET    | Returns bookmarks, categories, category tree, selected category ids, and DB flag. |
| `/api/bookmarks`             | Auth POST   | Creates a bookmark.                                                               |
| `/api/bookmarks/{id}`        | Auth PUT    | Updates a bookmark.                                                               |
| `/api/bookmarks/{id}`        | Auth DELETE | Deletes a bookmark.                                                               |
| `/api/categories`            | Auth POST   | Creates a category.                                                               |
| `/api/categories/{id}`       | Auth PUT    | Updates a category.                                                               |
| `/api/categories/{id}`       | Auth DELETE | Deletes a category with business-rule checks.                                     |
| `/api/stats`                 | Public POST | Stores snapshot CSV markers and runtime JSONL uploads in R2.                     |

> All `/api/*` routes require `Authorization: Bearer <ADMIN_TOKEN>` except
> public `POST /api/stats`.

---

## Development

## Backend structure

The Worker is assembled in `src/main.py` and keeps `src/app.py` as a
compatibility import for existing runtime/tests. Feature code is organized by
boundary:

- `src/api/`: HTTP middleware and route adapters.
- `src/core/`: context, settings, and response helpers.
- `src/features/bookmarks/`: bookmark/category schemas, use cases, repository.
- `src/features/stats/`: stats command, service, validators, path builder, handlers.
- `src/infra/`: Cloudflare D1/R2 adapter helpers.

### Cài đặt python 3.12

```bash
# Option 1: Add deadsnakes PPA (Recommended)
sudo apt update
sudo apt install -y software-properties-common

sudo add-apt-repository ppa:deadsnakes/ppa -y
```
```bash
#Option 2: Add deadsnakes repository (manually)

#Add repository
echo "deb https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu jammy main" \
| sudo tee /etc/apt/sources.list.d/deadsnakes.list

#Import repository signing key
sudo apt-key adv \
  --keyserver keyserver.ubuntu.com \
  --recv-keys F23C5A6CF475977595C89F51BA6932366A755776
```

```bash
# Refresh package index
sudo apt update

# Install Python 3.12
sudo apt install -y python3.12 python3.12-venv python3.12-dev
Verify installation
python3.12 --version

Expected output:

Python 3.12.x
```

### Run project local

```bash
python3.12 -m venv .venv
. .venv/bin/activate
make install
cp .dev.vars.example .dev.vars
make db-migrate-local
pip install uv
make run
```

`POST /api/stats` uses the `STATS_BUCKET` R2 binding and these path templates:

```bash
STATS_SNAPSHOT_PATH_TEMPLATE=lakehouse-raw/{product}/snapshot/loaddate={yyyymmdd}/{machine_id}.csv
STATS_RUNTIME_PATH_TEMPLATE=lakehouse-raw/{product}/runtime/loaddate={yyyymmdd}/{machine_id}_{batch_id}.jsonl
```

Run tests with:

```bash
make test
```

`make run` uses `pywrangler dev`, which is the recommended local runner for
Cloudflare Python Workers with FastAPI packages.

---

## Deployment

Set the production secret:

```bash
make secret-put-admin-token
```

Update `ALLOWED_ORIGINS` and the D1 `database_id` in `wrangler.jsonc`, then run:

```bash
make db-migrate-remote
make deploy
```

> Frontend integration uses `https://ndinhnguyen.pages.dev` and local
> development uses `http://localhost:3000` via `ALLOWED_ORIGINS`.
