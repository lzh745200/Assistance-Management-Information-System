import { logger } from '@/utils/logger'

/**
 * 请求去重器
 *
 * 用于合并并发的相同请求，避免重复请求
 *
 * Feature: frontend-production-readiness
 * Validates: Requirements 3.5
 */

// ==================== 类型定义 ====================

/** 请求去重器配置 */
export interface RequestDeduplicatorConfig {
  /** 最大并发请求数 */
  maxConcurrent?: number
  /** 请求超时时间（毫秒） */
  timeout?: number
}

/** 待处理请求信息 */
interface PendingRequest<T> {
  promise: Promise<T>
  resolve: (value: T) => void
  reject: (reason: any) => void
  subscribers: Array<{
    resolve: (value: T) => void
    reject: (reason: any) => void
  }>
  cancelled: boolean
}

// ==================== 请求去重器类 ====================

/**
 * 请求去重器
 *
 * 当多个相同的请求同时发起时，只执行一次实际请求，
 * 所有调用者共享同一个请求结果
 *
 * @example
 * ```ts
 * const deduplicator = new RequestDeduplicator()
 *
 * // 这三个调用只会发起一次实际请求
 * const [result1, result2, result3] = await Promise.all([
 *   deduplicator.dedupe('user:1', () => fetchUser(1)),
 *   deduplicator.dedupe('user:1', () => fetchUser(1)),
 *   deduplicator.dedupe('user:1', () => fetchUser(1))
 * ])
 * ```
 */
export class RequestDeduplicator {
  /** 待处理的请求映射 */
  private pending: Map<string, PendingRequest<any>> = new Map()

  /** 配置 */
  private _config: Required<RequestDeduplicatorConfig>

  constructor(config: RequestDeduplicatorConfig = {}) {
    this._config = {
      maxConcurrent: config.maxConcurrent ?? 10,
      timeout: config.timeout ?? 30000,
    }
  }

  /** 获取配置 */
  getConfig(): Required<RequestDeduplicatorConfig> {
    return { ...this._config }
  }

  /**
   * 去重执行请求
   *
   * @param key 请求的唯一标识
   * @param request 实际请求函数
   * @returns 请求结果
   */
  async dedupe<T>(key: string, request: () => Promise<T>): Promise<T> {
    // 如果已有相同key的请求在进行中，订阅该请求
    const existingRequest = this.pending.get(key)
    if (existingRequest && !existingRequest.cancelled) {
      return new Promise<T>((resolve, reject) => {
        existingRequest.subscribers.push({ resolve, reject })
      })
    }

    // 创建新的请求
    let pendingResolve: (value: T) => void
    let pendingReject: (reason: any) => void

    const promise = new Promise<T>((resolve, reject) => {
      pendingResolve = resolve
      pendingReject = reject
    })

    const pendingRequest: PendingRequest<T> = {
      promise,
      resolve: pendingResolve!,
      reject: pendingReject!,
      subscribers: [],
      cancelled: false,
    }

    this.pending.set(key, pendingRequest)

    try {
      // 执行实际请求
      const result = await request()

      // 如果请求被取消，不处理结果
      if (pendingRequest.cancelled) {
        return promise
      }

      // 解析主请求
      pendingRequest.resolve(result)

      // 解析所有订阅者
      pendingRequest.subscribers.forEach((sub) => sub.resolve(result))

      return result
    } catch (error) {
      // 如果请求被取消，不处理错误
      if (pendingRequest.cancelled) {
        return promise
      }

      // Suppress unhandled rejection on the internal promise
      // (the caller receives the error via the re-throw below)
      pendingRequest.promise.catch((err) => {
        // Log suppressed error for debugging
        logger.debug('[RequestDeduplicator] Suppressed promise rejection:', err)
      })

      // 拒绝主请求
      pendingRequest.reject(error)

      // 拒绝所有订阅者
      pendingRequest.subscribers.forEach((sub) => sub.reject(error))

      throw error
    } finally {
      // 清理已完成的请求
      if (!pendingRequest.cancelled) {
        this.pending.delete(key)
      }
    }
  }

  /**
   * 获取待处理请求数量
   */
  getPendingCount(): number {
    return this.pending.size
  }

  /**
   * 检查指定key是否有待处理的请求
   */
  isPending(key: string): boolean {
    const request = this.pending.get(key)
    return request !== undefined && !request.cancelled
  }

  /**
   * 获取所有待处理请求的key
   */
  getPendingKeys(): string[] {
    const keys: string[] = []
    this.pending.forEach((request, key) => {
      if (!request.cancelled) {
        keys.push(key)
      }
    })
    return keys
  }

  /**
   * 取消指定key的请求
   *
   * @param key 请求的唯一标识
   * @returns 是否成功取消
   */
  cancel(key: string): boolean {
    const request = this.pending.get(key)
    if (!request || request.cancelled) {
      return false
    }

    request.cancelled = true
    this.pending.delete(key)

    // Suppress unhandled rejection on the internal promise
    request.promise.catch((err) => {
      // Log suppressed error for debugging
      logger.debug('[RequestDeduplicator] Suppressed promise rejection on cancel:', err)
    })

    // 拒绝所有订阅者
    const error = new Error(`Request cancelled: ${key}`)
    request.reject(error)
    request.subscribers.forEach((sub) => sub.reject(error))

    return true
  }

  /**
   * 取消所有待处理的请求
   */
  cancelAll(): void {
    const keys = Array.from(this.pending.keys())
    keys.forEach((key) => this.cancel(key))
  }

  /**
   * 清理已完成的请求（通常不需要手动调用）
   */
  cleanup(): void {
    const keysToDelete: string[] = []
    this.pending.forEach((request, key) => {
      if (request.cancelled) {
        keysToDelete.push(key)
      }
    })
    keysToDelete.forEach((key) => this.pending.delete(key))
  }
}

// ==================== 全局实例 ====================

/** 默认的请求去重器实例 */
export const requestDeduplicator = new RequestDeduplicator()

// ==================== 便捷函数 ====================

/**
 * 去重执行请求（使用默认去重器）
 */
export function dedupeRequest<T>(key: string, request: () => Promise<T>): Promise<T> {
  return requestDeduplicator.dedupe(key, request)
}

/**
 * 创建带去重功能的请求函数
 */
export function createDedupedRequest<T, Args extends any[]>(
  keyGenerator: (...args: Args) => string,
  requestFn: (...args: Args) => Promise<T>,
  deduplicator: RequestDeduplicator = requestDeduplicator
): (...args: Args) => Promise<T> {
  return (...args: Args) => {
    const key = keyGenerator(...args)
    return deduplicator.dedupe(key, () => requestFn(...args))
  }
}

export default RequestDeduplicator
