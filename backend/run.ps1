#!/usr/bin/env pwsh
# Startup script for Missing Person Tracker Backend

$backendDir = "C:\Users\Muzammil\Desktop\missing_p_uav\missing-tracker\backend"
$pythonPath = "$backendDir\venv\Scripts\python.exe"

Write-Host "Starting Missing Person Tracker Backend..." -ForegroundColor Green
Write-Host "Backend Directory: $backendDir" -ForegroundColor Cyan
Write-Host ""

# Change to backend directory
Push-Location $backendDir

# Run uvicorn
& $pythonPath -m uvicorn main:app --reload --port 8000

# Restore directory
Pop-Location
