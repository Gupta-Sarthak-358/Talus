# TALUS demo launcher — legacy alias. Prefer start_all.ps1 / start_all.sh (single entry, validators + mnemo venv + live 32 zones x 8 corridors).
# This file now just forwards to start_all.ps1.

$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "start_all.ps1")
