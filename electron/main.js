'use strict';

const { app, BrowserWindow, dialog, Menu, Tray, shell, ipcMain, safeStorage } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const crypto = require('crypto');
const http = require('http');
const fs = require('fs');

// ─── 全局变量 ───
let mainWindow = null;
let backendProcess = null;
let tray = null;
let isQuitting = false;
let backendRestartCount = 0;
const MAX_BACKEND_RESTARTS = 3;
const INTERNAL_BACKUP_KEY = crypto.randomBytes(16).toString('hex');
const INTERNAL_SHUTDOWN_KEY = crypto.randomBytes(16).toString('hex');

const DEFAULT_BACKEND_PORT = 8000;
const MAX_PORT_ATTEMPTS = 11; // 尝试 8000-8010
let backendPort = DEFAULT_BACKEND_PORT; // 动态分配的实际端口
const APP_TITLE = '帮扶管理系统';
const BACKEND_READY_TIMEOUT = 60000; // 60 秒启动超时（首次启动数据库创建可能需要较长时间）
const AUTO_BACKUP_INTERVAL = 24 * 60 * 60 * 1000; // 24 小时
const WINDOW_STATE_FILE = path.join(getUserDataPath(), 'window-state.json');
const SECRETS_FILE = path.join(getUserDataPath(), 'secrets.json');
const CRASH_LOG_FILE = path.join(getUserDataPath(), 'crash.log');

// 从 package.json 读取版本号，确保前后端版本一致
const appVersion = (() => {
  try {
    const pkgPath = app.isPackaged
      ? path.join(process.resourcesPath, '..', 'package.json')
      : path.join(__dirname, '..', 'package.json');
    return JSON.parse(fs.readFileSync(pkgPath, 'utf-8')).version || '1.4.1';
  } catch (_) {
    return '1.4.1';
  }
})();

// ─── 路径解析 ───

// 获取用户数据路径（运行源码时使用本地data目录，不污染AppData）
function getUserDataPath() {
  // 优先使用环境变量
  if (process.env.ELECTRON_USER_DATA_PATH) {
    return process.env.ELECTRON_USER_DATA_PATH;
  }
  // 运行源码时使用项目根目录下的 data 文件夹
  if (!app.isPackaged) {
    return path.join(__dirname, '..', 'data');
  }
  // 打包后使用默认 AppData 路径
  return app.getPath('userData');
}

function getResourcePath(...segments) {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, ...segments);
  }
  return path.join(__dirname, '..', ...segments);
}

function getBackendExePath() {
  const isWin = process.platform === 'win32';
  const isMac = process.platform === 'darwin';
  const exeName = isWin ? 'assistance-management-backend.exe' : 'assistance-management-backend';
  
  // 检测 ARM 架构
  const isArm64 = process.arch === 'arm64';
  
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend', exeName);
  }
  // 开发模式使用 dist 目录
  let platform;
  if (isWin) {
    platform = 'windows';
  } else if (isMac) {
    platform = isArm64 ? 'darwin-arm64' : 'darwin';
  } else {
    // Linux: 根据架构选择
    platform = isArm64 ? 'linux-arm64' : 'linux';
  }
  return path.join(__dirname, '..', 'dist', 'backend', platform, exeName);
}

function getFrontendPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'frontend');
  }
  return path.join(__dirname, '..', 'frontend', 'dist');
}

function getIconPath() {
  const iconName = process.platform === 'win32' ? 'app-circle.ico' : 'bz-circle.png';
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'icons', iconName);
  }
  return path.join(__dirname, '..', 'resources', 'icons', iconName);
}

// ─── 密钥持久化（优先使用 safeStorage 加密） ───
function getOrCreateSecrets() {
  const canEncrypt = safeStorage.isEncryptionAvailable();

  // 尝试读取已有密钥
  try {
    if (fs.existsSync(SECRETS_FILE)) {
      const raw = fs.readFileSync(SECRETS_FILE);
      let data;
      if (canEncrypt) {
        try {
          // 尝试解密（加密存储）
          const decrypted = safeStorage.decryptString(raw);
          data = JSON.parse(decrypted);
        } catch (_decryptErr) {
          // 可能是旧的明文格式，尝试直接解析后重新加密保存
          try {
            data = JSON.parse(raw.toString('utf-8'));
            // 迁移到加密格式
            _writeSecrets(data, true);
            console.log('[Secrets] 已将明文密钥迁移为加密存储');
          } catch (parseErr) {
            console.error('[Secrets] 密钥文件解析失败:', parseErr.message);
            data = {};
          }
        }
      } else {
        data = JSON.parse(raw.toString('utf-8'));
      }
      if (data.SECRET_KEY && data.CSRF_SECRET_KEY) {
        return data;
      }
    }
  } catch (e) {
    console.warn('[Secrets] 读取密钥文件失败，将重新生成:', e.message);
  }

  // 生成新密钥
  const secrets = {
    SECRET_KEY: crypto.randomBytes(32).toString('hex'),
    CSRF_SECRET_KEY: crypto.randomBytes(32).toString('hex'),
  };
  _writeSecrets(secrets, canEncrypt);
  return secrets;
}

function _writeSecrets(secrets, encrypt) {
  try {
    if (encrypt) {
      const encrypted = safeStorage.encryptString(JSON.stringify(secrets));
      fs.writeFileSync(SECRETS_FILE, encrypted);
      console.log('[Secrets] 密钥已加密并持久化');
    } else {
      fs.writeFileSync(SECRETS_FILE, JSON.stringify(secrets), 'utf-8');
      console.log('[Secrets] 密钥已持久化（明文回退，无可用密钥环）');
    }
  } catch (e) {
    console.error('[Secrets] 密钥持久化失败:', e.message);
  }
}

function getDatabasePath() {
  let dbDir;

  if (process.platform === 'linux') {
    // Linux: 使用家目录隐藏文件夹（麒麟V10权限兼容）
    const homeDir = process.env.HOME || '/root';
    dbDir = path.join(homeDir, '.bumofu', 'data');
  } else {
    const userDataPath = getUserDataPath();
    dbDir = path.join(userDataPath, 'database');
  }

  if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
  }

  const dbPath = path.join(dbDir, 'bumofu.db');

  // 首次运行: 从资源目录复制初始数据库
  if (!fs.existsSync(dbPath)) {
    const sourceDb = getResourcePath('database', 'bumofu.db');
    if (fs.existsSync(sourceDb)) {
      fs.copyFileSync(sourceDb, dbPath);
      console.log('[DB] 初始数据库已复制到用户目录');
    }
    // 兼容旧数据库名称
    const oldDbPath = path.join(dbDir, 'rural_revitalization.db');
    if (!fs.existsSync(dbPath) && fs.existsSync(oldDbPath)) {
      fs.copyFileSync(oldDbPath, dbPath);
      console.log('[DB] 已从旧数据库迁移');
    }
  }
  return dbPath;
}

// ─── 端口检测 ───
function checkPortInUse(port) {
  return new Promise((resolve) => {
    const net = require('net');
    const server = net.createServer();
    server.once('error', (err) => {
      if (err.code === 'EADDRINUSE') {
        resolve(true);
      } else {
        resolve(false);
      }
    });
    server.once('listening', () => {
      server.close();
      resolve(false);
    });
    server.listen(port, '127.0.0.1');
  });
}

function killProcessOnPort(port) {
  return new Promise((resolve) => {
    console.warn(`[Port] 正在强制终止占用端口 ${port} 的进程（taskkill /f / kill -9）`);
    writeDiagnosticLog(`强制终止端口 ${port} 的进程`);
    const onExit = () => { setTimeout(resolve, 500); };
    if (process.platform === 'win32') {
      const findProc = spawn('cmd.exe', ['/c', `for /f "tokens=5" %a in ('netstat -aon ^| findstr :${port} ^| findstr LISTENING') do taskkill /f /pid %a`], { windowsHide: true });
      findProc.on('exit', onExit);
    } else {
      const findProc = spawn('sh', ['-c', `lsof -ti:${port} | xargs kill -9 2>/dev/null`]);
      findProc.on('exit', onExit);
    }
  });
}

/**
 * 动态查找可用端口：从 startPort 开始依次尝试，返回第一个可用端口
 * 对默认端口（最先尝试的）会先试 kill 占用进程
 */
async function findAvailablePort(startPort, maxAttempts) {
  for (let i = 0; i < maxAttempts; i++) {
    const port = startPort + i;
    const inUse = await checkPortInUse(port);
    if (!inUse) {
      return port;
    }
    console.log(`[Port] 端口 ${port} 已被占用`);
    writeDiagnosticLog(`端口 ${port} 已被占用`);

    // 仅对默认端口尝试 kill 占用进程（可能是上次残留的后端进程）
    if (i === 0) {
      console.log(`[Port] 尝试释放端口 ${port}...`);
      await killProcessOnPort(port);
      const stillInUse = await checkPortInUse(port);
      if (!stillInUse) {
        return port;
      }
      console.log(`[Port] 端口 ${port} 释放失败，尝试备用端口...`);
    }
  }
  return null; // 所有端口均不可用
}

// ─── 启动错误分析 ───
function analyzeStartupError(stderrCapture, process) {
  const logs = stderrCapture.join('\n').toLowerCase();

  // 检查常见的错误模式
  if (logs.includes('vcruntime140') || logs.includes('msvcp140') || logs.includes('dll load failed')) {
    return '【缺少 Visual C++ 运行时库】\n\n系统缺少必要的运行库组件。\n\n解决方案：\n1. 尝试自动安装 VC++ Redistributable（安装包应该已包含）\n2. 或手动下载安装：https://aka.ms/vs/17/release/vc_redist.x64.exe';
  }

  if (logs.includes('address already in use') || logs.includes('eaddrinuse') || logs.includes('port')) {
    return '【端口被占用】\n\n端口 8000-8010 被其他程序占用。\n\n解决方案：\n1. 关闭占用端口的程序\n2. 重启电脑后再次尝试\n3. 或修改配置文件使用其他端口';
  }

  if (logs.includes('database') || logs.includes('sqlite') || logs.includes('locked')) {
    return '【数据库错误】\n\n数据库文件可能被损坏或锁定。\n\n解决方案：\n1. 关闭其他可能正在使用数据库的程序\n2. 删除用户数据目录下的数据库文件（会丢失数据）\n3. 或尝试从备份恢复';
  }

  if (logs.includes('permission denied') || logs.includes('eacces')) {
    return '【权限不足】\n\n程序没有足够的权限访问必要的文件或目录。\n\n解决方案：\n1. 以管理员身份运行程序\n2. 不要将程序安装在 C:\\Program Files 目录\n3. 检查用户数据目录的写入权限';
  }

  if (logs.includes('importerror') || logs.includes('modulenotfounderror')) {
    return '【后端程序损坏】\n\n后端程序缺少必要的模块。\n\n解决方案：\n1. 重新安装程序\n2. 确保安装包完整下载（文件大小应约 240MB）';
  }

  if (logs.includes('timeout') || stderrCapture.length === 0) {
    return '【后端启动超时】\n\n后端服务未能在规定时间内启动。\n\n可能原因：\n1. 系统资源不足（内存/CPU）\n2. 杀毒软件阻止了程序运行\n3. 后端程序损坏\n\n解决方案：\n1. 关闭杀毒软件后重试\n2. 重启电脑后再次尝试\n3. 重新安装程序';
  }

  return '【未知错误】\n\n后端启动过程中发生错误，但无法确定具体原因。\n\n建议：\n1. 查看诊断日志获取更多信息\n2. 重新安装程序\n3. 联系技术支持';
}

// ─── VC++ 运行时检查 (Windows) ───
function checkVCRuntime() {
  if (process.platform !== 'win32') return true;

  // 检查注册表中的 VC++ Redistributable
  try {
    const { execSync } = require('child_process');
    const result = execSync(
      'reg query "HKLM\\SOFTWARE\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\x64" /v Installed 2>nul',
      { encoding: 'utf-8', windowsHide: true, timeout: 5000 }
    );
    if (result.includes('0x1')) {
      console.log('[VCRuntime] VC++ Redistributable 已安装');
      return true;
    }
  } catch (_) {
    // 也检查 WOW6432Node
    try {
      const { execSync } = require('child_process');
      const result = execSync(
        'reg query "HKLM\\SOFTWARE\\WOW6432Node\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\x64" /v Installed 2>nul',
        { encoding: 'utf-8', windowsHide: true, timeout: 5000 }
      );
      if (result.includes('0x1')) {
        console.log('[VCRuntime] VC++ Redistributable 已安装 (WOW64)');
        return true;
      }
    } catch (_) {}
  }

  console.warn('[VCRuntime] 未检测到 VC++ Redistributable');
  writeDiagnosticLog('VC++ Redistributable 未检测到');
  return false;
}

/**
 * 尝试自动安装 VC++ Redistributable（从打包的 vcredist 目录）
 */
async function tryInstallVCRuntime() {
  const vcredistPath = getResourcePath('vcredist', 'vc_redist.x64.exe');
  if (!fs.existsSync(vcredistPath)) {
    console.warn('[VCRuntime] vcredist 安装文件不存在:', vcredistPath);
    return false;
  }

  console.log('[VCRuntime] 正在安装 VC++ Redistributable...');
  writeDiagnosticLog(`尝试安装 VC++ Redistributable: ${vcredistPath}`);

  return new Promise((resolve) => {
    const proc = spawn(vcredistPath, ['/install', '/quiet', '/norestart'], {
      windowsHide: true,
    });
    proc.on('exit', (code) => {
      if (code === 0 || code === 3010) {
        console.log('[VCRuntime] VC++ Redistributable 安装成功');
        writeDiagnosticLog('VC++ Redistributable 安装成功');
        resolve(true);
      } else {
        console.warn(`[VCRuntime] 安装返回代码: ${code}`);
        writeDiagnosticLog(`VC++ Redistributable 安装失败, code=${code}`);
        resolve(false);
      }
    });
    proc.on('error', (err) => {
      console.error('[VCRuntime] 安装执行失败:', err.message);
      resolve(false);
    });
  });
}

function writeDiagnosticLog(message) {
  try {
    const timestamp = new Date().toISOString();
    fs.appendFileSync(CRASH_LOG_FILE, `[${timestamp}] [DIAG] ${message}\n`);
  } catch (_) {}
}

// ─── 后端进程管理 ───
async function startBackend(stderrCapture = null) {
  const exePath = getBackendExePath();
  let lastStderrLines = [];  // 收集用于退出诊断（20条上限）
  console.log('[Backend] 启动路径:', exePath);
  writeDiagnosticLog(`后端启动路径: ${exePath}`);

  // 检查后端 exe 是否存在
  if (!fs.existsSync(exePath)) {
    const msg = `后端程序不存在:\n${exePath}`;
    console.error('[Backend]', msg);
    writeDiagnosticLog(`错误: ${msg}`);
    dialog.showErrorBox('启动失败', msg);
    app.quit();
    return null;
  }

  // 在 Windows 上检查必要的 DLL 文件是否存在
  if (process.platform === 'win32') {
    const backendDir = path.dirname(exePath);
    const requiredDlls = ['python311.dll', 'vcruntime140.dll'];
    const missingDlls = [];
    for (const dll of requiredDlls) {
      const dllPath = path.join(backendDir, dll);
      if (!fs.existsSync(dllPath)) {
        // 也检查系统目录
        const sysDir = process.env.SystemRoot || 'C:\\Windows';
        const sysDllPath = path.join(sysDir, 'System32', dll);
        if (!fs.existsSync(sysDllPath)) {
          missingDlls.push(dll);
        }
      }
    }
    if (missingDlls.length > 0) {
      console.warn(`[Backend] 可能缺少 DLL: ${missingDlls.join(', ')}`);
      writeDiagnosticLog(`警告: 可能缺少 DLL: ${missingDlls.join(', ')}`);
    }
  }

  // 检查后端 exe 文件完整性 (大小应 > 1MB)
  try {
    const exeStat = fs.statSync(exePath);
    const sizeMB = exeStat.size / (1024 * 1024);
    writeDiagnosticLog(`后端文件大小: ${sizeMB.toFixed(1)} MB`);
    if (exeStat.size < 1024 * 1024) {
      const msg = `后端程序文件异常（仅 ${sizeMB.toFixed(1)} MB），可能已损坏。\n请重新安装程序。`;
      console.error('[Backend]', msg);
      writeDiagnosticLog(`错误: ${msg}`);
      dialog.showErrorBox('文件异常', msg);
      app.quit();
      return null;
    }
  } catch (e) {
    writeDiagnosticLog(`检查后端文件失败: ${e.message}`);
  }

  // 动态查找可用端口
  const availablePort = await findAvailablePort(DEFAULT_BACKEND_PORT, MAX_PORT_ATTEMPTS);
  if (availablePort === null) {
    const msg = `端口 ${DEFAULT_BACKEND_PORT}-${DEFAULT_BACKEND_PORT + MAX_PORT_ATTEMPTS - 1} 均被占用。\n\n请关闭占用这些端口的程序后重试。`;
    writeDiagnosticLog(`错误: ${msg}`);
    dialog.showErrorBox('端口冲突', msg);
    app.quit();
    return null;
  }
  backendPort = availablePort;
  if (backendPort !== DEFAULT_BACKEND_PORT) {
    console.log(`[Backend] 默认端口 ${DEFAULT_BACKEND_PORT} 不可用，使用备用端口 ${backendPort}`);
    writeDiagnosticLog(`使用备用端口: ${backendPort}`);
  }

  const dbPath = getDatabasePath();
  const logsDir = path.join(getUserDataPath(), 'logs');
  const uploadsDir = path.join(getUserDataPath(), 'uploads');
  const cacheDir = path.join(getUserDataPath(), 'cache');
  const exportsDir = path.join(getUserDataPath(), 'exports');

  [logsDir, uploadsDir, cacheDir, exportsDir].forEach(dir => {
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  });

  const env = {
    ...process.env,
    PYTHONIOENCODING: 'utf-8',  // 防止 GBK 编码崩溃
    DATABASE_URL: `sqlite:///${dbPath}`,
    HOST: '127.0.0.1',
    PORT: String(backendPort),
    LOG_FILE: path.join(logsDir, 'app.log'),
    UPLOAD_DIR: uploadsDir,
    CACHE_DIR: cacheDir,
    EXPORT_DIR: exportsDir,
    FRONTEND_DIST_PATH: app.isPackaged
      ? getResourcePath('frontend')
      : getResourcePath('frontend', 'dist'),
    ENVIRONMENT: 'production',
    PROJECT_VERSION: appVersion,
    INTERNAL_BACKUP_KEY: INTERNAL_BACKUP_KEY,
    INTERNAL_SHUTDOWN_KEY: INTERNAL_SHUTDOWN_KEY,
    ...getOrCreateSecrets(),
  };

  // Linux ARM64: 设置 LD_LIBRARY_PATH 以加载 ARM64 动态链接库
  if (process.platform === 'linux') {
    const libPath = path.join(path.dirname(exePath), '..', 'lib');
    const existingLdPath = process.env.LD_LIBRARY_PATH || '';
    env.LD_LIBRARY_PATH = existingLdPath ? `${libPath}:${existingLdPath}` : libPath;
    console.log('[Backend] LD_LIBRARY_PATH:', env.LD_LIBRARY_PATH);
  }

  const proc = spawn(exePath, [], {
    cwd: path.dirname(exePath),
    env,
    stdio: ['ignore', 'pipe', 'pipe'],
    ...{ windowsHide: process.platform === 'win32' },
  });

  proc.stdout.on('data', (data) => {
    console.log('[Backend stdout]', data.toString().trim());
  });

  proc.stderr.on('data', (data) => {
    const text = data.toString().trim();
    if (!text) return;
    console.error('[Backend stderr]', text);

    // 收集到 lastStderrLines 用于退出时诊断（20条上限）
    lastStderrLines.push(text);
    if (lastStderrLines.length > 20) lastStderrLines.shift();

    // 追加写入崩溃日志
    try {
      fs.appendFileSync(CRASH_LOG_FILE, `[${new Date().toISOString()}] ${text}\n`);
    } catch (_) {}

    // 捕获到 stderrCapture 用于超时诊断（100条上限）
    if (stderrCapture) {
      stderrCapture.push(text);
      if (stderrCapture.length > 100) stderrCapture.shift();
    }
  });

  proc.on('error', (err) => {
    console.error('[Backend] 启动错误:', err);
    writeDiagnosticLog(`启动错误: ${err.message}`);

    // 解析常见错误并提供用户友好的提示
    let userMsg = err.message;
    if (err.code === 'ENOENT') {
      userMsg = `后端程序文件不存在或无法执行。\n请尝试重新安装程序。`;
    } else if (err.code === 'EACCES') {
      userMsg = `权限不足，无法启动后端服务。\n请以管理员身份运行本程序。`;
    }
    dialog.showErrorBox('后端启动失败', userMsg);
  });

  proc.on('exit', (code) => {
    console.log('[Backend] 进程退出, code:', code);
    writeDiagnosticLog(`后端进程退出, code: ${code}`);
    backendProcess = null;

    if (!isQuitting && code !== 0) {
      // 解析 stderr 中的关键错误模式
      const stderrJoined = lastStderrLines.join('\n');
      let diagnosis = '';
      if (/dll.*(not found|missing|load)/i.test(stderrJoined) || /ImportError|ModuleNotFoundError/i.test(stderrJoined)) {
        if (process.platform === 'win32') {
          diagnosis = '\n\n可能原因: 缺少系统运行库 (DLL) 或 Python 模块。\n建议安装 Visual C++ 2015-2022 Redistributable (x64)。';
        } else {
          diagnosis = '\n\n可能原因: 缺少系统运行库或 Python 模块。\n请执行: sudo apt-get install -f 修复依赖。';
        }
      } else if (/address.*in use|EADDRINUSE|port.*occupied/i.test(stderrJoined)) {
        diagnosis = `\n\n可能原因: 端口 ${backendPort} 被其他程序占用。\n请关闭占用该端口的程序后重试。`;
      } else if (/permission|access denied|EACCES/i.test(stderrJoined)) {
        diagnosis = '\n\n可能原因: 权限不足。\n请以管理员身份运行本程序。';
      } else if (/database.*locked|sqlite.*lock/i.test(stderrJoined)) {
        diagnosis = '\n\n可能原因: 数据库文件被锁定。\n请确保没有其他程序正在使用数据库。';
      }

      // 显示实际错误信息而非泛化猜测
      const stderrSnippet = stderrJoined.substring(0, 500);
      if (stderrSnippet && !diagnosis) {
        diagnosis = `\n\n后端错误信息:\n${stderrSnippet}`;
      }

      writeDiagnosticLog(`后端 stderr 末尾:\n${stderrJoined.substring(0, 2000)}`);

      // 自动重启逻辑
      if (backendRestartCount < MAX_BACKEND_RESTARTS) {
        backendRestartCount++;
        console.log(`[Backend] 尝试自动重启 (${backendRestartCount}/${MAX_BACKEND_RESTARTS})...`);
        writeDiagnosticLog(`自动重启 (${backendRestartCount}/${MAX_BACKEND_RESTARTS})`);
        setTimeout(async () => {
          const restartStderr = [];
          backendProcess = await startBackend(restartStderr);
        }, 2000);
      } else {
        const logPath = path.join(getUserDataPath(), 'logs', 'app.log');
        dialog.showErrorBox('后端异常退出',
          `后端进程已重启 ${MAX_BACKEND_RESTARTS} 次后仍然失败。${diagnosis}\n\n诊断日志: ${CRASH_LOG_FILE}\n应用日志: ${logPath}`);
      }
    }
  });

  return proc;
}

function stopBackend() {
  return new Promise((resolve) => {
    if (!backendProcess) {
      resolve();
      return;
    }
    console.log('[Backend] 正在优雅停止后端进程...');

    const pid = backendProcess.pid;
    let resolved = false;
    const done = () => {
      if (!resolved) {
        resolved = true;
        resolve();
      }
    };

    const forceKill = () => {
      try {
        if (process.platform === 'win32') {
          spawn('taskkill', ['/pid', String(pid), '/f', '/t'], { windowsHide: true });
        } else {
          process.kill(pid, 'SIGKILL');
        }
      } catch (_e) { /* 进程可能已退出 */ }
    };

    // 监听进程退出事件
    const proc = backendProcess;
    proc.once('exit', () => {
      backendProcess = null;
      done();
    });

    // 先尝试通过 API 优雅关闭（给后端 3 秒完成 WAL checkpoint）
    const req = http.request({
      hostname: '127.0.0.1',
      port: backendPort,
      path: '/api/v1/shutdown',
      method: 'POST',
      timeout: 3000,
      headers: {
        'X-Internal-Shutdown': INTERNAL_SHUTDOWN_KEY,
      },
    }, (res) => {
      console.log('[Backend] shutdown 响应:', res.statusCode);
      // 设置 3 秒超时后强制终止
      setTimeout(forceKill, 3000);
    });
    req.on('error', () => {
      console.warn('[Backend] 优雅关闭失败，强制终止');
      forceKill();
    });
    req.on('timeout', () => {
      req.destroy();
      forceKill();
    });
    req.end();

    // 安全超时：5秒后无论如何都resolve，防止永久挂起
    setTimeout(() => {
      backendProcess = null;
      done();
    }, 5000);
  });
}

function waitForBackend(stderrCapture = []) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    let checkCount = 0;

    function check() {
      const elapsed = Date.now() - startTime;
      checkCount++;

      // 每5秒记录一次日志（帮助诊断启动进度）
      if (elapsed % 5000 < 200 && elapsed > 0) {
        console.log(`[Backend] 等待后端就绪... ${(elapsed / 1000).toFixed(1)}s`);
      }

      if (elapsed > BACKEND_READY_TIMEOUT) {
        // 收集最近的 stderr 输出用于诊断
        const recentLogs = stderrCapture.slice(-10).join('\n');
        reject(new Error(`后端启动超时 (${(elapsed / 1000).toFixed(0)}秒)\n\n后端日志:\n${recentLogs || '无日志输出'}`));
        return;
      }

      const req = http.get(`http://127.0.0.1:${backendPort}/health`, (res) => {
        if (res.statusCode === 200) {
          console.log(`[Backend] 后端就绪，共耗时 ${(elapsed / 1000).toFixed(1)}s`);
          resolve();
        } else {
          setTimeout(check, 300);
        }
      });

      req.on('error', (err) => {
        // 只在调试模式下记录连接错误，避免日志过多
        if (checkCount <= 3 || elapsed > 10000) {
          console.log(`[Backend] 健康检查连接失败 (${(elapsed / 1000).toFixed(1)}s): ${err.message}`);
        }
        setTimeout(check, 300);
      });

      req.setTimeout(3000, () => {
        req.destroy();
        setTimeout(check, 300);
      });
    }

    // 首次延迟1秒后检查，给后端初始化时间
    setTimeout(check, 1000);
  });
}

// ─── 窗口状态持久化 ───
function loadWindowState() {
  try {
    if (fs.existsSync(WINDOW_STATE_FILE)) {
      return JSON.parse(fs.readFileSync(WINDOW_STATE_FILE, 'utf-8'));
    }
  } catch (e) {
    console.warn('[WindowState] 读取窗口状态失败:', e.message);
  }
  return null;
}

function saveWindowState() {
  if (!mainWindow) return;
  try {
    const bounds = mainWindow.getBounds();
    const isMaximized = mainWindow.isMaximized();
    fs.writeFileSync(WINDOW_STATE_FILE, JSON.stringify({ bounds, isMaximized }), 'utf-8');
  } catch (e) {
    console.warn('[WindowState] 保存窗口状态失败:', e.message);
  }
}

// ─── 窗口管理 ───
function createMainWindow() {
  const iconPath = getIconPath();
  const savedState = loadWindowState();

  const windowOptions = {
    width: savedState?.bounds?.width || 1400,
    height: savedState?.bounds?.height || 900,
    x: savedState?.bounds?.x,
    y: savedState?.bounds?.y,
    minWidth: 1024,
    minHeight: 768,
    title: APP_TITLE,
    icon: fs.existsSync(iconPath) ? iconPath : undefined,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true,
    },
    show: false,
    autoHideMenuBar: true,
  };

  mainWindow = new BrowserWindow(windowOptions);

  if (savedState?.isMaximized) {
    mainWindow.maximize();
  }

  // 加载后端服务页面（统一由后端托管前端静态资源）
  const frontendUrl = `http://127.0.0.1:${backendPort}`;
  mainWindow.loadURL(frontendUrl).catch((err) => {
    const msg = `无法加载应用页面：${frontendUrl}\n\n错误：${err?.message || err}`;
    console.error('[Window]', msg);
    writeDiagnosticLog(msg);
    dialog.showErrorBox('页面加载失败', `${msg}\n\n请检查后端是否已成功启动。`);
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
  });

  // 窗口状态持久化：在移动/缩放时保存（节流，避免频繁磁盘写入）
  let _saveStateTimer = null;
  function debouncedSaveWindowState() {
    clearTimeout(_saveStateTimer);
    _saveStateTimer = setTimeout(saveWindowState, 500);
  }
  mainWindow.on('resize', debouncedSaveWindowState);
  mainWindow.on('move', debouncedSaveWindowState);

  mainWindow.on('close', (e) => {
    saveWindowState();
    if (!isQuitting) {
      e.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // 渲染进程异常终止防护（GPU 崩溃、内存溢出等导致白屏时自动恢复）
  mainWindow.webContents.on('render-process-gone', (event, details) => {
    console.error('[Renderer] 渲染进程异常终止:', details.reason, 'exitCode:', details.exitCode);
    writeDiagnosticLog(`渲染进程异常终止: ${details.reason}, exitCode=${details.exitCode}`);
    dialog.showErrorBox('页面异常',
      `应用页面因 ${details.reason} 异常终止，请重启程序。\n\n如问题持续出现，请在启动时按住 Shift 键跳过恢复窗口。`);
  });

  // 外部链接在系统浏览器中打开
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

async function restartBackend() {
  await stopBackend();
  const restartStderr = [];
  try {
    backendProcess = await startBackend(restartStderr);
  } catch (e) {
    console.error('[Tray] restart failed:', e);
  }
}

// ─── 系统托盘 ───
function createTray() {
  const iconPath = getIconPath();
  if (!fs.existsSync(iconPath)) return;

  tray = new Tray(iconPath);
  const contextMenu = Menu.buildFromTemplate([
    { label: '显示主窗口', click: () => { if (mainWindow) { mainWindow.show(); mainWindow.focus(); } } },
    { type: 'separator' },
    { label: '立即备份', click: () => { performAutoBackup(); showTrayNotification('备份任务', '正在执行数据备份...'); } },
    { label: '重启后端', click: () => { restartBackend(); } },
    { type: 'separator' },
    { label: '退出', click: () => { isQuitting = true; app.quit(); } },
  ]);

  tray.setToolTip(APP_TITLE);
  tray.setContextMenu(contextMenu);
  tray.on('double-click', () => {
    if (mainWindow) { mainWindow.show(); mainWindow.focus(); }
  });
}

/**
 * 显示托盘通知（静默失败，避免影响主流程）
 */
function showTrayNotification(title, body) {
  try {
    const { Notification } = require('electron');
    if (Notification.isSupported()) {
      new Notification({ title: `${APP_TITLE} - ${title}`, body }).show();
    }
  } catch (_) { /* 通知不可用时静默 */ }
}

// ─── 应用生命周期 ───
app.whenReady().then(async () => {
  console.log('[App] 应用启动...');

  // 注册 IPC 处理器
  setupIpcHandlers();

  // VC++ 运行时预检（仅 Windows）：启动后端前确保 VC++ 已安装
  if (process.platform === 'win32') {
    if (!checkVCRuntime()) {
      console.log('[App] VC++ 未检测到，尝试自动安装...');
      const installed = await tryInstallVCRuntime();
      if (!installed) {
        const vcredistPath = getResourcePath('vcredist', 'vc_redist.x64.exe');
        const result = dialog.showMessageBoxSync({
          type: 'warning',
          title: '缺少运行环境',
          message: `未检测到 Visual C++ 运行时库，后端服务可能无法启动。\n\n请手动安装：\n${fs.existsSync(vcredistPath) ? vcredistPath : 'Visual C++ 2015-2022 Redistributable (x64)\nhttps://aka.ms/vs/17/release/vc_redist.x64.exe'}\n\n是否仍然继续启动？`,
          buttons: ['继续', '退出'],
          defaultId: 0,
        });
        if (result === 1) {
          isQuitting = true;
          app.quit();
          return;
        }
      }
    }
  } else {
    console.log(`[App] ${process.platform} 平台，跳过 VC++ 运行时检查`);
  }

  // 启动后端
  const stderrCapture = []; // 捕获后端 stderr 用于诊断
  backendProcess = await startBackend(stderrCapture);

  // 显示 splash screen
  let splashWin = null;
  try {
    const splashPath = path.join(__dirname, 'splash.html');
    if (fs.existsSync(splashPath)) {
      splashWin = new BrowserWindow({
        width: 400, height: 300,
        frame: false, transparent: true,
        alwaysOnTop: true, resizable: false,
        webPreferences: { nodeIntegration: false, contextIsolation: true },
      });
      splashWin.loadFile(splashPath);
      splashWin.center();
    }
  } catch (e) {
    console.warn('[Splash] 加载失败:', e.message);
  }

  try {
    console.log('[App] 等待后端就绪...');
    writeDiagnosticLog('等待后端就绪...');
    await waitForBackend(stderrCapture);
    console.log('[App] 后端已就绪');
    writeDiagnosticLog('后端已就绪');
    backendRestartCount = 0; // 成功启动后重置重启计数
  } catch (err) {
    console.error('[App] 后端启动失败:', err.message);
    writeDiagnosticLog(`后端启动失败: ${err.message}`);

    // 分析错误原因
    const errorAnalysis = analyzeStartupError(stderrCapture, backendProcess);
    const logPath = path.join(getUserDataPath(), 'logs', 'app.log');

    const result = dialog.showMessageBoxSync({
      type: 'error',
      title: '后端启动失败',
      message: `后端服务无法启动。\n\n${errorAnalysis}\n\n诊断日志: ${CRASH_LOG_FILE}\n应用日志: ${logPath}\n\n是否查看详细日志？`,
      buttons: ['退出程序', '查看日志', '继续（可能无法正常使用）'],
      defaultId: 0,
      cancelId: 0,
    });

    if (result === 0) {
      isQuitting = true;
      stopBackend();
      app.quit();
      return;
    } else if (result === 1) {
      // 显示详细日志
      const fullLogs = stderrCapture.join('\n') || '无后端日志输出';
      dialog.showMessageBoxSync({
        type: 'info',
        title: '后端启动日志',
        message: '后端启动过程中的输出日志：',
        detail: fullLogs.substring(0, 2000) + (fullLogs.length > 2000 ? '\n\n... (日志已截断)' : ''),
      });
      isQuitting = true;
      stopBackend();
      app.quit();
      return;
    }
    // result === 2: 继续，但可能无法正常使用
  }

  // 后端就绪后再创建主窗口、托盘、备份（减少启动时并行任务）
  createMainWindow();

  // 关闭 splash screen
  if (splashWin && !splashWin.isDestroyed()) {
    splashWin.close();
    splashWin = null;
  }

  // 延迟执行非关键启动任务
  createTray();
  startAutoBackup();
});

app.on('before-quit', () => {
  isQuitting = true;
  stopBackend();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    // 不退出，保留在托盘
  }
});

app.on('activate', () => {
  if (!mainWindow) {
    createMainWindow();
  } else {
    mainWindow.show();
  }
});

// Chromium 稳定性配置（必须在 app.whenReady() 之前执行，确保子进程继承）
// 根因：集成显卡/GPU 驱动与 Chromium 120 不兼容，导致 GPU 进程崩溃和缓存权限冲突
// 对策：完全禁用 GPU 加速，由 CPU 软渲染替代。本系统为数据管理应用，禁用后对用户体验无实质影响。
app.disableHardwareAcceleration();

// Windows 平台：禁用 CacheControl 避免缓存文件权限冲突；重定向 GPU 缓存到用户目录；禁用后台节流
if (process.platform === 'win32') {
  app.commandLine.appendSwitch('disable-features', 'CacheControl');
  const gpuCacheDir = path.join(getUserDataPath(), 'gpu-cache');
  if (!fs.existsSync(gpuCacheDir)) fs.mkdirSync(gpuCacheDir, { recursive: true });
  app.commandLine.appendSwitch('gpu-disk-cache-dir', gpuCacheDir);
  app.commandLine.appendSwitch('disable-background-timer-throttling');
}

// Linux：chrome-sandbox 需要 SUID 位才能启用 Chromium 沙箱。
// 打包脚本（deploy/kylin/DEBIAN/postinst）安装时已对 chrome-sandbox 执行
// `chmod 4755 && chown root:root`，普通用户正常启动无需 --no-sandbox。
// 仅当以 root 运行（部分嵌入式/定制环境）时回退禁用沙箱（root 下 SUID 无效），
// 并打印告警日志便于安全审计追溯。
if (process.platform === 'linux') {
  const isLinuxRoot = typeof process.getuid === 'function' && process.getuid() === 0;
  if (isLinuxRoot) {
    console.warn('[Main][security] 以 root 运行 Linux Electron，回退使用 --no-sandbox（chrome-sandbox SUID 在 root 下无效）。建议以普通用户运行以启用完整沙箱。');
    app.commandLine.appendSwitch('no-sandbox');
  }
  // 普通用户：不传 --no-sandbox，依赖 chrome-sandbox SUID 启用渲染进程沙箱
}

// 主进程级未捕获异常和 Promise 拒绝处理，防止底层错误导致白屏
process.on('uncaughtException', (err) => {
  console.error('[Main] 未捕获异常:', err);
  writeDiagnosticLog(`未捕获异常: ${err.message}\n${err.stack || ''}`);
});

process.on('unhandledRejection', (reason) => {
  console.error('[Main] 未处理的 Promise 拒绝:', reason);
  writeDiagnosticLog(`未处理的 Promise 拒绝: ${String(reason)}`);
});

// 单实例锁
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.show();
      mainWindow.focus();
    }
  });
}

// ─── IPC 处理器 ───
function setupIpcHandlers() {
  // 应用信息
  ipcMain.handle('get-app-version', () => { return appVersion; });
  ipcMain.handle('get-platform', () => process.platform);
  ipcMain.handle('get-user-data-path', () => getUserDataPath());

  // 窗口控制
  ipcMain.on('window-minimize', () => {
    if (mainWindow) mainWindow.minimize();
  });
  ipcMain.on('window-maximize', () => {
    if (mainWindow) {
      mainWindow.isMaximized() ? mainWindow.unmaximize() : mainWindow.maximize();
    }
  });
  ipcMain.on('window-close', () => {
    if (mainWindow) mainWindow.close();
  });

  // 文件对话框：保存文件
  ipcMain.handle('show-save-dialog', async (_event, options) => {
    if (!mainWindow) return { canceled: true };
    return dialog.showSaveDialog(mainWindow, options || {
      title: '保存文件',
      filters: [{ name: '所有文件', extensions: ['*'] }],
    });
  });

  // 文件对话框：打开文件
  ipcMain.handle('show-open-dialog', async (_event, options) => {
    if (!mainWindow) return { canceled: true };
    return dialog.showOpenDialog(mainWindow, options || {
      title: '选择文件',
      properties: ['openFile'],
    });
  });

  // 桌面通知
  ipcMain.handle('send-notification', (_event, title, body) => {
    showTrayNotification(title, body);
  });

  // 在系统文件管理器中打开目录
  ipcMain.handle('open-path', async (_event, targetPath) => {
    shell.openPath(targetPath);
  });

  // ── Worker Thread 任务（避免主进程阻塞）──
  const { workerPool } = require('./worker-pool');
  ipcMain.handle('worker-exec', async (_event, task, payload, timeout) => {
    try {
      const result = await workerPool.exec(task, payload, timeout);
      return { success: true, data: result };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });
  ipcMain.handle('worker-stats', () => workerPool.stats);

  // ── 大数据 IPC（通过流式传输避免序列化阻塞）──
  ipcMain.handle('read-file-chunked', async (_event, filePath, chunkSize) => {
    return new Promise((resolve) => {
      const chunks = [];
      const stream = fs.createReadStream(filePath, {
        highWaterMark: chunkSize || 256 * 1024,
        encoding: 'base64',
      });
      stream.on('data', (chunk) => chunks.push(chunk));
      stream.on('end', () => resolve({ data: chunks.join('') }));
      stream.on('error', () => resolve({ error: 'read-failed' }));
    });
  });

  // ── 窗口恢复修复：强制重绘避免白屏 ──
  ipcMain.on('window-force-redraw', () => {
    if (mainWindow) {
      mainWindow.webContents.invalidate();
      mainWindow.focus();
      mainWindow.webContents.focus();
    }
  });

  console.log('[IPC] 处理器注册完成');
}

// ─── 自动定期备份 ───
function startAutoBackup() {
  // 首次延迟 5 分钟后执行，避免启动时负载过高
  setTimeout(() => {
    performAutoBackup();
    // 此后每 24 小时执行一次
    setInterval(performAutoBackup, AUTO_BACKUP_INTERVAL);
  }, 5 * 60 * 1000);
  console.log('[AutoBackup] 自动备份已调度（首次将在5分钟后执行）');
}

function performAutoBackup() {
  const req = http.request({
    hostname: '127.0.0.1',
    port: backendPort,
    path: '/api/v1/system/backup',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Internal-Backup': INTERNAL_BACKUP_KEY,
    },
    timeout: 30000,
  }, (res) => {
    let body = '';
    res.on('data', (chunk) => { body += chunk; });
    res.on('end', () => {
      if (res.statusCode === 200 || res.statusCode === 201) {
        console.log('[AutoBackup] 自动备份成功');
        showTrayNotification('备份完成', '数据自动备份已成功完成');
        cleanupOldBackups();
      } else {
        console.warn(`[AutoBackup] 备份返回状态码 ${res.statusCode}:`, body.substring(0, 200));
      }
    });
  });
  req.on('error', (err) => {
    console.warn('[AutoBackup] 备份请求失败:', err.message);
  });
  req.write(JSON.stringify({ description: '自动定时备份' }));
  req.end();
}

function cleanupOldBackups() {
  // 调用后端接口获取备份列表，删除 7 天前的自动备份
  const req = http.get(`http://127.0.0.1:${backendPort}/api/v1/system/backup`, (res) => {
    let body = '';
    res.on('data', (chunk) => { body += chunk; });
    res.on('end', () => {
      try {
        const backups = JSON.parse(body);
        const sevenDaysAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
        for (const backup of backups) {
          const createdAt = new Date(backup.created_at).getTime();
          if (createdAt < sevenDaysAgo && backup.filename.startsWith('backup_')) {
            // 删除旧备份
            const delReq = http.request({
              hostname: '127.0.0.1',
              port: backendPort,
              path: `/api/v1/system/backup/${backup.filename}`,
              method: 'DELETE',
              timeout: 10000,
            }, (res) => {
              if (res.statusCode >= 400) {
                console.warn(`[AutoBackup] 删除旧备份 ${backup.filename} 返回状态码 ${res.statusCode}`);
              }
            });
            delReq.on('error', (err) => {
              console.warn(`[AutoBackup] 删除旧备份 ${backup.filename} 失败:`, err.message);
            });
            delReq.end();
            console.log(`[AutoBackup] 清理旧备份: ${backup.filename}`);
          }
        }
      } catch (e) {
        console.warn('[AutoBackup] 清理旧备份失败:', e.message);
      }
    });
  });
  req.on('error', (err) => {
    console.warn('[AutoBackup] 获取备份列表失败:', err.message);
  });
}
