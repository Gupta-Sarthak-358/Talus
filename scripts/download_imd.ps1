# Talus — IMD 0.25-degree daily gridded rainfall downloader
# Member 2 data grounding. Resumable: skips files that already exist.
# Run this in your own PowerShell window and close it whenever; re-run to continue.
#
# Usage:   powershell -File download_imd.ps1
# Output:  data\raw\imd\ind<year>_rfp25.nc   (log: data\raw\imd\download.log)

$ErrorActionPreference = 'Continue'

$out = Join-Path $PSScriptRoot '..\data\raw\imd'
New-Item -ItemType Directory -Path $out -Force | Out-Null
$log = Join-Path $out 'download.log'

# Latest year used by IMD NetCDF archive (2024). Earlier years fill down to 1901.
$latest = 2024
$earliest = 1901

Write-Host "Downloading IMD 0.25deg daily rainfall, $earliest-$latest" -ForegroundColor Green
Write-Host "Output: $out  (existing files are skipped)" -ForegroundColor Green

$ok = 0; $fail = 0

foreach ($y in ($latest..$earliest)) {
    $f = Join-Path $out ("ind{0}_rfp25.nc" -f $y)

    if (Test-Path $f) {
        Add-Content -Path $log -Value ("{0} skip (exists)" -f $y)
        Write-Host "$y EXISTS - skip" -ForegroundColor DarkGray
        continue
    }

    Write-Host "Downloading $y ... " -NoNewline
    & curl.exe -s -L --data "RF25=$y" "https://imdpune.gov.in/cmpg/Griddata/RF25.php" -o $f

    if ($LASTEXITCODE -eq 0 -and (Test-Path $f) -and ((Get-Item $f).Length -gt 1000000)) {
        $size = [math]::Round((Get-Item $f).Length / 1MB, 1)
        Add-Content -Path $log -Value ("{0} OK {1}" -f $y, (Get-Item $f).Length)
        Write-Host "OK ($size MB)" -ForegroundColor Green
        $ok++
    } else {
        Add-Content -Path $log -Value ("{0} FAIL exit={1}" -f $y, $LASTEXITCODE)
        Write-Host "FAIL (exit=$LASTEXITCODE)" -ForegroundColor Red
        $fail++
    }

    # Be polite to the IMD server between requests.
    Start-Sleep -Seconds 2
}

Add-Content -Path $log -Value ("==== downloader completed: ok={0} fail={1} ====" -f $ok, $fail)
Write-Host "Done. Files OK: $ok  Failed: $fail" -ForegroundColor Green
Write-Host "Log: $log" -ForegroundColor Green