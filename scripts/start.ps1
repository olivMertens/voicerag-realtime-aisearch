if (-not (Test-Path -Path "./app/backend/.env")) {
    Write-Host ""
    Write-Host "No app/backend/.env found." -ForegroundColor Yellow
    if (Get-Command azd -ErrorAction SilentlyContinue) {
        Write-Host "Attempting to generate it via azd (scripts/write_env.ps1)..." -ForegroundColor Yellow
        try {
            ./scripts/write_env.ps1
        } catch {
            Write-Host "Failed to generate .env via azd. You may need to run 'azd auth login' and 'azd env select'." -ForegroundColor Yellow
        }
    } else {
        Write-Host "azd not found. Create app/backend/.env (or run scripts/write_env.ps1 after installing azd)." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Restoring frontend npm packages"
Write-Host ""
Set-Location ./app/frontend
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to restore frontend npm packages"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Building frontend"
Write-Host ""
npm audit fix
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to build frontend"
    exit $LASTEXITCODE
}


Write-Host ""
Write-Host "Starting backend"
Write-Host ""
Set-Location ../../app/backend
$venvPythonPath = "../../.venv/scripts/python.exe"
if (Test-Path -Path "/usr") {
  # fallback to Linux venv path
  $venvPythonPath = "../../.venv/bin/python"
}

# Start the backend process using the dedicated startup script
Start-Process -FilePath $venvPythonPath `
              -ArgumentList "start_backend.py" `
              -NoNewWindow `
              -PassThru | Out-Null

# Give some time for the backend to start and check if it's running
Start-Sleep -Seconds 5
# Optionally, add a health check here to verify the backend is up

Write-Host "Backend started successfully"

# Start API
Write-Host ""
Write-Host "Starting API"
Write-Host ""
Set-Location ../api

# Determine the Python executable path for API based on the operating system
$apiVenvPythonPath = "../../.venv/scripts/python.exe"  # Windows path
if ($IsLinux) {
    # Fallback to Linux virtual environment path
    $apiVenvPythonPath = "../../.venv/bin/python"
}

# Start the API process using Uvicorn
Start-Process -FilePath $apiVenvPythonPath `
              -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8765" `
              -NoNewWindow `
              -PassThru | Out-Null

# Give some time for the API to start and check if it's running
Start-Sleep -Seconds 5
# Optionally, add a health check here to verify the API is up

Write-Host "API started successfully"

# Return to the project root directory
Set-Location ../../

Write-Host ""
Write-Host "All services started successfully."