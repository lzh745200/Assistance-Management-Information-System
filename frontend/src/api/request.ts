/**
 * Axios HTTP 请求封装
 */
import axios, { type AxiosRequestConfig, type Canceler } from "axios";
import { AuthStorage } from "@/utils/authStorage";

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
function _makeRequestKey(method: string | undefined, url: string | undefined, params: any): string {
  const serialized = JSON.stringify(params || {}, Object.keys(params || {}).sort());
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
    const requestKey = _makeRequestKey(response.config.method, response.config.url, response.config.params);
    pendingRequests.delete(requestKey);
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      _cachedToken = null;
      AuthStorage.clear();
      // 委托路由守卫处理跳转（whiteList: /login, /register, /forgot-password）
    }
    return Promise.reject(error);
  },
);

/** 更新 token 缓存（登录/登出时由 auth store 调用） */
export function _setCachedToken(t: string | null) {
  _cachedToken = t;
}

// ── 泛型核心请求函数 ──

export async function apiRequest<T = any>(config: AxiosRequestConfig): Promise<T> {
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
