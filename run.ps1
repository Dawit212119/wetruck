# Run script for FastAPI application
# This script ensures you're in the correct directory before starting the server

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectPath = Join-Path $scriptPath "platform-backend"

if (Test-Path $projectPath) {
    Write-Host "Changing to project directory: $projectPath"
    Set-Location $projectPath
    Write-Host "Starting FastAPI server..."
    Write-Host "Server will be available at: http://127.0.0.1:8000"
    Write-Host "API Docs at: http://127.0.0.1:8000/docs"
    Write-Host ""
    python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
} else {
    Write-Host "Error: Project directory not found at: $projectPath"
    Write-Host "Please make sure you're running this from the platform-backend root directory"
    exit 1
}

