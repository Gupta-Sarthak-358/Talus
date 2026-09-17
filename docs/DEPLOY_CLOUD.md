# Cloud deploy — Postgres/PostGIS + hosted URL (audit gap f)

**Local**: `docker-compose up` (api on 8000) or `docker-compose -f docker-compose.prod.yml up` (api+postgis).
**Evidence** stays file-backed when `DATABASE_URL` absent — `ZoneStore` falls back to `slopes.json` + `feature_matrix.sample.csv` (honest, no fake DB).

### Live host options (any one)
- **Render**: `render.yaml` build `docker` + `healthCheckPath: /health`, env `DATABASE_URL` from Render Postgres (PostGIS extension `CREATE EXTENSION postgis`).
- **Fly.io**: `fly.toml` `app = talus-sih26001`, `[[services]] internal_port 8000`, `auto_stop_machines`.
- **AWS**: ECS Fargate + RDS PostGIS + EFS for `runs/` (dispatch log).

### Env (`.env` never committed)
```
CORS_ORIGINS=*
DATABASE_URL=postgres://talus:***@db:5432/talus   # when absent → fixture mode per docs/sih26001/02_ARCHITECTURE_SIH26001.md
AUTO_ALERT_ENABLED=true
AUTO_ALERT_SMS=false            # true only when SMS_PROVIDER+SMS_API_KEY set
SMS_PROVIDER=textbelt|msg91|twilio|fast2sms
SMS_API_KEY=***
SMS_TO=+91...
IMD_API_KEY=***                  # data.gov.in rainfall district live (fallback Open-Meteo)
```

### Health
`GET /health` returns `status ok + checks store:gangtok live_scores + fixture:slopes.json + fixture:roads.json`.
`GET /api/isolation` and `GET /api/alerts/auto/status` are the watcher liveness probes.

### Migration path (when DB provisioned)
1. `alembic upgrade head` (creates `zones`, `reports`, `dispatch_log` with PostGIS `geometry`).
2. `python scripts/seed_postgis.py` loads `slopes.json` + `feature_matrix.training.sample.csv` into DB.
3. Set `DATABASE_URL` → `ZoneStore` will prefer DB (code path in `backend/app/data.py` checks `DATABASE_URL` then falls back).

**Current live URL placeholder** (set after first deploy): `https://talus-sih26001.onrender.com/health` — update `README.md` + `frontend/.env` `VITE_API_URL` when live.
