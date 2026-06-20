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
  // 携带凭证（Cookie）：CSRF Double Submit Cookie 模式需要跨域/同源均能携带
  // csrftoken Cookie，服务端 CORS 已开启 allow_credentials。
  withCredentials: true,
});

export type RequestConfig = AxiosRequestConfig;

// 跟踪待处理请求
const pendingRequests = new Map<string, Canceler>();

/** 内存缓存 token，避免每条请求都读 sessionStorage */
let _cachedToken: string | null = null;

// ── CSRF Token 管理（Double Submit Cookie 模式）──
// 后端开启 CSRF 保护后，POST/PUT/DELETE/PATCH 需在 X-CSRF-Token 头回填 token。
// token 来源：优先从 csrftoken Cookie 读取；若无则懒加载 GET /auth/csrf-token 获取
// （响应会同时 Set-Cookie）。测试环境（MODE=test）不发起自动获取，避免影响单测。
const _CSRF_COOKIE_NAME = "csrftoken";
const _CSRF_HEADER_NAME = "X-CSRF-Token";
const _CSRF_TOKEN_ENDPOINT = "/auth/csrf-token";
const _UNSAFE_METHODS = new Set(["post", "put", "delete", "patch"]);
const _isTestEnv = import.meta.env.MODE === "test";
let _csrfToken: string | null = null;
let _csrfFetchInFlight: Promise<string | null> | null = null;

/** 从 document.cookie 读取指定 cookie 值 */
function _readCookie(name: string): string | null {
  if (typeof document === "undefined" || !document.cookie) return null;
  const match = document.cookie.match(
    new RegExp(
      "(?:^|; )" +
        name.replace(/([.$?*|{}()[\]\\/+^])/g, "\\$1") +
        "=([^;]*)",
    ),
  );
  return match ? decodeURIComponent(match[1]) : null;
}

/**
 * 确保已获取 CSRF token（cookie 优先，缺失时懒加载一次）。
 * 测试环境直接返回 null，不发起网络请求。
 */
async function _ensureCsrfToken(): Promise<string | null> {
  if (_csrfToken) return _csrfToken;
  // 1. 优先从 cookie 读取（Double Submit Cookie）
  const fromCookie = _readCookie(_CSRF_COOKIE_NAME);
  if (fromCookie) {
    _csrfToken = fromCookie;
    return _csrfToken;
  }
  // 2. 测试环境不自动获取，避免单测触发真实网络请求
  if (_isTestEnv || typeof document === "undefined") return null;
  // 3. 懒加载获取（去重并发请求）
  if (!_csrfFetchInFlight) {
    _csrfFetchInFlight = (async () => {
      try {
        // 用裸 axios.get 绕过自身拦截器，避免递归（GET 为安全方法本就不会触发 CSRF 分支）
        const res = await axios.get(
          (import.meta.env.VITE_API_BASE_URL || "/api/v1") +
            _CSRF_TOKEN_ENDPOINT,
          { withCredentials: true },
        );
        const token =
          (res.data && (res.data as any)?.data?.csrf_token) ||
          (res.data && (res.data as any)?.csrf_token) ||
          _readCookie(_CSRF_COOKIE_NAME);
        if (token) _csrfToken = token as string;
        return _csrfToken;
      } catch {
        // 获取失败不阻断请求；服务端会返回 403 由响应拦截器处理
        return null;
      } finally {
        _csrfFetchInFlight = null;
      }
    })();
  }
  await _csrfFetchInFlight;
  return _csrfToken;
}

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

request.interceptors.request.use(async (config) => {
  if (_cachedToken === null) {
    _cachedToken = AuthStorage.getToken();
  }
  if (_cachedToken) {
    config.headers.Authorization = `Bearer ${_cachedToken}`;
  }
  // ── CSRF：不安全方法自动回填 X-CSRF-Token ──
  const method = (config.method || "get").toLowerCase();
  if (_UNSAFE_METHODS.has(method)) {
    const token = await _ensureCsrfToken();
    if (token) {
      config.headers[_CSRF_HEADER_NAME] = token;
    }
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
          console.warn(
            "[API] 'items' field sanitized (was not an array)",
            data,
          );
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
        // 跳转登录页：避免在测试环境/已登录页重复跳转
        if (
          typeof window !== "undefined" &&
          !_isTestEnv &&
          !window.location.pathname.startsWith("/login")
        ) {
          window.location.href = "/login";
        }
      } else if (status === 403) {
        // CSRF 校验失败时重置 token 缓存，下次不安全请求重新获取
        const msg: string = data?.detail || data?.message || "";
        if (msg.includes("CSRF") || msg.includes("csrf")) {
          _csrfToken = null;
          ElMessage.error("安全校验已过期，请重试（CSRF）");
        } else {
          ElMessage.error(msg || "权限不足，无法执行此操作");
        }
      } else if (status === 404) {
        // 404 资源不存在：弹窗提示（避免静默失败）
        const url = error.config?.url || "";
        ElMessage.warning(
          data?.detail || data?.message || `请求的资源不存在: ${url}`,
        );
      } else if (status >= 500) {
        ElMessage.error("服务器错误，请稍后重试");
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

/** 主动获取并缓存 CSRF token（应用初始化/登录后可调用以预热） */
export async function prefetchCsrfToken(): Promise<string | null> {
  return _ensureCsrfToken();
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

export async function post<T = any>(
  url: string,
  data?: any,
  extra?: AxiosRequestConfig,
): Promise<T> {
  const config: AxiosRequestConfig = {
    method: "POST",
    url,
    data,
    ...(extra || {}),
  };
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
