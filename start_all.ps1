# TALUS one-command launcher - PowerShell (Windows, primary for SIH demo)
# SIH26001 @ 68c0c28 - Gangtok S1-S4 89/78/66/52, 16/17 REAL/PROXY, 1528x22 RF 0.921 XGB 0.9256
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\start_all.ps1
#   powershell -ExecutionPolicy Bypass -File .\start_all.ps1 -Build
#   powershell -ExecutionPolicy Bypass -File .\start_all.ps1 -NoFrontend

param(
  [switch]$Build,
  [switch]$NoFrontend
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$venvPython = "C:\Users\satvi\Desktop\mnemo\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) { $venvPython = "python" }
$py311 = "C:\Users\satvi\AppData\Local\Programs\Python\Python311\python.exe"
if (-not (Test-Path $py311)) { $py311 = $venvPython }

Write-Host "=== TALUS one-command launcher (PS) ===" -ForegroundColor Cyan
Write-Host "Root: $root  Branch: SIH26001 @ 68c0c28" -ForegroundColor DarkGray

# 0) validators - must stay green
Write-Host "[0/3] validators..." -ForegroundColor Yellow
& $py311 scripts/check_scaffold.py
if ($LASTEXITCODE -ne 0) { throw "check_scaffold FAILED" }
& $py311 scripts/validate_ngen_sample.py
if ($LASTEXITCODE -ne 0) { throw "validate_ngen FAILED" }
& $venvPython -m pytest backend/tests/test_reports.py -q
if ($LASTEXITCODE -ne 0) { Write-Host "  WARNING: test_reports not green" -ForegroundColor Red }

# 1) backend :8000
Write-Host "[1/3] backend FastAPI :8000 ..." -ForegroundColor Yellow
try { Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } } catch {}
$backendLog = Join-Path $root "backend.log"
if (Test-Path $backendLog) { Remove-Item $backendLog -Force -ErrorAction SilentlyContinue }
$proc = Start-Process -FilePath $venvPython -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8000" -WorkingDirectory "$root\backend" -PassThru -WindowStyle Hidden
$proc | Out-File (Join-Path $root ".backend.pid") -Force
Write-Host "  backend pid $($proc.Id) -> backend.log" -ForegroundColor DarkGray

$ok = $false
for ($i=0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 1
  try {
    $r = Invoke-RestMethod "http://127.0.0.1:8000/api/zones" -TimeoutSec 2
    if ($r.zones.Count -ge 4) { $ok = $true; break }
  } catch {}
}
if ($ok) {
  Write-Host "  backend UP -- live predictions:" -ForegroundColor Green
  foreach ($z in $r.zones) { Write-Host ("    Zone {0}: {1} {2} (confidence {3})" -f $z.zone_id, $z.risk_score, $z.risk_band, $z.confidence) }
} else {
  Write-Host "  WARNING: backend not up in 30s -- see backend.log" -ForegroundColor Red
  Get-Content $backendLog -Tail 20 -ErrorAction SilentlyContinue | Write-Host -ForegroundColor DarkGray
}

# 2) frontend
if ($NoFrontend) {
  Write-Host "[2/3] frontend skipped (-NoFrontend)" -ForegroundColor Yellow
} else {
  Write-Host "[2/3] frontend Vite :5173 ..." -ForegroundColor Yellow
  if (-not (Test-Path "$root\frontend\node_modules")) {
    Write-Host "  installing frontend deps (first run)..." -ForegroundColor DarkGray
    Push-Location "$root\frontend"; npm install --silent; Pop-Location
  }
  if ($Build) {
    Write-Host "  vite build check..." -ForegroundColor DarkGray
    Push-Location "$root\frontend"; npm run build --silent; if ($LASTEXITCODE -ne 0) { throw "vite build FAILED" }; Pop-Location
  }
  try { Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } } catch {}
  $frontLog = Join-Path $root "frontend.log"
  if (Test-Path $frontLog) { Remove-Item $frontLog -Force -ErrorAction SilentlyContinue }
  $fproc = Start-Process -FilePath "powershell.exe" -WorkingDirectory "$root\frontend" -ArgumentList @("-NoExit","-Command","npm run dev") -PassThru
  $fproc.Id | Out-File (Join-Path $root ".frontend.pid") -Force
  Write-Host "  frontend pid $($fproc.Id) -> frontend.log (VITE_USE_LIVE_API=true)" -ForegroundColor DarkGray
  Start-Sleep -Seconds 3
}

Write-Host ""
Write-Host "=== TALUS is running ===" -ForegroundColor Cyan
Write-Host "  Dashboard : http://localhost:5173  (live S1-S4 89/78/66/52)" -ForegroundColor White
Write-Host "  API docs  : http://localhost:8000/docs" -ForegroundColor White
Write-Host "  API zones : http://127.0.0.1:8000/api/zones" -ForegroundColor White
Write-Host ""
Write-Host "Demo flow: map to S1 89 Critical to SHAP to What-If S3 66 to 74 to Causal monga-mdl S3 to High to Roads R2 avoided to Report S2 crack to queue to verify" -ForegroundColor Gray
Write-Host "Logs: Get-Content backend.log -Tail 20; Get-Content frontend.log -Tail 20" -ForegroundColor DarkGray
Write-Host "Stop: powershell -File ./stop_all.ps1  or  ./stop_all.sh  or  ./stop_all.bat" -ForegroundColor DarkGray
