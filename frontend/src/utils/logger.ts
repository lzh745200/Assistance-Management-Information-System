/**
 * 日志工具模块
 *
 * 提供日志记录、存储、导出、错误边界等功能
 */

// ==================== 日志级别 ====================

export enum LogLevel {
  DEBUG = "debug",
  INFO = "info",
  WARN = "warn",
  ERROR = "error",
  FATAL = "fatal",
}

// ==================== 日志条目接口 ====================

export interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: number;
  context?: Record<string, unknown>;
  stack?: string;
}

// ==================== 日志记录器 ====================

const MAX_LOGS = 500;
const IS_PRODUCTION = import.meta.env.MODE === "production";
const IS_DEBUG = import.meta.env.VITE_DEBUG === "true";

class Logger {
  private logs: LogEntry[] = [];

  debug(message: string, context?: unknown) {
    const normalizedContext = this._normalizeContext(context);
    this._log(LogLevel.DEBUG, message, undefined, normalizedContext);
    // 仅在开发模式或启用调试时输出
    if (!IS_PRODUCTION || IS_DEBUG) {
      console.debug(message, ...(context !== undefined ? [context] : []));
    }
  }

  info(message: string, context?: unknown) {
    const normalizedContext = this._normalizeContext(context);
    this._log(LogLevel.INFO, message, undefined, normalizedContext);
    // 仅在开发模式或启用调试时输出
    if (!IS_PRODUCTION || IS_DEBUG) {
      console.log(message, ...(context !== undefined ? [context] : []));
    }
  }

  warn(message: string, context?: unknown) {
    const normalizedContext = this._normalizeContext(context);
    this._log(LogLevel.WARN, message, undefined, normalizedContext);
    // 警告在生产环境也输出
    console.warn(message, ...(context !== undefined ? [context] : []));
  }

  error(message: string, error?: unknown, context?: unknown) {
    const stack = error instanceof Error ? error.stack : undefined;
    const normalizedContext = this._normalizeContext(context);
    this._log(LogLevel.ERROR, message, stack, normalizedContext);
    // 错误在生产环境也输出
    console.error(message, ...(error !== undefined ? [error] : []));
  }

  fatal(message: string, error?: unknown, context?: unknown) {
    const stack = error instanceof Error ? error.stack : undefined;
    const normalizedContext = this._normalizeContext(context);
    this._log(LogLevel.FATAL, message, stack, normalizedContext);
    // 致命错误在生产环境也输出
    console.error(message, ...(error !== undefined ? [error] : []));
  }

  getLogs(level?: LogLevel): LogEntry[] {
    if (!level) return [...this.logs];
    return this.logs.filter((entry) => entry.level === level);
  }

  clear() {
    this.logs = [];
  }

  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  private _normalizeContext(
    context?: unknown,
  ): Record<string, unknown> | undefined {
    if (context === undefined || context === null) {
      return undefined;
    }

    // 如果已经是对象，直接返回
    if (typeof context === "object" && !Array.isArray(context)) {
      return context as Record<string, unknown>;
    }

    // 如果是基本类型或数组，包装成对象
    return { value: context };
  }

  private _log(
    level: LogLevel,
    message: string,
    stack?: string,
    context?: Record<string, unknown>,
  ) {
    const entry: LogEntry = {
      level,
      message,
      timestamp: Date.now(),
      ...(context !== undefined ? { context } : {}),
      ...(stack ? { stack } : {}),
    };
    this.logs.push(entry);
    if (this.logs.length > MAX_LOGS) {
      this.logs = this.logs.slice(-MAX_LOGS);
    }
  }
}

export const logger = new Logger();

// ==================== 辅助函数 ====================

/**
 * 包装同步函数，捕获异常并记录日志
 */
export function tryCatch<T>(
  fn: () => T,
  errorMessage?: string,
  defaultValue?: T,
): T | undefined {
  try {
    return fn();
  } catch (error) {
    logger.error(
      errorMessage || "An error occurred",
      error instanceof Error ? error : new Error(String(error)),
    );
    return defaultValue;
  }
}

/**
 * 包装异步函数，捕获异常并记录日志
 */
export async function tryCatchAsync<T>(
  fn: () => Promise<T>,
  errorMessage?: string,
  defaultValue?: T,
): Promise<T | undefined> {
  try {
    return await fn();
  } catch (error) {
    logger.error(
      errorMessage || "An async error occurred",
      error instanceof Error ? error : new Error(String(error)),
    );
    return defaultValue;
  }
}

/**
 * 创建带错误边界的函数包装器
 */
export function withErrorBoundary<
  T extends (...args: unknown[]) => Promise<unknown>,
>(fn: T, errorMessage?: string): T {
  const wrapped = async (...args: unknown[]) => {
    try {
      return await fn(...args);
    } catch (error) {
      logger.error(
        errorMessage || "Error in wrapped function",
        error instanceof Error ? error : new Error(String(error)),
      );
      throw error;
    }
  };
  return wrapped as T;
}

export default Logger;
