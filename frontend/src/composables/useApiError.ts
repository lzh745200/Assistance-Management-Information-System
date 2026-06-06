/**
 * API 错误处理 Composable
 */
import { ref } from "vue";

export interface ApiError {
  code: number;
  message: string;
  details?: any;
}

export function useApiError() {
  const error = ref<ApiError | null>(null);

  function handleError(err: any) {
    if (err?.response) {
      error.value = {
        code: err.response.status,
        message: err.response.data?.message || err.message || "请求失败",
        details: err.response.data,
      };
    } else if (err?.request) {
      error.value = { code: 0, message: "网络连接失败，请检查网络" };
    } else {
      error.value = { code: -1, message: err?.message || "未知错误" };
    }
    return error.value;
  }

  function clearError() {
    error.value = null;
  }

  return { error, handleError, clearError };
}
