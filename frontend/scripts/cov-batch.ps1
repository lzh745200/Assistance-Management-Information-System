param(
  [int]$MaxRetries = 6
)
# 批量覆盖率验证：依次运行每个测试文件并收集目标视图的覆盖率表格行
$targets = @(
  @{ Test = "tests/unit/views/auth/LoginEnhanced.test.ts"; Include = "src/views/auth/LoginEnhanced.vue" },
  @{ Test = "tests/unit/views/auth/ForgotPassword.test.ts"; Include = "src/views/auth/ForgotPassword.vue" },
  @{ Test = "tests/unit/views/auth/ChangePassword.test.ts"; Include = "src/views/auth/ChangePassword.vue" },
  @{ Test = "tests/unit/views/auth/TwoFactorSettings.test.ts"; Include = "src/views/auth/TwoFactorSettings.vue" },
  @{ Test = "tests/unit/views/auth/Register.test.ts"; Include = "src/views/auth/Register.vue" },
  @{ Test = "tests/unit/views/auth/Profile.test.ts"; Include = "src/views/auth/Profile.vue" },
  @{ Test = "tests/unit/views/auth/GetMachineCode.test.ts"; Include = "src/views/auth/GetMachineCode.vue" },
  @{ Test = "tests/unit/views/system/ConfigPackage.test.ts"; Include = "src/views/system/ConfigPackage.vue" },
  @{ Test = "tests/unit/views/system/SecretsManagement.test.ts"; Include = "src/views/system/SecretsManagement.vue" },
  @{ Test = "tests/unit/views/system/EncryptionSettings.test.ts"; Include = "src/views/system/EncryptionSettings.vue" },
  @{ Test = "tests/unit/views/system/MapTileManager.test.ts"; Include = "src/views/system/MapTileManager.vue" },
  @{ Test = "tests/unit/views/system/DataTier.test.ts"; Include = "src/views/system/DataTier.vue" },
  @{ Test = "tests/unit/views/system/UpdateLogs.test.ts"; Include = "src/views/system/UpdateLogs.vue" },
  @{ Test = "tests/unit/views/system/Menu.test.ts"; Include = "src/views/system/Menu.vue" },
  @{ Test = "tests/unit/views/system/I18nManagement.test.ts"; Include = "src/views/system/I18nManagement.vue" },
  @{ Test = "tests/unit/views/system/ErrorReports.test.ts"; Include = "src/views/system/ErrorReports.vue" },
  @{ Test = "tests/unit/views/system/CacheManagement.test.ts"; Include = "src/views/system/CacheManagement.vue" },
  @{ Test = "tests/unit/views/system/ZeroTrust.test.ts"; Include = "src/views/system/ZeroTrust.vue" },
  @{ Test = "tests/unit/views/system/EnvCheck.test.ts"; Include = "src/views/system/EnvCheck.vue" },
  @{ Test = "tests/unit/views/system/AuditManagement.test.ts"; Include = "src/views/system/AuditManagement.vue" },
  @{ Test = "tests/unit/views/system/Feedback.test.ts"; Include = "src/views/system/Feedback.vue" },
  @{ Test = "tests/unit/views/NotFound.test.ts"; Include = "src/views/NotFound.vue" },
  @{ Test = "tests/unit/views/system/UserManagement.test.ts tests/unit/views/system/UserManagementMenuPerm.test.ts"; Include = "src/views/system/UserManagement.vue" },
  @{ Test = "tests/unit/views/MonitoringDashboard.test.ts tests/unit/views/MonitoringDashboardExtra.test.ts"; Include = "src/views/system/MonitoringDashboard.vue" }
)

foreach ($t in $targets) {
  $out = $null
  for ($i = 1; $i -le $MaxRetries; $i++) {
    $out = cmd /c "npx vitest run $($t.Test) --coverage --coverage.include=$($t.Include) --coverage.reporter=text 2>&1"
    $row = $out | Where-Object { $_ -match "\|" -and $_ -notmatch "^\s*File|^----|All files" } | Select-Object -First 1
    if ($row) { break }
    Start-Sleep -Seconds 2
  }
  $name = ($t.Include -split "/")[-1]
  $clean = ($row -replace '\x1b\[[0-9;]*m', '' -replace '\s+', ' ').Trim()
  Write-Output "$name => $clean"
}
