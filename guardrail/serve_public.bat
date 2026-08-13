@echo off
REM Runs the GuardRail demo and exposes it on a public URL via a cloudflared
REM quick tunnel (no account, no API key needed). Double-click this file, or run
REM it from a terminal. Keep this window open — closing it stops the tunnel.
REM The public https://...trycloudflare.com URL is printed below once it connects.

cd /d %~dp0

echo Starting the GuardRail backend (serves the page + API on port 8000)...
start "guardrail-backend" ..\backend\.venv\Scripts\python.exe -m uvicorn main:app --app-dir . --host 127.0.0.1 --port 8000

echo Waiting for the backend to come up...
timeout /t 4 >nul

echo Opening a public tunnel — your shareable URL appears below:
echo ------------------------------------------------------------
cloudflared.exe tunnel --url http://localhost:8000 --no-autoupdate
