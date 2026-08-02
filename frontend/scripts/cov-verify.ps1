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
Remove-Item -Path (Join-Path $frontend 'coverage') -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path (Join-Path $frontend 'coverage\.tmp') -Force | Out-Null

# 使用默认 reportsDirectory（coverage/）避免自定义目录下 .tmp 写入竞态，结束后改名到目标目录
$ok = $false
for ($i = 1; $i -le $MaxAttempts -and -not $ok; $i++) {
  $p = Start-Process -FilePath "cmd.exe" -ArgumentList '/c', ".\node_modules\.bin\vitest.cmd run $TestFile --coverage --coverage.include=$SrcFile > `"$out`" 2>&1" -WorkingDirectory $frontend -Wait -PassThru -NoNewWindow
  Start-Sleep -Seconds 2
  $ok = Test-Path (Join-Path $frontend 'coverage\coverage-final.json')
  if (-not $ok -and $i -lt $MaxAttempts) {
    Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Remove-Item -Path (Join-Path $frontend 'coverage') -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path (Join-Path $frontend 'coverage\.tmp') -Force | Out-Null
    Start-Sleep -Seconds 3
  }
  Write-Output "attempt $i exit=$($p.ExitCode) ok=$ok"
}
if ($ok) {
  $src = Join-Path $frontend 'coverage'
  $dst = Join-Path $frontend $ReportDir
  $leaf = Split-Path $dst -Leaf
  for ($c = 1; $c -le 5; $c++) {
    if (Test-Path (Join-Path $src 'coverage-final.json')) {
      New-Item -ItemType Directory -Path $dst -Force | Out-Null
      Get-ChildItem $src -Exclude '.tmp' -Exclude $leaf | Copy-Item -Destination $dst -Recurse -Force
      Start-Sleep -Milliseconds 300
      if (Test-Path (Join-Path $dst 'coverage-final.json')) { break }
    }
    Start-Sleep -Seconds 2
  }
}
Get-Content $out -Encoding UTF8 | Select-String -Pattern "All files|Tests |Test Files|Uncovered|ERROR" | Select-Object -First 8
if ($ok) {
  $json = Join-Path $frontend "$ReportDir\coverage-final.json"
  node -e "const fs=require('fs');const c=JSON.parse(fs.readFileSync(process.argv[1],'utf8'));const entry=Object.entries(c).find(([k])=>k.includes(process.argv[2]));if(!entry){console.log('target not found');process.exit(0)}const file=entry[1];const bm=file.branchMap;for(const id in file.b){const hits=file.b[id];if(hits.some(h=>h===0)){const br=bm[id];console.log('BRANCH line',br.loc.start.line,'hits',JSON.stringify(hits));}}for(const id in file.f){if(file.f[id]===0){const fn=file.fnMap[id];console.log('UNCOVERED FN line',fn.decl.start.line,JSON.stringify(fn.name));}}" $json $SrcFile
}
