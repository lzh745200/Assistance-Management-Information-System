/**
 * Axios HTTP 请求封装
 */
import axios, { type AxiosRequestConfig, type Canceler } from "axios";
import { ElMessage } from "element-plus";
import { AuthStorage } from "@/utils/authStorage";
import { safeArray } from "@/composables/useSafeData";
import { isOfflineMode, getMockResponse } from "@/utils/offlineMock";

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

export type RequestConfig = AxiosRequestConfig;

// 跟踪待处理请求
const pendingRequests = new Map<string, Canceler>();

/** 内存缓存 token，避免每条请求都读 sessionStorage */
let _cachedToken: string | null = null;

/** 生成稳定排序的请求标识 key */
function _makeRequestKey(
  method: string | undefined,
  url: string | undefined,
  params: any,
): string {
  const serialized = JSON.stringify(
    params || {},
    Object.keys(params || {}).sort(),
  );
  return `${method}:${url}:${serialized}`;
}

request.interceptors.request.use((config) => {
  if (_cachedToken === null) {
    _cachedToken = AuthStorage.getToken();
  }
  if (_cachedToken) {
    config.headers.Authorization = `Bearer ${_cachedToken}`;
  }
  const requestKey = _makeRequestKey(config.method, config.url, config.params);
  if (pendingRequests.has(requestKey)) {
    pendingRequests.get(requestKey)!();
  }
  config.cancelToken = new axios.CancelToken((cancel) => {
    pendingRequests.set(requestKey, cancel);
  });
  return config;
});

request.interceptors.response.use(
  (response) => {
    const requestKey = _makeRequestKey(
      response.config.method,
      response.config.url,
      response.config.params,
    );
    pendingRequests.delete(requestKey);

    // ── 脏数据过滤：使用 safeData 守卫确保常见字段类型安全 ──
    const data = response.data;
    if (data && typeof data === "object") {
      // 安全化 items 字段（非数组 → []）
      if ("items" in data) {
        const safe = safeArray(data.items);
        if (safe !== data.items) {
          console.warn(
            "[API] 'items' field sanitized (was not an array)",
            data,
          );
          data.items = safe;
        }
      }
      // 安全化 data 字段（null → {}）
      if ("data" in data && (data.data === null || data.data === undefined)) {
        data.data = {};
      }
      // 安全化 total 字段（非数字 → items.length）
      if ("total" in data && typeof data.total !== "number") {
        data.total = safeArray(data.items).length;
      }
    }
    return response;
  },
  (error) => {
    // ── 已取消的请求不提示 ──
    if (error.__CANCEL__ || error.code === "ERR_CANCELED") {
      return Promise.reject(error);
    }

    // ── HTTP 状态码分类处理 ──
    if (error.response) {
      const { status, data } = error.response;
      if (status === 401) {
        _cachedToken = null;
        AuthStorage.clear();
        ElMessage.error("登录已过期，请重新登录");
      } else if (status === 403) {
        ElMessage.error(data?.detail || "权限不足，无法执行此操作");
      } else if (status >= 500) {
        ElMessage.error("服务器错误，请稍后重试");
      } else if (status === 404) {
        console.warn(`[API] 404: ${error.config?.url}`);
      } else {
        console.error(
          "[API] Request failed:",
          status,
          data?.detail || data?.message || "",
        );
      }
    } else if (
      error.code === "ERR_NETWORK" ||
      error.message?.includes("NetworkError")
    ) {
      // 离线回退：检查是否处于离线模式，尝试从离线 Mock 提供数据
      if (isOfflineMode()) {
        const { method, url } = error.config || {};
        const mockData = getMockResponse(method || "GET", url || "");
        if (mockData) {
          console.info("[API] Offline fallback:", method, url);
          return Promise.resolve(mockData);
        }
      }
      ElMessage.error("网络连接失败，请检查服务是否启动");
    } else if (error.code === "ECONNABORTED") {
      ElMessage.warning("请求超时，请重试");
    } else {
      console.error("[API] Unexpected error:", error.message || error);
    }

    return Promise.reject(error);
  },
);

/** 更新 token 缓存（登录/登出时由 auth store 调用） */
export function _setCachedToken(t: string | null) {
  _cachedToken = t;
}

// ── 泛型核心请求函数 ──

export async function apiRequest<T = any>(
  config: AxiosRequestConfig,
): Promise<T> {
  const res = await request.request<T>(config);
  return res.data;
}

// ── 便捷方法别名 ──

export async function get<T = any>(url: string, params?: any): Promise<T> {
  return apiRequest<T>({ method: "GET", url, params });
}

export async function post<T = any>(url: string, data?: any): Promise<T> {
  return apiRequest<T>({ method: "POST", url, data });
}

export async function put<T = any>(url: string, data?: any): Promise<T> {
  return apiRequest<T>({ method: "PUT", url, data });
}

export async function del<T = any>(url: string): Promise<T> {
  return apiRequest<T>({ method: "DELETE", url });
}

export async function patch<T = any>(url: string, data?: any): Promise<T> {
  return apiRequest<T>({ method: "PATCH", url, data });
}

// ── 取消管理 ──

/** 取消指定 URL 的挂起请求（精确匹配 URL 段，避免子串误伤） */
export function cancelRequest(url: string): void {
  const urlSegment = `:${url}:`;
  for (const [key, cancel] of pendingRequests.entries()) {
    if (key.includes(urlSegment)) {
      cancel();
      pendingRequests.delete(key);
    }
  }
}

/** 取消所有挂起请求 */
export function cancelAllRequests(): void {
  for (const cancel of pendingRequests.values()) {
    cancel();
  }
  pendingRequests.clear();
}

/** 检查错误是否为请求取消 */
export function isRequestCancelled(error: any): boolean {
  return axios.isCancel(error);
}

/** 获取挂起请求数量 */
export function getPendingRequestCount(): number {
  return pendingRequests.size;
}

/** 创建可取消请求 */
export function createCancelableRequest<T = any>(
  config: AxiosRequestConfig,
): { promise: Promise<T>; cancel: Canceler } {
  const source = axios.CancelToken.source();
  const promise = request({
    ...config,
    cancelToken: source.token,
  }) as Promise<T>;
  return { promise, cancel: source.cancel };
}

/** 带超时的请求 */
export function requestWithTimeout<T = any>(
  config: AxiosRequestConfig,
  timeoutMs: number,
): Promise<T> {
  return new Promise((resolve, reject) => {
    const { promise, cancel } = createCancelableRequest<T>(config);
    const timer = setTimeout(() => {
      cancel();
      reject(new Error(`Request timeout after ${timeoutMs}ms`));
    }, timeoutMs);
    promise.then(resolve, reject).finally(() => clearTimeout(timer));
  });
}

/** 检查响应是否成功 */
export function isSuccess(status: number): boolean {
  return status >= 200 && status < 300;
}

export default request;
