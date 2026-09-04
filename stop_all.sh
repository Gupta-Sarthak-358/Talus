#!/usr/bin/env bash
# TALUS stop helper (Linux/macOS/WSL)
if [ -f .backend.pid ]; then kill "$(cat .backend.pid)" 2>/dev/null || true; rm .backend.pid; fi
if [ -f .frontend.pid ]; then kill "$(cat .frontend.pid)" 2>/dev/null || true; rm .frontend.pid; fi
if command -v lsof >/dev/null 2>&1; then lsof -ti:8000 | xargs kill -9 2>/dev/null || true; lsof -ti:5173 | xargs kill -9 2>/dev/null || true; fi
if command -v fuser >/dev/null 2>&1; then fuser -k 8000/tcp 2>/dev/null || true; fuser -k 5173/tcp 2>/dev/null || true; fi
echo "stopped"
