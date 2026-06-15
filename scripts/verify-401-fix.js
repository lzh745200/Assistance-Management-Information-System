/**
 * 401修复验证测试脚本
 * 使用 Node.js 直接测试API交互和token刷新逻辑
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

// 测试配置
const config = {
  backendUrl: 'http://localhost:8000',
  testTimeout: 30000
};

// 检查结果
const results = {
  passed: 0,
  failed: 0,
  tests: []
};

function addTest(name, passed, details = '') {
  results.tests.push({ name, passed, details });
  if (passed) results.passed++;
  else results.failed++;
}

// 检查文件修改
async function checkCodeChanges() {
  log('\n==========================================', 'cyan');
  log('检查401修复代码修改', 'cyan');
  log('==========================================\n', 'cyan');

  const projectRoot = path.resolve(__dirname, '..');

  // 检查 guards.ts
  const guardsPath = path.join(projectRoot, 'frontend', 'src', 'router', 'guards.ts');
  if (fs.existsSync(guardsPath)) {
    const content = fs.readFileSync(guardsPath, 'utf-8');

    // 检查 ADMIN_ROLES 常量
    if (content.includes('ADMIN_ROLES')) {
      log('✓ guards.ts: ADMIN_ROLES 常量已定义', 'green');
      addTest('ADMIN_ROLES 常量', true);
    } else {
      log('✗ guards.ts: ADMIN_ROLES 常量缺失', 'red');
      addTest('ADMIN_ROLES 常量', false, '未找到 ADMIN_ROLES 定义');
    }

    // 检查缓存优化
    if (content.includes('cachedAuthInfo')) {
      log('✓ guards.ts: 认证信息缓存已添加', 'green');
      addTest('认证信息缓存', true);
    } else {
      log('✗ guards.ts: 认证信息缓存缺失', 'red');
      addTest('认证信息缓存', false, '未找到 cachedAuthInfo');
    }

    // 检查迁移优化
    if (content.includes('migrationChecked')) {
      log('✓ guards.ts: 迁移检查优化已添加', 'green');
      addTest('迁移检查优化', true);
    } else {
      log('✗ guards.ts: 迁移检查优化缺失', 'red');
      addTest('迁移检查优化', false, '未找到 migrationChecked');
    }
  } else {
    log('✗ guards.ts 文件不存在', 'red');
    addTest('guards.ts 存在', false, '文件未找到');
  }

  // 检查 auth.ts
  const authPath = path.join(projectRoot, 'frontend', 'src', 'stores', 'auth.ts');
  if (fs.existsSync(authPath)) {
    const content = fs.readFileSync(authPath, 'utf-8');

    // 检查全局锁
    if (content.includes('isRefreshing') && content.includes('refreshPromise')) {
      log('✓ auth.ts: 全局刷新锁已添加', 'green');
      addTest('全局刷新锁', true);
    } else {
      log('✗ auth.ts: 全局刷新锁缺失', 'red');
      addTest('全局刷新锁', false, '未找到 isRefreshing/refreshPromise');
    }

    // 检查预防性刷新
    if (content.includes('scheduleTokenRefresh')) {
      log('✓ auth.ts: 预防性token刷新已添加', 'green');
      addTest('预防性token刷新', true);
    } else {
      log('✗ auth.ts: 预防性token刷新缺失', 'red');
      addTest('预防性token刷新', false);
    }
  }

  // 检查 jwt.ts
  const jwtPath = path.join(projectRoot, 'frontend', 'src', 'utils', 'jwt.ts');
  if (fs.existsSync(jwtPath)) {
    log('✓ jwt.ts: JWT工具文件存在', 'green');
    addTest('jwt.ts 存在', true);

    const content = fs.readFileSync(jwtPath, 'utf-8');
    if (content.includes('MAX_TIMEOUT_MS')) {
      log('✓ jwt.ts: setTimeout安全限制已添加', 'green');
      addTest('setTimeout安全限制', true);
    }
  } else {
    log('✗ jwt.ts 文件不存在', 'red');
    addTest('jwt.ts 存在', false);
  }

  // 检查 request.ts
  const requestPath = path.join(projectRoot, 'frontend', 'src', 'api', 'request.ts');
  if (fs.existsSync(requestPath)) {
    const content = fs.readFileSync(requestPath, 'utf-8');

    if (content.includes('tryRefreshToken') && content.includes('failedQueue')) {
      log('✓ request.ts: Token刷新队列已添加', 'green');
      addTest('Token刷新队列', true);
    } else {
      log('✗ request.ts: Token刷新队列缺失', 'red');
      addTest('Token刷新队列', false);
    }
  }
}

// 测试后端API可用性
async function testBackendAPI() {
  log('\n==========================================', 'cyan');
  log('测试后端API可用性', 'cyan');
  log('==========================================\n', 'cyan');

  return new Promise((resolve) => {
    const req = http.get(`${config.backendUrl}/api/v1/health`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          log('✓ 后端健康检查通过', 'green');
          addTest('后端健康检查', true);
          try {
            const health = JSON.parse(data);
            log(`  状态: ${health.status || 'unknown'}`, 'blue');
          } catch (e) {}
        } else {
          log(`✗ 后端健康检查失败: ${res.statusCode}`, 'red');
          addTest('后端健康检查', false, `状态码: ${res.statusCode}`);
        }
        resolve();
      });
    });

    req.on('error', (err) => {
      log(`✗ 后端连接失败: ${err.message}`, 'red');
      log('  请确保后端服务已启动: python -m uvicorn app.main:app --port 8000', 'yellow');
      addTest('后端健康检查', false, err.message);
      resolve();
    });

    req.setTimeout(5000, () => {
      req.abort();
      log('✗ 后端连接超时', 'red');
      addTest('后端健康检查', false, '连接超时');
      resolve();
    });
  });
}

// 测试登录和Token机制
async function testLoginFlow() {
  log('\n==========================================', 'cyan');
  log('测试登录和Token机制', 'cyan');
  log('==========================================\n', 'cyan');

  const testCredentials = {
    username: 'admin',
    password: 'admin123'
  };

  return new Promise((resolve) => {
    const postData = JSON.stringify(testCredentials);

    const options = {
      hostname: 'localhost',
      port: 8000,
      path: '/api/v1/auth/login',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            const response = JSON.parse(data);
            if (response.data?.access_token || response.access_token) {
              log('✓ 登录API正常工作', 'green');
              addTest('登录API', true);

              // 检查响应结构
              const token = response.data?.access_token || response.access_token;
              log(`  Token长度: ${token.length}`, 'blue');

              // 验证token格式 (JWT)
              const parts = token.split('.');
              if (parts.length === 3) {
                log('✓ Token格式正确 (JWT)', 'green');
                addTest('JWT Token格式', true);

                // 解析payload检查过期时间
                try {
                  const payload = JSON.parse(Buffer.from(parts[1], 'base64url').toString());
                  if (payload.exp) {
                    const expiry = new Date(payload.exp * 1000);
                    log(`  Token过期时间: ${expiry.toLocaleString()}`, 'blue');
                    addTest('Token过期时间', true);
                  }
                } catch (e) {
                  log('  无法解析Token payload', 'yellow');
                }
              } else {
                log('✗ Token格式不正确', 'red');
                addTest('JWT Token格式', false);
              }
            } else {
              log('✗ 登录响应缺少token', 'red');
              addTest('登录API', false, '响应缺少token');
            }
          } catch (e) {
            log('✗ 登录响应解析失败', 'red');
            addTest('登录API', false, e.message);
          }
        } else if (res.statusCode === 401) {
          log('⚠ 登录认证失败 (401) - 检查测试账号', 'yellow');
          addTest('登录API', false, '认证失败，检查账号');
        } else {
          log(`✗ 登录请求失败: ${res.statusCode}`, 'red');
          addTest('登录API', false, `状态码: ${res.statusCode}`);
        }
        resolve();
      });
    });

    req.on('error', (err) => {
      log(`✗ 登录请求失败: ${err.message}`, 'red');
      addTest('登录API', false, err.message);
      resolve();
    });

    req.write(postData);
    req.end();
  });
}

// 测试受保护端点的401处理
async function testProtectedEndpoint() {
  log('\n==========================================', 'cyan');
  log('测试受保护端点401响应', 'cyan');
  log('==========================================\n', 'cyan');

  return new Promise((resolve) => {
    const options = {
      hostname: 'localhost',
      port: 8000,
      path: '/api/v1/auth/me',
      method: 'GET',
      headers: {
        'Authorization': 'Bearer invalid_token_xyz'
      }
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 401) {
          log('✓ 无效Token正确返回401', 'green');
          addTest('401错误处理', true);

          // 检查是否有WWW-Authenticate头
          if (res.headers['www-authenticate']) {
            log('  包含WWW-Authenticate头', 'blue');
          }
        } else {
          log(`⚠ 预期401，实际返回: ${res.statusCode}`, 'yellow');
          addTest('401错误处理', false, `实际状态码: ${res.statusCode}`);
        }
        resolve();
      });
    });

    req.on('error', (err) => {
      log(`✗ 请求失败: ${err.message}`, 'red');
      addTest('401错误处理', false, err.message);
      resolve();
    });

    req.setTimeout(5000, () => {
      req.abort();
      log('✗ 请求超时', 'red');
      addTest('401错误处理', false, '请求超时');
      resolve();
    });

    req.end();
  });
}

// 打印测试报告
function printReport() {
  log('\n==========================================', 'cyan');
  log('测试报告', 'cyan');
  log('==========================================\n', 'cyan');

  const total = results.passed + results.failed;
  const passRate = total > 0 ? Math.round((results.passed / total) * 100) : 0;

  log(`总测试数: ${total}`, 'blue');
  log(`通过: ${results.passed}`, 'green');
  log(`失败: ${results.failed}`, results.failed > 0 ? 'red' : 'green');
  log(`通过率: ${passRate}%`, passRate >= 80 ? 'green' : passRate >= 50 ? 'yellow' : 'red');

  if (results.failed > 0) {
    log('\n失败的测试:', 'red');
    results.tests
      .filter(t => !t.passed)
      .forEach(t => {
        log(`  ✗ ${t.name}`, 'red');
        if (t.details) log(`    ${t.details}`, 'yellow');
      });
  }

  log('\n==========================================', 'cyan');

  if (passRate === 100) {
    log('✓ 所有检查通过！401修复验证成功。', 'green');
  } else if (passRate >= 80) {
    log('⚠ 大部分检查通过，但有一些警告。', 'yellow');
  } else {
    log('✗ 检查未通过，请修复上述问题。', 'red');
  }

  log('==========================================\n', 'cyan');

  return results.failed === 0;
}

// 主函数
async function main() {
  log('\n');
  log('╔══════════════════════════════════════════════════════════╗', 'cyan');
  log('║     帮扶管理信息系统 - 401修复验证工具              ║', 'cyan');
  log('╚══════════════════════════════════════════════════════════╝', 'cyan');
  log('\n');

  try {
    // 1. 检查代码修改
    await checkCodeChanges();

    // 2. 测试后端API（如果后端运行中）
    await testBackendAPI();

    // 3. 测试登录流程
    await testLoginFlow();

    // 4. 测试401处理
    await testProtectedEndpoint();

  } catch (err) {
    log(`\n执行错误: ${err.message}`, 'red');
    console.error(err);
  }

  // 打印报告
  const success = printReport();

  // 返回退出码
  process.exit(success ? 0 : 1);
}

main();
