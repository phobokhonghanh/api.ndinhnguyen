# Simple Skill API

FastAPI backend deployed as a Cloudflare Python Worker. It owns the bookmark
API, the D1 binding, migrations, CORS policy, and the `ADMIN_TOKEN` secret.

## Setup

```bash
npm install
uv sync
cp .dev.vars.example .dev.vars
npm run db:migrate:local
npm run dev
```

Set the production secret and allowed Pages origin before deployment:

```bash
npx wrangler secret put ADMIN_TOKEN
```

Update `ALLOWED_ORIGINS` and the D1 `database_id` in `wrangler.jsonc`, then:

```bash
npm run db:migrate:remote
npm run deploy
```

Run unit tests with `uv run pytest`.
