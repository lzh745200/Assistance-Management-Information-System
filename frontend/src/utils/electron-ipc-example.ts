/**
 * Electron 主进程 IPC 通信示例
 *
 * 提供桌面端系统资源（CPU/内存/文件大小）的获取方式。
 *
 * === 架构 ===
 *
 *   主进程 (electron/main.js)
 *     ↓ ipcMain.handle()
 *   Preload (electron/preload.js)
 *     ↓ contextBridge.exposeInMainWorld()
 *   渲染进程 (Vue)
 *     ↓ window.electronAPI.xxx()
 *
 * === 集成步骤 ===
 *
 * 1. 复制下方 "electron/main.js" 代码到实际的 electron/main.js
 * 2. 复制下方 "electron/preload.js" 代码到实际的 electron/preload.js
 * 3. 在 electron/main.js 创建 BrowserWindow 时指定 preload 脚本
 * 4. 前端通过 window.electronAPI 调用，或使用下方的 useElectronSystem composable
 *
 * === 示例：创建窗口时指定 preload ===
 *
 *   const win = new BrowserWindow({
 *     webPreferences: {
 *       preload: path.join(__dirname, "preload.js"),
 *       contextIsolation: true,   // 安全：隔离渲染进程
 *       nodeIntegration: false,   // 安全：禁用 Node
 *     },
 *   });
 */

// ============================================================================
// TypeScript 类型声明（放入 frontend/src/types/electron.d.ts）
// ============================================================================

export interface ElectronCpuInfo {
  usagePercent: number;
  count: number;
  model: string;
  arch: string;
}

export interface ElectronMemoryInfo {
  totalMB: number;
  usedMB: number;
  freeMB: number;
  usagePercent: number;
}

export interface ElectronDbSize {
  sizeBytes: number;
  sizeMB: string;
  exists: boolean;
  error?: string;
}

export interface ElectronSystemStatus {
  timestamp: string;
  hostname: string;
  platform: string;
  uptime: number;
  cpu: {
    usagePercent: number;
    count: number;
    model: string;
  };
  memory: {
    totalMB: number;
    usedMB: number;
    usagePercent: number;
  };
  database: {
    sizeBytes: number;
    sizeMB: string;
  };
}

export interface ElectronAPI {
  getCpuInfo: () => Promise<ElectronCpuInfo>;
  getMemoryInfo: () => Promise<ElectronMemoryInfo>;
  getDbSize: () => Promise<ElectronDbSize>;
  getSystemStatus: () => Promise<ElectronSystemStatus>;
  platform: NodeJS.Platform;
  isElectron: boolean;
}

// 扩展全局 Window 接口
declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}

// ============================================================================
// Vue Composable: useElectronSystem
// 用法：const { cpuPercent, memPercent, dbSizeMB } = useElectronSystem(30000);
// ============================================================================

/*
import { ref, onMounted, onUnmounted } from "vue";

export function useElectronSystem(pollInterval = 30000) {
  const cpuPercent = ref(0);
  const memPercent = ref(0);
  const memUsedMB = ref(0);
  const memTotalMB = ref(0);
  const dbSizeMB = ref("0.00");
  const hostname = ref("");
  const uptime = ref(0);
  const isElectron = ref(false);

  let timer: ReturnType<typeof setInterval> | null = null;

  const fetchStatus = async () => {
    if (!window.electronAPI) return;
    isElectron.value = true;

    try {
      const [cpu, mem, db] = await Promise.all([
        window.electronAPI.getCpuInfo(),
        window.electronAPI.getMemoryInfo(),
        window.electronAPI.getDbSize(),
      ]);

      cpuPercent.value = cpu.usagePercent;
      memPercent.value = mem.usagePercent;
      memUsedMB.value = mem.usedMB;
      memTotalMB.value = mem.totalMB;
      dbSizeMB.value = db.sizeMB;
    } catch (err) {
      console.warn("[useElectronSystem]", err);
    }
  };

  onMounted(() => {
    fetchStatus();
    if (pollInterval > 0) {
      timer = setInterval(fetchStatus, pollInterval);
    }
  });

  onUnmounted(() => {
    if (timer !== null) {
      clearInterval(timer);
      timer = null;
    }
  });

  return {
    cpuPercent,
    memPercent,
    memUsedMB,
    memTotalMB,
    dbSizeMB,
    hostname,
    uptime,
    isElectron,
    refresh: fetchStatus,
  };
}
*/
