# api.ndinhnguyen

> _Bookmark API for Nguyen Dinh Nguyen_

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

> All `/api/*` routes require `Authorization: Bearer <ADMIN_TOKEN>`.

---

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
make install
cp .dev.vars.example .dev.vars
make db-migrate-local
make run
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
