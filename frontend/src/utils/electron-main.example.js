/**
 * Electron 主进程 — 系统资源 IPC 处理器
 *
 * 将以下代码合并到 electron/main.js 中。
 * 依赖: Node.js 内置 os, fs, path 模块（无需额外 npm 包）。
 */

// === 粘贴到 electron/main.js 顶部 ===

const os = require("os");
const fs = require("fs");
const path = require("path");
const { ipcMain } = require("electron");

// 数据库文件路径（与后端 Settings.DATABASE_URL 中的路径保持一致）
const DB_PATH = path.join(__dirname, "..", "resources", "data", "rural_revitalization.db");

// ─── IPC: 获取 CPU 信息 ────────────────────────────────────────────

ipcMain.handle("system:cpu", async () => {
  const cpus = os.cpus();
  const totalIdle = cpus.reduce((sum, cpu) => sum + cpu.times.idle, 0);
  const totalTick = cpus.reduce(
    (sum, cpu) =>
      sum +
      cpu.times.user +
      cpu.times.nice +
      cpu.times.sys +
      cpu.times.idle +
      cpu.times.irq,
    0,
  );

  return {
    usagePercent: Math.round((1 - totalIdle / totalTick) * 100),
    count: cpus.length,
    model: cpus[0]?.model || "Unknown",
    arch: os.arch(),
  };
});

// ─── IPC: 获取内存信息 ──────────────────────────────────────────────

ipcMain.handle("system:memory", async () => {
  const total = os.totalmem();
  const free = os.freemem();
  const used = total - free;

  return {
    totalMB: Math.round(total / (1024 * 1024)),
    usedMB: Math.round(used / (1024 * 1024)),
    freeMB: Math.round(free / (1024 * 1024)),
    usagePercent: Math.round((used / total) * 100),
  };
});

// ─── IPC: 获取数据库文件大小 ────────────────────────────────────────

ipcMain.handle("system:db-size", async () => {
  try {
    const stats = fs.statSync(DB_PATH);
    return {
      sizeBytes: stats.size,
      sizeMB: (stats.size / (1024 * 1024)).toFixed(2),
      exists: true,
    };
  } catch {
    return {
      sizeBytes: 0,
      sizeMB: "0.00",
      exists: false,
      error: "数据库文件不存在: " + DB_PATH,
    };
  }
});

// ─── IPC: 聚合完整系统状态 ──────────────────────────────────────────

ipcMain.handle("system:status", async () => {
  const cpus = os.cpus();
  const totalMem = os.totalmem();
  const freeMem = os.freemem();

  const totalIdle = cpus.reduce((s, c) => s + c.times.idle, 0);
  const totalTick = cpus.reduce(
    (s, c) =>
      s +
      c.times.user +
      c.times.nice +
      c.times.sys +
      c.times.idle +
      c.times.irq,
    0,
  );

  let dbSizeBytes = 0;
  try {
    dbSizeBytes = fs.statSync(DB_PATH).size;
  } catch {
    // 数据库文件不存在
  }

  return {
    timestamp: new Date().toISOString(),
    hostname: os.hostname(),
    platform: os.platform(),
    uptime: Math.round(os.uptime()),
    cpu: {
      usagePercent: Math.round((1 - totalIdle / totalTick) * 100),
      count: cpus.length,
      model: cpus[0]?.model || "",
    },
    memory: {
      totalMB: Math.round(totalMem / (1024 * 1024)),
      usedMB: Math.round((totalMem - freeMem) / (1024 * 1024)),
      usagePercent: Math.round(((totalMem - freeMem) / totalMem) * 100),
    },
    database: {
      sizeBytes: dbSizeBytes,
      sizeMB: dbSizeBytes ? (dbSizeBytes / (1024 * 1024)).toFixed(2) : "0.00",
    },
  };
});
