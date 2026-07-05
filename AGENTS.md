# AGENTS.md - Agent Quick Reference

## Project Identity

Assistance Management Information System (帮扶管理信息系统) - Offline-first desktop app for military-civilian rural aid.
FastAPI + Vue 3 + Electron + SQLite. Windows primary, Linux ARM64 (Kylin V10) secondary.

**Full context**: See `CLAUDE.md` and `.cursorrules` for architecture details, API formats, and security requirements.

## Quick Commands

### Backend

```bash
cd backend
.venv\Scripts\python start.py                          # Start server (http://localhost:8000)
python -m pytest tests/ -v --tb=short -q --timeout=60  # Run all tests (~8890)
python -m pytest tests/unit/test_xxx.py -v              # Run single test file
python -m flake8 app/ --max-line-length=120             # Lint (CI gate, 0 errors)
python -m mypy app/ --config-file=mypy.ini --ignore-missing-imports  # Type check (non-blocking)
python -m bandit -r app/ -ll                            # Security scan
```

### Frontend

```bash
cd frontend
npm run dev                                             # Dev server (http://localhost:5173)
npm run test -- --run                                   # Run all tests (~1700)
npx vitest run src/views/xxx/xxx.test.ts               # Run single test file
npm run lint                                            # ESLint (CI gate, --max-warnings=0)
npx vue-tsc --noEmit                                    # Type check (CI gate)
npm run build                                           # Production build
```

### Combined

```bash
make test           # Run backend + frontend tests
make test-backend   # Backend tests only
make test-frontend  # Frontend tests only
make deploy-check   # Full pre-deploy validation
make clean          # Clean test artifacts
```

## Architecture Gotchas

### Dual API Response Format

The API uses **two response formats** - this causes most integration bugs:

| Format | Shape | Used by |
|--------|-------|---------|
| Bare | `{total, page, page_size, items}` | 18 endpoints (see "Remaining bare-format endpoints" below) |
| Envelope | `{code:200, data:{...}, message:"成功"}` | `/auth/login`, `/users`, `/rbac`, `/supported-villages`, `/funds`, `/projects`, `/schools` |

**Unification progress (2026-07-05)**: 4 main list endpoints (`supported-villages`, `funds`, `projects`, `schools`) converted from bare → envelope via `ok_list()` helper in `backend/app/core/response.py`:
```python
def ok_list(items, total, page=1, page_size=20, message="成功", **kwargs):
    return success_response(data={"items": items, "total": total, ...}, message=message, **kwargs)
```
When adding new list endpoints, **use `ok_list()`** (envelope) — not bare dict.

Frontend stores use `_unwrapList()` / `_unwrapSingle()` to normalize both. The Axios response interceptor auto-expands `data.data` fields to top level of `response.data`, making envelope format transparent to frontend stores.

**Remaining bare-format endpoints** (18 — frontend handles both transparently, future unification TBD):
`/work-logs`, `/scholarship-students`, `/rural-works`, `/policies`, `/organizations`, `/machine-codes`, `/pass-codes`, `/data-sync/*`, `/import-export/*`, `/map/*`, `/audit-logs`, `/operation-logs`, `/system/backup`, `/system/update-logs`, `/reports/templates`, `/funds/contracts`, `/funds/transfers`, `/funds/anomalies`

### Data Isolation

- `organization_id` field is **mandatory** on all queries
- Use `filter_by_data_scope(query, model, user, db=db)` from `app/core/data_permission.py`
- Missing this = security vulnerability (military audit will fail)

### Soft Delete Pattern

Models use `is_active` column (Boolean, default=True, nullable=False) for soft deletes:
- `is_active=False` = deleted (hidden from default queries)
- `include_deleted=true` query param shows all records (admin only)
- `to_dict()` exposes `isDeleted` (camelCase) and `is_deleted` (snake_case) fields
- Currently applied to: `SupportedVillage`, `School`
- Migration: `alembic/versions/village_softdel_001_add_is_active.py`
- List endpoints filter `is_active=True` by default; detail endpoints show soft-deleted records (for audit)
- Cross-org access returns **403** (not 404) to distinguish "exists but not yours" from "doesn't exist"

### Route Registration

New backend routes must be registered in `app/api/v1/__init__.py`:
- Sub-packages (auth, data, import_export, system): add explicit import
- Business modules: add name to `_BUSINESS_MODULES` list (line 112)

### Frontend Route Loading

All routes use lazy loading: `component: () => import('@/views/xxx/List.vue')`

## Testing

### Backend Coverage

- Minimum: 45% (CI gate via `--cov-fail-under=45`)
- Local target: 50% (Makefile)
- Test env vars: `ENVIRONMENT=test`, `SECRET_KEY=test-secret-key-for-ci`

### Frontend Coverage

- Vitest with V8 coverage provider
- Coverage thresholds in `vitest.config.ts`

### Pre-commit Hooks

Installed via `pre-commit install`:
- black (Python formatter, line-length=120)
- isort (import sorting)
- flake8 (lint)
- Standard hooks (trailing whitespace, YAML/JSON validation, large file check)

## Build Pipeline

### Frontend Build

```bash
cd frontend && npm run build  # Outputs to frontend/dist/
```

### Sync to Backend (for production)

```bash
bash scripts/build/sync-frontend-dist.sh   # Copies dist/ → resources/frontend/ with integrity check
python scripts/audit_static_assets.py --verbose  # Verify static assets
```

### Electron Packaging

```bash
# PyInstaller 打包后端（内含 Python 解释器 + 全部 pip 依赖 + SQLite）
cd backend && python -m PyInstaller assistance-backend.spec --clean --noconfirm

# electron-builder 打包 NSIS 安装包
npx electron-builder --win --x64    # Windows x64

# 或通过 Makefile
make build-win-x64                  # 一键构建 Windows x64
make build-kylin                    # Linux ARM64 DEB
```

安装包结构：Electron 运行时 + `assistance-backend.exe`（PyInstaller）+ Vue3 前端 + VC++ Redistributable（NSIS 钩子静默安装）。目标机器零依赖。

### DEB Packages (Docker cross-compile)

```bash
make build-deb-amd64    # x86_64
make build-deb-arm64    # ARM64 (for Kylin V10)
make build-kylin        # Kylin V10 standalone (no Electron, pure web)
```

## Known Issues & Fixes

### WinError 10054 (Connection Reset)

Auto-fixed by `app/utils/win_proactor_fix.py`. Loaded by `start.py` and `main.py`. No action needed.

### bcrypt Login Timeout

Passlib + bcrypt 5.x incompatibility fixed in `app/core/security.py`. Verify `verify_password()` takes ~200ms, not 30s.

### PasswordPolicy REQUIRE_SPECIAL

`PasswordPolicy` class in `app/core/security.py` has `REQUIRE_SPECIAL = True` attribute (added 2026-07-05 — was missing, caused `AttributeError` when `validate()` referenced it). Also defines `SPECIAL_WHITELIST = set("!@#$%^&*()-_=+[]{}|;:,.<>?")`. When adding new password rules, ensure the class attribute exists BEFORE `validate()` references it.

### Frontend 404 on Static Files

After `npm run build`, run `scripts/build/sync-frontend-dist.sh` to sync. Browser cache may need clearing.

### ARM64 Build: Never Use --no-cache

`build-arm64.yml` uses Docker buildx with QEMU (ARM64 emulation on x86 CI runners). Docker layer caching is the only reason builds finish in ~30min instead of hours. Never add `--no-cache` to the `docker buildx build` command.

### Dockerfile Output Truncation (Intentional)

`Dockerfile.kylin-standalone` pipes RUN commands through `tail -N` (npm ci: `-5`, build: `-10`, pip: `-10`, pyinstaller: `-20`) to keep CI logs manageable. Downstream `test -f`/`test -d` commands in the same stage still catch failures. Don't remove `tail` pipes.

### Pre-commit Hooks: Dockerfile Check

`.pre-commit-config.yaml` includes a `check-dockerfile-tail` hook that rejects Dockerfile RUN commands ending in `2>&1` without `| tail`. This prevents accidental removal of output truncation in ARM64 builds.

### Audit Log Persistence (Military Compliance)

AuditLogger.log() writes to both Python logging (app.log) AND database (audit_logs + login_attempts tables). The DB persistence was added 2026-06-23 after discovering audit events were only going to file logs. End-to-end verified: login failure → login_attempts table count increments.

### Database Path (Packaged Mode)

In packaged (Electron) mode, the SQLite database is stored at `%LOCALAPPDATA%\bumofu-assistance\data\rural_revitalization.db` — NOT the install directory (Program Files requires admin write). Electron main.js injects `DATABASE_URL` env var to backend.exe.

## Common Frontend Bug Patterns (Fixed 2026-07-05)

Three bug patterns were found across the codebase and batch-fixed. **When adding new views/API calls, verify these patterns are followed.**

### 1. `response.success` on raw AxiosResponse

**Bug**: Files using `import request/api from './request'` (raw axios) checked `response.success` — but `AxiosResponse` has no `.success` property (only the envelope body does). Silent `undefined` → no error thrown → code path skipped.

**Fix**: Use `response.data.success` (access the envelope body first). Affected files (6 fixed): `PackageVersion.vue`, `ConflictResolution.vue`, `Export.vue`, `Import.vue`, `MapTileManager.vue`.

**Rule**: 
- `import { get, post, apiRequest } from '@/api/request'` → returns auto-unwrapped `res.data` → use `response.success`
- `import request/api from './request'` → returns raw `AxiosResponse` → use `response.data.success`

### 2. `get()` params double-wrapping

**Bug**: `get(url, { params: { marker_type } })` is WRONG for the auto-unwrapped wrapper from `@/api/request`. The wrapper passes the 2nd arg directly as `params` to axios — nesting it under `params` again means the marker_type never reaches the backend.

**Fix**: Use `get(url, { marker_type })` (flat params as 2nd arg). Only raw `request.get()` uses `{ params: {...} }`.

**Rule**: ALL api files MUST use `{ get, post, apiRequest } from '@/api/request'`. NEVER `import api/request from './request'` (returns raw AxiosResponse). Blob downloads: API funcs must chain `.then(r => triggerDownload(r.data, name))` internally; callers just `await`, don't access `res.data`.

### 3. Pagination reset missing in list views

**Bug**: Create/edit/delete/import handlers called `loadData()`/`fetchData()` without first resetting pagination to page 1. If user was on page 2+, the new item was invisible (page 2 of a shorter result set = empty).

**Fix**: ALL list view create/edit/delete/import handlers MUST reset pagination to page 1 BEFORE calling `loadData`/`fetchData`:
```typescript
// ✅ Correct
const handleCreate = async () => {
  await createApi(payload)
  currentPage.value = 1   // ← reset BEFORE loadData
  await loadData()
}
// ❌ Wrong (omitted reset)
const handleCreate = async () => {
  await createApi(payload)
  await loadData()         // ← user stays on page 2, sees nothing
}
```
Fixed in 16 files (43 handler instances): `funds/{ContractManage,TransferVoucher,EnhancedList,AnomalyList}.vue`, `projects/{List,ProjectManagement}.vue`, `schools/List.vue`, `policies/List.vue`, `system/{UserManagement,TaskManager,UpdateLogs}.vue`, `dataPackage/{List,ReceivePackage}.vue`, `ruralWorks/Task.vue`, `organization/PassCodeManagement.vue`, `admin/MachineCodeManagement.vue`.

### 4. `router.push()` without error handling

**Bug**: Raw `router.push()` returns a Promise; if navigation is aborted (e.g., duplicate route) it throws `NavigationFailureType.aborted` — an unhandled rejection.

**Fix**: Use `pushSafe()` from `@/composables/useRouterSafe` (wraps `router.push` with try/catch + optional fallback to `window.location.href`). Fixed in 9 files: `analytics/map/index.vue`, `analytics/supported-villages/YearlyIndex.vue`, `auth/{ForgotPassword,LoginEnhanced}.vue`, `dashboard/{index,PageHeader}.vue`, `dataSync/{ConflictResolution,Import}.vue`, `funds/index.vue`.

**Rule**: `useRouterSafe()` MUST be called at Vue `<script setup>` top level (NOT inside event handlers — `inject()` only works during setup).

## Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/auth/login` | 5 | 60s |
| `/auth/register` | 3 | 60s |
| `/auth/refresh` | 10 | 60s |
| `/auth/csrf-token` | 30 | 60s |

Implementation: `app/core/security.py` → `check_rate_limit()` (sliding window, in-memory).
CSRF token rate limiting added in `app/api/v1/auth/auth.py` line ~509.

## CI Workflow Permissions

| Workflow | Explicit permissions | Rationale |
|----------|---------------------|-----------|
| `pr-checks.yml` | `contents: read`, `pull-requests: read` | Read-only; no releases |
| `build-arm64.yml` | `contents: write` | Needs write for `softprops/action-gh-release` |
| `build-windows.yml` | `contents: write` | Needs write for `electron-builder` + gh-release |

## Security Checklist (Military Audit Required)

Every new feature must verify:
1. [ ] Write operations call `write_work_log()`
2. [ ] Data queries use `filter_by_data_scope()`
3. [ ] Sensitive fields encrypted via `EncryptionService`
4. [ ] Frontend displays masked data via `DataMaskingService`
5. [ ] Errors logged (logger.error + audit log)

## Key Files Reference

| Purpose | Path |
|---------|------|
| Version number | `backend/app/core/config.py` → `Settings.PROJECT_VERSION` |
| DB schema source | `backend/app/models/` + `backend/alembic/versions/` |
| API router registry | `backend/app/api/v1/__init__.py` → `_BUSINESS_MODULES` |
| Envelope list helper | `backend/app/core/response.py` → `ok_list()` |
| Soft delete migration | `backend/alembic/versions/village_softdel_001_add_is_active.py` |
| Password policy | `backend/app/core/security.py` → `PasswordPolicy` class |
| Frontend HTTP client | `frontend/src/api/request.ts` |
| Safe router composable | `frontend/src/composables/useRouterSafe.ts` |
| Design tokens | `frontend/src/styles/tokens.scss` |
|贵州 region data | `frontend/src/data/guizhouRegion.ts` |
| Electron main | `electron/main.js` |
| PyInstaller spec | `backend/assistance-backend.spec` |
| NSIS hook | `build-scripts/electron-builder-nsis-hook.nsh` |
| CI pipeline | `.github/workflows/build-windows.yml` |
| ARM64 build | `.github/workflows/build-arm64.yml` + `docker/Dockerfile.kylin-standalone` |
