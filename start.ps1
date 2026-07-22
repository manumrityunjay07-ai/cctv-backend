# ============================================================
#  CCTV NL Search — One-Click Launcher
#  Starts backend (FastAPI) and frontend (Vite) simultaneously
#  Run from the project root:  .\start.ps1
# ============================================================

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VENV = "$ROOT\venv_fixed\Scripts"
$FRONTEND = "$ROOT\frontend"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  CCTV NL Search - Starting Servers      " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# --- Backend ---
Write-Host "[1/2] Starting Backend (FastAPI) on http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$ROOT'; `$env:KMP_DUPLICATE_LIB_OK='TRUE'; `$env:OPENBLAS_NUM_THREADS='1'; `$env:OMP_NUM_THREADS='1'; & '$VENV\Activate.ps1'; Write-Host 'Backend starting...' -ForegroundColor Green; uvicorn src.app:app --reload --port 8000 --host 0.0.0.0"
) -WindowStyle Normal

Start-Sleep -Seconds 3

# --- Frontend ---
Write-Host "[2/2] Starting Frontend (Vite) on http://localhost:5173 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$FRONTEND'; Write-Host 'Frontend starting...' -ForegroundColor Green; npm run dev"
) -WindowStyle Normal

Start-Sleep -Seconds 4

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  Both servers are starting!             " -ForegroundColor Green
Write-Host "                                         " -ForegroundColor Green
Write-Host "  Frontend  -> http://localhost:5173     " -ForegroundColor Green
Write-Host "  Backend   -> http://localhost:8000     " -ForegroundColor Green
Write-Host "  API Docs  -> http://localhost:8000/docs" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# Open browser automatically
Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"

Write-Host "Browser opened! Close the server windows to stop." -ForegroundColor Cyan
