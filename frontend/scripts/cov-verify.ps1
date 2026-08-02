param(
  [Parameter(Mandatory=$true)][string]$TestFile,
  [Parameter(Mandatory=$true)][string]$SrcFile,
  [Parameter(Mandatory=$true)][string]$ReportDir,
  [int]$MaxAttempts = 15
)
$ErrorActionPreference = 'Continue'
$frontend = 'C:\military-Rural Revitalization-system\frontend'
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3
$out = Join-Path $env:TEMP ('cov-' + (Split-Path $ReportDir -Leaf) + '.txt')
Remove-Item -Path (Join-Path $frontend $ReportDir) -Recurse -Force -ErrorAction SilentlyContinue
$ok = $false
for ($i = 1; $i -le $MaxAttempts -and -not $ok; $i++) {
  $p = Start-Process -FilePath "cmd.exe" -ArgumentList '/c', ".\node_modules\.bin\vitest.cmd run $TestFile --coverage --coverage.include=$SrcFile --coverage.reportsDirectory=$ReportDir > `"$out`" 2>&1" -WorkingDirectory $frontend -Wait -PassThru -NoNewWindow
  Start-Sleep -Seconds 3
  $ok = Test-Path (Join-Path $frontend "$ReportDir\coverage-final.json")
  if (-not $ok -and $i -lt $MaxAttempts) {
    Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
  }
  Write-Output "attempt $i exit=$($p.ExitCode) ok=$ok"
}
Get-Content $out -Encoding UTF8 | Select-String -Pattern "All files|Tests |Test Files|Uncovered|ERROR" | Select-Object -First 8
if ($ok) {
  $json = Join-Path $frontend "$ReportDir\coverage-final.json"
  node -e "const fs=require('fs');const c=JSON.parse(fs.readFileSync(process.argv[1],'utf8'));const file=Object.values(c).find(f=>f.path&&f.path.includes(process.argv[2]));if(!file){console.log('target not found');process.exit(0)}const bm=file.branchMap;for(const id in file.b){const hits=file.b[id];if(hits.some(h=>h===0)){const br=bm[id];console.log('BRANCH line',br.loc.start.line,'hits',JSON.stringify(hits));}}for(const id in file.f){if(file.f[id]===0){const fn=file.fnMap[id];console.log('UNCOVERED FN line',fn.decl.start.line,JSON.stringify(fn.name));}}" $json $SrcFile
}
