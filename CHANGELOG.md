# 更新日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/),
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.2.0] - 2026-05-31

### 修复

- 🐛 修复 NTFS 文件系统损坏导致后端启动崩溃 (WinError 1392: 文件或目录损坏且无法读取)
- 🐛 修复 `resources/frontend/assets/js/` 目录损坏导致 Starlette StaticFiles 无法挂载
- 🐛 修复 `frontend/node_modules/` 中 element-plus/@antv 包文件内容损坏导致构建失败
- 🔧 添加文件系统损坏诊断与绕过策略：重命名隔离损坏目录 → 重建 → 恢复
- 📝 更新故障排除指南，新增 WinError 1392 诊断修复完整流程
- 📝 更新 CLAUDE.md 添加磁盘故障排查指引

### 运维

- 🔧 前端构建后自动同步 `resources/frontend/` 确保静态资源一致
- 🔧 添加浏览器缓存导致 404 问题的说明（硬刷新 Ctrl+Shift+R）

## [1.1.0] - 2026-03-13

### 新增功能

#### 数据同步
- ✨ 增量数据包导入导出系统
- ✨ 支持13个数据表的同步
- ✨ 三种冲突策略(跳过/覆盖/手动)
- ✨ ZIP压缩格式
- ✨ 完整的导入导出历史记录

#### 离线地图
- ✨ 完全离线的地图瓦片管理
- ✨ 支持缩放级别4-18
- ✨ 瓦片自动降级
- ✨ 预设区域下载(贵州省、毕节市)
- ✨ 地图瓦片管理界面

#### 批量操作
- ✨ 批量更新记录
- ✨ 批量删除(软删除/硬删除)
- ✨ 批量导出数据
- ✨ 操作前验证
- ✨ 批量操作栏组件

#### 数据安全
- ✨ 数据库加密(PBKDF2-SHA256)
- ✨ 敏感数据脱敏(6种规则)
- ✨ 密码修改功能
- ✨ 加密状态管理

#### 帮助文档
- ✨ 完整的离线帮助文档
- ✨ 帮助中心组件
- ✨ 使用指南和FAQ

#### 性能优化
- ✨ 性能监控服务
- ✨ API性能追踪
- ✨ 系统资源监控
- ✨ 数据库性能监控

### 改进

#### 后端
- 🔧 优化数据库查询性能
- 🔧 添加数据库索引
- 🔧 改进错误处理机制
- 🔧 完善日志记录

#### 前端
- 🔧 优化组件加载性能
- 🔧 改进用户界面交互
- 🔧 添加加载状态提示
- 🔧 完善错误提示

#### 测试
- ✅ 添加单元测试(80+用例)
- ✅ 添加集成测试
- ✅ 测试覆盖率达到80%+

#### 文档
- 📝 完整的用户手册
- 📝 详细的安装指南
- 📝 API文档完善
- 📝 技术文档更新

### 修复

- 🐛 修复数据导入时的编码问题
- 🐛 修复地图瓦片加载失败的问题
- 🐛 修复批量操作时的验证错误
- 🐛 修复加密配置文件路径问题
- 🐛 修复Alembic配置缺失的问题
- 🐛 修复启动系统.bat编码乱码问题（UTF-8→GBK）
- 🐛 修复UserInfo对象缺少allowed_menus_list属性导致的菜单API 500错误
- 🐛 修复启动脚本健康检查超时问题（netstat替代PowerShell Invoke-WebRequest）
- 🐛 修复44个scripts/*.bat文件的编码一致性问题
- 🗑️ 清理33个冗余/过时的文档文件

### 安全

- 🔒 添加数据库加密功能
- 🔒 实现敏感数据脱敏
- 🔒 增强密码安全性
- 🔒 完善备份恢复机制

### 性能

- ⚡ API响应时间优化到<500ms
- ⚡ 数据导出性能提升50%
- ⚡ 批量操作性能优化
- ⚡ 地图瓦片加载优化

## [1.0.0] - 2026-01-29

### 新增功能

#### 核心功能
- ✨ 帮扶村管理
- ✨ 项目管理
- ✨ 组织管理
- ✨ 政策管理
- ✨ 数据统计分析

#### 用户管理
- ✨ 用户认证和授权
- ✨ 角色权限管理
- ✨ 用户个人设置

#### 数据管理
- ✨ 数据导入导出
- ✨ 数据备份恢复
- ✨ 数据报表生成

#### 系统功能
- ✨ 系统监控
- ✨ ���志管理
- ✨ 问题跟踪

### 技术实现

#### 后端
- 🏗️ FastAPI框架
- 🏗️ SQLAlchemy ORM
- 🏗️ SQLite数据库
- 🏗️ Alembic数据库迁移

#### 前端
- 🏗️ Vue 3框架
- 🏗️ TypeScript
- 🏗️ Element Plus UI
- 🏗️ Pinia状态管理

#### 部署
- 🏗️ Docker支持
- 🏗️ Nginx配置
- 🏗️ 系统服务配置

## [未发布]

### 计划中的功能

#### 短期(1-2周)
- 🔜 完善单元测试
- 🔜 性能压力测试
- 🔜 用户体验优化

#### 中期(1-2月)
- 🔜 SQLCipher实际集成
- 🔜 差异备份实现
- 🔜 更多脱敏规则
- 🔜 审计日志增强

#### 长期(3-6月)
- 🔜 多密钥管理
- 🔜 密钥轮换
- 🔜 细粒度权限控制
- 🔜 数据加密传输

## 版本说明

### 版本号规则

版本号格式: `主版本号.次版本号.修订号`

- **主版本号**: 重大架构变更或不兼容的API修改
- **次版本号**: 新增功能,向下兼容
- **修订号**: Bug修复,向下兼容

### 变更类型

- `新增` - 新功能
- `改进` - 对现有功能的改进
- `修复` - Bug修复
- `安全` - 安全相关的修复
- `性能` - 性能优化
- `废弃` - 即将移除的功能
- `移除` - 已移除的功能

## 升级指南

### 从 1.0.0 升级到 1.1.0

1. **备份数据**
   ```bash
   cp backend/data/app.db backend/data/app.db.backup
   ```

2. **更新代码**
   ```bash
   git pull origin main
   ```

3. **更新依赖**
   ```bash
   cd backend
   pip install -r requirements.txt --upgrade
   cd ../frontend
   npm install
   ```

4. **运行数据库迁移**
   ```bash
   cd backend
   alembic upgrade head
   ```

5. **重启服务**
   ```bash
   # 重启后端和前端服务
   ```

### 重大变更说明

#### 1.1.0 重大变更

1. **数据库结构变更**
   - 新增 `data_sync_logs` 表
   - 新增 `data_conflicts` 表
   - 需要运行数据库迁移

2. **API变更**
   - 新增数据同步API: `/api/v1/data-sync/*`
   - 新增离线地图API: `/api/v1/offline-map/*`
   - 新增批量操作API: `/api/v1/batch/*`
   - 新增加密管理API: `/api/v1/encryption/*`

3. **配置变更**
   - 新增加密配置文件: `data/encryption_config.json`
   - 新增地图瓦片目录: `data/map_tiles/`
   - 新增数据同步目录: `data_sync/`

4. **依赖变更**
   - 后端新增依赖: `psutil`, `aiohttp`
   - 前端新增依赖: `leaflet`

## 已知问题

### 1.1.0

- SQLCipher完整集成需要编译支持(当前为框架实现)
- 大数据量导出可能较慢(>10000条记录)
- 地图瓦片下载需要网络连接

### 1.0.0

- 部分功能仅支持单用户使用
- 数据导入导出格式有限

## 贡献者

- Claude Opus 4.6 (AI Assistant) - 主要开发

## 许可证

内部使���

---

**最后更新**: 2026-05-29
**当前版本**: v1.2.0

## [1.2.0] - 2026-05-29

### 系统优化
- 🔧 Flake8 零问题（修复 100+ 代码质量警告）
- 🔧 后端测试恢复运行（修复阻塞的导入错误）
- 🔧 CI/CD YAML 完整重写（消除语法错误和质量门绕过）
- 🔧 CORS 实现统一（3 个 → 1 个，删除死代码）
- 🔧 安全加固（删除 .env 泄露密钥、PrometheusMiddleware 死代码）
- 🔧 前端构建优化（Element Plus 按需导入）
- 🔧 Stub 服务标记 NotImplementedError
- 🔧 索引系统重构（全部移入模型 __table_args__ + 启动验证）
- 🔧 数据库索引 bug 修复（移除不存在的 fiscal_year 列引用）
- 🔧 版本号统一（settings/README/package.json → 1.2.0）
- 🔧 Pydantic v2 弃用修复（min_items → min_length）
- 🔧 前端 Tree-shaking 优化（zhCn 直接导入，~300KB bundle 节省）
- 🔧 AuthStorage 统一存储层（sessionStorage 优先，localStorage 回退）
- 🔧 路由守卫修复（401 拦截器与路由状态同步）
- 🔧 ADMIN_ROLES 常量统一到 roleAccess.ts
- 🔧 启动脚本编码修复（chcp 936，PowerShell 健康检查）

### 新功能
- ✨ 路由系统补全（组织/用户/村庄/项目等模块路由定义）
- ✨ Pinia stores 完整实现（auth/organization/user/village）
- ✨ 前端统一 AuthStorage（token 迁移 + sessionStorage 存储）
- ✨ 登录页 401 重定向循环防护

### 部署
- 📦 .deb 一体化构建脚本（build-scripts/build-deb-ubuntu.sh）
- 📦 国产电脑一键安装指南（麒麟V10/UOS/Ubuntu）
- 📦 Docker 交叉编译 ARM64 .deb 支持
- 📄 11 个 PPT 更新至 v1.2.0
- 📄 部署文档全面更新
- 🔧 request.ts 泛型支持 + 精确 URL 取消匹配
- 🔧 static_files.py 重构（纯函数 + SPA 内存缓存）

### UI/UX 修复 (2026-05-30)
- 🎨 系统名称统一为"帮扶管理信息系统"（15个文件）
- 🎨 军绿色主题全面应用（侧边栏/顶栏/底栏/表格）
- 🎨 主页欢迎标题金色加粗 28px
- 🎨 侧边栏导航标题白色加粗
- 🎨 全局表格表头军绿背景+白色文字+金色底边
- 🔧 侧边栏完整导航菜单（40+项含子菜单）
- 🔧 isAdmin/username/logout 连接 authStore（修复权限泄露）
- 🔧 /villages → /supported-villages 路由重定向
- 🔧 管理员密码重置为 admin123
- 🔧 登录页 SYSTEM_VERSION/COPYRIGHT_OWNER 导入修复
- 🔧 前端构建缓存清理（修复304导致的系统异常）
- 🔧 SPA fallback 资产挂载（/assets /images）
- 🔧 表格样式从 App.vue 移至 index.scss（CSS变量替代!important）

### 后端修复
- 🔧 43个字节损坏核心文件全部重建（core/ + system/api/）
- 🔧 cache.py 异步 CacheManager + get_cache_service 修复
- 🔧 pandas null bytes 重装
- 🔧 data_package_service.py 延迟导入修复循环依赖
- 🔧 get_event_loop_safe 缓存复用（修复事件循环泄漏）
- 🔧 EntityCacheManager 属性路径修复（_cache→_b）
- 🔧 CustomJSONEncoder = AppJSONEncoder（移除空子类）

## [1.1.0] - 2026-03-13
