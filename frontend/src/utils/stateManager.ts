import { logger } from "@/utils/logger";

/**
 * 统一状态管理工具
 * 提供状态持久化、缓存、同步等功能
 */

interface StorageOptions {
  prefix?: string;
  persist?: boolean;
  ttl?: number; // 过期时间（毫秒）
}

interface StateItem<T> {
  value: T;
  timestamp: number;
  ttl?: number;
}

export class StateManager {
  private storagePrefix = "assistance_management_";
  private memoryCache = new Map<string, StateItem<any>>();
  private listeners = new Map<string, Set<Function>>();

  /**
   * 设置状态
   */
  setState<T>(key: string, value: T, options: StorageOptions = {}): void {
    const { prefix = "", persist = true, ttl } = options;
    const fullKey = this.getFullKey(key, prefix);

    const stateItem: StateItem<T> = {
      value,
      timestamp: Date.now(),
      ttl,
    };

    // 内存缓存
    this.memoryCache.set(fullKey, stateItem);

    // 持久化到 localStorage
    if (persist) {
      try {
        localStorage.setItem(fullKey, JSON.stringify(stateItem));
      } catch (e) {
        logger.error("Failed to persist state:", e);
      }
    }

    // 触发监听器
    this.notifyListeners(fullKey, value);
  }

  /**
   * 获取状态
   */
  getState<T>(
    key: string,
    defaultValue?: T,
    options: StorageOptions = {},
  ): T | undefined {
    const { prefix = "" } = options;
    const fullKey = this.getFullKey(key, prefix);

    // 先从内存缓存获取
    if (this.memoryCache.has(fullKey)) {
      const stateItem = this.memoryCache.get(fullKey)!;
      if (!this.isExpired(stateItem)) {
        return stateItem.value as T;
      } else {
        this.memoryCache.delete(fullKey);
      }
    }

    // 从 localStorage 获取
    try {
      const stored = localStorage.getItem(fullKey);
      if (stored) {
        const stateItem = JSON.parse(stored) as StateItem<T>;
        if (!this.isExpired(stateItem)) {
          // 恢复到内存缓存
          this.memoryCache.set(fullKey, stateItem);
          return stateItem.value;
        } else {
          // 已过期，清除
          localStorage.removeItem(fullKey);
        }
      }
    } catch (e) {
      logger.error("Failed to get state:", e);
    }

    return defaultValue;
  }

  /**
   * 删除状态
   */
  removeState(key: string, options: StorageOptions = {}): void {
    const { prefix = "" } = options;
    const fullKey = this.getFullKey(key, prefix);

    this.memoryCache.delete(fullKey);
    localStorage.removeItem(fullKey);
    this.notifyListeners(fullKey, undefined);
  }

  /**
   * 清空所有状态
   */
  clearState(prefix?: string): void {
    const fullPrefix = prefix
      ? this.getFullKey("", prefix)
      : this.storagePrefix;

    // 清空内存缓存
    for (const key of this.memoryCache.keys()) {
      if (key.startsWith(fullPrefix)) {
        this.memoryCache.delete(key);
      }
    }

    // 清空 localStorage
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(fullPrefix)) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach((key) => localStorage.removeItem(key));
  }

  /**
   * 订阅状态变化
   */
  subscribe(
    key: string,
    callback: Function,
    options: StorageOptions = {},
  ): () => void {
    const { prefix = "" } = options;
    const fullKey = this.getFullKey(key, prefix);

    if (!this.listeners.has(fullKey)) {
      this.listeners.set(fullKey, new Set());
    }

    this.listeners.get(fullKey)!.add(callback);

    // 返回取消订阅的函数
    return () => {
      const listeners = this.listeners.get(fullKey);
      if (listeners) {
        listeners.delete(callback);
        if (listeners.size === 0) {
          this.listeners.delete(fullKey);
        }
      }
    };
  }

  /**
   * 批量设置状态
   */
  batchSetState(
    states: Record<string, any>,
    options: StorageOptions = {},
  ): void {
    Object.entries(states).forEach(([key, value]) => {
      this.setState(key, value, options);
    });
  }

  /**
   * 批量获取状态
   */
  batchGetState<T>(
    keys: string[],
    options: StorageOptions = {},
  ): Record<string, T> {
    const result: Record<string, T> = {};
    keys.forEach((key) => {
      result[key] = this.getState<T>(key, undefined, options)!;
    });
    return result;
  }

  /**
   * 检查状态是否存在
   */
  hasState(key: string, options: StorageOptions = {}): boolean {
    return this.getState(key, undefined, options) !== undefined;
  }

  /**
   * 获取所有状态键
   */
  getStateKeys(prefix?: string): string[] {
    const fullPrefix = prefix
      ? this.getFullKey("", prefix)
      : this.storagePrefix;

    const keys: string[] = [];

    // 从内存缓存获取
    for (const key of this.memoryCache.keys()) {
      if (key.startsWith(fullPrefix)) {
        keys.push(key);
      }
    }

    // 从 localStorage 获取
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(fullPrefix) && !keys.includes(key)) {
        keys.push(key);
      }
    }

    return keys;
  }

  /**
   * 导出状态
   * 返回包含完整键名的状态对象
   */
  exportState(prefix?: string): Record<string, any> {
    const fullPrefix = prefix
      ? this.getFullKey("", prefix)
      : this.storagePrefix;
    const states: Record<string, any> = {};

    // 从内存缓存获取
    for (const [key, stateItem] of this.memoryCache.entries()) {
      if (key.startsWith(fullPrefix) && !this.isExpired(stateItem)) {
        states[key] = stateItem.value;
      }
    }

    // 从 localStorage 获取
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(fullPrefix) && !states[key]) {
        try {
          const stored = localStorage.getItem(key);
          if (stored) {
            const stateItem = JSON.parse(stored);
            if (!this.isExpired(stateItem)) {
              states[key] = stateItem.value;
            }
          }
        } catch (e) {
          // 解析失败，跳过
        }
      }
    }

    return states;
  }

  /**
   * 导入状态
   * 键名已经包含完整前缀，直接存储
   */
  importState(states: Record<string, any>, options: StorageOptions = {}): void {
    const { persist = true } = options;

    Object.entries(states).forEach(([fullKey, value]) => {
      const stateItem: StateItem<any> = {
        value,
        timestamp: Date.now(),
      };

      // 内存缓存
      this.memoryCache.set(fullKey, stateItem);

      // 持久化到 localStorage
      if (persist) {
        try {
          localStorage.setItem(fullKey, JSON.stringify(stateItem));
        } catch (e) {
          logger.error("Failed to persist imported state:", e);
        }
      }
    });
  }

  /**
   * 清理过期状态
   */
  cleanupExpiredStates(): void {
    const now = Date.now();

    // 清理内存缓存
    for (const [key, stateItem] of this.memoryCache.entries()) {
      if (this.isExpired(stateItem)) {
        this.memoryCache.delete(key);
      }
    }

    // 清理 localStorage
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(this.storagePrefix)) {
        try {
          const stored = localStorage.getItem(key);
          if (stored) {
            const stateItem = JSON.parse(stored);
            if (stateItem.ttl && now - stateItem.timestamp > stateItem.ttl) {
              keysToRemove.push(key);
            }
          }
        } catch (e) {
          // 解析失败，移除
          keysToRemove.push(key);
        }
      }
    }
    keysToRemove.forEach((key) => localStorage.removeItem(key));
  }

  /**
   * 获取完整键名
   */
  private getFullKey(key: string, prefix: string): string {
    return `${this.storagePrefix}${prefix}${key}`;
  }

  /**
   * 检查状态是否过期
   */
  private isExpired(stateItem: StateItem<any>): boolean {
    if (!stateItem.ttl) return false;
    return Date.now() - stateItem.timestamp > stateItem.ttl;
  }

  /**
   * 通知监听器
   */
  private notifyListeners(key: string, value: any): void {
    const listeners = this.listeners.get(key);
    if (listeners) {
      listeners.forEach((callback) => {
        try {
          callback(value);
        } catch (e) {
          logger.error("Error in state listener:", e);
        }
      });
    }
  }
}

// 创建单例实例
const stateManager = new StateManager();

// 定期清理过期状态（每5分钟）
let cleanupIntervalId: ReturnType<typeof setInterval> | null = null;

if (typeof window !== "undefined") {
  cleanupIntervalId = setInterval(
    () => {
      stateManager.cleanupExpiredStates();
    },
    5 * 60 * 1000,
  );
}

/** 清理函数 - 用于应用退出时清除定时器 */
export function cleanupStateManager(): void {
  if (cleanupIntervalId !== null) {
    clearInterval(cleanupIntervalId);
    cleanupIntervalId = null;
  }
}

export default stateManager;

// 导出类型
export type { StorageOptions, StateItem };
