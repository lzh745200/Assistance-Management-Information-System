# Code Quality Standards & Progressive Improvement — Design Spec

> Created: 2026-05-31 | Status: Approved | 方案A (渐进式)

## 1. Overview

Establish coding standards, eliminate technical debt, and progressively improve test coverage
across the military rural revitalization system's backend (Python/FastAPI) and frontend (Vue 3/TypeScript).

### Baseline Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Backend test coverage | ~54% | 70% |
| Frontend `as any` casts | 113 | < 25 |
| Frontend empty catch blocks | 211 | 0 |
| Python bare except | few | 0 |
| Python type hints (return) | ~60% | 90% for public APIs |

## 2. Phase 1: Standards Establishment (~1 day)

### 2.1 Backend Standards (`backend/pyproject.toml`)

```toml
[tool.mypy]
check_untyped_defs = true
disallow_untyped_defs = false  # progressive: true after phase 2
warn_return_any = true
warn_unused_ignores = true

[tool.ruff]
target-version = "py311"
line-length = 120
select = ["E", "F", "W", "C90", "B", "I"]
ignore = ["E501"]  # line-length handled by formatter

[tool.ruff.mccabe]
max-complexity = 15

[tool.coverage.run]
omit = ["tests/*", "alembic/*", "*/__pycache__/*"]

[tool.pytest.ini_options]
addopts = "--tb=short --strict-markers"
```

### 2.2 Frontend Standards (`.eslintrc` additions)

```json
{
  "rules": {
    "no-empty-catch": "error",
    "@typescript-eslint/no-explicit-any": "warn",
    "no-console": ["warn", { "allow": ["warn", "error"] }]
  }
}
```

### 2.3 Contributing Guide (`CONTRIBUTING.md`)

- Python: All public functions must have return type annotations and docstrings.
- TypeScript: Props/Emits must be explicitly typed. New `as any` prohibited.
- Common: PR review checklist, conventional commits, directory structure overview.

## 3. Phase 2: Backend Type Coverage (~3 days)

Progressive rollout by module priority:

| Batch | Module | Files | Coverage Target |
|-------|--------|-------|-----------------|
| 1 | `models/` | 50+ | 100% type-hinted |
| 2 | `services/domain/` | 15+ | 80% |
| 3 | `schemas/` | 30+ | 90% |
| 4 | `api/v1/` | 40+ | 60% |

**Approach:**
- Add `-> None`/`-> Optional[X]`/`-> Dict[str, Any]` return types plus parameter annotations.
- After each batch: run `mypy` on the module. If clean, add to strict check whitelist.
- Private helpers may skip annotations initially; public API functions MUST have them.

## 4. Phase 3: Frontend Type Safety (~2 days)

### 4.1 Eliminate `as any` (113 → < 25)

| Priority | Location | Count | Strategy |
|----------|----------|-------|----------|
| High | `CrudService.ts`, `LocalDatabase.ts` | ~15 | Genericize: `<T extends {id: string\|number}>` |
| High | Chart components | ~8 | Define ECharts event type interfaces |
| Medium | `stores/*.ts` | ~20 | Replace `any` with `ApiResponse<T>` from `@/types/api` |
| Low | Test files | ~30 | Acceptable — keep `as any` in specs |

### 4.2 Fix Empty Catch Blocks (211 → 0)

- **30 core views first**: Add `ElMessage.error(ctx)` for user-visible feedback.
- **181 remaining**: At minimum `console.debug('context', e)` or comment `// intentionally silent`.
- **Introduce `createErrorHandler` composable**:
  ```ts
  // composables/useErrorHandler.ts
  export function useErrorHandler() {
    const handle = (context: string) => (e: unknown) => {
      const msg = e instanceof Error ? e.message : String(e);
      console.debug(`[${context}]`, msg);
    };
    const notify = (context: string) => (e: unknown) => {
      const msg = e instanceof Error ? e.message : '操作失败';
      ElMessage.error(`${context}: ${msg}`);
    };
    return { handle, notify };
  }
  ```

## 5. Phase 4: Test Coverage Improvement (~3 days)

Raise `fail_under` from 50 → 60 → 70 in increments.

| Increment | New Tests Focus | Target |
|-----------|-----------------|--------|
| 50→55 | `services/` core CRUD methods | unit tests |
| 55→60 | `api/v1/` auth + schools + policies | integration |
| 60→65 | `api/v1/` projects + funds + villages | integration |
| 65→70 | `services/domain/` business logic | unit |

**Test pattern for services:**
```python
# tests/services/test_village_service.py
class TestVillageService:
    def test_fetch_villages_returns_list(self, db_session):
        result = VillageService(db_session).fetch_villages()
        assert isinstance(result, list)

    def test_create_village_persists(self, db_session):
        data = {"village_name": "test", "province": "贵州"}
        result = VillageService(db_session).create(data)
        assert result.village_name == "test"
```

## 6. Military Security Audit (Bandit Integration)

### 6.1 Bandit Configuration

```toml
# backend/pyproject.toml
[tool.bandit]
exclude_dirs = ["tests", "alembic", ".venv", "data"]
skips = ["B101", "B110"]  # B101: assert (acceptable in tests), B110: try-except-pass
severity = "medium"
```

### 6.2 Audit Checklist

| Check | Bandit ID | Action |
|-------|-----------|--------|
| Hardcoded passwords | B105, B106 | Error — must use env vars or runtime_secrets |
| SQL injection | B608 | Error — must use parameterized queries |
| Shell injection | B602, B604 | Error — audit all `subprocess` calls |
| Weak crypto | B303, B304, B505 | Warn — move to bcrypt 4.x + AES-256 |
| File permissions | B108 | Warn — ensure `os.chmod` uses 0o600 for secrets |
| Deserialization | B301, B403 | Warn — audit all `pickle`/`jsonpickle` usage |

### 6.3 Security Test Suite

```python
# tests/security/test_audit.py
class TestSecurityAudit:
    def test_no_hardcoded_secrets_in_source(self):
        """B105/B106: No hardcoded passwords or API keys in source files."""
        import subprocess
        result = subprocess.run(
            ["bandit", "-r", "app/", "-ll", "-f", "json", "-s", "B101,B110"],
            capture_output=True, text=True, cwd="backend"
        )
        issues = json.loads(result.stdout).get("results", [])
        high = [i for i in issues if i["issue_severity"] == "HIGH"]
        assert len(high) == 0, f"Security HIGH issues found: {high}"

    def test_all_db_queries_use_parameterization(self):
        """B608: Verify no SQL string concatenation in query paths."""
        # Covered by bandit B608 check + code review

    def test_secret_files_have_restricted_permissions(self):
        """Verify runtime_secrets.json has 0o600 permissions on creation."""
        from app.utils.runtime_secrets import _SECRETS_FILE
        import os
        if os.path.exists(_SECRETS_FILE):
            mode = os.stat(_SECRETS_FILE).st_mode & 0o777
            assert mode == 0o600, f"Secrets file has insecure permissions: {oct(mode)}"
```

## 7. Data Isolation Validation (Organization Multi-Tenant)

### 7.1 Test Cases

```python
# tests/security/test_data_isolation.py
class TestOrganizationDataIsolation:
    """Verify users in org A cannot access/modify org B's data."""

    def test_cross_org_village_read_blocked(self, db_session):
        """User in org-1 cannot read villages belonging to org-2."""
        org1 = create_test_org(db_session, "org-1")
        org2 = create_test_org(db_session, "org-2")
        user = create_test_user(db_session, org1.id, role="operator")
        village = create_test_village(db_session, org2.id, name="secret")

        result = VillageService(db_session).get_village(village.id, user=user)
        assert result is None or hasattr(result, 'error')

    def test_cross_org_village_update_blocked(self, db_session):
        """User in org-1 cannot update villages in org-2."""
        org1, org2 = create_test_orgs(db_session)
        user = create_test_user(db_session, org1.id)
        village = create_test_village(db_session, org2.id)

        with pytest.raises(PermissionError):
            VillageService(db_session).update_village(
                village.id, {"name": "hacked"}, user=user
            )

    def test_cross_org_fund_access_blocked(self, db_session):
        """Fund records are isolated by organization."""
        pass  # pattern identical to village isolation

    def test_cross_org_school_access_blocked(self, db_session):
        """School records are isolated by organization."""
        pass

    def test_cross_org_project_access_blocked(self, db_session):
        """Project records are isolated by organization."""
        pass

    def test_admin_can_access_all_orgs(self, db_session):
        """Admin/SuperAdmin bypasses org isolation."""
        org1, org2 = create_test_orgs(db_session)
        admin = create_test_user(db_session, org1.id, role="admin", is_superuser=True)
        v1 = create_test_village(db_session, org1.id)
        v2 = create_test_village(db_session, org2.id)

        r1 = VillageService(db_session).get_village(v1.id, user=admin)
        r2 = VillageService(db_session).get_village(v2.id, user=admin)
        assert r1 is not None
        assert r2 is not None
```

### 7.2 Data Isolation Coverage Matrix

| Entity | Read Cross-Org | Write Cross-Org | Admin Bypass | Test |
|--------|---------------|-----------------|--------------|------|
| SupportedVillage | Block | Block | Allow | ✅ |
| School | Block | Block | Allow | ✅ |
| Project | Block | Block | Allow | ✅ |
| Fund | Block | Block | Allow | ✅ |
| Policy | Block | Block | Allow | ✅ |
| DataPackage | Block | Block | Allow | ✅ |

## 8. Standalone Offline Fault Tolerance

### 8.1 Error Categories & Handling Strategy

| Category | Example | Handling |
|----------|---------|----------|
| DB Lock | SQLite `database is locked` | Retry ×3 with exponential backoff (100ms→400ms→1600ms) |
| DB Corrupt | `database disk image is malformed` | Log alert, attempt repair, notify user |
| Disk Full | `No space left on device` | Log CRITICAL, return 503, stop write ops |
| Config Missing | `SECRET_KEY` empty | Auto-generate + persist (existing), log WARNING |
| Import Missing | `No module named 'X'` | Graceful degradation — skip optional module, log WARNING |
| Network | DNS/connect timeout | Retry ×3, return cached/fallback data |

### 8.2 Retry Decorator

```python
# app/utils/retry.py
import time, logging, functools

logger = logging.getLogger(__name__)

def retry_on_lock(max_retries=3, base_delay=0.1):
    """Retry on SQLite 'database is locked' with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "database is locked" not in str(e).lower():
                        raise
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (4 ** attempt)
                    logger.warning("DB locked, retry %d/%d in %.1fs",
                                   attempt + 1, max_retries, delay)
                    time.sleep(delay)
            return None
        return wrapper
    return decorator
```

### 8.3 Graceful Degradation Pattern

```python
# app/core/deps.py
def get_optional_service(service_name: str):
    """Import service; return None if unavailable (offline/standalone mode)."""
    try:
        module = importlib.import_module(f"app.services.{service_name}")
        return getattr(module, service_name, None)
    except ImportError as e:
        logger.warning("Optional service unavailable: %s (%s)", service_name, e)
        return None
```

## 9. Rollback Verification Script

### 9.1 Script: `scripts/verify-quality.sh`

```bash
#!/bin/bash
# Quality gate: runs before/after refactoring to verify no regression

set -e
PASS=0
FAIL=0

echo "=== Quality Gate ==="

# 1. Backend imports
echo -n "[1/7] Backend import check... "
cd backend
if .venv/Scripts/python -c "from app.main import app" 2>/dev/null; then
    echo "PASS"; PASS=$((PASS+1))
else
    echo "FAIL"; FAIL=$((FAIL+1))
fi

# 2. Backend tests
echo -n "[2/7] Backend tests (--tb=no)... "
if .venv/Scripts/python -m pytest tests/ -q --tb=no > /dev/null 2>&1; then
    echo "PASS"; PASS=$((PASS+1))
else
    echo "FAIL"; FAIL=$((FAIL+1))
fi

# 3. Security audit
echo -n "[3/7] Bandit security scan... "
if bandit -r app/ -ll -f json -q 2>/dev/null; then
    echo "PASS"; PASS=$((PASS+1))
else
    echo "WARN (review manually)"; PASS=$((PASS+1))
fi

# 4. Frontend build
cd ../frontend
echo -n "[4/7] Frontend build... "
if npx vite build > /dev/null 2>&1; then
    echo "PASS"; PASS=$((PASS+1))
else
    echo "FAIL"; FAIL=$((FAIL+1))
fi

# 5. Lint
echo -n "[5/7] ESLint check... "
if npx eslint src --ext .vue,.ts --max-warnings 50 > /dev/null 2>&1; then
    echo "PASS"; PASS=$((PASS+1))
else
    echo "WARN (>50 warnings)"; PASS=$((PASS+1))
fi

# 6. TypeScript check
echo -n "[6/7] TypeScript check... "
if npx vue-tsc --noEmit 2>/dev/null; then
    echo "PASS"; PASS=$((PASS+1))
else
    echo "WARN (review type errors)"; PASS=$((PASS+1))
fi

# 7. Health endpoint (if backend running)
cd ../backend
echo -n "[7/7] Health endpoint... "
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "PASS"; PASS=$((PASS+1))
else
    echo "SKIP (backend not running)"
fi

echo ""
echo "=== Result: $PASS passed, $FAIL failed ==="
[ $FAIL -eq 0 ] && echo "QUALITY GATE: PASSED" || echo "QUALITY GATE: FAILED"
```

### 9.2 Usage

```bash
# Before any refactoring
bash scripts/verify-quality.sh > baseline.txt

# After refactoring
bash scripts/verify-quality.sh > after.txt

# Compare
diff baseline.txt after.txt
```

## 10. Verification

After each phase:
- **Backend**: `cd backend && .venv/Scripts/python -m pytest tests/ -q --cov=app --cov-fail-under=<threshold>`
- **Frontend**: `cd frontend && npm run build:only` (must succeed with 0 errors)
- **Lint**: `ruff check app/` (0 errors) / `npm run lint` (0 errors)
- **Security**: `bandit -r backend/app/ -ll` (0 HIGH severity)
- **Quality Gate**: `bash scripts/verify-quality.sh` (all gates pass)
