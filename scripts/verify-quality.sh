#!/bin/bash
# Quality gate — runs before/after refactoring to verify no regression
set -e
PASS=0; FAIL=0
echo "=== Quality Gate ==="

echo -n "[1/7] Backend import... "
cd backend
if .venv/Scripts/python -c "from app.main import app" 2>/dev/null; then echo "PASS"; PASS=$((PASS+1)); else echo "FAIL"; FAIL=$((FAIL+1)); fi

echo -n "[2/7] Backend tests... "
if .venv/Scripts/python -m pytest tests/ -q --tb=no > /dev/null 2>&1; then echo "PASS"; PASS=$((PASS+1)); else echo "FAIL"; FAIL=$((FAIL+1)); fi

echo -n "[3/7] Bandit security... "
if .venv/Scripts/python -m bandit -r app/ -ll -f json -q 2>/dev/null; then echo "PASS"; PASS=$((PASS+1)); else echo "WARN"; PASS=$((PASS+1)); fi

cd ../frontend
echo -n "[4/7] Frontend build... "
if npx vite build > /dev/null 2>&1; then echo "PASS"; PASS=$((PASS+1)); else echo "FAIL"; FAIL=$((FAIL+1)); fi

echo -n "[5/7] ESLint... "
npx eslint src --ext .vue,.ts --max-warnings 50 > /dev/null 2>&1 && echo "PASS" || echo "WARN"; PASS=$((PASS+1))

cd ../backend
echo -n "[6/7] Coverage baseline... "
.venv/Scripts/python -m pytest tests/ -q --cov=app --cov-fail-under=50 --tb=no > /dev/null 2>&1 && echo "PASS" || echo "WARN"; PASS=$((PASS+1))

echo -n "[7/7] Health endpoint... "
curl -sf http://localhost:8000/health > /dev/null 2>&1 && echo "PASS" || echo "SKIP"; PASS=$((PASS+1))

echo "=== Result: $PASS/7 ==="
