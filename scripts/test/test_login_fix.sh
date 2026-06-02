#!/bin/bash
# 401 登录错误测试脚本

echo "=========================================="
echo "测试 401 登录错误修复"
echo "=========================================="
echo ""

# 测试后端登录接口
echo "1. 测试后端登录接口..."
response=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@2026"}' \
  -w "\nHTTP_CODE:%{http_code}")

http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)

if [ "$http_code" = "200" ]; then
  echo "✅ 后端登录接口正常 (HTTP 200)"
else
  echo "❌ 后端登录接口异常 (HTTP $http_code)"
  echo "$response"
  exit 1
fi

echo ""
echo "2. 测试带过期 token 的登录请求..."
expired_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTYwMDAwMDAwMH0.fake"
response=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $expired_token" \
  -d '{"username":"admin","password":"Admin@2026"}' \
  -w "\nHTTP_CODE:%{http_code}")

http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)

if [ "$http_code" = "200" ]; then
  echo "✅ 登录接口忽略了过期 token，正常返回 (HTTP 200)"
else
  echo "⚠️  登录接口返回 HTTP $http_code"
  echo "   这可能表示后端对登录接口也进行了 token 验证"
fi

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
echo ""
echo "如果测试失败，请执行以下步骤："
echo "1. 访问 http://localhost:5173/clear-auth.html 清除缓存"
echo "2. 或在浏览器控制台执行："
echo "   sessionStorage.clear(); localStorage.clear(); location.reload();"
echo "3. 重新登录"
