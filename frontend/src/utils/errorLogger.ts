/**
 * 前端错误日志模块
 *
 * 收集错误信息（时间、位置、上下文），写入 localStorage 环形缓冲区。
 * 支持导出为 JSON 文件，便于问题追踪和分析。
 */

const STORAGE_KEY = "app_error_logs";
const MAX_ENTRIES = 200;

export interface ErrorLogEntry {
  /** ISO 时间戳 */
  timestamp: string;
  /** 错误级别 */
  level: "error" | "warn" | "info";
  /** 错误来源（组件名 / API URL / 模块名） */
  source: string;
  /** 错误消息 */
  message: string;
  /** 附加上下文信息 */
  context?: Record<string, unknown>;
}

/** 从 localStorage 读取日志 */
function readLogs(): ErrorLogEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

/** 写入日志到 localStorage（环形缓冲区） */
function writeLogs(logs: ErrorLogEntry[]): void {
  try {
    // 只保留最近 MAX_ENTRIES 条
    const trimmed = logs.slice(-MAX_ENTRIES);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  } catch {
    // localStorage 满或不可用时静默忽略
  }
}

/** 记录一条错误日志 */
export function logError(
  source: string,
  message: string,
  context?: Record<string, unknown>,
): void {
  const entry: ErrorLogEntry = {
    timestamp: new Date().toISOString(),
    level: "error",
    source,
    message,
    context,
  };
  const logs = readLogs();
  logs.push(entry);
  writeLogs(logs);
}

/** 记录一条警告日志 */
export function logWarn(
  source: string,
  message: string,
  context?: Record<string, unknown>,
): void {
  const entry: ErrorLogEntry = {
    timestamp: new Date().toISOString(),
    level: "warn",
    source,
    message,
    context,
  };
  const logs = readLogs();
  logs.push(entry);
  writeLogs(logs);
}

/** 记录一条信息日志 */
export function logInfo(
  source: string,
  message: string,
  context?: Record<string, unknown>,
): void {
  const entry: ErrorLogEntry = {
    timestamp: new Date().toISOString(),
    level: "info",
    source,
    message,
    context,
  };
  const logs = readLogs();
  logs.push(entry);
  writeLogs(logs);
}

/** 获取所有日志（最新在后） */
export function getErrorLogs(): ErrorLogEntry[] {
  return readLogs();
}

/** 清空日志 */
export function clearErrorLogs(): void {
  localStorage.removeItem(STORAGE_KEY);
}

/** 导出日志为 JSON 文件并触发下载 */
export function exportErrorLogs(): void {
  const logs = readLogs();
  const blob = new Blob([JSON.stringify(logs, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `error_logs_${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
