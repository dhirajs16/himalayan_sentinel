$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendPath = Join-Path $projectRoot 'backend'
$frontendPath = Join-Path $projectRoot 'frontend'
$pythonPath = Join-Path $backendPath '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Install backend dependencies with cd backend; uv sync --locked first.' }
if (-not (Test-Path -LiteralPath (Join-Path $frontendPath 'node_modules'))) { throw 'Install frontend dependencies with cd frontend; npm ci first.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot '.env'))) {
    Copy-Item -LiteralPath (Join-Path $projectRoot '.env.example') -Destination (Join-Path $projectRoot '.env')
}
Push-Location $backendPath
try {
    & $pythonPath -m app.db
    if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
    & $pythonPath -m app.scripts.seed_demo
    if ($LASTEXITCODE -ne 0) { throw 'Demo seeding failed.' }
    if (Get-ChildItem -LiteralPath (Join-Path $projectRoot 'data') -Filter PDGLs.shp -Recurse -ErrorAction SilentlyContinue) {
        & $pythonPath scripts/import_geospatial_data.py
        if ($LASTEXITCODE -ne 0) { throw 'Dataset import failed.' }
    }
    & $pythonPath scripts/import_context_data.py
    if ($LASTEXITCODE -ne 0) { throw 'Context dataset preparation failed.' }
    $backendProcess = Start-Process -FilePath $pythonPath -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $backendPath -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $backendPath 'var/backend.log') -RedirectStandardError (Join-Path $backendPath 'var/backend-error.log')
    $workerProcess = Start-Process -FilePath $pythonPath -ArgumentList '-m','app.jobs' -WorkingDirectory $backendPath -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $backendPath 'var/worker.log') -RedirectStandardError (Join-Path $backendPath 'var/worker-error.log')
} finally { Pop-Location }
try {
    Push-Location $frontendPath
    Write-Host 'Opening local service at http://localhost:3000; backend logs: backend/var/backend-error.log'
    npm run dev
} finally {
    Pop-Location
    if ($backendProcess -and -not $backendProcess.HasExited) { Stop-Process -Id $backendProcess.Id }
    if ($workerProcess -and -not $workerProcess.HasExited) { Stop-Process -Id $workerProcess.Id }
}
