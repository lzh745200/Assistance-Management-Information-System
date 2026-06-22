import { logger } from '@/utils/logger'

/**
 * 缓存管理器
 *
 * 实现带TTL、LRU淘汰和localStorage持久化的缓存层
 *
 * 功能特性:
 * - 可配置的TTL（生存时间）
 * - LRU（最近最少使用）淘汰策略
 * - localStorage持久化支持
 * - 缓存统计（命中率、大小等）
 * - 模式匹配失效（精确字符串和正则表达式）
 */

// ============================================================================
// 类型定义
// ============================================================================

/**
 * 缓存配置接口
 */
export interface CacheConfig {
  /** 最大缓存条目数 */
  maxSize: number
  /** 默认TTL（毫秒） */
  defaultTTL: number
  /** 需要持久化的键列表 */
  persistKeys: string[]
  /** localStorage前缀 */
  storagePrefix: string
}

/**
 * 缓存条目接口
 */
export interface CacheEntry<T = unknown> {
  /** 缓存值 */
  value: T
  /** 创建时间戳 */
  timestamp: number
  /** TTL（毫秒） */
  ttl: number
  /** 访问次数 */
  accessCount: number
  /** 最后访问时间 */
  lastAccess: number
}

/**
 * 缓存统计接口
 */
export interface CacheStats {
  /** 当前缓存大小 */
  size: number
  /** 命中次数 */
  hits: number
  /** 未命中次数 */
  misses: number
  /** 命中率 */
  hitRate: number
  /** 淘汰次数 */
  evictions: number
}

/**
 * 序列化后的缓存数据（用于localStorage）
 */
interface SerializedCache {
  entries: Array<[string, CacheEntry<unknown>]>
  version: number
}

// ============================================================================
// 默认配置
// ============================================================================

const DEFAULT_CONFIG: CacheConfig = {
  maxSize: 100,
  defaultTTL: 5 * 60 * 1000, // 5分钟
  persistKeys: [],
  storagePrefix: 'cache:',
}

const CACHE_VERSION = 1

// ============================================================================
// CacheManager 类
// ============================================================================

/**
 * 缓存管理器类
 *
 * @example
 * ```typescript
 * const cache = new CacheManager({ maxSize: 50, defaultTTL: 60000 })
 *
 * // 设置缓存
 * cache.set('user:1', { name: 'John' })
 *
 * // 获取缓存
 * const user = cache.get<User>('user:1')
 *
 * // 失效匹配的缓存
 * cache.invalidate(/^user:/)
 * ```
 */
export class CacheManager {
  private cache: Map<string, CacheEntry<unknown>>
  private config: CacheConfig
  private stats: {
    hits: number
    misses: number
    evictions: number
  }

  constructor(config: Partial<CacheConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config }
    this.cache = new Map()
    this.stats = {
      hits: 0,
      misses: 0,
      evictions: 0,
    }

    // 从localStorage恢复持久化数据
    this.restoreFromStorage()
  }

  /**
   * 获取缓存值
   *
   * @param key 缓存键
   * @returns 缓存值，如果不存在或已过期则返回undefined
   */
  get<T>(key: string): T | undefined {
    const entry = this.cache.get(key)

    if (!entry) {
      this.stats.misses++
      return undefined
    }

    // 检查是否过期
    if (this.isExpired(entry)) {
      this.delete(key)
      this.stats.misses++
      return undefined
    }

    // 更新访问信息（LRU）
    entry.accessCount++
    entry.lastAccess = Date.now()

    this.stats.hits++
    return entry.value as T
  }

  /**
   * 设置缓存值
   *
   * @param key 缓存键
   * @param value 缓存值
   * @param ttl 可选的TTL（毫秒），默认使用配置的defaultTTL
   */
  set<T>(key: string, value: T, ttl?: number): void {
    // 检查是否需要淘汰
    if (this.cache.size >= this.config.maxSize && !this.cache.has(key)) {
      this.evictLRU()
    }

    const now = Date.now()
    const entry: CacheEntry<T> = {
      value,
      timestamp: now,
      ttl: ttl ?? this.config.defaultTTL,
      accessCount: 1,
      lastAccess: now,
    }

    this.cache.set(key, entry)

    // 持久化到localStorage
    if (this.shouldPersist(key)) {
      this.persistToStorage()
    }
  }

  /**
   * 检查缓存键是否存在且未过期
   *
   * @param key 缓存键
   * @returns 是否存在
   */
  has(key: string): boolean {
    const entry = this.cache.get(key)
    if (!entry) return false
    if (this.isExpired(entry)) {
      this.delete(key)
      return false
    }
    return true
  }

  /**
   * 删除缓存条目
   *
   * @param key 缓存键
   * @returns 是否成功删除
   */
  delete(key: string): boolean {
    const result = this.cache.delete(key)
    if (result && this.shouldPersist(key)) {
      this.persistToStorage()
    }
    return result
  }

  /**
   * 失效匹配模式的缓存条目
   *
   * @param pattern 匹配模式（精确字符串或正则表达式）
   * @returns 被删除的条目数量
   */
  invalidate(pattern: string | RegExp): number {
    let count = 0
    const keysToDelete: string[] = []

    for (const key of this.cache.keys()) {
      const matches =
        typeof pattern === 'string' ? key === pattern || key.startsWith(pattern) : pattern.test(key)

      if (matches) {
        keysToDelete.push(key)
      }
    }

    for (const key of keysToDelete) {
      if (this.cache.delete(key)) {
        count++
      }
    }

    if (count > 0) {
      this.persistToStorage()
    }

    return count
  }

  /**
   * 清空所有缓存
   */
  clear(): void {
    this.cache.clear()
    this.stats = {
      hits: 0,
      misses: 0,
      evictions: 0,
    }
    this.clearStorage()
  }

  /**
   * 获取缓存统计信息
   *
   * @returns 缓存统计
   */
  getStats(): CacheStats {
    const total = this.stats.hits + this.stats.misses
    return {
      size: this.cache.size,
      hits: this.stats.hits,
      misses: this.stats.misses,
      hitRate: total > 0 ? this.stats.hits / total : 0,
      evictions: this.stats.evictions,
    }
  }

  /**
   * 获取所有缓存键
   *
   * @returns 缓存键数组
   */
  keys(): string[] {
    return Array.from(this.cache.keys())
  }

  /**
   * 获取缓存大小
   *
   * @returns 缓存条目数量
   */
  size(): number {
    return this.cache.size
  }

  // ============================================================================
  // 私有方法
  // ============================================================================

  /**
   * 检查缓存条目是否过期
   */
  private isExpired(entry: CacheEntry<unknown>): boolean {
    if (entry.ttl <= 0) return false // TTL为0或负数表示永不过期
    return Date.now() > entry.timestamp + entry.ttl
  }

  /**
   * LRU淘汰策略：淘汰最近最少使用的条目
   */
  private evictLRU(): void {
    let oldestKey: string | null = null
    let oldestAccess = Infinity

    for (const [key, entry] of this.cache.entries()) {
      if (entry.lastAccess < oldestAccess) {
        oldestAccess = entry.lastAccess
        oldestKey = key
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey)
      this.stats.evictions++
    }
  }

  /**
   * 检查键是否应该持久化
   */
  private shouldPersist(key: string): boolean {
    return this.config.persistKeys.some((pattern) => {
      if (pattern.includes('*')) {
        const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$')
        return regex.test(key)
      }
      return key === pattern || key.startsWith(pattern)
    })
  }

  /**
   * 持久化缓存到localStorage
   */
  private persistToStorage(): void {
    try {
      const entriesToPersist: Array<[string, CacheEntry<unknown>]> = []

      for (const [key, entry] of this.cache.entries()) {
        if (this.shouldPersist(key) && !this.isExpired(entry)) {
          entriesToPersist.push([key, entry])
        }
      }

      const data: SerializedCache = {
        entries: entriesToPersist,
        version: CACHE_VERSION,
      }

      localStorage.setItem(this.config.storagePrefix + 'data', JSON.stringify(data))
    } catch (error) {
      logger.warn('Failed to persist cache to localStorage:', error)
    }
  }

  /**
   * 从localStorage恢复缓存
   */
  private restoreFromStorage(): void {
    try {
      const stored = localStorage.getItem(this.config.storagePrefix + 'data')
      if (!stored) return

      const data: SerializedCache = JSON.parse(stored)

      // 版本检查
      if (data.version !== CACHE_VERSION) {
        this.clearStorage()
        return
      }

      for (const [key, entry] of data.entries) {
        // 跳过已过期的条目
        if (!this.isExpired(entry)) {
          this.cache.set(key, entry)
        }
      }
    } catch (error) {
      logger.warn('Failed to restore cache from localStorage:', error)
      this.clearStorage()
    }
  }

  /**
   * 清除localStorage中的缓存数据
   */
  private clearStorage(): void {
    try {
      localStorage.removeItem(this.config.storagePrefix + 'data')
    } catch (error) {
      logger.warn('Failed to clear cache from localStorage:', error)
    }
  }
}

// ============================================================================
// 序列化工具函数
// ============================================================================

/**
 * 序列化数据（用于缓存存储）
 *
 * @param data 要序列化的数据
 * @returns JSON字符串
 */
export function serialize<T>(data: T): string {
  return JSON.stringify(data)
}

/**
 * 反序列化数据（从缓存恢复）
 *
 * @param str JSON字符串
 * @returns 反序列化后的数据
 */
export function deserialize<T>(str: string): T {
  return JSON.parse(str) as T
}

// ============================================================================
// 默认实例导出
// ============================================================================

/**
 * 默认缓存管理器实例
 */
export const cacheManager = new CacheManager()

export default CacheManager
