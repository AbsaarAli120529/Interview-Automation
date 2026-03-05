@echo off
title AI Interview Automation Platform
echo ========================================================
echo Starting AI Interview Automation...
echo ========================================================
echo.

echo [1/2] Starting FastAPI Backend...
start "Backend (FastAPI)" cmd /k "cd mock_backend && .\venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

echo [2/2] Starting Next.js Frontend...
start "Frontend (Next.js)" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers have been launched in separate terminal windows.
echo - Frontend App: http://localhost:3000
echo - Backend API: http://localhost:8000
echo.
echo Keep this window open or press any key to close this launcher (the servers will keep running).
pause
