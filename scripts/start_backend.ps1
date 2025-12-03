$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

Set-Location $RootDir

# Ensure .env exists
if (-not (Test-Path ".env")) {
    Write-Warning ".env file not found. Creating default..."
    Set-Content -Path ".env" -Value "DATABASE_URL=postgresql+asyncpg://postgres@localhost:5432/mul_in_one" -Encoding UTF8
}

# Check/Create Database
Write-Host "Checking database connection..."
try {
    uv run python scripts/check_db.py
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Database check failed. Please ensure PostgreSQL is running and accessible."
        Write-Warning "If you are using the local script, run: .\scripts\db_control.ps1 start"
        # We do not exit here, we let uvicorn try, maybe it works differently or user wants to see the error
    }
} catch {
    Write-Warning "Could not run database check script."
}

Write-Host "Starting FastAPI backend server..."
Write-Host "API will be available at: http://localhost:8000"
Write-Host ""

# Start uvicorn
uv run uvicorn mul_in_one_nemo.service.app:create_app `
  --factory `
  --reload `
  --host 0.0.0.0 `
  --port 8000 `
  --reload-exclude external `
  --reload-exclude .postgresql `
  --reload-exclude .milvus `
  --reload-exclude node_modules `
  --reload-exclude .venv

