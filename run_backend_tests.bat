@echo off
cd /d c:\military-Rural Revitalization-system\backend
.venv\Scripts\python.exe -m pytest tests/unit/ -x -q --tb=short --timeout=120 2>&1
echo EXIT_CODE=%ERRORLEVEL%
