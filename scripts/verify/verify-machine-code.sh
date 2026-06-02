#!/bin/bash
# 机器码系统完整验证脚本

echo "=========================================="
echo "机器码系统完整验证"
echo "=========================================="
echo ""

# 1. 检查后端服务
echo "1. 检查后端服务..."
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "   ✓ 后端服务运行正常"
else
    echo "   ✗ 后端服务未运行"
    exit 1
fi
echo ""

# 2. 获取机器码
echo "2. 获取机器码..."
MACHINE_CODE_RESPONSE=$(curl -s http://localhost:8000/api/v1/machine-code/get-machine-code)
MACHINE_CODE=$(echo $MACHINE_CODE_RESPONSE | grep -o '"machine_code":"[^"]*"' | cut -d'"' -f4)
VERIFICATION_CODE=$(echo $MACHINE_CODE_RESPONSE | grep -o '"verification_code":"[^"]*"' | cut -d'"' -f4)

if [ -n "$MACHINE_CODE" ]; then
    echo "   ✓ 机器码: ${MACHINE_CODE:0:30}..."
    echo "   ✓ 校验码: $VERIFICATION_CODE"
else
    echo "   ✗ 获取机器码失败"
    exit 1
fi
echo ""

# 3. 登录获取 Token
echo "3. 管理员登录..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"Admin@123456"}')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo "   ✓ 登录成功"
else
    echo "   ✗ 登录失败"
    echo "   响应: $LOGIN_RESPONSE"
    exit 1
fi
echo ""

# 4. 查询机器码列表
echo "4. 查询机器码列表..."
LIST_RESPONSE=$(curl -s http://localhost:8000/api/v1/machine-code/admin/list \
    -H "Authorization: Bearer $TOKEN")

TOTAL=$(echo $LIST_RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)
PASS_CODE=$(echo $LIST_RESPONSE | grep -o '"pass_code":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ "$TOTAL" -gt 0 ]; then
    echo "   ✓ 找到 $TOTAL 条机器码记录"
    echo "   ✓ 通行码: $PASS_CODE"
else
    echo "   ✗ 没有找到机器码记录"
    exit 1
fi
echo ""

# 5. 验证机器码
echo "5. 验证机器码和通行码..."
VERIFY_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/machine-code/verify-machine-code \
    -H "Content-Type: application/json" \
    -d "{\"machine_code\":\"$MACHINE_CODE\",\"pass_code\":\"$PASS_CODE\",\"verification_code\":\"$VERIFICATION_CODE\"}")

IS_VALID=$(echo $VERIFY_RESPONSE | grep -o '"is_valid":true')

if [ -n "$IS_VALID" ]; then
    echo "   ✓ 验证成功"
else
    echo "   ✗ 验证失败"
    echo "   响应: $VERIFY_RESPONSE"
    exit 1
fi
echo ""

echo "=========================================="
echo "✓ 所有测试通过！"
echo "=========================================="
echo ""
echo "系统信息："
echo "  机器码: ${MACHINE_CODE:0:30}..."
echo "  校验码: $VERIFICATION_CODE"
echo "  通行码: $PASS_CODE"
echo "  状态: 活动"
echo ""
echo "您现在可以："
echo "  1. 使用 admin/Admin@123456 登录系统"
echo "  2. 在机器码管理页面查看活动的机器码"
echo "  3. 使用机器码和通行码注册新用户"
echo ""
