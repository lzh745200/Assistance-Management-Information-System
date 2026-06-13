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

/**
 * RESPONSE UNWRAP INTERCEPTOR
 *
 * Backend wraps most responses as: { code: 200, data: <payload>, message: "success" }
 * This interceptor expands <payload> keys into the top-level response.data object
 * so callers can access fields directly without `.data.data.xxx`.
 *
 * Behavior:
 * - Object payload → keys copied to response.data (existing keys like code/message/data preserved)
 * - Array payload  → set as response.data.items (if items not already present)
 *
 * IMPORTANT: This mutates response.data IN PLACE. Both raw axios callers (Pattern A:
 * `import request from "./request"` → use `.data`) and auto-unwrapped callers (Pattern B:
 * `import { get, post } from "./request"` → `.data` NOT needed) see the same expanded shape.
 *
 * @see apiRequest — auto-unwrapped access (returns res.data directly)
 */
request.interceptors.response.use(
  (response) => {
    const requestKey = _makeRequestKey(
      response.config.method,
      response.config.url,
      response.config.params,
    );
    pendingRequests.delete(requestKey);

    // ── 统一响应格式：自动展开 {data: payload} → 顶层字段 ──
    // 保持 data 键不变以兼容旧代码（res.data / res.data.data），同时将内部字段提升到顶层
    // 注意：不覆盖 code/message/data 顶层键（若 payload 内同名字段需通过 .data.xxx 访问）
    const data = response.data;
    if (data && typeof data === "object") {
      if ("data" in data) {
        const inner = data.data;
        if (inner !== null && inner !== undefined) {
          if (typeof inner === "object" && !Array.isArray(inner)) {
            // 对象 → 展开到顶层，但跳过已有键（保护 code/message/data 元数据）
            for (const key of Object.keys(inner)) {
              if (!(key in data)) {
                data[key] = inner[key];
              }
            }
          } else if (Array.isArray(inner)) {
            // 数组 → 设为 items（不覆盖已有 items）
            if (!("items" in data)) {
              data.items = inner;
            }
          }
        }
      }
      // 安全化 items 字段（非数组 → []）
      if ("items" in data) {
        const safe = safeArray(data.items);
        if (safe !== data.items) {
          console.warn("[API] 'items' field sanitized (was not an array)", data);
          data.items = safe;
        }
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
      if (isOfflineMode() && error.config) {
        const { method, url } = error.config;
        const mockData = getMockResponse(method || "GET", url || "");
        if (mockData) {
          // 清理 pending 请求追踪（模拟成功拦截器的清理逻辑）
          const requestKey = `${method}:${url}`;
          pendingRequests.delete(requestKey);
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

/**
 * Generic request function with automatic response unwrapping.
 *
 * Unlike raw `request.get()` which returns `AxiosResponse<T>`,
 * this function returns `T` directly (`res.data`), unwrapping one level.
 *
 * Combined with the response interceptor's in-place expansion,
 * callers receive the backend's `data` payload directly.
 *
 * USAGE: Prefer `get<T>(url)` / `post<T>(url, data)` convenience wrappers.
 *        DO NOT access `.data` on their return values — they are already unwrapped.
 *
 * @example
 *   // Pattern B — auto-unwrapped via apiRequest()
 *   const items = await get<Item[]>("/items");  // Item[], not AxiosResponse
 *   items[0].name   // correct
 *   items.data      // WRONG (double-unwrap)
 *
 *   // Pattern A — raw axios instance
 *   const res = await request.get<Item[]>("/items");
 *   res.data[0].name  // correct (.data needed on AxiosResponse)
 */
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

export async function post<T = any>(url: string, data?: any, extra?: AxiosRequestConfig): Promise<T> {
  const config: AxiosRequestConfig = { method: "POST", url, data, ...(extra || {}) };
  if (data instanceof FormData && config.headers) {
    // 移除 Content-Type 让浏览器自动设置 multipart boundary
    // 保留其他自定义 headers（如 Authorization）
    const h = { ...config.headers } as Record<string, any>;
    delete h["Content-Type"];
    delete h["content-type"];
    config.headers = h;
  }
  return apiRequest<T>(config);
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
