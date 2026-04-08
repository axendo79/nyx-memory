@echo off
echo Stopping Nyx...
taskkill /F /FI "WINDOWTITLE eq Nyx Watcher" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Nyx" >nul 2>&1
timeout /t 1 >nul
echo Starting Nyx...
cd /d D:\Nyx\nyx_v1\nyx
start "Nyx Watcher" cmd /k ".venv\Scripts\python.exe watcher.py"
start "Nyx" cmd /k ".venv\Scripts\python.exe main.py"
echo Nyx started.
