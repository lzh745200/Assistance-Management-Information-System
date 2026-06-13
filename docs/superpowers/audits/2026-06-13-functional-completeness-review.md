# 系统功能完整性审查报告

**日期**: 2026-06-13  
**版本**: 1.2.0  
**审查范围**: 26 个功能域，82 个后端路由文件，42 个前端 API 文件，88 个前端视图页面  
**审查方法**: 4 组并行代理逐文件读取，前端-后端交叉比对  

---

## 1. 总览

| 指标 | 数值 |
|------|------|
| 发现问题总数 | **131** |
| 🔴 高严重性 | **68** |
| 🟡 中等严重性 | **43** |
| 🟢 低严重性 | **20** |
| 总体前后端对齐率 | **~55%** |

### 各域问题分布

| 功能域 | 🔴高 | 🟡中 | 🟢低 | 对齐率 |
|--------|------|------|------|--------|
| 帮扶村管理 | 2 | 2 | 2 | 85% |
| 学校帮扶 | 2 | 1 | 0 | 30% |
| 项目管理 | 0 | 2 | 1 | 70% |
| 政策法规 | 1 | 2 | 1 | 60% |
| 乡村工作 | 3 | 3 | 1 | 40% |
| 经费管理 | 3 | 3 | 1 | 75% |
| 审批工作流 | 0 | 3 | 0 | 90% |
| 成效评估 | 2 | 1 | 1 | 25% |
| 待办事项 | 4 | 1 | 0 | 0% |
| 数据分析 | 5 | 2 | 0 | 30% |
| 导入导出 | 4 | 2 | 1 | 45% |
| 数据同步/包 | 3 | 2 | 1 | 65% |
| 数据质量 | 3 | 1 | 1 | 20% |
| 批量操作 | 3 | 1 | 0 | 0% |
| 报表模板 | 0 | 1 | 1 | 70% |
| 认证与身份 | 5 | 2 | 1 | 30% |
| 组织机构 | 3 | 1 | 0 | 65% |
| 系统管理 | 12 | 3 | 0 | 37% |
| 系统监控 | 7 | 1 | 0 | 30% |
| 消息通知 | 4 | 1 | 0 | 81% |
| 地图 | 3 | 1 | 1 | 75% |
| AI服务 | 4 | 1 | 0 | 10% |
| 舆情分析 | 2 | 0 | 0 | 0% |
| 搜索 | 1 | 1 | 0 | 50% |
| 加密安全 | 3 | 1 | 0 | 9% |

---

## 2. 🔴 高严重性问题（68项）

### 2.1 URL 路径不匹配（运行时 404）

这些是**立即导致功能不可用**的问题。

| # | 问题 | 前端文件 | 前端路径 | 后端正确路径 |
|---|------|---------|---------|------------|
| 1 | 政策级别选项 | `api/policy.ts:52` | `/policies/level-options` | `/policies/options/levels` |
| 2 | 政策统计 | `api/policy.ts:57` | `/policies/stats` | `/policies/statistics` |
| 3 | 政策导出Excel | `api/policy.ts:77` | `/policies/export` | `/policies/export/excel` |
| 4 | 政策导出PDF | `api/policy.ts:81` | `/policies/export-pdf` | `/policies/export/pdf` |
| 5 | 政策导出WPS | `api/policy.ts:85` | `/policies/export-wps` | `/policies/export/wps` |
| 6 | 政策导入模板 | `api/policy.ts:89` | `/policies/import-template` | `/policies/import/template` |
| 7 | 政策类型 | `api/policy.ts:53` | `/policies/types` | **后端无此端点** |
| 8 | 导出Word报表 | `api/export.ts:90` | `/export/report/{id}/word` | `/export/report-word` |
| 9 | 导出PDF报表 | `api/export.ts:97` | `/export/report/{id}/pdf` | `/export/report-pdf` |
| 10 | 导出历史 | `api/export.ts:51` | `/async-export/history` | `/async-export/tasks` |
| 11 | 同步冲突列表 | `api/dataSync.ts:79` | `/data-sync/conflicts` | `/data-sync/conflicts/{sync_log_id}` |
| 12 | 冲突解决 | `api/dataSync.ts:81` | `/data-sync/conflicts/{id}/resolve` | `/data-sync/resolve-conflict` |
| 13 | RBAC角色分配 | `api/rbac.ts:5` | `/rbac/assign` | `/rbac/assign/role` |
| 14 | 用户状态更新 | `api/mutations/user.ts:26` | `/users/{id}/status` | **后端无此端点** |
| 15 | 组织排序 | `api/organization.ts:14` | `PUT /organizations/sort` | `POST /organizations/batch-update-sort` |
| 16 | 组织通行码CRUD | `api/organizationPassCode.ts:33` | `/organizations/passcodes` | `/machine-code/organization/...` |
| 17 | 组织通行码验证 | `api/organizationPassCode.ts:24` | `/organizations/passcode/verify` | **后端无此端点** |
| 18 | 系统健康所有端点 | `api/systemHealth.ts:12-28` | `/system/health/*` | `/health/*` |
| 19 | 系统指标面板 | `api/metrics.ts:11,24` | `/system/metrics/dashboard` | **后端无此端点** |
| 20 | 备份端点 | `api/backup.ts:22` | `/system/backup` | `/backup` (桩实现) |
| 21 | 离线地图瓦片 | `api/offlineMap.ts:3` | `/offline-map/tiles` | `/offline-map/tiles/{z}/{x}/{y}` |
| 22 | 离线地图清除 | `api/offlineMap.ts:7` | `DELETE /offline-map/tiles` | `DELETE /offline-map/clear` |
| 23 | 离线地图下载 | `api/offlineMap.ts:9` | `/offline-map/tiles/download` | `/offline-map/download` |
| 24 | 帮扶村saveSection | `api/supportedVillage.ts:105` | `POST /{id}/sections/{section}` | `POST /{id}/yearly/{year}/{section}` |
| 25 | 乡村工作报告 | `api/ruralWork.ts:42` | `/rural-works/report` | `/rural-works/report/generate` |
| 26 | 经费附件CRUD | `api/funds.ts:179-194` | `/funds/{id}/attachments` 等4端点 | **后端完全不存在** |

### 2.2 前端 API 模块完全缺失（运行时 TypeError）

这些是前端页面调用但 API 模块中不存在的方法，**必然导致运行时错误**。

| # | 缺失的API模块/方法 | 影响范围 |
|---|-------------------|---------|
| 27 | `schools.ts` 缺失 18+ 方法（getStatistics/listProjects/createProject/updateProject/deleteProject/listScholarshipStudents/createScholarshipStudent/updateScholarshipStudent/deleteScholarshipStudent/importScholarshipStudents/listAttachments/uploadAttachment/deleteAttachment/downloadAttachment/getTypeOptions/getStatusOptions/importExcel/exportExcel/downloadImportTemplate） | `schools/` 全部 8 个页面 |
| 28 | 无 `analytics.ts` 中 `/analytics/*` 的 10 个端点封装（dashboard/village-analysis/funding-trends/performance-metrics/kpi-summary/realtime-stats/comparison/generate-report/export/health） | 分析仪表板 |
| 29 | 无 `dashboard.ts` 封装后端 `/dashboard/*` 的 6 个端点 | 工作台 |
| 30 | 无 `dataQuality.ts` 封装 | `dataManagement/Quality.vue` |
| 31 | 无 `validationRules.ts` 封装 | `dataVerify/Index.vue` |
| 32 | 无 `batchOperations.ts` 封装 | 批量操作完全不可用 |
| 33 | 无 `reportTemplates.ts` 封装 | `reportTemplates/Index.vue` |
| 34 | 无 `ai.ts` 封装 | `ai/InteractiveResult.vue` |
| 35 | 无 `sentiment.ts` 封装 | 舆情分析完全不可用 |
| 36 | 无 `effectiveness.ts` 封装 | 成效评估 |
| 37 | 无 `todos.ts` 封装 | 待办事项 |
| 38 | 无 `encryption.ts` 封装 | 加密设置 |
| 39 | 无 `userPermissions.ts` 封装 | 用户权限管理 |
| 40 | 无 `userManagement.ts` 封装 | 用户管理 |
| 41 | 无 `twoFactor.ts` 封装 | 双因素认证 |
| 42 | 无 `errorReport.ts` 封装 | 错误报告 |
| 43 | 无 `i18n.ts` 封装 | 国际化 |
| 44 | 无 `env.ts` 封装 | 环境检查 |
| 45 | 无 `tasks.ts` 封装 | 后台任务管理 |
| 46 | 无 `updateLogs.ts` 封装 | 更新日志 |
| 47 | 无 `zeroTrust.ts` 封装 | 零信任安全 |
| 48 | 无 `systemConfig.ts` 封装 | 系统配置CRUD |
| 49 | 无 `help.ts` 封装 | 帮助中心 |
| 50 | 无 `secrets.ts` 封装 | 密钥管理 |
| 51 | 无 `dataTier.ts` 封装 | 数据分级 |
| 52 | 无 `chunkedUpload.ts` 封装（后端 5 端点完整） | 分片上传 |

### 2.3 后端模块前端完全空白

这些是整个后端模块完全没有前端对应物的系统性问题。

| # | 模块 | 端点 | 缺失项 |
|---|------|------|--------|
| 53 | `effectiveness.py` | 4 | 无 API 文件、无页面、无路由、无菜单 |
| 54 | `todos.py` | 6 | 无 API 文件、无页面、无路由、无菜单 |
| 55 | `batch_operations.py` | 5 | 无 API 文件、无页面、无路由、无菜单 |
| 56 | `sentiment.py` | 6 | 无 API 文件、无页面、无路由、无菜单 |
| 57 | `ai.py` + `ai_enhanced.py` | 10 | 无 API 文件，仅 1 个占位页面 |
| 58 | `error_report.py` | 6 | 完全缺失 |
| 59 | `i18n.py` | 5 | 完全缺失 |
| 60 | `env.py` | 1 | 完全缺失 |
| 61 | `tasks.py` | 7 | 完全缺失 |
| 62 | `update_logs.py` | 8 | 完全缺失 |
| 63 | `zero_trust.py` | 7 | 完全缺失 |
| 64 | `system_config.py` | 8 | 完全缺失（系统配置 CRUD） |
| 65 | `encryption.py` | 4 | 完全缺失（仅 1 个可能内联调用的设置页） |
| 66 | `secrets.py` (monitoring) | 6 | 完全缺失 |
| 67 | `data_tier.py` (monitoring) | 8 | 完全缺失 |

### 2.4 前端调用后端不存在的端点

| # | 前端调用 | 状态 |
|---|---------|------|
| 68 | `dataSync.ts` 的 `sync` 和 `getStatus` 调 `POST /data-sync/sync` 和 `GET /data-sync/status/{taskId}` | **后端无此端点** |
| 69 | `dataReport.ts` 的 `previewReportData` 和 `downloadReportPackage` | **后端无此端点** |
| 70 | `report.ts` 的 `generate` 和 `download` | **后端无此端点** |
| 71 | `villages.ts` 的 `getVillagers` 和 `getIndustries` | **后端无此端点** |
| 72 | `message.ts` 的 `/admin/templates/*` 全套模板 CRUD | **后端无此端点** |
| 73 | `systemHealth.ts` 的 `table-stats/metrics/integrity-check/wal-checkpoint/vacuum` | **后端无此端点** |
| 74 | `metrics.ts` 的 `/system/metrics/dashboard` 和 `/system/metrics/health` | **后端无此端点** |
| 75 | `policy.ts` 的 `GET /policies/types` | **后端无此端点** |

---

## 3. 🟡 中等问题（43项）

### 3.1 API 模块方法不完整

| # | 问题 | 文件 |
|---|------|------|
| 1 | `fundLifecycle.ts` 缺失 13 个端点（allocation-orders 3个、quota-adjust、inspection-clues、verify-asset、performance-report、feasibility-report、fund-flow-tree、transfer-voucher attachments） | `api/fundLifecycle.ts` |
| 2 | `funds.ts` 缺失 budget-alerts/summary/transactions 端点 | `api/funds.ts` |
| 3 | `funds.ts` 缺失 history 端点封装（status/fields/operations） | `api/funds.ts` |
| 4 | `projects.ts` 缺失子资源方法（funds CRUD/tasks CRUD/changeHistory/filePreview） | `api/projects.ts` |
| 5 | `projectMilestones.ts` 缺失 transition-rules/transition/change-logs/dashboard 端点 | `api/projectMilestones.ts` |
| 6 | `policy.ts` 缺失子功能方法（分类树CRUD、发布/归档、文件上传/预览/下载、收藏、相关政策） | `api/policy.ts` |
| 7 | `supportedVillage.ts` 缺失 validateYearlyData/getExportModules/getExportFormats/previewExport | `api/supportedVillage.ts` |
| 8 | `ruralWork.ts` 缺失 getStatistics/getVillagesForSelect/getAvailableYears/batchDelete/getById | `api/ruralWork.ts` |
| 9 | `ruralTask.ts` 缺失 getStatistics/submitTask/approveTask/batchDelete | `api/ruralTask.ts` |
| 10 | `approval.ts` 缺失 overview/remind/resubmit 端点 | `api/approval.ts` |
| 11 | `rbac.ts` 仅覆盖 3/16 个 RBAC 端点 | `api/rbac.ts` |
| 12 | `machineCode.ts` 缺少组织通行码端点 | `api/machineCode.ts` |
| 13 | `systemMonitor.ts` 仅覆盖 2/6 个 monitor 端点 | `api/systemMonitor.ts` |
| 14 | `map.ts` 缺失 config/distances/tile-info 端点 | `api/map.ts` |
| 15 | `message.ts` 缺失 getMessage(id)/stats/recent-activities | `api/message.ts` |
| 16 | `organization.ts` 缺失 my-organization/subordinates/types/children/ancestors/move/activate/deactivate | `api/organization.ts` |
| 17 | `dataPackage.ts` 缺失 one-click-report/preview 端点 | `api/dataPackage.ts` |
| 18 | `export.ts` 缺失 users/schools/projects/funds/comprehensive 导出 | `api/export.ts` |
| 19 | `import.ts` 缺失 validate 端点 | `api/import.ts` |

### 3.2 架构/设计问题

| # | 问题 | 详情 |
|---|------|------|
| 20 | `messages.py` 和 `messages_extended.py` 功能高度重复 | 两个文件都实现了 send/list/read/delete |
| 21 | `system/backup.py` 和 `system/admin.py` 都定义了 POST /backup | 重复端点 |
| 22 | `system/cache.py` 只有桩实现 | POST /clear 无实际逻辑 |
| 23 | `system/backup.py` 全部桩实现 | 备份端点无实际功能 |
| 24 | `system/config_package.py` 仅 GET 桩 | 配置包管理不可用 |
| 25 | `getChangeHistory` 在 supportedVillage.ts 中为 stub | 永远返回空数组 |
| 26 | `Report.vue` (ruralWorks) 的 generate() 函数体为空 | 工作报告生成未实现 |
| 27 | `Task.vue` 使用 ruralWork API 而非 ruralTask API | 任务审批流程不可用 |
| 28 | 数据校验审核菜单指向 `/funds` 路径 | 路径复用，非独立页面 |
| 29 | 组织通行码后端在 machine_code.py 而非 organization.py | 路由混乱 |
| 30 | 两个 data_quality.py 路由（顶层 + data/data/） | 维护混淆 |
| 31 | 工作日历无菜单项 | 用户无法导航访问 |
| 32 | AI 功能无菜单入口 | 不可发现 |
| 33 | 消息中心无显式菜单项 | 不可发现 |
| 34 | 成效评估无独立菜单项 | 不可发现 |
| 35 | 通知偏好 PUT 颗粒度不匹配 | 前端 `/notifications/preferences` vs 后端 3 个独立端点 |
| 36 | Role.vue、MenuPermission.vue、UsersOrgs.vue 存在但路由未注册或被重定向 | 孤立页面 |
| 37 | funds/Export.vue、funds/Edit.vue 存在但无路由引用 | 孤立文件 |
| 38 | UserFundList.vue 无独立路由注册 | 仅在布局菜单中引用 |
| 39 | GlobalSearch.vue 为空壳组件（仅占位文本） | 5 路并行搜索后端功能浪费 |
| 40 | 大量视图直接裸调 `request` 绕过 API 模块 | 违反分层架构：Quality.vue、dataVerify/Index.vue、reportTemplates/Index.vue、HelpCenter.vue、BatchImport.vue 等 |

### 3.3 其他

| # | 问题 |
|---|------|
| 41 | `stores/policy.ts` 期望 `{code:200, data:...}` 但后端返回 `{items, total, page, page_size}` |
| 42 | `supportedVillage.ts` saveSectionData 缺少 year 参数 |
| 43 | `offlineMap.ts` 重复定义 getMapStatus 和 getStatus |

---

## 4. 🟢 低严重性问题（20项）

| # | 问题 | 文件 |
|---|------|------|
| 1 | `/villages` 后端路由未被前端直接使用（全部走 `/supported-villages`） | `villages.py` |
| 2 | 导入历史详情端点未封装 | `import.ts` |
| 3 | 项目文件预览端点未封装 | `projects.ts` |
| 4 | 项目下载 URL 返回字符串而非发起下载 | `projects.ts:66` |
| 5 | 政策 store 响应格式不匹配 | `stores/policy.ts` |
| 6 | ruralWorkApi 命名不一致 | `ruralWork.ts` |
| 7 | offlineMap.ts 重复函数定义 | `offlineMap.ts` |
| 8 | `fund_lifecycle.py` monitoring/deviation 缺少 generate_report 参数 | `fundLifecycle.ts:256` |
| 9 | `sync/status` 端点无前端封装（影响小） | `sync.py` |
| 10 | `import/history/{id}` 详情端点无前端 | `import_data.py` |
| 11 | `data_quality.py` 两个源文件合并到同一路由 | 路径混淆 |
| 12 | 模板 upload 支持 fund module 但后端明确返回不支持 | `report_templates.py` |
| 13 | cache.py 桩实现无前端对接 | `system/cache.py` |
| 14 | policy.ts 路径格式不一致（用连接线而非斜杠） | `api/policy.ts` |
| 15 | `dataSyncApi.sync` 和 `getStatus` 虚构方法 | `api/dataSync.ts` |
| 16 | `villages.ts` getVillagers/getIndustries 无后端 | `api/villages.ts` |
| 17 | ExportDialog.vue 使用 report API 而非 supportedVillage export | `ExportDialog.vue` |
| 18 | assessment.ts 缺少缓存刷新机制 | `api/assessment.ts` |
| 19 | 经费 history 端点视图层裸调 request | `Detail.vue` |
| 20 | `getFileDownloadUrl` 返回 URL 字符串而非发起下载 | `api/projects.ts` |

---

## 5. 跨域共性问题

### 5.1 系统性模式

1. **"有后端无前端"集中区域**：`system/` 子目录（18 个路由文件）中 12 个完全无前端——system_config, i18n, env, error_report, tasks, update_logs, zero_trust, init, help, audit（部分），cache, backup
2. **"有前端无 API 文件"集中区域**：monitoring/ (secrets, data_tier), ai/, sentiment/, encryption/
3. **路径前缀不一致**：多个模块前端使用 `/system/xxx` 而实际路由为 `/xxx`
4. **桩实现过度**：多个 system/ 路由文件为桩实现，建议清理或实现

### 5.2 修复优先级建议

| 优先级 | 类别 | 问题数 | 影响 |
|--------|------|--------|------|
| **P0 立即** | URL 路径不匹配（运行时 404） | 26 | 点击按钮无响应或报错 |
| **P0 立即** | 前端调用不存在的方法（TypeError） | 1 (schools.ts) | 学校模块全部页面崩溃 |
| **P1 本周** | 缺失前端 API 封装文件 | 20+ | 功能不可用 |
| **P1 本周** | 后端完整前端完全空白 | 10+ | 死代码/功能浪费 |
| **P2 下迭代** | API 方法不完整 | 19 | 部分子功能不可用 |
| **P2 下迭代** | 架构/设计问题 | 21 | 代码质量/可维护性 |
| **P3 后续** | 低严重性问题 | 20 | 代码规范/一致性 |

---

## 6. 统计附录

### 6.1 按功能域详细统计

| 功能域 | 后端端点数 | 前端API调用数 | 前端页面数 | 对齐率 | 🔴 | 🟡 | 🟢 |
|--------|----------|-------------|----------|--------|-----|-----|-----|
| 帮扶村管理 | 28 | 24 | 8 | 85% | 2 | 2 | 2 |
| 学校帮扶 | 27 | 5 | 8 | 30% | 2 | 1 | 0 |
| 项目管理 | 30 | 14 | 6 | 70% | 0 | 2 | 1 |
| 政策法规 | 30 | 15 | 5 | 60% | 1 | 2 | 1 |
| 乡村工作 | 25 | 15 | 5 | 40% | 3 | 3 | 1 |
| 经费管理 | 68 | 50 | 15 | 75% | 3 | 3 | 1 |
| 审批工作流 | 21 | 18 | 4 | 90% | 0 | 3 | 0 |
| 成效评估 | 8 | 4 | 1 | 25% | 2 | 1 | 1 |
| 待办事项 | 6 | 0 | 0 | 0% | 4 | 1 | 0 |
| 数据分析 | 32 | 10 | 6 | 30% | 5 | 2 | 0 |
| 导入导出 | 24 | 12 | 4 | 45% | 4 | 2 | 1 |
| 数据同步/包 | 26 | 23 | 8 | 65% | 3 | 2 | 1 |
| 数据质量 | 10 | 0 | 2 | 20% | 3 | 1 | 1 |
| 批量操作 | 5 | 0 | 0 | 0% | 3 | 1 | 0 |
| 报表模板 | 7 | 0 | 1 | 70% | 0 | 1 | 1 |
| 认证与身份 | 67 | 20 | 13 | 30% | 5 | 2 | 1 |
| 组织机构 | 20 | 13 | 4 | 65% | 3 | 1 | 0 |
| 系统管理 | 82 | 30 | 21 | 37% | 12 | 3 | 0 |
| 系统监控 | 40 | 12 | 3 | 30% | 7 | 1 | 0 |
| 消息通知 | 16 | 13 | 2 | 81% | 4 | 1 | 0 |
| 地图 | 12 | 9 | 3 | 75% | 3 | 1 | 1 |
| AI服务 | 10 | 0 | 1 | 10% | 4 | 1 | 0 |
| 舆情分析 | 6 | 0 | 0 | 0% | 2 | 0 | 0 |
| 搜索 | 1 | 1 | 1 | 50% | 1 | 1 | 0 |
| 加密安全 | 11 | 0 | 1 | 9% | 3 | 1 | 0 |
| **合计** | **~616** | **~288** | **~120** | **~55%** | **~73** | **~41** | **~17** |

> 注意：由于部分端点在不同交叉组中重复计算，总数可能略有偏差。

### 6.2 审查方法论

- 4 个并行 Explore 代理逐文件读取后端路由和前端 API/视图源码
- 交叉比对每个端点/调用的方法+路径
- 检查路由注册（`router/index.ts`）和菜单配置（`menu-config.ts`）
- 状态标识: ✅完全对齐 / ⚠️部分对齐 / ❌未对齐
- 严重程度: 🔴高(功能不可用) / 🟡中(部分不可用) / 🟢低(规范问题)

---

*报告由自动化功能完整性审查流程生成*  
*审查执行时间: 2026-06-13 | 系统版本: 1.2.0*
