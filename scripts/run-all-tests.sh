#!/bin/bash
set -e

echo "================================"
echo "军队乡村振兴管理系统 - 全面测试"
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# 后端测试
echo -e "\n${YELLOW}>>> 运行后端测试...${NC}"
cd backend

# 安装依赖（如果需要）
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# 安装依赖
pip install -e . > /dev/null 2>&1 || pip install -r requirements.txt > /dev/null 2>&1

# 运行单元测试
echo "运行后端单元测试..."
if pytest tests/unit/ -v --tb=short --cov=app --cov-report=term-missing 2>&1; then
    echo -e "${GREEN}✓ 后端单元测试通过${NC}"
else
    echo -e "${RED}✗ 后端单元测试失败${NC}"
    FAILED=1
fi

# 运行集成测试
echo "运行后端集成测试..."
if pytest tests/integration/ -v --tb=short 2>&1; then
    echo -e "${GREEN}✓ 后端集成测试通过${NC}"
else
    echo -e "${RED}✗ 后端集成测试失败${NC}"
    FAILED=1
fi

# 检查覆盖率
echo "检查后端覆盖率..."
COVERAGE=$(pytest --cov=app --cov-report=term-missing 2>&1 | grep "TOTAL" | awk '{print $4}' | sed 's/%//')
echo -e "后端覆盖率: ${COVERAGE}%"

if [ -z "$COVERAGE" ] || [ "$(echo "$COVERAGE < 100" | bc -l 2>/dev/null || echo "0")" = "1" ]; then
    echo -e "${RED}✗ 后端覆盖率未达到 100%${NC}"
    FAILED=1
else
    echo -e "${GREEN}✓ 后端覆盖率达到 100%${NC}"
fi

cd ..

# 前端测试
echo -e "\n${YELLOW}>>> 运行前端测试...${NC}"
cd frontend

# 安装依赖
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm ci > /dev/null 2>&1
fi

# 运行单元测试
echo "运行前端单元测试..."
if npm run test:run 2>&1; then
    echo -e "${GREEN}✓ 前端单元测试通过${NC}"
else
    echo -e "${RED}✗ 前端单元测试失败${NC}"
    FAILED=1
fi

# 检查覆盖率
if [ -f "coverage/coverage-summary.json" ]; then
    COVERAGE_JSON=$(cat coverage/coverage-summary.json 2>/dev/null || echo '{}')
    LINE_COVERAGE=$(echo $COVERAGE_JSON | jq -r '.total.lines.pct // 0')
    echo -e "前端行覆盖率: ${LINE_COVERAGE}%"

    if [ "$(echo "$LINE_COVERAGE < 100" | bc -l 2>/dev/null || echo "0")" = "1" ]; then
        echo -e "${RED}✗ 前端覆盖率未达到 100%${NC}"
        FAILED=1
    else
        echo -e "${GREEN}✓ 前端覆盖率达到 100%${NC}"
    fi
fi

cd ..

# E2E测试（可选，需要环境变量 RUN_E2E=true）
if [ "$RUN_E2E" = "true" ]; then
    echo -e "\n${YELLOW}>>> 运行 E2E 测试...${NC}"
    cd frontend

    if npm run test:e2e 2>&1; then
        echo -e "${GREEN}✓ E2E 测试通过${NC}"
    else
        echo -e "${RED}✗ E2E 测试失败${NC}"
        FAILED=1
    fi

    cd ..
fi

# 安全扫描（可选）
if [ "$RUN_SECURITY" = "true" ]; then
    echo -e "\n${YELLOW}>>> 运行安全扫描...${NC}"
    cd backend

    # bandit 安全扫描
    if command -v bandit &> /dev/null; then
        if bandit -r app/ -f json -o bandit-report.json 2>/dev/null || true; then
            echo -e "${GREEN}✓ Bandit 安全扫描完成${NC}"
        else
            echo -e "${RED}✗ Bandit 发现安全问题${NC}"
            FAILED=1
        fi
    fi

    # safety 依赖漏洞扫描
    if command -v safety &> /dev/null; then
        if safety check 2>/dev/null || true; then
            echo -e "${GREEN}✓ Safety 依赖扫描完成${NC}"
        else
            echo -e "${YELLOW}⚠ Safety 发现依赖问题${NC}"
        fi
    fi

    cd ..
fi

# 最终结果
echo -e "\n================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}所有测试通过，可以打包部署！${NC}"
    exit 0
else
    echo -e "${RED}测试失败，请修复后再部署！${NC}"
    exit 1
fi
