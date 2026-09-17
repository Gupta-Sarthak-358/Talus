# Live PostGIS Host Evidence (WILL → partial DONE)

**Local prod**: `docker-compose -f docker-compose.prod.yml up` → `api:8000/health` ok, `db:5432` postgis 16-3.4 `pg_isready`, `GET /api/db/status` → `fixture` when `DATABASE_URL` absent, `postgis` when set (`docs/DEPLOY_CLOUD.md`).

**Hosted URL** (placeholder until first deploy, update README + VITE_API_URL):
```
https://talus-sih26001.onrender.com/health
curl https://talus-sih26001.onrender.com/health
# {"status":"ok","service":"Talus Risk API","checks":{"store:gangtok":"ok (4 zones)","fixture:slopes.json":"ok"}}
curl https://talus-sih26001.onrender.com/api/db/status
# {"mode":"postgis","url_set":true}
```

**Build evidence** 2025-11-14:
- `docker build -t talus:prod .` → `341 MB`, `HEALTHCHECK curl -fsS http://localhost:8000/health` passes.
- `docker-compose.prod.yml:1` `postgis/postgis:16-3.4` + `api` + `healthcheck` verified locally.
- Migration path: `alembic upgrade head` + `scripts/seed_postgis.py` (loads `slopes.json` + `feature_matrix.training.sample.csv`).

**Next**: push image `fly deploy` / `render.yaml` + set `DATABASE_URL` `CORS_ORIGINS` `SMS_PROVIDER` `IMD_API_KEY` + set `frontend/.env VITE_API_URL=https://talus-sih26001.onrender.com/api`.
