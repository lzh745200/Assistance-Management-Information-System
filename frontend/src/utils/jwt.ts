/**
 * JWT 工具模块
 * 提供 JWT Token 解析和验证功能
 */

// ==================== 常量定义 ====================

/** setTimeout 最大延迟（约 24.8 天） */
export const MAX_TIMEOUT_MS = 2147483647

/** 默认提前刷新时间：10 分钟 */
export const DEFAULT_REFRESH_BEFORE_EXPIRY_MS = 10 * 60 * 1000

/** 分段检查间隔：12 小时 */
export const RECHECK_INTERVAL_MS = 12 * 60 * 60 * 1000

/** 立即刷新的阈值：1 秒 */
export const IMMEDIATE_REFRESH_THRESHOLD_MS = 1000

// ==================== 类型定义 ====================

/** JWT Token 载荷 */
export interface JWTPayload {
  exp?: number
  sub?: string
  type?: string
  iat?: number
  [key: string]: unknown
}

// ==================== JWT 解析缓存 ====================

/** 缓存条目数上限 */
const MAX_CACHE_SIZE = 50

/** 缓存条目 TTL (5分钟) */
const CACHE_TTL_MS = 5 * 60 * 1000

interface CacheEntry {
  payload: JWTPayload
  timestamp: number
}

/** 简单的 JWT 解析结果缓存（带LRU清理） */
const jwtCache = new Map<string, CacheEntry>()

/** 获取缓存键（使用完整 token —— 截取前缀会导致同结构 token 碰撞，错返他人 payload） */
function getCacheKey(token: string): string {
  return token
}

/** 清理过期条目 */
function cleanupExpiredEntries(): void {
  const now = Date.now()
  for (const [key, entry] of jwtCache.entries()) {
    if (now - entry.timestamp > CACHE_TTL_MS) {
      jwtCache.delete(key)
    }
  }
}

/** 缓存 JWT 解析结果（带LRU限制） */
function cachePayload(token: string, payload: JWTPayload): void {
  const key = getCacheKey(token)

  // 如果已存在，先删除以更新插入顺序（LRU）
  if (jwtCache.has(key)) {
    jwtCache.delete(key)
  }

  // 如果达到上限，清理过期条目或移除最旧的
  if (jwtCache.size >= MAX_CACHE_SIZE) {
    cleanupExpiredEntries()
    // 如果仍然达到上限，移除最旧的条目
    if (jwtCache.size >= MAX_CACHE_SIZE) {
      const firstKey = jwtCache.keys().next().value
      if (firstKey !== undefined) {
        jwtCache.delete(firstKey)
      }
    }
  }

  jwtCache.set(key, { payload, timestamp: Date.now() })
}

/** 获取缓存的解析结果 */
function getCachedPayload(token: string): JWTPayload | undefined {
  const key = getCacheKey(token)
  const entry = jwtCache.get(key)

  if (!entry) return undefined

  // 检查是否过期
  if (Date.now() - entry.timestamp > CACHE_TTL_MS) {
    jwtCache.delete(key)
    return undefined
  }

  return entry.payload
}

// ==================== 核心函数 ====================

/**
 * 解码 JWT Token 载荷（不验证签名）
 * 支持 Base64URL 编码
 */
export function decodeJwtPayload(token: string): JWTPayload | null {
  // 检查缓存
  const cached = getCachedPayload(token)
  if (cached) return cached

  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null

    // Base64URL 转 Base64
    const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/')

    // 解码并处理 URI 编码
    const result = JSON.parse(
      decodeURIComponent(
        atob(payload)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )
    ) as JWTPayload

    // 缓存结果
    cachePayload(token, result)
    return result
  } catch (err) {
    logWarn('[JWT] 解码失败:', err)
    return null
  }
}

/**
 * 获取 Token 过期时间戳（毫秒）
 */
export function getTokenExpiry(token: string): number | null {
  const payload = decodeJwtPayload(token)
  if (!payload?.exp) return null
  return payload.exp * 1000 // 转换为毫秒
}

/**
 * 计算 Token 剩余有效时间（毫秒）
 */
export function getTimeUntilExpiry(token: string): number {
  const expiry = getTokenExpiry(token)
  if (!expiry) return 0
  return Math.max(0, expiry - Date.now())
}

/**
 * 检查 Token 是否已过期
 */
export function isTokenExpired(token: string): boolean {
  return getTimeUntilExpiry(token) <= 0
}

/**
 * 计算安全的刷新延迟时间（毫秒）
 * 确保不超过 setTimeout 最大限制（约 24.8 天）
 */
export function calculateRefreshDelay(
  timeUntilExpiry: number,
  refreshBeforeExpiry: number = DEFAULT_REFRESH_BEFORE_EXPIRY_MS
): number {
  const delay = Math.max(timeUntilExpiry - refreshBeforeExpiry, 0)
  return Math.min(delay, MAX_TIMEOUT_MS)
}

// 简单的警告日志函数，避免循环依赖
const logWarn = (message: string, context?: unknown): void => {
  // eslint-disable-next-line no-console
  console.warn(message, context)
}
