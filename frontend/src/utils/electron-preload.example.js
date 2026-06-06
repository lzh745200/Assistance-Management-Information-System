/**
 * Electron 预加载脚本
 *
 * 通过 contextBridge 安全地暴露有限 API 给渲染进程。
 * contextIsolation=true + nodeIntegration=false 确保渲染进程无法直接访问 Node.js。
 *
 * 放置位置: electron/preload.js
 * 构建时: 确保此文件与 main.js 在 electron-builder 的 "files" 配置中
 */
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  /** 获取 CPU 使用率、核心数、型号 */
  getCpuInfo: () => ipcRenderer.invoke("system:cpu"),

  /** 获取内存总量/已用/可用/使用率 */
  getMemoryInfo: () => ipcRenderer.invoke("system:memory"),

  /** 获取 SQLite 数据库文件大小 */
  getDbSize: () => ipcRenderer.invoke("system:db-size"),

  /** 聚合获取完整系统状态 */
  getSystemStatus: () => ipcRenderer.invoke("system:status"),

  /** 当前平台标识 */
  platform: process.platform,

  /** 是否在 Electron 环境中 */
  isElectron: true,
});
