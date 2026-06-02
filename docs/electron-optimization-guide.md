# Electron 桌面体验优化指南

## 1. 冷启动优化（目标 <3秒）

### 后端启动加速
- 延迟加载非关键模块（在 main.py lifespan 中按需导入）
- 使用 .pyc 预编译缓存（打包时 -OO 优化）
- 数据库健康检查异步化，不阻塞 API 就绪

### 前端加载加速
- Vite 构建启用 code-splitting (已默认)
- 大组件异步加载 (defineAsyncComponent)
  
- 首屏仅加载关键 CSS，非关键 CSS 延迟加载

### Electron 主进程
- 窗口显示前预加载 splash 页面
- 后端启动同步显示进度
- 非关键 IPC handler 延迟注册

## 2. 大数据表格虚拟滚动

### 实施方案
- 已存在 VirtualTable.vue 和 VirtualList.vue 组件
- 检查 
- 在 FundTransaction 列表和 ApprovalRecord 列表中替换普通 Table 为 VirtualTable
- 配置项: itemHeight=48, overscan=10

## 3. IPC 通信优化

### 批量数据传输
- 分块传输：大文件超过 10MB 时分块传输
- 压缩：传输前 gzip 压缩
- 进度回调：长时间操作通过 IPC 报告进度

### 推荐实现


## 4. 离线状态指示器

### 前端组件
- 已存在  
- 在 DefaultLayout 中集成
- 后端不可达时显示离线横幅+缓存提示

## 5. 优雅退出

### 实现
- main.js 中  事件
- 关闭前检查：是否有进行中的导出/同步任务
- 有未完成任务 → 弹窗确认
- 等待任务完成（最多30秒）→ 强制退出
- 自动备份

### 代码位置
 约150行附近

## 6. 窗口状态管理
- 已实现：WINDOW_STATE_FILE 持久化窗口位置/大小
- 建议添加：多显示器支持、最小窗口尺寸限制

## 执行优先级
1. 虚拟滚动（用户感知最大）
2. 冷启动加速（首次体验关键）
3. 优雅退出（稳定性）
4. IPC 优化（性能细节）
5. 离线指示器（锦上添花）
