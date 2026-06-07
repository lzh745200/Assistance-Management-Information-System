/**
 * 全局错误处理工具
 *
 * 提供统一的错误类型、解析、策略与处理机制
 */
import { logger } from "@/utils/logger";
import { ElMessage, ElNotification } from "element-plus";
import { getEventBus } from "@/composables/useEventBus";

// ==================== 错误类型枚举 ====================

export enum ErrorType {
  NETWORK = "NETWORK",
  AUTH = "AUTH",
  PERMISSION = "PERMISSION",
  VALIDATION = "VALIDATION",
  NOT_FOUND = "NOT_FOUND",
  SERVER = "SERVER",
  TIMEOUT = "TIMEOUT",
  BUSINESS = "BUSINESS",
  UNKNOWN = "UNKNOWN",
}

// ==================== 接口定义 ====================

export interface AppError {
  type: ErrorType;
  message: string;
  code?: number | string;
  details?: any;
  retryable: boolean;
  timestamp: number;
}

export interface ErrorStrategy {
  shouldNotify: boolean;
  shouldLog: boolean;
  shouldRedirect: boolean;
  retryable: boolean;
  notificationType: "message" | "notification";
  severity: "info" | "warning" | "error";
  redirectPath?: string;
}

// ==================== 默认策略 ====================

const defaultStrategies: Record<ErrorType, ErrorStrategy> = {
  [ErrorType.NETWORK]: {
    shouldNotify: true,
    shouldLog: true,
    shouldRedirect: false,
    retryable: true,
    notificationType: "notification",
    severity: "error",
  },
  [ErrorType.AUTH]: {
    shouldNotify: true,
    shouldLog: true,
    shouldRedirect: true,
    retryable: false,
    notificationType: "message",
    severity: "warning",
    redirectPath: "/login",
  },
  [ErrorType.PERMISSION]: {
    shouldNotify: true,
    shouldLog: true,
    shouldRedirect: true,
    retryable: false,
    notificationType: "message",
    severity: "warning",
    redirectPath: "/403",
  },
  [ErrorType.VALIDATION]: {
    shouldNotify: true,
    shouldLog: false,
    shouldRedirect: false,
    retryable: false,
    notificationType: "message",
    severity: "warning",
  },
  [ErrorType.NOT_FOUND]: {
    shouldNotify: true,
    shouldLog: true,
    shouldRedirect: false,
    retryable: false,
    notificationType: "message",
    severity: "warning",
  },
  [ErrorType.SERVER]: {
    shouldNotify: true,
    shouldLog: true,
    shouldRedirect: false,
    retryable: true,
    notificationType: "notification",
    severity: "error",
  },
  [ErrorType.TIMEOUT]: {
    shouldNotify: true,
    shouldLog: true,
    shouldRedirect: false,
    retryable: true,
    notificationType: "notification",
    severity: "error",
  },
  [ErrorType.BUSINESS]: {
    shouldNotify: true,
    shouldLog: true,
    shouldRedirect: false,
    retryable: false,
    notificationType: "message",
    severity: "warning",
  },
  [ErrorType.UNKNOWN]: {
    shouldNotify: true,
    shouldLog: true,
    shouldRedirect: false,
    retryable: false,
    notificationType: "message",
    severity: "error",
  },
};

// ==================== HTTP 状态码映射 ====================

function statusToErrorType(status: number): ErrorType {
  if (status === 400 || status === 422) return ErrorType.VALIDATION;
  if (status === 401) return ErrorType.AUTH;
  if (status === 403) return ErrorType.PERMISSION;
  if (status === 404) return ErrorType.NOT_FOUND;
  if (status === 408 || status === 504) return ErrorType.TIMEOUT;
  if (status >= 500) return ErrorType.SERVER;
  return ErrorType.UNKNOWN;
}

// ==================== 错误解析 ====================

export function parseError(error: any): AppError {
  const timestamp = Date.now();

  // Axios response error
  if (error?.response) {
    const { status, data } = error.response;
    const type = statusToErrorType(status);
    const message =
      data?.message ||
      data?.detail ||
      data?.error?.message ||
      `请求失败 (${status})`;
    return {
      type,
      message: typeof message === "string" ? message : `请求失败 (${status})`,
      code: status,
      details: data,
      retryable: defaultStrategies[type].retryable,
      timestamp,
    };
  }

  // Axios network/timeout error (has request but no response)
  if (error?.request) {
    if (error.code === "ECONNABORTED" || error.message?.includes("timeout")) {
      return {
        type: ErrorType.TIMEOUT,
        message: error.message || "请求超时",
        code: error.code,
        details: undefined,
        retryable: true,
        timestamp,
      };
    }
    return {
      type: ErrorType.NETWORK,
      message: error.message || "网络连接失败",
      code: error.code,
      details: undefined,
      retryable: true,
      timestamp,
    };
  }

  // Business error (has code property as string)
  if (
    error?.code &&
    typeof error.code === "string" &&
    error.code !== "ECONNABORTED"
  ) {
    return {
      type: ErrorType.BUSINESS,
      message: error.message || "业务错误",
      code: error.code,
      details: error.details,
      retryable: false,
      timestamp,
    };
  }

  // Standard Error object / Plain object with message / String — unified unknown error
  const buildUnknown = (msg: string) => ({
    type: ErrorType.UNKNOWN,
    message: msg,
    details: undefined,
    retryable: false,
    timestamp,
  });
  if (error instanceof Error) return buildUnknown(error.message);
  if (error && typeof error.message === "string")
    return buildUnknown(error.message);
  if (typeof error === "string") return buildUnknown(error);

  // Unknown
  return {
    type: ErrorType.UNKNOWN,
    message: String(error ?? "未知错误"),
    details: undefined,
    retryable: false,
    timestamp,
  };
}

// ==================== 错误处理 ====================

export function handleError(
  error: any,
  showMessage: boolean | string = "操作失败",
): AppError {
  const appError = parseError(error);
  const strategy = {
    ...defaultStrategies[appError.type],
    ...customStrategies[appError.type],
  };
  const bus = getEventBus();

  // 发布事件
  const eventMap: Partial<Record<ErrorType, string>> = {
    [ErrorType.NETWORK]: "error:network",
    [ErrorType.SERVER]: "error:server",
    [ErrorType.VALIDATION]: "error:validation",
    [ErrorType.AUTH]: "auth:expired",
    [ErrorType.BUSINESS]: "error:business",
    [ErrorType.TIMEOUT]: "error:timeout",
    [ErrorType.PERMISSION]: "error:permission",
    [ErrorType.NOT_FOUND]: "error:not_found",
    [ErrorType.UNKNOWN]: "error:unknown",
  };
  const eventName = eventMap[appError.type];
  if (eventName) {
    bus.emit(eventName, appError);
  }

  // 显示消息
  if (showMessage && strategy.shouldNotify) {
    if (strategy.notificationType === "notification") {
      ElNotification({
        type: "error",
        title: "错误",
        message: appError.message,
      });
    } else {
      ElMessage.warning(appError.message);
    }
  }

  // 日志
  if (strategy.shouldLog) {
    logger.error("[Error]", appError);
  }

  return appError;
}

// ==================== 业务错误工厂 ====================

export function createBusinessError(
  code: string,
  message: string,
  details?: any,
): AppError {
  return {
    type: ErrorType.BUSINESS,
    message,
    code,
    details,
    retryable: false,
    timestamp: Date.now(),
  };
}

// ==================== 策略管理 ====================

const customStrategies: Partial<Record<ErrorType, Partial<ErrorStrategy>>> = {};

class ErrorHandler {
  getStrategy(errorType: ErrorType): ErrorStrategy {
    return { ...defaultStrategies[errorType], ...customStrategies[errorType] };
  }

  configureStrategy(errorType: ErrorType, overrides: Partial<ErrorStrategy>) {
    customStrategies[errorType] = {
      ...customStrategies[errorType],
      ...overrides,
    };
  }

  async handleAsyncOperation<T>(
    operation: () => Promise<T>,
    options: {
      successMessage?: string;
      showError?: boolean;
      retryCount?: number;
      retryDelay?: number;
      onRetry?: (attempt: number, error: any) => void;
    } = {},
  ): Promise<T | null> {
    const {
      successMessage,
      showError = true,
      retryCount = 0,
      retryDelay = 1000,
      onRetry,
    } = options;

    let lastError: any;

    for (let attempt = 0; attempt <= retryCount; attempt++) {
      try {
        const result = await operation();
        if (successMessage) {
          ElMessage.success(successMessage);
        }
        return result;
      } catch (error) {
        lastError = error;
        if (attempt < retryCount) {
          onRetry?.(attempt + 1, error);
          await new Promise((r) => setTimeout(r, retryDelay));
        }
      }
    }

    if (showError) {
      handleError(lastError, true);
    }
    return null;
  }
}

export const errorHandler = new ErrorHandler();

// ==================== 便捷方法 ====================

/**
 * 处理 API 错误（简化版）
 * @param error 错误对象
 * @param defaultMsg 默认错误消息
 * @returns 是否是用户取消操作
 */
export function handleApiError(
  error: any,
  defaultMsg: string = "操作失败",
): boolean {
  // 用户取消操作
  if (error === "cancel" || error?.message === "cancel") {
    return true;
  }

  handleError(error, defaultMsg);
  return false;
}

/**
 * 处理删除操作的错误
 */
export function handleDeleteError(error: any): boolean {
  return handleApiError(error, "删除失败");
}

/**
 * 处理保存操作的错误
 */
export function handleSaveError(error: any): boolean {
  return handleApiError(error, "保存失败");
}

/**
 * 处理加载操作的错误
 */
export function handleLoadError(error: any): boolean {
  return handleApiError(error, "加载失败");
}

/**
 * 处理导出操作的错误
 */
export function handleExportError(error: any): boolean {
  return handleApiError(error, "导出失败");
}

/**
 * 处理导入操作的错误
 */
export function handleImportError(error: any): boolean {
  return handleApiError(error, "导入失败");
}

export function setupGlobalErrorHandler() {
  // ── 同步未捕获异常 ──
  window.onerror = (message, source, lineno, colno, error) => {
    if (typeof message === "string") {
      // 忽略 ChunkLoadError（已由 ErrorBoundary 处理）
      if (message.includes("dynamically imported module")) {
        return false;
      }
      // 忽略 ResizeObserver 良性警告
      if (message.includes("ResizeObserver")) {
        return false;
      }
    }
    console.error("[GlobalError]", {
      message: String(message),
      source,
      line: lineno,
      col: colno,
      error: error instanceof Error ? error.message : error,
    });
    return false;
  };

  // ── 未处理 Promise rejection ──
  window.addEventListener("unhandledrejection", (event) => {
    const reason = event.reason;
    if (
      reason?.message?.includes("Failed to fetch dynamically imported module")
    ) {
      // ChunkLoadError → ErrorBoundary 已处理，仅记录
      console.warn("[UnhandledRejection] ChunkLoadError:", reason.message);
    } else if (reason?.response?.status === 401) {
      console.warn("[UnhandledRejection] 401 — token may be expired");
    } else {
      logger.error("[Unhandled Promise Rejection]", reason);
    }
    event.preventDefault();
  });
}

export default {
  handleError,
  setupGlobalErrorHandler,
  errorHandler,
  handleApiError,
  handleDeleteError,
  handleSaveError,
  handleLoadError,
  handleExportError,
  handleImportError,
};
