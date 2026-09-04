# TALUS stop helper — PowerShell (Windows, primary for SIH demo)
# Usage: powershell -ExecutionPolicy Bypass -File .\stop_all.ps1
# Kills :8000 (FastAPI) and :5173 (Vite) and removes .backend.pid/.frontend.pid

$ErrorActionPreference = "SilentlyContinue"
$root = $PSScriptRoot

Write-Host "Stopping TALUS..." -ForegroundColor Yellow

# Kill by port (most reliable on Windows)
try { Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } } catch {}
try { Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } } catch {}

# Kill by pid files (fallback)
foreach ($pidFile in @(".backend.pid", ".frontend.pid")) {
  $p = Join-Path $root $pidFile
  if (Test-Path $p) {
    $id = (Get-Content $p -Raw).Trim()
    if ($id -match "^\d+$") { Stop-Process -Id ([int]$id) -Force -ErrorAction SilentlyContinue }
    Remove-Item $p -Force -ErrorAction SilentlyContinue
  }
}

# Fallback: netstat + taskkill (if Get-NetTCPConnection not available)
try {
  $out = netstat -aon | Select-String ":8000.*LISTENING"
  foreach ($line in $out) { $pid = ($line -split "\s+")[-1]; taskkill /PID $pid /F 2>$null }
} catch {}
try {
  $out = netstat -aon | Select-String ":5173.*LISTENING"
  foreach ($line in $out) { $pid = ($line -split "\s+")[-1]; taskkill /PID $pid /F 2>$null }
} catch {}

# Clean logs (optional, keep for debugging — comment out if you want to keep)
# Remove-Item (Join-Path $root "backend.log") -Force -ErrorAction SilentlyContinue
# Remove-Item (Join-Path $root "frontend.log") -Force -ErrorAction SilentlyContinue

Write-Host "Stopped (ports 8000, 5173 cleared; pid files removed)" -ForegroundColor Green
