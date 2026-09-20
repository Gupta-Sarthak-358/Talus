# TALUS SIH26001 — single-image deploy (backend + built frontend via FastAPI static)
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# Memory contract (Render free = 512MB): single worker, single-threaded numerics.
# Measured: ~200MB boot, ~450MB after first TreeSHAP build. Keep margin, not speed.
ENV OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
WORKDIR /app

# System deps for geospatial + ssl
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    libgdal-dev libgeos-dev proj-bin \
  && rm -rf /var/lib/apt/lists/*

# Python deps — layer-cached before code copy
COPY backend/requirements.txt ./backend/requirements.txt
COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip \
 && pip install -r backend/requirements.txt \
 && pip install -r requirements.txt || true

# Frontend build (needs node)
FROM node:20-slim AS fe
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install
COPY frontend/ ./
RUN npm run build

# Final image
FROM base AS final
COPY --from=fe /fe/dist ./frontend/dist
COPY . .
# Mount-safe runs dir for live-feed simulator + dispatch log
RUN mkdir -p runs data/sih26001/evidence
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
