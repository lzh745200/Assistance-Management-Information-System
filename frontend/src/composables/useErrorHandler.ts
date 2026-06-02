/**
 * 统一错误处理 Composable
 *
 * 提供控制台日志 + 用户可见通知的双通道错误反馈。
 * 取代之前的 console.error-only 模式，确保用户能感知操作失败。
 */
import { ref } from "vue";
import { ElMessage } from "element-plus";

export interface ErrorState {
  message: string;
  code?: string | number;
  details?: any;
}

export function useErrorHandler() {
  const errorState = ref<ErrorState | null>(null);

  /**
   * 处理错误：记录控制台日志 + 展示用户通知
   *
   * @param err - 错误对象
   * @param context - 操作上下文描述（如"加载预算数据"）
   * @param showNotification - 是否展示用户通知（默认 true）
   */
  function handleError(err: any, context?: string, showNotification: boolean = true) {
    const message =
      err?.response?.data?.message ||
      err?.response?.data?.detail ||
      err?.message ||
      err ||
      "未知错误";

    const userMessage = context
      ? `${context}失败: ${message}`
      : `操作失败: ${message}`;

    errorState.value = {
      message: userMessage,
      code: err?.response?.status || err?.code,
      details: err?.response?.data || err,
    };

    // 控制台日志（用于调试）
    console.error("[ErrorHandler]", context || "unknown context", errorState.value);

    // 用户可见通知（Element Plus ElMessage）
    if (showNotification) {
      ElMessage({
        type: "error",
        message: userMessage,
        duration: 5000,
        showClose: true,
      });
    }

    return errorState.value;
  }

  /**
   * 处理警告：展示用户通知但不标记为 error
   */
  function handleWarning(message: string) {
    console.warn("[WarningHandler]", message);
    ElMessage({
      type: "warning",
      message,
      duration: 3000,
      showClose: true,
    });
  }

  /**
   * 处理成功消息
   */
  function handleSuccess(message: string) {
    ElMessage({
      type: "success",
      message,
      duration: 2000,
    });
  }

  function clearError() {
    errorState.value = null;
  }

  return { errorState, handleError, handleWarning, handleSuccess, clearError };
}
