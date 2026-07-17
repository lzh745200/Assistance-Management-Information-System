# AGENTS.md - Agent Quick Reference

## Project Identity

Assistance Management Information System (帮扶管理信息系统) - Offline-first desktop app for military-civilian rural aid.
FastAPI + Vue 3 + Electron + SQLite. Windows primary, Linux ARM64 (Kylin V10) secondary.

**Full context**: See `CLAUDE.md` and `.cursorrules` for architecture details, API formats, and security requirements.

## Quick Commands

### Backend

```bash
cd backend
.venv\\Scripts\\python start.py                          # Start server (http://localhost:8000)
python -m pytest tests/ -v --tb=short -q --timeout=60   # Run all tests (8890+)
python -m pytest tests/unit/test_xxx.py -v              # Run single test file
python -m flake8 app/ --max-line-length=120             # Lint (CI gate, 0 errors)
python -m mypy app/ --config-file=mypy.ini --ignore-missing-imports  # Type check (non-blocking)
python -m bandit -r app/ -ll                            # Security scan
```

### Frontend

```bash
cd frontend
npm run dev                                             # Dev server (http://localhost:5173)
npm run test -- --run                                   # Run all tests (1681, 137 test files)
npx vitest run src/views/xxx/xxx.test.ts               # Run single test file
npm run lint                                            # ESLint (CI gate, --max-warnings=0)
npx vue-tsc --noEmit                                    # Type check (CI gate)
npm run build                                           # Production build
npx lint-staged                                         # Lint only git-staged *.vue/*.ts/*.tsx files
```

### Combined

```bash
make test           # Run backend + frontend tests
make test-backend   # Backend tests only
make test-frontend  # Frontend tests only
make deploy-check   # Full pre-deploy validation
make clean          # Clean test artifacts
```

### Docker E2E Tests

```bash
# Playwright browser-based E2E (uses docker/docker-compose.e2e.yml)
docker compose -f docker-compose.yml -f docker/docker-compose.e2e.yml --profile e2e up

# Locust performance testing
docker compose -f docker-compose.yml -f docker/docker-compose.e2e.yml --profile performance up

# Full E2E + performance
docker compose -f docker-compose.yml -f docker/docker-compose.e2e.yml --profile full up
```

## Architecture Gotchas

### Dual API Response Format

The API uses **two response formats** - this causes most integration bugs:

| Format | Shape | Used by |
|--------|-------|---------|
| Bare | `{total, page, page_size, items}` | 0 endpoints (all converted to envelope) |
| Envelope | `{code:200, data:{...}, message:"成功"}` | `/auth/login`, `/users`, `/rbac`, `/supported-villages`, `/funds`, `/projects`, `/schools` |

**Unification progress (2026-07-05)**: 4 main list endpoints (`supported-villages`, `funds`, `projects`, `schools`) converted from bare → envelope via `ok_list()` helper in `backend/app/core/response.py`:
```python
def ok_list(items, total, page=1, page_size=20, message="成功", **kwargs):
    return success_response(data={"items": items, "total": total, ...}, message=message, **kwargs)
```
When adding new list endpoints, **use `ok_list()`** (envelope) — not bare dict.

Frontend stores use `_unwrapList()` / `_unwrapSingle()` to normalize both. The Axios response interceptor auto-expands `data.data` fields to top level of `response.data`, making envelope format transparent to frontend stores.

**Unification progress (2026-07-08)**: All list endpoints now use `ok_list()` (envelope). Previously bare-format endpoints converted: `/machine-codes`, `/pass-codes`, `/system/backup`, `/system/update-logs`, `/reports/templates`, `/funds/contracts`, `/funds/transfers`, `/funds/anomalies`, `/users` (list + pending), `/projects/{id}/funds`, `/projects/{id}/tasks`, `/data/reports/villages`, `/data/reports/subscriptions`, `/data/data-reports/pending`, `/data/data-reports/received`. Earlier conversions (2026-07-05): `/work-logs`, `/scholarship-students`, `/rural-works`, `/policies`, `/organizations`, `/audit-logs`, `/operation-logs`, `/data-sync/*`, `/import-export/*`, `/map/*`.

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
- Nightly: 50% (`.github/workflows/nightly-full.yml`)
- Test env vars: `ENVIRONMENT=test`, `SECRET_KEY=test-secret-key-for-ci`

### Frontend Coverage

- Vitest with V8 coverage provider
- Coverage thresholds in `vitest.config.ts`

### Codecov Integration

Coverage is uploaded to Codecov via `codecov/codecov-action@v4` in two workflows:
- **PR Checks** (`.github/workflows/pr-checks.yml`): Shows coverage diff on each pull request
- **Nightly Full** (`.github/workflows/nightly-full.yml`): Uploads with `backend-nightly` / `frontend-nightly` flags for trend tracking

### Pre-commit Hooks (Staged Strategy)

Installed via `pre-commit install`. Uses a two-stage strategy defined in `.pre-commit-config.yaml`:

| Stage | Hooks | Scope |
|-------|-------|-------|
| **pre-commit** | ruff (Python lint+fix, line-length=120), trailing-whitespace, YAML/JSON validation, Dockerfile tail check | Changed files only (fast) |
| **pre-push** | flake8, bandit (security scan), vue-tsc (frontend type check) | Full project (quality gate) |

All stage-2 hooks are orchestrated through `scripts/pre_commit_hooks.py`.

**lint-staged** (`frontend/package.json` `"lint-staged"` config): Runs `eslint --fix` only on git-staged `*.vue`, `*.ts`, `*.tsx` files. Use `npx lint-staged` before committing frontend changes to catch issues early.

### Docker E2E Testing

`docker/docker-compose.e2e.yml` provides two optional service profiles:

- **e2e**: Playwright-based browser automation (`mcr.microsoft.com/playwright:v1.45.0-jammy`), runs `tests/e2e/test_e2e.py`
- **performance**: Locust load testing (`locustio/locust:2.28`), runs `tests/performance/locustfile.py`

Both depend on `assistance-system` service with `condition: service_healthy`. Use `--profile e2e|performance|full` to select.

## Transaction Management (with_transaction Refactoring)

`backend/app/core/transaction.py` provides 6 convenience functions for transaction control:

| Function | Type | Purpose |
|----------|------|---------|
| `transaction(db)` | Context manager | Basic transaction, auto commit/rollback |
| `transactional` | Decorator | Auto-detect db param or create new session |
| `with_transaction(isolation_level, readonly)` | Decorator | Isolation levels (READ COMMITTED/REPEATABLE READ/SERIALIZABLE) + read-only mode |
| `nested_transaction(db)` | Context manager | Nested transaction via savepoints |
| `savepoint(db, name)` | Context manager | Named savepoint, independently rollback-able |
| `retry_on_deadlock(max_retries)` | Decorator | Deadlock auto-retry (default 3 attempts) |

Isolation levels are validated at decorator definition time via a whitelist (`_VALID_ISOLATION_LEVELS`) to prevent SQL injection.

Also includes `BatchOperation` class with `batch_insert` / `batch_update` / `batch_delete` (1000 records/batch).

## Build Pipeline

### Frontend Build

```bash
cd frontend && npm run build  # Outputs to frontend/dist/
```

**Sass**: v1.101.0 with modern-compiler API (`vite.config.ts` → `css.preprocessorOptions.scss.api: 'modern-compiler'`). Significantly faster compilation.

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

## CI Workflows

### PR Checks (`.github/workflows/pr-checks.yml`)

Triggered on every PR. Runs backend tests, frontend tests, flake8, and uploads coverage to Codecov.

### Nightly Full (`.github/workflows/nightly-full.yml`)

Scheduled daily at 2:00 UTC + manual trigger (`workflow_dispatch`). Three jobs:
- `backend-full`: Full test suite with HTML/JSON coverage + JUnit XML + Codecov upload
- `frontend-full`: Full test suite with coverage + Codecov upload
- `quality-report`: Aggregated pass/fail summary artifact (depends on both)

### CI Workflow Permissions

| Workflow | Explicit permissions | Rationale |
|----------|---------------------|-----------|
| `pr-checks.yml` | `contents: read`, `pull-requests: read` | Read-only; no releases |
| `build-arm64.yml` | `contents: write` | Needs write for `softprops/action-gh-release` |
| `build-windows.yml` | `contents: write` | Needs write for `electron-builder` + gh-release |
| `nightly-full.yml` | `contents: read` | Read-only; artifacts only |

## Migration Management

### Baseline Consolidation

`backend/alembic/versions/012_consolidate_baseline.py` consolidates early scattered migration scripts into a single baseline migration, reducing the Alembic migration chain length for faster new-environment initialization.

## Known Issues & Fixes

### Pytest Config Conflict (Fixed 2026-07-15)

Previously, both `pytest.ini` and `pyproject.toml` had `[tool.pytest.ini_options]` sections, causing pytest to warn: `WARNING: ignoring pytest config in pyproject.toml!`. Fixed by consolidating all pytest config into `pytest.ini` and removing the `[tool.pytest.ini_options]` section from `pyproject.toml`. The `pyproject.toml` now only retains `[tool.coverage.*]` sections.

### Misplaced `safe_commit` Import (Fixed 2026-07-15)

A previous automated edit inserted `from app.core.transaction import safe_commit` at wrong indentation levels inside 20+ API files, causing `SyntaxError`/`IndentationError` in 11 route modules. All instances have been removed — the import belongs at module top-level (already present in most files) or should use `safe_commit(db)` at call site without a local import.

### `with_transaction` Missing Return (Fixed 2026-07-15)

`_execute_in_transaction()` in `app/core/transaction.py` was missing `return` before `_execute_with_existing_session()` call, causing all `@with_transaction`-decorated functions with an existing session to return `None`. Fixed by adding the missing `return` statement.

### `pytest.skip()` Removal (Fixed 2026-07-15)

Removed all 3 `pytest.skip()` calls in `test_comprehensive_coverage.py` — tests now fail on import errors instead of silently skipping. Also updated `SCHEMA_FILES` list to reference actual existing schema modules.

### WinError 10054 (Connection Reset)

Auto-fixed by `app/utils/win_proactor_fix.py`. Loaded by `start.py` and `main.py`. No action needed.

> **v1.2.0 Logger Fix**: The logger in `win_proactor_fix.py` was refactored to use `logging.getLogger(__name__)` at module level with defensive instantiation, avoiding `KeyError` / `"No section: 'formatters'"` errors that occurred when the logging system wasn't yet initialized during early module import.

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

In packaged (Electron) mode, the SQLite database is stored at `%LOCALAPPDATA%\\bumofu-assistance\\data\\rural_revitalization.db` — NOT the install directory (Program Files requires admin write). Electron main.js injects `DATABASE_URL` env var to backend.exe.

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

## Test-Writing Conventions (Added 2026-07-17)

The 2026-07 coverage sprint introduced **244 failing tests** written against assumed APIs. These conventions prevent recurrence.

### Frontend (vitest)

1. **Mock ALL named exports the source imports**: `vi.mock('@/api/request')` must return every named export the module under test imports (`get`/`post`/`put`/`del`/`apiRequest`), plus `default` if the source uses it, plus `parseContentDisposition`/`downloadBlob` when `src/api/helpers/blobDownload.ts` is in the import chain. Missing export → `No "X" export is defined on the mock`. Define mock fns via `vi.hoisted`.
2. **Helpers return the unwrapped body**: `get/post/put/del/apiRequest` auto-unwrap the envelope — `mockResolvedValue(body)` NOT `mockResolvedValue({ data: body })`.
3. **`get(url, params)` takes params directly** (2nd arg), NOT axios-style `{ params: {...} }`. Assert `toHaveBeenCalledWith(url, { page: 1 })`.
4. **Never mock `@/utils/request`** — the module does not exist.
5. **Blob downloads** go through `downloadBlobAsFile`: mock `downloadBlob` and assert it received `(Blob, filename)` instead of spying on DOM anchor clicks.

### Backend (pytest)

6. **List endpoints return the `ok_list()` envelope**: assert `resp.json()["data"]["total"]`, never `resp.json()["total"]`.
7. **`dependency_overrides` is app-global**: two fixtures overriding `get_current_user` cannot be used in the same test (last one wins for BOTH). Switch identity explicitly per phase inside one test with try/finally restore (see `test_security_data_isolation.py`).
8. **Data scope semantics** (`get_data_scope`): role `user` → OWN (own records only); `admin`/`manager`/`approval_leader` → OWN_DEPT; `super_admin` → ALL. Write `check_record_access` assertions accordingly.
9. **Verify model class names** against `app/models/` before importing in tests (e.g., `TeaPlantation` not `Industry`, `FundStatusHistory` not `FundHistory`, `Issue` not `IssueTracking`).
10. **No leaked threads/timers in tests**: functions submitted to the global executor must finish in ≤2s even when testing timeouts (a `sleep(100)` leaked thread once hung the whole suite at 18%).
11. **No module-level `os.environ` mutation** in test files — use a `monkeypatch` fixture (`monkeypatch.setattr` on the target module constant).
12. **Before `mock.patch(target)`, confirm the attribute exists** on the current source module (refactors rename things; stale patch targets fail with AttributeError).

## Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/auth/login` | 5 | 60s |
| `/auth/register` | 3 | 60s |
| `/auth/refresh` | 10 | 60s |
| `/auth/csrf-token` | 30 | 60s |

Implementation: `app/core/security.py` → `check_rate_limit()` (sliding window, in-memory).
CSRF token rate limiting added in `app/api/v1/auth/auth.py` line ~509.

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
| Version number | `backend/app/core/config.py` → `Settings.PROJECT_VERSION` (v1.2.0) |
| DB schema source | `backend/app/models/` + `backend/alembic/versions/` |
| Baseline migration | `backend/alembic/versions/012_consolidate_baseline.py` |
| API router registry | `backend/app/api/v1/__init__.py` → `_BUSINESS_MODULES` |
| Envelope list helper | `backend/app/core/response.py` → `ok_list()` |
| Transaction utilities | `backend/app/core/transaction.py` (6 helper functions) |
| Soft delete migration | `backend/alembic/versions/village_softdel_001_add_is_active.py` |
| Password policy | `backend/app/core/security.py` → `PasswordPolicy` class |
| Frontend HTTP client | `frontend/src/api/request.ts` |
| Safe router composable | `frontend/src/composables/useRouterSafe.ts` |
| Design tokens | `frontend/src/styles/tokens.scss` |
| lint-staged config | `frontend/package.json` → `"lint-staged"` |
| Pre-commit config | `.pre-commit-config.yaml` (staged strategy: pre-commit + pre-push) |
| E2E Docker compose | `docker/docker-compose.e2e.yml` |
| Guizhou region data | `frontend/src/data/guizhouRegion.ts` |
| Electron main | `electron/main.js` |
| PyInstaller spec | `backend/assistance-backend.spec` |
| NSIS hook | `build-scripts/electron-builder-nsis-hook.nsh` |
| CI pipeline | `.github/workflows/build-windows.yml` |
| ARM64 build | `.github/workflows/build-arm64.yml` + `docker/Dockerfile.kylin-standalone` |
| PR checks | `.github/workflows/pr-checks.yml` |
| Nightly CI | `.github/workflows/nightly-full.yml` |
| WinError 10054 fix | `backend/app/utils/win_proactor_fix.py` |
