$ErrorActionPreference = "Continue"
$outputFile = "c:\military-Rural Revitalization-system\_test_summary.txt"

"=== TEST RUN START ===" | Out-File -FilePath $outputFile -Encoding UTF8

# Backend tests
"=== BACKEND TESTS ===" | Out-File -FilePath $outputFile -Encoding UTF8 -Append
$env:ENVIRONMENT = "test"
$env:SECRET_KEY = "test-secret-key-for-ci"

Set-Location "c:\military-Rural Revitalization-system\backend"
$backendResult = & ".\.venv\Scripts\python.exe" -m pytest tests/ -q --tb=line --timeout=60 --cov=app --cov-report=term-missing 2>&1
$backendResult | Out-File -FilePath $outputFile -Encoding UTF8 -Append
"BACKEND_EXIT: $LASTEXITCODE" | Out-File -FilePath $outputFile -Encoding UTF8 -Append

# Frontend tests
"=== FRONTEND TESTS ===" | Out-File -FilePath $outputFile -Encoding UTF8 -Append
Set-Location "c:\military-Rural Revitalization-system\frontend"
$frontendResult = & npx vitest run --coverage 2>&1
$frontendResult | Out-File -FilePath $outputFile -Encoding UTF8 -Append
"FRONTEND_EXIT: $LASTEXITCODE" | Out-File -FilePath $outputFile -Encoding UTF8 -Append

"=== TEST RUN COMPLETE ===" | Out-File -FilePath $outputFile -Encoding UTF8 -Append
