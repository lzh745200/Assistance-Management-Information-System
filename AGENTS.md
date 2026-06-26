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
python -m pytest tests/ -v --tb=short -q --timeout=60  # Run all tests (~2300)
python -m pytest tests/unit/test_xxx.py -v              # Run single test file
python -m flake8 app/ --max-line-length=120             # Lint (CI gate)
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
| Bare | `{total, page, page_size, items}` | `/supported-villages`, `/funds`, `/work-logs` |
| Envelope | `{code:200, data:{...}, message:"成功"}` | `/auth/login`, `/users`, `/rbac` |

Frontend stores use `_unwrapList()` / `_unwrapSingle()` to normalize both. When adding new endpoints, pick one format consistently.

### Data Isolation

- `organization_id` field is **mandatory** on all queries
- Use `filter_by_data_scope(query, model, user, db=db)` from `app/core/data_permission.py`
- Missing this = security vulnerability (military audit will fail)

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
npm run electron:build           # Build for current platform
npm run electron:build:win       # Windows NSIS installer
```

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

### Frontend 404 on Static Files

After `npm run build`, run `scripts/build/sync-frontend-dist.sh` to sync. Browser cache may need clearing.

### ARM64 Build: Never Use --no-cache

`build-arm64.yml` uses Docker buildx with QEMU (ARM64 emulation on x86 CI runners). Docker layer caching is the only reason builds finish in ~30min instead of hours. Never add `--no-cache` to the `docker buildx build` command.

### Dockerfile Output Truncation (Intentional)

`Dockerfile.kylin-standalone` pipes RUN commands through `tail -N` (npm ci: `-5`, build: `-10`, pip: `-10`, pyinstaller: `-20`) to keep CI logs manageable. Downstream `test -f`/`test -d` commands in the same stage still catch failures. Don't remove `tail` pipes.

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
| Frontend HTTP client | `frontend/src/api/request.ts` |
| Design tokens | `frontend/src/styles/tokens.scss` |
|贵州 region data | `frontend/src/data/guizhouRegion.ts` |
| Electron main | `electron/main.js` |
| CI pipeline | `.github/workflows/ci-cd.yml` |
| ARM64 build | `.github/workflows/build-arm64.yml` + `docker/Dockerfile.kylin-standalone` |
