#!/usr/bin/env bash
# TALUS — One-command launcher (Linux/macOS/WSL/Git Bash)
# SIH26001 @ 68c0c28 — Gangtok pilot S1-S4 89/78/66/52, 16/17 REAL/PROXY, 1528×22 training RF 0.921 XGB 0.9256
# Usage:  ./start_all.sh            # validators + backend :8000 + frontend :5173
#         ./start_all.sh --build    # + vite build check
#         ./start_all.sh --no-frontend  # backend only
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PY_MNEMO="$HOME/Desktop/mnemo/.venv/Scripts/python.exe"
PY_FALLBACK="python3"
if [ -f "$ROOT/../mnemo/.venv/Scripts/python.exe" ]; then PY_MNEMO="$ROOT/../mnemo/.venv/Scripts/python.exe"; fi
if [ -f "C:/Users/satvi/Desktop/mnemo/.venv/Scripts/python.exe" ]; then PY_MNEMO="C:/Users/satvi/Desktop/mnemo/.venv/Scripts/python.exe"; fi
# auto-detect
if command -v python >/dev/null 2>&1; then PY="$PY_MNEMO"; else PY="$PY_FALLBACK"; fi
if [ ! -f "$PY" ]; then PY="python3"; fi
if [ ! -f "$PY" ] && command -v python >/dev/null 2>&1; then PY="python"; fi

echo "=== TALUS one-command launcher ==="
echo "Root: $ROOT"

# 0) validators (must stay green)
echo "[0/3] validators..."
if command -v "$PY" >/dev/null 2>&1; then
  "$PY" scripts/check_scaffold.py || { echo "check_scaffold FAILED"; exit 1; }
  "$PY" scripts/validate_ngen_sample.py || { echo "validate_ngen FAILED"; exit 1; }
else
  python scripts/check_scaffold.py
  python scripts/validate_ngen_sample.py
fi

# 1) backend :8000
echo "[1/3] backend FastAPI :8000 ..."
if [ -f "$PY_MNEMO" ]; then PY="$PY_MNEMO"; fi
# kill old :8000 if any (best effort)
if command -v lsof >/dev/null 2>&1; then lsof -ti:8000 | xargs kill -9 2>/dev/null || true; fi
if command -v fuser >/dev/null 2>&1; then fuser -k 8000/tcp 2>/dev/null || true; fi

# start backend in background
(
  cd "$ROOT/backend"
  nohup "$PY" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$ROOT/backend.log" 2>&1 &
  echo $! > "$ROOT/.backend.pid"
)
echo "  backend pid $(cat "$ROOT/.backend.pid") → $ROOT/backend.log"

# wait for /api/zones
ok=0
for i in $(seq 1 30); do
  sleep 1
  if curl -sf http://127.0.0.1:8000/api/zones >/dev/null 2>&1; then
    ok=1; break
  fi
done
if [ "$ok" -eq 1 ]; then
  echo "  backend UP — live predictions:"
  curl -s http://127.0.0.1:8000/api/zones | python3 -c "import sys,json; d=json.load(sys.stdin); [print(f\"    Zone {z['zone_id']}: {z['risk_score']} {z['risk_band']} (confidence {z['confidence']})\") for z in d['zones']]" 2>/dev/null || curl -s http://127.0.0.1:8000/api/zones
else
  echo "  WARNING: backend not up in 30s — see $ROOT/backend.log"
fi

# 2) frontend handling
if [ "${1:-}" = "--no-frontend" ]; then
  echo "[2/3] frontend skipped (--no-frontend)"
else
  echo "[2/3] frontend Vite :5173 ..."
  if [ ! -d "$ROOT/frontend/node_modules" ]; then
    echo "  installing frontend deps (first run)..."
    (cd "$ROOT/frontend" && npm install --silent)
  fi
  if [ "${1:-}" = "--build" ]; then
    echo "  vite build check..."
    (cd "$ROOT/frontend" && npm run build --silent)
  fi
  if command -v lsof >/dev/null 2>&1; then lsof -ti:5173 | xargs kill -9 2>/dev/null || true; fi
  (
    cd "$ROOT/frontend"
    nohup npm run dev > "$ROOT/frontend.log" 2>&1 &
    echo $! > "$ROOT/.frontend.pid"
  )
  echo "  frontend pid $(cat "$ROOT/.frontend.pid") → $ROOT/frontend.log"
  sleep 3
fi

echo ""
echo "=== TALUS is running ==="
echo "  Dashboard : http://localhost:5173  (VITE_USE_LIVE_API=true → :8000)"
echo "  API docs  : http://localhost:8000/docs"
echo "  API zones : http://127.0.0.1:8000/api/zones"
echo ""
echo "Demo flow: map → click S1 (89 Critical) → SHAP → What-If S3 66→74 → Causal monga-mdl S3→High → Roads R2 avoided → Report S2 crack → queue → verify"
echo ""
echo "Logs: tail -f backend.log frontend.log"
echo "Stop: kill \$(cat .backend.pid .frontend.pid)  or  ./stop_all.sh"
