@echo off
cd /d c:\military-Rural Revitalization-system\backend
.venv\Scripts\python.exe -m pytest tests/unit/test_auth_users_api.py -v --tb=short --timeout=60
echo EXIT_CODE=%ERRORLEVEL%
