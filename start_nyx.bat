@echo off
cd /d "%~dp0"

echo Starting Nyx Watcher...
start "Nyx Watcher" cmd /k ".venv\Scripts\python.exe watcher.py"

echo Starting Nyx...
echo.
.venv\Scripts\python.exe main.py

echo.
echo Nyx stopped. Shutting down watcher...
taskkill /FI "WINDOWTITLE eq Nyx Watcher" /F >nul 2>&1
