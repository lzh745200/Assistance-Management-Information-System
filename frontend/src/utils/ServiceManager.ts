/**
 * 服务管理器
 *
 * 负责系统服务的初始化、健康检查和状态管理
 *
 * Feature: frontend-production-readiness
 */

import { logger as Logger } from '@/utils/logger'

// ==================== 类型定义 ====================

/** 服务状态 */
export interface ServiceStatus {
  name: string
  healthy: boolean
  message?: string
  lastCheck?: number
}

/** 系统健康状态 */
export interface SystemHealthStatus {
  healthy: boolean
  services: ServiceStatus[]
  timestamp: number
}

/** 服务配置 */
export interface ServiceConfig {
  name: string
  initialize: () => Promise<boolean>
  healthCheck?: () => Promise<boolean>
  required?: boolean
}

// ==================== 服务管理器类 ====================

/**
 * 服务管理器
 *
 * 管理系统中各个服务的初始化和健康状态
 */
class ServiceManager {
  /** 已注册的服务 */
  private services: Map<string, ServiceConfig> = new Map()

  /** 服务状态 */
  private serviceStatuses: Map<string, ServiceStatus> = new Map()

  /** 是否已初始化 */
  private initialized: boolean = false

  constructor() {
    // 注册默认服务
    this.registerDefaultServices()
  }

  /**
   * 注册默认服务
   */
  private registerDefaultServices(): void {
    // 本地存储服务
    this.registerService({
      name: 'localStorage',
      initialize: async () => {
        try {
          const testKey = '__service_test__'
          localStorage.setItem(testKey, 'test')
          localStorage.removeItem(testKey)
          return true
        } catch {
          return false
        }
      },
      healthCheck: async () => {
        try {
          const testKey = '__health_check__'
          localStorage.setItem(testKey, Date.now().toString())
          localStorage.removeItem(testKey)
          return true
        } catch {
          return false
        }
      },
      required: true,
    })

    // IndexedDB 服务
    this.registerService({
      name: 'indexedDB',
      initialize: async () => {
        try {
          if (!window.indexedDB) {
            return false
          }
          return true
        } catch {
          return false
        }
      },
      healthCheck: async () => {
        return !!window.indexedDB
      },
      required: false,
    })
  }

  /**
   * 注册服务
   */
  registerService(config: ServiceConfig): void {
    this.services.set(config.name, config)
    this.serviceStatuses.set(config.name, {
      name: config.name,
      healthy: false,
      lastCheck: 0,
    })
  }

  /**
   * 初始化所有服务
   */
  async initializeServices(): Promise<boolean> {
    if (this.initialized) {
      Logger.info('[ServiceManager] 服务已初始化，跳过')
      return true
    }

    Logger.info('[ServiceManager] 开始初始化服务...')

    let allRequiredSucceeded = true

    for (const [name, config] of this.services) {
      try {
        Logger.info(`[ServiceManager] 初始化服务: ${name}`)
        const success = await config.initialize()

        this.serviceStatuses.set(name, {
          name,
          healthy: success,
          message: success ? '初始化成功' : '初始化失败',
          lastCheck: Date.now(),
        })

        if (!success && config.required) {
          Logger.error(`[ServiceManager] 必需服务 ${name} 初始化失败`)
          allRequiredSucceeded = false
        }
      } catch (error) {
        Logger.error(`[ServiceManager] 服务 ${name} 初始化异常`, error)

        this.serviceStatuses.set(name, {
          name,
          healthy: false,
          message: `初始化异常: ${error}`,
          lastCheck: Date.now(),
        })

        if (config.required) {
          allRequiredSucceeded = false
        }
      }
    }

    this.initialized = allRequiredSucceeded

    Logger.info(`[ServiceManager] 服务初始化完成，状态: ${allRequiredSucceeded ? '成功' : '失败'}`)

    return allRequiredSucceeded
  }

  /**
   * 检查系统健康状态
   */
  async checkSystemHealth(): Promise<SystemHealthStatus> {
    const services: ServiceStatus[] = []
    let allHealthy = true

    for (const [name, config] of this.services) {
      let healthy = false
      let message = ''

      try {
        if (config.healthCheck) {
          healthy = await config.healthCheck()
          message = healthy ? '正常' : '异常'
        } else {
          // 没有健康检查函数，使用上次状态
          const lastStatus = this.serviceStatuses.get(name)
          healthy = lastStatus?.healthy ?? false
          message = '无健康检查'
        }
      } catch (error) {
        healthy = false
        message = `检查异常: ${error}`
      }

      const status: ServiceStatus = {
        name,
        healthy,
        message,
        lastCheck: Date.now(),
      }

      services.push(status)
      this.serviceStatuses.set(name, status)

      if (!healthy && config.required) {
        allHealthy = false
      }
    }

    return {
      healthy: allHealthy,
      services,
      timestamp: Date.now(),
    }
  }

  /**
   * 获取服务状态
   */
  getServiceStatus(name: string): ServiceStatus | undefined {
    return this.serviceStatuses.get(name)
  }

  /**
   * 获取所有服务状态
   */
  getAllServiceStatuses(): ServiceStatus[] {
    return Array.from(this.serviceStatuses.values())
  }

  /**
   * 检查是否已初始化
   */
  isInitialized(): boolean {
    return this.initialized
  }

  /**
   * 重置服务管理器
   */
  reset(): void {
    this.initialized = false
    this.serviceStatuses.forEach((_status, name) => {
      this.serviceStatuses.set(name, {
        name,
        healthy: false,
        lastCheck: 0,
      })
    })
  }
}

// ==================== 导出 ====================

/** 服务管理器单例 */
export const serviceManager = new ServiceManager()

export default serviceManager
