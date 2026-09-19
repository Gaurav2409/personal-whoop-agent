@echo off
REM Store WHOOP client credentials in the Windows keychain (service whoop-dev-app)
"C:\Users\gaura\Documents\Projects\whoop-app\.venv\Scripts\python.exe" -m whoop_mcp --store
pause
