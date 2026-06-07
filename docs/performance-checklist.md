# 系统性能与 Bug 排查 Checklist

> 版本: v1.2.0 | 日期: 2026-06-06 | 目标: 全面体检 → 定位瓶颈 → 修复验证

---

## A. 后端性能检查 (FastAPI + SQLite)

### A1. SQLite 配置
- [ ] **WAL 模式**: `PRAGMA journal_mode=WAL;` 是否已开启？
  - 预期: 并发读不阻塞写，吞吐提升 3-5x
  - 检查: `sqlite3 data/rural_revitalization.db "PRAGMA journal_mode;"`
- [ ] **同步模式**: `PRAGMA synchronous=NORMAL;`（非 FULL）
  - 预期: 写入延迟降低 50%
- [ ] **缓存大小**: `PRAGMA cache_size=-8000;`（~8MB）
  - 预期: 减少磁盘 I/O
- [ ] **外键**: `PRAGMA foreign_keys=ON;` 确认开启
- [ ] **忙等待**: `PRAGMA busy_timeout=5000;`

### A2. 慢查询排查
- [ ] 运行 `python scripts/profile_api.py --batch --count 50` 识别慢端点
- [ ] 检查 `backend/app/core/query_optimizer.py` 的 `N+1` 查询
  - 重点模块: `projects.py`(79KB), `fund_lifecycle.py`(73KB), `school.py`(37KB)
- [ ] 为高频过滤字段检查索引：
  - `supported_villages.organization_id`
  - `projects.village_id`, `projects.status`
  - `funds.created_at`, `funds.village_id`
  - `schools.organization_id`
  - `messages.user_id`, `messages.is_read`

### A3. 异步化检查
- [ ] 文件 I/O 操作（数据导入/导出）是否已异步化？
- [ ] 大数据加密/解密（数据包同步）是否使用 `run_in_executor`？
- [ ] PDF/Excel 报表生成是否使用后台任务？

### A4. 连接池与事务
- [ ] SQLite 单写锁场景下是否存在长事务阻塞？
- [ ] 批量操作是否使用 `session.bulk_insert_mappings()` 代替逐条 insert？

---

## B. 前端性能检查 (Vue 3 + Element Plus + ECharts)

### B1. ECharts 内存泄漏
- [ ] 所有 ECharts 组件在 `onUnmounted` 中调用 `chart.dispose()`
  - 重点检查文件:
    - `views/analytics/dashboard/Dashboard.vue`
    - `views/analytics/map/MapVisualization.vue`
    - `views/funds/Analysis.vue`
    - `views/schools/Analysis.vue`
    - `views/ruralWorks/Analysis.vue`
    - `components/charts/*.vue`
- [ ] `window.addEventListener('resize', handler)` 在 unmount 时正确移除
- [ ] ECharts 实例数在路由切换后不持续增长

### B2. 大数据量渲染
- [ ] 长列表（审批历史 > 500 条）是否使用虚拟滚动？
  - 文件: `views/approval/History.vue`, `views/system/AuditManagement.vue`
- [ ] `el-table` 的 `row-key` 是否正确设置避免全量重渲染？
- [ ] 复杂表单是否使用 `v-memo` / `shallowRef` 减少响应式开销？

### B3. 首屏加载
- [ ] 非首屏路由是否配置懒加载 `() => import(...)`？
- [ ] ECharts / Element Plus Icons 是否按需引入？
- [ ] `vite build` 产物中是否有超过 500KB 的 chunk？

### B4. 组件渲染
- [ ] 运行 `startPerfMonitor({ logFps: true, logMemory: true })` 监控 FPS
- [ ] 使用 Vue Devtools Performance 面板录制关键操作（打开列表→编辑→保存）
- [ ] Lighthouse 评分是否 > 80？
  - 命令: `npx lighthouse http://localhost:8000 --view`

---

## C. Electron 桌面端检查

### C1. 主进程阻塞
- [ ] 大文件加密/解密是否使用 Worker Thread？
  - 文件: `electron/main.js` 中的 `ipcMain.handle('encrypt-file', ...)`
- [ ] 数据包导入（>100MB）是否阻塞 UI？
- [ ] 系统资源采集（CPU/内存/磁盘）是否在独立线程？

### C2. 内存泄漏
- [ ] 使用 Chrome DevTools → Performance → Memory 面板：
  1. 打开系统 → 录基线
  2. 执行 10 次页面切换（工作台→学校→项目→资金→工作台）
  3. 执行垃圾回收 → 录快照
  4. 检查 detached DOM 节点和未释放的 ECharts 实例
- [ ] `BrowserView` / `webview` 是否正确销毁？

### C3. IPC 通信
- [ ] 大数据传输（>1MB JSON）是否使用 `MessageChannel`？
- [ ] `ipcRenderer.invoke` 的超时时间是否合理（默认 30s）
- [ ] 是否避免在主进程中执行 `JSON.parse(largePayload)`？

### C4. 窗口管理
- [ ] 窗口最小化/恢复时是否出现白屏？
- [ ] 系统托盘图标状态是否正确同步？
- [ ] 自动更新检测是否卡死（需离线环境降级处理）？

---

## D. 通用 Bug 排查

### D1. 数据一致性
- [ ] 审批流状态机转换是否完整（pending→approved→rejected→withdrawn）？
- [ ] 删除关联数据时的级联删除是否正确？
- [ ] 数据同步冲突解决策略是否正确应用到所有同步模块？

### D2. 错误处理
- [ ] 所有 API 端点的 `try/except` 是否正确返回统一错误格式？
- [ ] 前端 API 调用是否有合适的错误提示（ElMessage.error）？
- [ ] 离线场景下 Electron 网络错误是否有友好降级？

### D3. 安全
- [ ] Token 过期后的刷新机制是否正常？
- [ ] CSRF 中间件是否正确处理所有状态变更请求？
- [ ] 数据导出是否验证用户权限？

---

## E. 诊断命令速查

```bash
# 后端
cd backend
python scripts/profile_api.py --batch --count 50          # 批量 API 压测
python scripts/profile_api.py --endpoint /api/v1/funds --output profile.pstats  # 单端 cProfile
snakeviz profile.pstats                                     # 火焰图可视化

# SQLite
sqlite3 data/rural_revitalization.db "PRAGMA journal_mode;" # 检查 WAL
sqlite3 data/rural_revitalization.db "EXPLAIN QUERY PLAN SELECT ..." # 查询计划

# 前端
npx lighthouse http://localhost:8000 --view                 # 性能评分
npx vite build --mode production && ls -lh dist/assets/ | sort -k5 -rh | head -10  # 大 chunk

# Electron (在 DevTools Console 中执行)
performance.memory                                          # 内存快照
document.querySelectorAll('canvas').length                  # ECharts 实例计数
```

---

## F. 预期性能指标

| 指标 | 优化前 | 目标 |
|------|--------|------|
| API 平均响应 | ? ms | < 200ms |
| 慢 API 阈值 | — | 无 > 500ms |
| 首屏加载 | ? s | < 2s |
| FPS (图表页) | ? | > 50 |
| 内存 (10 次页面切换) | ? | < 200MB, 增长 < 20MB |
| SQLite 写入延迟 | ? | < 50ms |
| 数据包加密 (100MB) | ? | 不阻塞 UI |
