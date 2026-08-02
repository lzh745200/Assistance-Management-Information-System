param(
  [Parameter(Mandatory = $true)][string]$TestFile,
  [Parameter(Mandatory = $true)][string]$Include,
  [int]$MaxRetries = 5
)
# 并发冲突时自动重试的覆盖率运行助手
$out = $null
for ($i = 1; $i -le $MaxRetries; $i++) {
  Remove-Item -Recurse -Force "C:\military-Rural Revitalization-system\frontend\coverage" -ErrorAction SilentlyContinue
  $out = cmd /c "npx vitest run $TestFile --coverage --coverage.include=$Include --coverage.reporter=text --coverage.reporter=json 2>&1"
  $summary = $out | Select-String -Pattern "\.vue \|.*Uncovered|All files"
  if ($summary) {
    $out | Select-String -Pattern "Test Files|Tests |\.vue \||All files|ERROR" | ForEach-Object { $_.Line }
    exit 0
  }
  Start-Sleep -Seconds 3
}
$out | Select-Object -Last 10
exit 1
