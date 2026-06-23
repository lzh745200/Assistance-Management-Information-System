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
const MAX_PORT_ATTEMPTS = 11;
let backendPort = DEFAULT_BACKEND_PORT;
const APP_TITLE = '帮扶管理系统';
const BACKEND_READY_TIMEOUT = 60000;
const AUTO_BACKUP_INTERVAL = 24 * 60 * 60 * 1000;
const WINDOW_STATE_FILE = path.join(getUserDataPath(), 'window-state.json');
const SECRETS_FILE = path.join(getUserDataPath(), 'secrets.json');
const CRASH_LOG_FILE = path.join(getUserDataPath(), 'crash.log');

const appVersion = (() => {
  try {
    const pkgPath = app.isPackaged
      ? path.join(process.resourcesPath, '..', 'package.json')
      : path.join(__dirname, '..', 'package.json');
    return JSON.parse(fs.readFileSync(pkgPath, 'utf-8')).version || '1.2.0';
  } catch (_) {
    return '1.2.0';
  }
})();

// ─── 路径解析 ───

function getUserDataPath() {
  if (process.env.ELECTRON_USER_DATA_PATH) return process.env.ELECTRON_USER_DATA_PATH;
  if (!app.isPackaged) return path.join(__dirname, '..', 'data');
  return app.getPath('userData');
}

function getResourcePath(...segments) {
  if (app.isPackaged) return path.join(process.resourcesPath, ...segments);
  return path.join(__dirname, '..', ...segments);
}

function getBackendExePath() {
  const isWin = process.platform === 'win32';
  const exeName = isWin ? 'assistance-backend.exe' : 'assistance-backend';
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend', exeName);
  }
  return path.join(__dirname, '..', 'backend', 'dist', exeName);
}

function getFrontendPath() {
  if (app.isPackaged) return path.join(process.resourcesPath, 'frontend');
  return path.join(__dirname, '..', 'frontend', 'dist');
}

function getIconPath() {
  // 统一使用 resources/icon.png（打包后位于 /opt/.../resources/icon.png）
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'icon.png');
  }
  return path.join(__dirname, '..', 'resources', 'icon.png');
}

// ─── 密钥持久化 ───
// 后端启动时通过 app.utils.runtime_secrets.ensure_runtime_secrets() 自行生成并
// 持久化运行时密钥（写入 %LOCALAPPDATA%\bumofu-assistance\runtime_secrets.json），
// 因此 Electron 侧无需注入密钥环境变量。此处保留接口以兼容现有调用，返回空对象。
function getOrCreateSecrets() {
  return {};
}
function _writeSecrets(secrets, encrypt) {
  // 密钥由后端自行管理，Electron 侧不持久化。保留空实现以兼容接口。
}

// ─── 数据库路径 ───
// 数据库放在 %LOCALAPPDATA%\bumofu-assistance\data\ (而非安装目录)，
// 避免 Program Files 非管理员用户写入失败。由 Electron 通过 DATABASE_URL
// 环境变量注入后端，后端 paths.py 中 is_bundled() 作为兜底默认值。
function getDatabasePath() {
  // Windows: %LOCALAPPDATA% = C:\Users\<user>\AppData\Local
  // Linux:   ~/.local/share (XDG_DATA_HOME 约定)
  let localAppData;
  if (process.platform === 'win32') {
    localAppData = process.env.LOCALAPPDATA
      || path.join(app.getPath('appData'), '..', 'Local');
  } else {
    localAppData = process.env.XDG_DATA_HOME
      || path.join(app.getPath('home'), '.local', 'share');
  }
  return path.join(localAppData, 'bumofu-assistance', 'data', 'rural_revitalization.db');
}

// ─── 端口检测、启动错误分析等函数（与您原有的一致，保持不变） ───
// 此处省略 checkPortInUse、killProcessOnPort、findAvailablePort 等函数

// ─── 后端启动（直接运行二进制） ───
async function startBackend(stderrCapture = null) {
  const exePath = getBackendExePath();
  console.log('[Backend] 启动路径:', exePath);
  writeDiagnosticLog(`后端路径: ${exePath}`);

  if (!fs.existsSync(exePath)) {
    const msg = `后端程序不存在:\n${exePath}`;
    console.error('[Backend]', msg);
    writeDiagnosticLog(msg);
    dialog.showErrorBox('启动失败', msg);
    app.quit();
    return null;
  }

  // 赋予执行权限（如果缺失）
  try {
    fs.accessSync(exePath, fs.constants.X_OK);
  } catch (_) {
    try { fs.chmodSync(exePath, 0o755); } catch (e) {}
  }

  const availablePort = await findAvailablePort(DEFAULT_BACKEND_PORT, MAX_PORT_ATTEMPTS);
  if (availablePort === null) {
    const msg = `端口 ${DEFAULT_BACKEND_PORT}-${DEFAULT_BACKEND_PORT + MAX_PORT_ATTEMPTS - 1} 均被占用。`;
    writeDiagnosticLog(msg);
    dialog.showErrorBox('端口冲突', msg);
    app.quit();
    return null;
  }
  backendPort = availablePort;
  if (backendPort !== DEFAULT_BACKEND_PORT) {
    console.log(`[Backend] 使用备用端口 ${backendPort}`);
    writeDiagnosticLog(`备用端口: ${backendPort}`);
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
    DATABASE_URL: `sqlite:///${dbPath.replace(/\\/g, '/')}`,
    HOST: '127.0.0.1',
    PORT: String(backendPort),
    LOG_FILE: path.join(logsDir, 'app.log'),
    UPLOAD_DIR: uploadsDir,
    CACHE_DIR: cacheDir,
    EXPORT_DIR: exportsDir,
    FRONTEND_DIST_PATH: getFrontendPath(),
    ENVIRONMENT: 'production',
    PROJECT_VERSION: appVersion,
    INTERNAL_BACKUP_KEY,
    INTERNAL_SHUTDOWN_KEY,
    ...getOrCreateSecrets(),
  };

  // Linux 下设置 LD_LIBRARY_PATH（如果有 lib 目录）
  if (process.platform === 'linux') {
    const libDir = path.join(path.dirname(exePath), '..', 'lib');
    if (fs.existsSync(libDir)) {
      const existing = env.LD_LIBRARY_PATH || '';
      env.LD_LIBRARY_PATH = libDir + (existing ? ':' + existing : '');
      console.log('[Backend] LD_LIBRARY_PATH:', env.LD_LIBRARY_PATH);
    }
  }

  const proc = spawn(exePath, [], {
    cwd: path.dirname(exePath),
    env,
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: process.platform === 'win32',
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
    if (err.code === 'ENOENT') userMsg = '后端程序不存在。';
    else if (err.code === 'EACCES') userMsg = '权限不足，请以管理员身份运行。';
    dialog.showErrorBox('后端启动失败', userMsg);
  });

  proc.on('exit', (code) => {
    console.log('[Backend] 退出, code:', code);
    writeDiagnosticLog(`后端退出, code: ${code}`);
    backendProcess = null;
    if (!isQuitting && code !== 0) {
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
          `后端已重启 ${MAX_BACKEND_RESTARTS} 次仍失败。\n诊断日志: ${CRASH_LOG_FILE}\n应用日志: ${logPath}`);
      }
    }
  });

  return proc;
}

function stopBackend() {
  return new Promise((resolve) => {
    if (!backendProcess) { resolve(); return; }
    console.log('[Backend] 停止...');
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
      } catch (_) {}
    };
    const proc = backendProcess;
    proc.once('exit', () => { backendProcess = null; done(); });
    const req = http.request({
      hostname: '127.0.0.1',
      port: backendPort,
      path: '/api/v1/shutdown',
      method: 'POST',
      timeout: 3000,
      headers: { 'X-Internal-Shutdown': INTERNAL_SHUTDOWN_KEY },
    }, () => { setTimeout(forceKill, 3000); });
    req.on('error', forceKill);
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
        const recent = stderrCapture.slice(-10).join('\n');
        reject(new Error(`后端启动超时 (${(elapsed / 1000).toFixed(0)}秒)\n日志:\n${recent || '无日志'}`));
        return;
      }
      const req = http.get(`http://127.0.0.1:${backendPort}/health`, (res) => {
        if (res.statusCode === 200) {
          console.log(`[Backend] 就绪，耗时 ${(elapsed / 1000).toFixed(1)}s`);
          resolve();
        } else setTimeout(check, 300);
      });
      req.on('error', () => {
        if (checkCount <= 3 || elapsed > 10000) console.log(`[Backend] 健康检查失败 (${(elapsed / 1000).toFixed(1)}s)`);
        setTimeout(check, 300);
      });
      req.setTimeout(3000, () => { req.destroy(); setTimeout(check, 300); });
    }
    setTimeout(check, 1000);
  });
}

// ─── 窗口管理、托盘、备份等（与您原有的完全相同，但需更新图标路径） ───
// 这里仅展示关键修改：createMainWindow 和 createTray 中调用 getIconPath()
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
  const url = `http://127.0.0.1:${backendPort}`;
  mainWindow.loadURL(url).catch((err) => {
    const msg = `加载页面失败: ${url}\n${err?.message || err}`;
    console.error('[Window]', msg);
    writeDiagnosticLog(msg);
    dialog.showErrorBox('页面加载失败', msg);
  });
  mainWindow.once('ready-to-show', () => { mainWindow.show(); mainWindow.focus(); });
  let timer = null;
  mainWindow.on('resize', () => { clearTimeout(timer); timer = setTimeout(saveWindowState, 500); });
  mainWindow.on('move', () => { clearTimeout(timer); timer = setTimeout(saveWindowState, 500); });
  mainWindow.on('close', (e) => {
    saveWindowState();
    if (!isQuitting) { e.preventDefault(); mainWindow.hide(); }
  });
  mainWindow.on('closed', () => { mainWindow = null; });
  mainWindow.webContents.on('render-process-gone', (event, details) => {
    console.error('[Renderer] 崩溃:', details.reason);
    dialog.showErrorBox('页面异常', `渲染进程崩溃 (${details.reason})，请重启程序。`);
  });
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

function createTray() {
  const iconPath = getIconPath();
  if (!fs.existsSync(iconPath)) return;
  tray = new Tray(iconPath);
  const menu = Menu.buildFromTemplate([
    { label: '显示主窗口', click: () => { if (mainWindow) { mainWindow.show(); mainWindow.focus(); } } },
    { type: 'separator' },
    { label: '立即备份', click: () => { performAutoBackup(); showTrayNotification('备份任务', '执行中...'); } },
    { label: '重启后端', click: () => { restartBackend(); } },
    { type: 'separator' },
    { label: '退出', click: () => { isQuitting = true; app.quit(); } },
  ]);
  tray.setToolTip(APP_TITLE);
  tray.setContextMenu(menu);
  tray.on('double-click', () => { if (mainWindow) { mainWindow.show(); mainWindow.focus(); } });
}

// ─── 其他函数（loadWindowState, saveWindowState, restartBackend, showTrayNotification 等）请保留原有实现 ───

// ─── 应用生命周期（与您原有的相同，但需确保调用 createTray 等） ───
app.whenReady().then(async () => {
  console.log('[App] 启动...');
  setupIpcHandlers();

  const stderrCapture = [];
  backendProcess = await startBackend(stderrCapture);

  let splash = null;
  try {
    const splashPath = path.join(__dirname, 'splash.html');
    if (fs.existsSync(splashPath)) {
      splash = new BrowserWindow({ width: 400, height: 300, frame: false, transparent: true, alwaysOnTop: true, resizable: false, webPreferences: { nodeIntegration: false, contextIsolation: true } });
      splash.loadFile(splashPath);
      splash.center();
    }
  } catch (e) {}

  try {
    console.log('[App] 等待后端就绪...');
    await waitForBackend(stderrCapture);
    console.log('[App] 后端已就绪');
    backendRestartCount = 0;
  } catch (err) {
    console.error('[App] 后端启动失败:', err.message);
    const analysis = analyzeStartupError(stderrCapture);
    const logPath = path.join(getUserDataPath(), 'logs', 'app.log');
    const choice = dialog.showMessageBoxSync({
      type: 'error',
      title: '后端启动失败',
      message: `后端启动失败。\n${analysis}\n诊断日志: ${CRASH_LOG_FILE}\n应用日志: ${logPath}\n查看详细日志？`,
      buttons: ['退出', '查看日志', '继续'],
      defaultId: 0,
    });
    if (choice === 0) { isQuitting = true; stopBackend(); app.quit(); return; }
    if (choice === 1) {
      const logs = stderrCapture.join('\n') || '无日志';
      dialog.showMessageBoxSync({ type: 'info', title: '后端日志', message: '后端输出：', detail: logs.substring(0, 2000) });
      isQuitting = true; stopBackend(); app.quit(); return;
    }
  }

  createMainWindow();
  if (splash && !splash.isDestroyed()) { splash.close(); splash = null; }
  createTray();
  startAutoBackup();
});

app.on('before-quit', () => { isQuitting = true; stopBackend(); });
app.on('activate', () => { if (!mainWindow) createMainWindow(); else mainWindow.show(); });

app.disableHardwareAcceleration();
if (process.platform === 'win32') {
  app.commandLine.appendSwitch('disable-features', 'CacheControl');
  const gpuCache = path.join(getUserDataPath(), 'gpu-cache');
  if (!fs.existsSync(gpuCache)) fs.mkdirSync(gpuCache, { recursive: true });
  app.commandLine.appendSwitch('gpu-disk-cache-dir', gpuCache);
  app.commandLine.appendSwitch('disable-background-timer-throttling');
}
if (process.platform === 'linux' && typeof process.getuid === 'function' && process.getuid() === 0) {
  console.warn('[Main] root 用户，启用 --no-sandbox');
  app.commandLine.appendSwitch('no-sandbox');
}

process.on('uncaughtException', (err) => {
  console.error('[Main] 未捕获异常:', err);
  writeDiagnosticLog(`未捕获异常: ${err.message}\n${err.stack || ''}`);
});
process.on('unhandledRejection', (reason) => {
  console.error('[Main] 未处理的拒绝:', reason);
  writeDiagnosticLog(`未处理的拒绝: ${String(reason)}`);
});

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) { app.quit(); } else {
  app.on('second-instance', () => {
    if (mainWindow) { if (mainWindow.isMinimized()) mainWindow.restore(); mainWindow.show(); mainWindow.focus(); }
  });
}

// ─── IPC 处理器、自动备份（与原有相同，此处省略） ───
// 请确保 setupIpcHandlers、startAutoBackup、performAutoBackup、cleanupOldBackups 等函数已存在。

console.log('[Main] 主进程加载完成');