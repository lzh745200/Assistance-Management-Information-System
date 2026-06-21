'use strict';

const { app, BrowserWindow, dialog, Menu, Tray, shell, ipcMain, safeStorage } = require('electron');
const path = require('path');
const { spawn, execSync } = require('child_process');
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
const MAX_PORT_ATTEMPTS = 11;
let backendPort = DEFAULT_BACKEND_PORT;
const APP_TITLE = '帮扶管理系统';
const BACKEND_READY_TIMEOUT = 60000;
const AUTO_BACKUP_INTERVAL = 24 * 60 * 60 * 1000;
const WINDOW_STATE_FILE = path.join(getUserDataPath(), 'window-state.json');
const SECRETS_FILE = path.join(getUserDataPath(), 'secrets.json');
const CRASH_LOG_FILE = path.join(getUserDataPath(), 'crash.log');

// 版本号
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
function getUserDataPath() {
  if (process.env.ELECTRON_USER_DATA_PATH) {
    return process.env.ELECTRON_USER_DATA_PATH;
  }
  if (!app.isPackaged) {
    return path.join(__dirname, '..', 'data');
  }
  return app.getPath('userData');
}

function getResourcePath(...segments) {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, ...segments);
  }
  return path.join(__dirname, '..', ...segments);
}

function getBackendScriptPath() {
  // 后端源码目录
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend-source', 'start.py');
  }
  return path.join(__dirname, '..', 'backend', 'start.py');
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

// ─── 密钥持久化 ───
function getOrCreateSecrets() {
  const canEncrypt = safeStorage.isEncryptionAvailable();
  try {
    if (fs.existsSync(SECRETS_FILE)) {
      const raw = fs.readFileSync(SECRETS_FILE);
      let data;
      if (canEncrypt) {
        try {
          const decrypted = safeStorage.decryptString(raw);
          data = JSON.parse(decrypted);
        } catch (_decryptErr) {
          try {
            data = JSON.parse(raw.toString('utf-8'));
            _writeSecrets(data, true);
            console.log('[Secrets] 迁移到加密存储');
          } catch (parseErr) {
            console.error('[Secrets] 密钥文件解析失败:', parseErr.message);
            data = {};
          }
        }
      } else {
        data = JSON.parse(raw.toString('utf-8'));
      }
      if (data.SECRET_KEY && data.CSRF_SECRET_KEY) return data;
    }
  } catch (e) {
    console.warn('[Secrets] 读取失败，重新生成:', e.message);
  }
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
      console.log('[Secrets] 已加密持久化');
    } else {
      fs.writeFileSync(SECRETS_FILE, JSON.stringify(secrets), 'utf-8');
      console.log('[Secrets] 明文持久化');
    }
  } catch (e) {
    console.error('[Secrets] 写入失败:', e.message);
  }
}

function getDatabasePath() {
  let dbDir;
  if (process.platform === 'linux') {
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
  if (!fs.existsSync(dbPath)) {
    const sourceDb = getResourcePath('database', 'bumofu.db');
    if (fs.existsSync(sourceDb)) {
      fs.copyFileSync(sourceDb, dbPath);
      console.log('[DB] 初始数据库已复制');
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
      if (err.code === 'EADDRINUSE') resolve(true);
      else resolve(false);
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
    console.warn(`[Port] 强制终止端口 ${port} 的进程`);
    writeDiagnosticLog(`强制终止端口 ${port}`);
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

async function findAvailablePort(startPort, maxAttempts) {
  for (let i = 0; i < maxAttempts; i++) {
    const port = startPort + i;
    const inUse = await checkPortInUse(port);
    if (!inUse) return port;
    console.log(`[Port] 端口 ${port} 被占用`);
    if (i === 0) {
      await killProcessOnPort(port);
      const stillInUse = await checkPortInUse(port);
      if (!stillInUse) return port;
    }
  }
  return null;
}

function analyzeStartupError(stderrCapture) {
  const logs = stderrCapture.join('\n').toLowerCase();
  if (logs.includes('vcruntime') || logs.includes('msvcp')) {
    return '【缺少 Visual C++ 运行时库】请安装 VC++ Redistributable。';
  }
  if (logs.includes('address already in use') || logs.includes('eaddrinuse')) {
    return '【端口被占用】请关闭占用 8000-8010 端口的程序。';
  }
  if (logs.includes('database') || logs.includes('sqlite') || logs.includes('locked')) {
    return '【数据库错误】可能文件损坏或被锁定。';
  }
  if (logs.includes('permission denied') || logs.includes('eacces')) {
    return '【权限不足】请以管理员身份运行。';
  }
  if (logs.includes('importerror') || logs.includes('modulenotfounderror')) {
    return '【Python 依赖缺失】请检查网络或手动安装依赖。';
  }
  if (logs.includes('timeout') || stderrCapture.length === 0) {
    return '【后端启动超时】请检查系统资源或网络。';
  }
  return '【未知错误】请查看诊断日志。';
}

function writeDiagnosticLog(message) {
  try {
    const timestamp = new Date().toISOString();
    fs.appendFileSync(CRASH_LOG_FILE, `[${timestamp}] [DIAG] ${message}\n`);
  } catch (_) {}
}

// ─── 后端启动（使用 Python 源码） ───
async function startBackend(stderrCapture = null) {
  const scriptPath = getBackendScriptPath();
  const scriptDir = path.dirname(scriptPath);
  console.log('[Backend] 脚本路径:', scriptPath);
  writeDiagnosticLog(`后端脚本路径: ${scriptPath}`);

  // 检查 Python3
  let pythonCmd = 'python3';
  try {
    execSync('which python3', { stdio: 'ignore' });
  } catch (_) {
    dialog.showErrorBox('缺少 Python', '系统未安装 Python3，请运行:\nsudo apt install python3 python3-pip');
    app.quit();
    return null;
  }

  // 检查脚本是否存在
  if (!fs.existsSync(scriptPath)) {
    const msg = `后端脚本不存在:\n${scriptPath}`;
    console.error('[Backend]', msg);
    writeDiagnosticLog(`错误: ${msg}`);
    dialog.showErrorBox('启动失败', msg);
    app.quit();
    return null;
  }

  // 动态查找可用端口
  const availablePort = await findAvailablePort(DEFAULT_BACKEND_PORT, MAX_PORT_ATTEMPTS);
  if (availablePort === null) {
    const msg = `端口 ${DEFAULT_BACKEND_PORT}-${DEFAULT_BACKEND_PORT + MAX_PORT_ATTEMPTS - 1} 均被占用。`;
    writeDiagnosticLog(`错误: ${msg}`);
    dialog.showErrorBox('端口冲突', msg);
    app.quit();
    return null;
  }
  backendPort = availablePort;
  if (backendPort !== DEFAULT_BACKEND_PORT) {
    console.log(`[Backend] 使用备用端口 ${backendPort}`);
    writeDiagnosticLog(`使用备用端口: ${backendPort}`);
  }

  // 创建必要目录
  const dbPath = getDatabasePath();
  const logsDir = path.join(getUserDataPath(), 'logs');
  const uploadsDir = path.join(getUserDataPath(), 'uploads');
  const cacheDir = path.join(getUserDataPath(), 'cache');
  const exportsDir = path.join(getUserDataPath(), 'exports');
  [logsDir, uploadsDir, cacheDir, exportsDir].forEach(dir => {
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  });

  // 首次运行：安装依赖
  const reqFile = path.join(scriptDir, 'requirements.txt');
  if (fs.existsSync(reqFile)) {
    console.log('[Backend] 检查 Python 依赖...');
    // 检查是否已安装（简单判断，可更精确）
    const check = spawn(pythonCmd, ['-c', 'import fastapi'], { stdio: 'ignore' });
    await new Promise((resolve) => {
      check.on('exit', (code) => {
        if (code !== 0) {
          console.log('[Backend] 安装依赖...');
          const install = spawn(pythonCmd, ['-m', 'pip', 'install', '-r', reqFile, '--user'], {
            cwd: scriptDir,
            stdio: 'inherit',
          });
          install.on('exit', resolve);
        } else {
          resolve();
        }
      });
    });
  }

  const env = {
    ...process.env,
    PYTHONIOENCODING: 'utf-8',
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

  const proc = spawn(pythonCmd, [scriptPath], {
    cwd: scriptDir,
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
    try {
      fs.appendFileSync(CRASH_LOG_FILE, `[${new Date().toISOString()}] ${text}\n`);
    } catch (_) {}
    if (stderrCapture) {
      stderrCapture.push(text);
      if (stderrCapture.length > 100) stderrCapture.shift();
    }
  });

  proc.on('error', (err) => {
    console.error('[Backend] 启动错误:', err);
    writeDiagnosticLog(`启动错误: ${err.message}`);
    let userMsg = err.message;
    if (err.code === 'ENOENT') {
      userMsg = `Python 或脚本不存在。\n请确保已安装 python3。`;
    } else if (err.code === 'EACCES') {
      userMsg = `权限不足，请以管理员身份运行。`;
    }
    dialog.showErrorBox('后端启动失败', userMsg);
  });

  proc.on('exit', (code) => {
    console.log('[Backend] 进程退出, code:', code);
    writeDiagnosticLog(`后端退出, code: ${code}`);
    backendProcess = null;
    if (!isQuitting && code !== 0) {
      // 自动重启
      if (backendRestartCount < MAX_BACKEND_RESTARTS) {
        backendRestartCount++;
        console.log(`[Backend] 自动重启 (${backendRestartCount}/${MAX_BACKEND_RESTARTS})...`);
        setTimeout(async () => {
          const restartStderr = [];
          backendProcess = await startBackend(restartStderr);
        }, 2000);
      } else {
        const logPath = path.join(getUserDataPath(), 'logs', 'app.log');
        dialog.showErrorBox('后端异常退出',
          `后端进程已重启 ${MAX_BACKEND_RESTARTS} 次后仍然失败。\n诊断日志: ${CRASH_LOG_FILE}\n应用日志: ${logPath}`);
      }
    }
  });

  return proc;
}

function stopBackend() {
  return new Promise((resolve) => {
    if (!backendProcess) { resolve(); return; }
    console.log('[Backend] 正在停止后端...');
    const pid = backendProcess.pid;
    let resolved = false;
    const done = () => { if (!resolved) { resolved = true; resolve(); } };
    const forceKill = () => {
      try {
        if (process.platform === 'win32') {
          spawn('taskkill', ['/pid', String(pid), '/f', '/t'], { windowsHide: true });
        } else {
          process.kill(pid, 'SIGKILL');
        }
      } catch (_e) {}
    };
    const proc = backendProcess;
    proc.once('exit', () => { backendProcess = null; done(); });
    // 尝试优雅关闭
    const req = http.request({
      hostname: '127.0.0.1',
      port: backendPort,
      path: '/api/v1/shutdown',
      method: 'POST',
      timeout: 3000,
      headers: { 'X-Internal-Shutdown': INTERNAL_SHUTDOWN_KEY },
    }, () => {
      setTimeout(forceKill, 3000);
    });
    req.on('error', () => { forceKill(); });
    req.on('timeout', () => { req.destroy(); forceKill(); });
    req.end();
    setTimeout(() => { backendProcess = null; done(); }, 5000);
  });
}

function waitForBackend(stderrCapture = []) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    let checkCount = 0;
    function check() {
      const elapsed = Date.now() - startTime;
      checkCount++;
      if (elapsed % 5000 < 200 && elapsed > 0) {
        console.log(`[Backend] 等待就绪... ${(elapsed / 1000).toFixed(1)}s`);
      }
      if (elapsed > BACKEND_READY_TIMEOUT) {
        const recentLogs = stderrCapture.slice(-10).join('\n');
        reject(new Error(`后端启动超时 (${(elapsed / 1000).toFixed(0)}秒)\n\n后端日志:\n${recentLogs || '无日志输出'}`));
        return;
      }
      const req = http.get(`http://127.0.0.1:${backendPort}/health`, (res) => {
        if (res.statusCode === 200) {
          console.log(`[Backend] 就绪，耗时 ${(elapsed / 1000).toFixed(1)}s`);
          resolve();
        } else {
          setTimeout(check, 300);
        }
      });
      req.on('error', () => {
        if (checkCount <= 3 || elapsed > 10000) {
          console.log(`[Backend] 健康检查失败 (${(elapsed / 1000).toFixed(1)}s)`);
        }
        setTimeout(check, 300);
      });
      req.setTimeout(3000, () => { req.destroy(); setTimeout(check, 300); });
    }
    setTimeout(check, 1000);
  });
}

// ─── 窗口管理（不变） ───
function loadWindowState() {
  try {
    if (fs.existsSync(WINDOW_STATE_FILE)) {
      return JSON.parse(fs.readFileSync(WINDOW_STATE_FILE, 'utf-8'));
    }
  } catch (e) { console.warn('[WindowState] 读取失败:', e.message); }
  return null;
}

function saveWindowState() {
  if (!mainWindow) return;
  try {
    const bounds = mainWindow.getBounds();
    const isMaximized = mainWindow.isMaximized();
    fs.writeFileSync(WINDOW_STATE_FILE, JSON.stringify({ bounds, isMaximized }), 'utf-8');
  } catch (e) { console.warn('[WindowState] 保存失败:', e.message); }
}

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
  if (savedState?.isMaximized) mainWindow.maximize();
  const frontendUrl = `http://127.0.0.1:${backendPort}`;
  mainWindow.loadURL(frontendUrl).catch((err) => {
    const msg = `无法加载页面：${frontendUrl}\n错误：${err?.message || err}`;
    console.error('[Window]', msg);
    writeDiagnosticLog(msg);
    dialog.showErrorBox('页面加载失败', msg);
  });
  mainWindow.once('ready-to-show', () => { mainWindow.show(); mainWindow.focus(); });
  let _saveStateTimer = null;
  function debouncedSave() {
    clearTimeout(_saveStateTimer);
    _saveStateTimer = setTimeout(saveWindowState, 500);
  }
  mainWindow.on('resize', debouncedSave);
  mainWindow.on('move', debouncedSave);
  mainWindow.on('close', (e) => {
    saveWindowState();
    if (!isQuitting) { e.preventDefault(); mainWindow.hide(); }
  });
  mainWindow.on('closed', () => { mainWindow = null; });
  mainWindow.webContents.on('render-process-gone', (event, details) => {
    console.error('[Renderer] 崩溃:', details.reason);
    dialog.showErrorBox('页面异常', `渲染进程因 ${details.reason} 崩溃，请重启程序。`);
  });
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

async function restartBackend() {
  await stopBackend();
  const restartStderr = [];
  backendProcess = await startBackend(restartStderr);
}

function createTray() {
  const iconPath = getIconPath();
  if (!fs.existsSync(iconPath)) return;
  tray = new Tray(iconPath);
  const contextMenu = Menu.buildFromTemplate([
    { label: '显示主窗口', click: () => { if (mainWindow) { mainWindow.show(); mainWindow.focus(); } } },
    { type: 'separator' },
    { label: '立即备份', click: () => { performAutoBackup(); showTrayNotification('备份任务', '执行中...'); } },
    { label: '重启后端', click: () => { restartBackend(); } },
    { type: 'separator' },
    { label: '退出', click: () => { isQuitting = true; app.quit(); } },
  ]);
  tray.setToolTip(APP_TITLE);
  tray.setContextMenu(contextMenu);
  tray.on('double-click', () => { if (mainWindow) { mainWindow.show(); mainWindow.focus(); } });
}

function showTrayNotification(title, body) {
  try {
    const { Notification } = require('electron');
    if (Notification.isSupported()) {
      new Notification({ title: `${APP_TITLE} - ${title}`, body }).show();
    }
  } catch (_) {}
}

// ─── 应用生命周期 ───
app.whenReady().then(async () => {
  console.log('[App] 启动...');
  setupIpcHandlers();
  // 启动后端
  const stderrCapture = [];
  backendProcess = await startBackend(stderrCapture);
  // 显示 splash
  let splashWin = null;
  try {
    const splashPath = path.join(__dirname, 'splash.html');
    if (fs.existsSync(splashPath)) {
      splashWin = new BrowserWindow({ width: 400, height: 300, frame: false, transparent: true, alwaysOnTop: true, resizable: false, webPreferences: { nodeIntegration: false, contextIsolation: true } });
      splashWin.loadFile(splashPath);
      splashWin.center();
    }
  } catch (e) { console.warn('[Splash] 加载失败:', e.message); }
  try {
    console.log('[App] 等待后端就绪...');
    await waitForBackend(stderrCapture);
    console.log('[App] 后端已就绪');
    backendRestartCount = 0;
  } catch (err) {
    console.error('[App] 后端启动失败:', err.message);
    const errorAnalysis = analyzeStartupError(stderrCapture);
    const logPath = path.join(getUserDataPath(), 'logs', 'app.log');
    const result = dialog.showMessageBoxSync({
      type: 'error',
      title: '后端启动失败',
      message: `后端服务无法启动。\n\n${errorAnalysis}\n\n诊断日志: ${CRASH_LOG_FILE}\n应用日志: ${logPath}\n\n是否查看详细日志？`,
      buttons: ['退出', '查看日志', '继续'],
      defaultId: 0,
    });
    if (result === 0) { isQuitting = true; stopBackend(); app.quit(); return; }
    if (result === 1) {
      const fullLogs = stderrCapture.join('\n') || '无日志';
      dialog.showMessageBoxSync({ type: 'info', title: '后端日志', message: '后端输出：', detail: fullLogs.substring(0, 2000) });
      isQuitting = true; stopBackend(); app.quit(); return;
    }
    // result 2: 继续
  }
  createMainWindow();
  if (splashWin && !splashWin.isDestroyed()) { splashWin.close(); splashWin = null; }
  createTray();
  startAutoBackup();
});

app.on('before-quit', () => { isQuitting = true; stopBackend(); });
app.on('activate', () => { if (!mainWindow) createMainWindow(); else mainWindow.show(); });

// Chromium 稳定性
app.disableHardwareAcceleration();
if (process.platform === 'win32') {
  app.commandLine.appendSwitch('disable-features', 'CacheControl');
  const gpuCacheDir = path.join(getUserDataPath(), 'gpu-cache');
  if (!fs.existsSync(gpuCacheDir)) fs.mkdirSync(gpuCacheDir, { recursive: true });
  app.commandLine.appendSwitch('gpu-disk-cache-dir', gpuCacheDir);
  app.commandLine.appendSwitch('disable-background-timer-throttling');
}
if (process.platform === 'linux') {
  if (typeof process.getuid === 'function' && process.getuid() === 0) {
    console.warn('[Main] root 用户，启用 --no-sandbox');
    app.commandLine.appendSwitch('no-sandbox');
  }
}

process.on('uncaughtException', (err) => {
  console.error('[Main] 未捕获异常:', err);
  writeDiagnosticLog(`未捕获异常: ${err.message}\n${err.stack || ''}`);
});
process.on('unhandledRejection', (reason) => {
  console.error('[Main] 未处理的拒绝:', reason);
  writeDiagnosticLog(`未处理的拒绝: ${String(reason)}`);
});

const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) { app.quit(); } else {
  app.on('second-instance', () => {
    if (mainWindow) { if (mainWindow.isMinimized()) mainWindow.restore(); mainWindow.show(); mainWindow.focus(); }
  });
}

// ─── IPC 处理器 ───
function setupIpcHandlers() {
  ipcMain.handle('get-app-version', () => appVersion);
  ipcMain.handle('get-platform', () => process.platform);
  ipcMain.handle('get-user-data-path', () => getUserDataPath());
  ipcMain.on('window-minimize', () => { if (mainWindow) mainWindow.minimize(); });
  ipcMain.on('window-maximize', () => { if (mainWindow) { mainWindow.isMaximized() ? mainWindow.unmaximize() : mainWindow.maximize(); } });
  ipcMain.on('window-close', () => { if (mainWindow) mainWindow.close(); });
  ipcMain.handle('show-save-dialog', async (_event, options) => {
    if (!mainWindow) return { canceled: true };
    return dialog.showSaveDialog(mainWindow, options || { title: '保存文件', filters: [{ name: '所有文件', extensions: ['*'] }] });
  });
  ipcMain.handle('show-open-dialog', async (_event, options) => {
    if (!mainWindow) return { canceled: true };
    return dialog.showOpenDialog(mainWindow, options || { title: '选择文件', properties: ['openFile'] });
  });
  ipcMain.handle('send-notification', (_event, title, body) => { showTrayNotification(title, body); });
  ipcMain.handle('open-path', async (_event, targetPath) => { shell.openPath(targetPath); });
  const { workerPool } = require('./worker-pool');
  ipcMain.handle('worker-exec', async (_event, task, payload, timeout) => {
    try { const result = await workerPool.exec(task, payload, timeout); return { success: true, data: result }; }
    catch (err) { return { success: false, error: err.message }; }
  });
  ipcMain.handle('worker-stats', () => workerPool.stats);
  ipcMain.handle('read-file-chunked', async (_event, filePath, chunkSize) => {
    return new Promise((resolve) => {
      const chunks = [];
      const stream = fs.createReadStream(filePath, { highWaterMark: chunkSize || 256 * 1024, encoding: 'base64' });
      stream.on('data', (chunk) => chunks.push(chunk));
      stream.on('end', () => resolve({ data: chunks.join('') }));
      stream.on('error', () => resolve({ error: 'read-failed' }));
    });
  });
  ipcMain.on('window-force-redraw', () => {
    if (mainWindow) { mainWindow.webContents.invalidate(); mainWindow.focus(); mainWindow.webContents.focus(); }
  });
  console.log('[IPC] 已注册');
}

// ─── 自动备份 ───
function startAutoBackup() {
  setTimeout(() => { performAutoBackup(); setInterval(performAutoBackup, AUTO_BACKUP_INTERVAL); }, 5 * 60 * 1000);
  console.log('[AutoBackup] 已调度');
}

function performAutoBackup() {
  const req = http.request({
    hostname: '127.0.0.1',
    port: backendPort,
    path: '/api/v1/system/backup',
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Internal-Backup': INTERNAL_BACKUP_KEY },
    timeout: 30000,
  }, (res) => {
    let body = '';
    res.on('data', (chunk) => { body += chunk; });
    res.on('end', () => {
      if (res.statusCode === 200 || res.statusCode === 201) {
        console.log('[AutoBackup] 成功');
        showTrayNotification('备份完成', '自动备份成功');
        cleanupOldBackups();
      } else {
        console.warn(`[AutoBackup] 状态码 ${res.statusCode}`);
      }
    });
  });
  req.on('error', (err) => { console.warn('[AutoBackup] 请求失败:', err.message); });
  req.write(JSON.stringify({ description: '自动定时备份' }));
  req.end();
}

function cleanupOldBackups() {
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
            const delReq = http.request({
              hostname: '127.0.0.1',
              port: backendPort,
              path: `/api/v1/system/backup/${backup.filename}`,
              method: 'DELETE',
              timeout: 10000,
            }, (res) => { if (res.statusCode >= 400) console.warn(`删除 ${backup.filename} 失败`); });
            delReq.on('error', (err) => { console.warn(`删除 ${backup.filename} 错误:`, err.message); });
            delReq.end();
            console.log(`[AutoBackup] 删除旧备份: ${backup.filename}`);
          }
        }
      } catch (e) { console.warn('[AutoBackup] 清理失败:', e.message); }
    });
  });
  req.on('error', (err) => { console.warn('[AutoBackup] 获取列表失败:', err.message); });
}
