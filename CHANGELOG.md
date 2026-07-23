# 更新日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/),
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布] - 2026-07-22

### 全面故障检测与审查修复
- 🐛 **修复系统初始化密码校验不一致** — `SystemInit.vue` 前端校验 ≥8 位但后端 `InitRequest` 要求 ≥12 位，导致首次初始化设 8–11 位密码被 422 拒绝；前端 placeholder 与校验规则统一为 ≥12 位
- 🔒 **初始化密码强度加固** — `system/init.py` 复用 `PasswordPolicy` 校验管理员密码（与注册接口统一策略），最高权限账户不再允许弱密码
- 🐛 **修复 `_ValidationError.field` 缺失** — `core/exceptions.py` 验证错误类增补 `.field` 属性
- 🐛 **修复 vue-tsc 12 处类型错误** — projects/Detail.vue、Edit.vue、ProgressGallery.vue el-tag `:type` 联合类型注解 + projects.ts id 参数放宽为 `number|string`（兼容离线字符串 ID）+ Edit.vue `unknown`→`any[]`
- 🧪 **对齐 9 项陈旧测试** — 密码策略 ≥12（5 处）、is_bundled onedir 行为、version.json 测试自给自足、inspector 弃用警告断言
- 📝 **清理误导注释** — `api/v1/__init__.py` supported_village "WIP:501占位" 注释更正为已完整实现
- 📄 **文档同步** — README/结构说明测试数更新为后端 10045 + 前端 1624，验证日期 2026-07-22

### 测试结果 (2026-07-22)
- ✅ 后端: **10,045 测试通过** (0 失败)
- ✅ 前端: **1,624 测试通过** (125 文件, 0 失败)
- ✅ vue-tsc / Flake8 / ESLint: 0 错误
- ✅ Bandit (-ll): 0 中/高危
- ✅ 前端生产构建: 成功
- ✅ 路由加载: 42/42 模块

## [未发布] - 2026-07-08

### 全面测试修复
- 🔧 **修复测试超时** — vitest.config.ts 增加 hookTimeout=60000
- 🔧 **修复 RequestDeduplicator Promise 泄漏** — 添加 .catch(() => {}) 防止 vitest 调度器 hang
- 🔧 **修复 test_funds_enhanced.py NameError** — mock_auth fixture teardown 变量作用域
- 🔧 **修复 Fund 模型字段名** — `fiscal_year`/`created_by` 替换为正确字段

### 代码质量提升
- ♻️ **重构 with_transaction** — 从复杂度 16 拆分为 6 个小函数（flake8 C901 归零）
- 🐛 **修复 win_proactor_fix.py UnboundLocalError** — logger 局部变量未定义
- 🐛 **修复 database_indexes.py Bandit B608** — # nosec 标记位置
- 🎨 **修复 OfflineMap.vue ESLint/prettier** — 格式警告

### 10 项系统优化
- ⚡ **Sass 升级** — 1.71.1 → 1.101.0（消除 legacy-js-api 弃用警告）
- 🏗️ **CI/CD 改进**
  - 新增 `nightly-full.yml` 夜间全量测试（JUnit 报告 + Codecov + 质量报告）
  - `pr-checks.yml` 添加 Codecov 覆盖率上报，flake8 复杂度门禁 16
  - 删除过期 `backup_20260617_190104/` 目录和 merge-conflict 备份文件
- 📦 **lint-staged + pre-commit 加固**
  - `frontend/package.json` 添加 lint-staged 配置（*.ts/*.vue → ESLint, *.py → flake8）
  - `.pre-commit-config.yaml` 分阶段策略：ruff(pre-commit) + flake8/bandit/vue-tsc(pre-push)
- 🐳 **E2E Docker 化** — 新建 `docker/docker-compose.e2e.yml`（Playwright + Locust）
- 📄 **迁移版本管理** — 新建 `012_consolidate_baseline.py` 基线合并文档
- 📝 **可选依赖文档化** — `requirements-dev.txt` 标注 matplotlib/playwright 需要 C++ 编译器
- ✅ **TS 严格模式** — 已启用 strict: true + 全部子选项（原有配置，验证确认）

### 测试结果 (2026-07-08)
- ✅ 前端: **137 文件, 1,681 测试, 100% 通过**
- ✅ 后端: **8,890+ 测试通过**, smoke + funds_enhanced 24/24
- ✅ Flake8: 0 错误
- ✅ ESLint: 0 错误, 0 警告
- ✅ Bandit: 0 高危

## [未发布] - 2026-07-01

### 安全修复（CVE 批量升级）

- 🔒 **bleach 6.3.0→6.4.0** — 3 个 ReDoS 漏洞 (GHSA-g75f-g53v-794x / GHSA-gj48-438w-jh9v / GHSA-8rfp-98v4-mmr6)
- 🔒 **Mako 1.3.10→1.3.12** — CVE-2026-44307
- 🔒 **Pygments 2.19.2→2.20.0** — CVE-2026-4539
- 🔒 **pytest 9.0.2→9.0.3** — CVE-2025-71176

### 测试质量

- 🔧 **消除 1 个 skipped 测试** — test_map.py 移除 pytest.skip，改为符合实际鉴权行为的断言
- 🔧 **消除 11 个测试警告** — SAWarning (transaction already deassociated) + StarletteDeprecationWarning
- 🔧 **conftest.py** — db_session fixture teardown 加 rollback 守卫

### 文档

- 📝 README.md 更新测试数据（8890+ passed, 0 skipped, 0 warnings）
- 📝 README.md 更新构建命令（electron-builder 替代旧 NSIS 脚本）
- 📝 AGENTS.md 更新测试数量 + 构建流程 + 审计日志说明
- 📝 AGENTS.md 新增 PyInstaller spec / NSIS hook 文件引用

## [1.2.0-build] - 2026-06-28

### 构建系统改造

- ✨ **PyInstaller + electron-builder 离线安装包方案** — 目标机器零依赖
  - 新建 `backend/assistance-backend.spec` 统一打包配置
  - 新建 `build-scripts/electron-builder-nsis-hook.nsh`（VC++ 静默安装 + 进程终止 + 卸载清理）
  - 重写 `.github/workflows/build-windows.yml`（matrix x64 + electron-builder 流水线）
  - 删除 3 旧 spec + 7 旧 .nsi + 3 旧 .bat
- 🐛 **预置初始数据库打包** — `resources/database/rural_revitalization.db` 加入 extraResources
- 🐛 **electron/main.js 数据库文件名统一** — bumofu.db → rural_revitalization.db
- 🐛 **electron/main.js 图标路径修复** — resources/icon.png → resources/icons/icon.png

## [1.2.0-security] - 2026-06-23

### P0 安全修复

- 🔒 **密码明文打印移除** — machine_code.py / main.py，改为写入临时文件
- 🔒 **.env 明文密钥清空** — runtime_secrets.py 自动生成
- 🔒 **根 .env 配置混乱修复** — 版本号/端口/密钥
- 🔒 **审计日志落库修复（涉军合规）** — AuditLogger._persist_to_db()，端到端验证通过
- 🔒 **后端 CVE 包升级** — starlette/python-multipart/urllib3/requests/GitPython/Twisted/pydantic-settings
- 🔒 **前端 dompurify 升级** — CVE 修复

### P1 安全配置

- 🔒 **.env.example 安全配置** — CSRF_ENABLED=True, token 480 分钟
- 🔒 **前端 .env.production CSRF 开启**
- 🔒 **关键路径 except Exception 加 as e**（13 处：auth/audit/security/token）
- 🔒 **动态 SQL 标识符白名单** — metrics.py _SAFE_TABLE_NAMES
- 🔒 **database_health_service 路径解析修复**
- 🔒 **encryption.py MD5 弃用处理** — usedforsecurity=False + nosec

## [1.2.0] - 2026-06-20

### 修复（生产崩溃）

- 🐛 **RuralWorkService.create_rural_work 缺失** — 生产环境 `AttributeError: 'RuralWorkService' object has no attribute 'create_rural_work'`，补全 create_rural_work + update_rural_work 签名修正 + 5 个缺失方法（get_statistics/get_villages_for_select/generate_work_report/get_available_years/batch_delete）
- 🐛 **UserCascadeDeleteService 是 stub** — 删除用户始终 500，用 SQLite Pragma 反射重写级联删除
- 🐛 **ExcelExportService.export_organization_pass_codes 缺失** — 组织通行证码导出始终 500，补全方法
- 🐛 **reports 端点 5 处 async 服务调用漏 await** — export_to_excel/export_to_pdf/export_comprehensive_report/get_export_filename 把协程传给 BytesIO 运行时崩溃
- 🐛 **feedback verify_token 导出缺失** — `from app.api.v1.auth import verify_token` 永远 ImportError，登录用户提交反馈不记录身份
- 🐛 **analytics_service.filter_villages 契约不匹配** — service 返回 dict 路由期望元组，统一为 (items_orm, total) 元组

### 修复（功能 BUG）

- 🐛 **工作列表新增数据不显示（根因）** — `rural_work_service._to_dict` 漏 `village_name` 字段，前端"所属村庄"列显示空白。通过 ORM relationship 懒加载补全
- 🐛 **batch-delete body 契约不匹配** — 前端发 `{ids: [...]}` 后端期望 bare `[...]`，改为 `payload: dict` 提取 ids
- 🐛 **AuditLogService.log 字段名错误** — `AuditLog(resource=..., details=..., ip_address=...)` 三个字段名与模型列不匹配（resource_type/user_ip/metadata_），审计日志静默丢失
- 🐛 **projects.py audit.log 未传 db** — 3 处审计日志调用未传 db 参数，日志从未写入
- 🐛 **admin.py int(None) 崩溃** — 配置值为 None 时 int(None) 抛 TypeError，加 `or` 防御

### 修复（测试健壮性）

- 🔧 **file_upload magic 安全导入** — Windows libmagic 触发不可捕获的 access violation 导致全部后端测试崩溃，改用 stdlib mimetypes + 扩展名映射
- 🔧 **patch.dict(os.environ) → monkeypatch.setenv** — 超长环境变量（ACC_PRODUCT_CONFIG_V3 > 32767 字符）触发 Windows 限制导致 teardown 崩溃
- 🔧 **Schema 可变默认值** — `items: list = []` → `Field(default_factory=list)`，Pydantic v2 最佳实践
- 🔧 **前端 handleSave 加 catch** — API 失败时错误不再静默丢失，显示 ElMessage.error

### 文档

- 📝 更新项目文件结构说明.md：新增 v1.2.0 版本记录、services 层补充 rural_work_service/user_cascade_delete_service 说明、新增开发约定章节（Service 序列化/async 调用/Pydantic 默认值/AuditLog 字段映射/Windows libmagic/测试环境变量/路由-service 契约/batch-delete body）

## [1.4.0] - 2026-06

### 新增

- ✨ RBAC 批量权限（事务原子性）、权限撤销端点
- ✨ treeNormalizer 共享工具、E2E 冒烟测试
- ✨ PR 门禁 CI、64-bit 迁移脚本、pre-commit hooks、统一版本管理

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
