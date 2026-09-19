@echo off
REM Run the WHOOP OAuth consent flow: opens browser, listens for callback, stores tokens
cd /d C:\Users\gaura\Documents\Projects\whoop-app
".venv\Scripts\python.exe" -m whoop_mcp
pause
