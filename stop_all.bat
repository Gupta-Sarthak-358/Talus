@echo off
REM TALUS stop helper (Windows) — kills :8000 and :5173
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /PID %%a /F 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do taskkill /PID %%a /F 2>nul
if exist .backend.pid del .backend.pid
if exist .frontend.pid del .frontend.pid
echo stopped
