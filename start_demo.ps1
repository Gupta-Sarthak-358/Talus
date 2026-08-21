# TALUS demo launcher -- starts backend (FastAPI, frozen Model v1) and
# frontend (Vite) together. Deterministic; no network required.

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$venvPython = "C:\Users\satvi\Desktop\mnemo\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) { $venvPython = "python" }

Write-Host "=== TALUS demo launcher ===" -ForegroundColor Cyan

# 1) Backend: FastAPI on :8000 (frozen RF + calibration + Scenario Engine)
Write-Host "[1/2] starting backend on http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process -FilePath "powershell.exe" -WorkingDirectory "$root\backend" -ArgumentList @(
    "-NoExit", "-Command",
    "& '$venvPython' -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
)

# wait for the API to come up
$ok = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-RestMethod "http://127.0.0.1:8000/api/zones" -TimeoutSec 2
        if ($r.zones.Count -ge 4) { $ok = $true; break }
    } catch { }
}
if ($ok) {
    Write-Host "      backend UP -- live predictions:" -ForegroundColor Green
    foreach ($z in $r.zones) {
        Write-Host ("      Zone {0}: {1} {2} (confidence {3})" -f $z.zone_id, $z.risk_score, $z.risk_band, $z.confidence)
    }
} else {
    Write-Host "      WARNING: backend did not respond within 30s" -ForegroundColor Red
}

# 2) Frontend: Vite dev server on :3000 (live API mode via .env.local)
Write-Host "[2/2] starting frontend on http://localhost:3000 ..." -ForegroundColor Yellow
Start-Process -FilePath "powershell.exe" -WorkingDirectory "$root\frontend" -ArgumentList @(
    "-NoExit", "-Command", "npm run dev"
)

Start-Sleep -Seconds 3
Write-Host ""
Write-Host "=== TALUS is running ===" -ForegroundColor Cyan
Write-Host "  Dashboard : http://localhost:3000" -ForegroundColor White
Write-Host "  API docs  : http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Demo flow: map -> click Zone C -> SHAP -> What-If drawer -> CAUSAL PHYSICS tab -> Dec-1902 replay (3-year horizon)."
Write-Host "Close the two spawned windows to stop."
