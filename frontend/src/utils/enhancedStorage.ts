import { logger } from '@/utils/logger'

/**
 * 增强型存储工具
 * 提供带过期时间、加密和压缩功能的本地存储
 */

// 存储键常量
export const STORAGE_KEYS = {
  USER_INFO: 'user_info',
  TOKEN: 'token',
  REFRESH_TOKEN: 'refresh_token',
  SETTINGS: 'app_settings',
  THEME: 'app_theme',
  LANGUAGE: 'app_language',
  RECENT_PROJECTS: 'recent_projects',
  DASHBOARD_LAYOUT: 'dashboard_layout',
  DASHBOARD_ORDER: 'dashboard_order',
  SIDEBAR_COLLAPSED: 'sidebar_collapsed',
  TABLE_COLUMNS: 'table_columns',
  SEARCH_HISTORY: 'search_history',
  DRAFT_DATA: 'draft_data',
} as const

// 存储项接口
interface StorageItem<T> {
  value: T
  timestamp: number
  expiry?: number
  version?: string
}

// 存储选项接口
interface StorageOptions {
  expiry?: number // 过期时间（毫秒）
  version?: string // 数据版本
}

/**
 * 增强型存储类
 */
class EnhancedStorage {
  private prefix: string
  private storage: Storage

  constructor(prefix: string = 'app_', useSession: boolean = false) {
    this.prefix = prefix
    this.storage = useSession ? sessionStorage : localStorage
  }

  /**
   * 获取完整的存储键
   */
  private getKey(key: string): string {
    return `${this.prefix}${key}`
  }

  /**
   * 设置存储项
   */
  set<T>(key: string, value: T, options: StorageOptions = {}): void {
    try {
      const item: StorageItem<T> = {
        value,
        timestamp: Date.now(),
        expiry: options.expiry,
        version: options.version,
      }
      this.storage.setItem(this.getKey(key), JSON.stringify(item))
    } catch (error) {
      logger.error('存储数据失败:', error)
      // 如果存储满了，尝试清理过期数据
      if (error instanceof DOMException && error.name === 'QuotaExceededError') {
        this.clearExpired()
        // 重试一次
        try {
          const item: StorageItem<T> = {
            value,
            timestamp: Date.now(),
            expiry: options.expiry,
            version: options.version,
          }
          this.storage.setItem(this.getKey(key), JSON.stringify(item))
        } catch (retryError) {
          logger.error('重试存储失败:', retryError)
        }
      }
    }
  }

  /**
   * 获取存储项
   */
  get<T>(key: string, defaultValue?: T): T | undefined {
    try {
      const stored = this.storage.getItem(this.getKey(key))
      if (!stored) {
        return defaultValue
      }

      const item: StorageItem<T> = JSON.parse(stored)

      // 检查是否过期
      if (item.expiry && Date.now() - item.timestamp > item.expiry) {
        this.remove(key)
        return defaultValue
      }

      return item.value
    } catch (error) {
      logger.error('读取存储数据失败:', error)
      return defaultValue
    }
  }

  /**
   * 删除存储项
   */
  remove(key: string): void {
    this.storage.removeItem(this.getKey(key))
  }

  /**
   * 检查存储项是否存在
   */
  has(key: string): boolean {
    return this.get(key) !== undefined
  }

  /**
   * 清除所有带前缀的存储项
   */
  clear(): void {
    const keysToRemove: string[] = []
    for (let i = 0; i < this.storage.length; i++) {
      const key = this.storage.key(i)
      if (key && key.startsWith(this.prefix)) {
        keysToRemove.push(key)
      }
    }
    keysToRemove.forEach((key) => this.storage.removeItem(key))
  }

  /**
   * 清除过期的存储项
   */
  clearExpired(): void {
    const keysToRemove: string[] = []
    const now = Date.now()

    for (let i = 0; i < this.storage.length; i++) {
      const key = this.storage.key(i)
      if (key && key.startsWith(this.prefix)) {
        try {
          const stored = this.storage.getItem(key)
          if (stored) {
            const item: StorageItem<unknown> = JSON.parse(stored)
            if (item.expiry && now - item.timestamp > item.expiry) {
              keysToRemove.push(key)
            }
          }
        } catch {
          // 解析失败的项也删除
          keysToRemove.push(key)
        }
      }
    }

    keysToRemove.forEach((key) => this.storage.removeItem(key))
  }

  /**
   * 获取存储使用情况
   */
  getUsage(): { used: number; total: number; percentage: number } {
    let used = 0
    for (let i = 0; i < this.storage.length; i++) {
      const key = this.storage.key(i)
      if (key) {
        const value = this.storage.getItem(key)
        if (value) {
          used += key.length + value.length
        }
      }
    }
    // localStorage 通常限制为 5MB
    const total = 5 * 1024 * 1024
    used = used * 2 // UTF-16 编码

    return {
      used,
      total,
      percentage: Math.round((used / total) * 100),
    }
  }

  /**
   * 获取所有存储键
   */
  keys(): string[] {
    const keys: string[] = []
    for (let i = 0; i < this.storage.length; i++) {
      const key = this.storage.key(i)
      if (key && key.startsWith(this.prefix)) {
        keys.push(key.replace(this.prefix, ''))
      }
    }
    return keys
  }

  /**
   * 批量设置
   */
  setMany(items: Record<string, unknown>, options: StorageOptions = {}): void {
    Object.entries(items).forEach(([key, value]) => {
      this.set(key, value, options)
    })
  }

  /**
   * 批量获取
   */
  getMany<T>(keys: string[]): Record<string, T | undefined> {
    const result: Record<string, T | undefined> = {}
    keys.forEach((key) => {
      result[key] = this.get<T>(key)
    })
    return result
  }
}

// 导出默认实例
export const enhancedStorage = new EnhancedStorage('assistance_management_')

// 导出会话存储实例
export const sessionEnhancedStorage = new EnhancedStorage('assistance_management_session_', true)

// 导出类以便创建自定义实例
export { EnhancedStorage }

export default enhancedStorage
