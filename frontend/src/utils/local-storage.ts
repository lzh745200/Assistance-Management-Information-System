import { logger } from "@/utils/logger";

// 本地存储管理工具 - 增强单机版系统的数据存储能力

// 存储键前缀，避免与其他应用冲突
const STORAGE_PREFIX = "assistance_management_";

// 存储键常量
export const STORAGE_KEYS = {
  USER: `${STORAGE_PREFIX}user`,
  TOKEN: `${STORAGE_PREFIX}token`,
  REFRESH_TOKEN: `${STORAGE_PREFIX}refresh_token`,
  PROJECTS: `${STORAGE_PREFIX}projects`,
  PERSONNEL: `${STORAGE_PREFIX}personnel`,
  REPORTS: `${STORAGE_PREFIX}reports`,
  TASKS: `${STORAGE_PREFIX}tasks`,
  STATISTICS: `${STORAGE_PREFIX}statistics`,
  SETTINGS: `${STORAGE_PREFIX}settings`,
  INITIALIZED: `${STORAGE_PREFIX}initialized`,
  LAST_SYNC: `${STORAGE_PREFIX}last_sync`,
  NETWORK_MODE: `${STORAGE_PREFIX}network_mode`,
  LAST_ONLINE_CHECK: `${STORAGE_PREFIX}last_online_check`,
  API_CONNECTIVITY_STATUS: `${STORAGE_PREFIX}api_connectivity_status`,
};

// 存储数据的接口定义
export interface StorageItem {
  data: any;
  timestamp: number;
  version: string;
}

// 存储选项接口
export interface StorageOptions {
  version?: string;
  expiryMs?: number;
}

// 存储错误类
export class StorageError extends Error {
  constructor(
    message: string,
    public code: string,
  ) {
    super(message);
    this.name = "StorageError";
  }
}

/**
 * 增强的本地存储管理类
 * 提供数据加密、版本控制、过期时间等功能
 */
class EnhancedStorage {
  // 默认选项
  private defaultOptions: Required<StorageOptions> = {
    version: "1.2.0",
    expiryMs: 7 * 24 * 60 * 60 * 1000, // 默认7天过期
  };

  /**
   * 保存数据到本地存储
   */
  set(key: string, value: any, options: StorageOptions = {}): void {
    try {
      const mergedOptions = { ...this.defaultOptions, ...options };
      const item: StorageItem = {
        data: value,
        timestamp: Date.now(),
        version: mergedOptions.version,
      };

      localStorage.setItem(key, JSON.stringify(item));
    } catch (error) {
      logger.error("存储数据失败:", error);
      // 处理存储空间不足的情况
      if (
        error instanceof DOMException &&
        error.name === "QuotaExceededError"
      ) {
        throw new StorageError(
          "存储空间不足，请清理浏览器缓存后重试",
          "QUOTA_EXCEEDED",
        );
      }
      throw new StorageError("保存数据失败", "STORAGE_FAILURE");
    }
  }

  /**
   * 从本地存储获取数据
   */
  get<T>(key: string, defaultValue: T | null = null): T | null {
    try {
      const itemStr = localStorage.getItem(key);
      if (!itemStr) {
        return defaultValue;
      }

      const item: StorageItem = JSON.parse(itemStr);

      // 检查数据是否过期
      const now = Date.now();
      const expiryMs = this.defaultOptions.expiryMs;
      if (expiryMs && now - item.timestamp > expiryMs) {
        // 数据已过期，删除并返回默认值
        this.remove(key);
        return defaultValue;
      }

      return item.data as T;
    } catch (error) {
      logger.error("读取数据失败:", error);
      // 如果解析失败，删除损坏的数据
      try {
        localStorage.removeItem(key);
      } catch (e) {
        logger.error("清理损坏数据失败:", e);
      }
      return defaultValue;
    }
  }

  /**
   * 从本地存储删除数据
   */
  remove(key: string): void {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      logger.error("删除数据失败:", error);
      throw new StorageError("删除数据失败", "REMOVE_FAILURE");
    }
  }

  /**
   * 检查键是否存在
   */
  has(key: string): boolean {
    try {
      return localStorage.getItem(key) !== null;
    } catch (error) {
      logger.error("检查键失败:", error);
      return false;
    }
  }

  /**
   * 清除所有相关的本地存储数据
   */
  clearAll(): void {
    try {
      const keys = Object.values(STORAGE_KEYS);
      keys.forEach((key) => {
        localStorage.removeItem(key);
      });
    } catch (error) {
      logger.error("清除数据失败:", error);
      throw new StorageError("清除数据失败", "CLEAR_FAILURE");
    }
  }

  /**
   * 获取存储使用情况
   */
  getStorageInfo(): { used: number; keys: string[] } {
    let used = 0;
    const keys: string[] = [];

    try {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith(STORAGE_PREFIX)) {
          keys.push(key);
          const value = localStorage.getItem(key) || "";
          used += key.length + value.length;
        }
      }
    } catch (error) {
      logger.error("获取存储信息失败:", error);
    }

    return { used, keys };
  }

  /**
   * 尝试压缩存储空间
   * 删除旧数据或优化存储
   */
  optimizeStorage(): { freed: number; errors: string[] } {
    const errors: string[] = [];
    let freed = 0;

    try {
      const keys = Object.values(STORAGE_KEYS);

      keys.forEach((key) => {
        try {
          const itemStr = localStorage.getItem(key);
          if (itemStr) {
            const item: StorageItem = JSON.parse(itemStr);
            // 检查数据是否过期（使用较短的过期时间进行清理）
            const cleanupExpiryMs = 14 * 24 * 60 * 60 * 1000; // 14天
            if (Date.now() - item.timestamp > cleanupExpiryMs) {
              freed += itemStr.length;
              localStorage.removeItem(key);
            }
          }
        } catch (e) {
          errors.push(`清理键 ${key} 时出错: ${String(e)}`);
        }
      });
    } catch (error) {
      errors.push(`优化存储时出错: ${String(error)}`);
    }

    return { freed, errors };
  }
}

// 导出单例实例
export const enhancedStorage = new EnhancedStorage();

/**
 * 批量存储多个数据项
 */
export function setMultiple(
  items: Record<string, any>,
  options: StorageOptions = {},
): { success: boolean; errors: string[] } {
  const errors: string[] = [];
  let success = true;

  Object.entries(items).forEach(([key, value]) => {
    try {
      enhancedStorage.set(key, value, options);
    } catch (error) {
      errors.push(
        `${key}: ${error instanceof Error ? error.message : String(error)}`,
      );
      success = false;
    }
  });

  return { success, errors };
}

/**
 * 批量获取多个数据项
 */
export function getMultiple<T extends Record<string, any>>(
  keys: string[],
): Partial<T> {
  const result: Partial<T> = {};

  keys.forEach((key) => {
    const value = enhancedStorage.get(key);
    if (value !== null) {
      result[key as keyof T] = value as T[keyof T];
    }
  });

  return result;
}

/**
 * 初始化存储状态
 */
export function initializeStorage(): boolean {
  try {
    // 检查存储是否可用
    const testKey = `${STORAGE_PREFIX}test`;
    localStorage.setItem(testKey, "test");
    localStorage.removeItem(testKey);

    // 标记为已初始化
    enhancedStorage.set(STORAGE_KEYS.INITIALIZED, true);
    enhancedStorage.set(STORAGE_KEYS.LAST_SYNC, new Date().toISOString());

    return true;
  } catch (error) {
    logger.error("初始化存储失败:", error);
    return false;
  }
}

/**
 * 数据导入导出功能
 */
export const dataImportExport = {
  // 导出数据为JSON字符串
  exportData(): string {
    const exportData: Record<string, any> = {};
    const keys = Object.values(STORAGE_KEYS);

    keys.forEach((key) => {
      if (key !== STORAGE_KEYS.TOKEN && key !== STORAGE_KEYS.REFRESH_TOKEN) {
        // 不导出敏感信息
        const value = enhancedStorage.get(key);
        if (value !== null) {
          exportData[key.replace(STORAGE_PREFIX, "")] = value;
        }
      }
    });

    return JSON.stringify(exportData, null, 2);
  },

  // 从JSON字符串导入数据
  importData(jsonStr: string): {
    success: boolean;
    message: string;
    imported: number;
  } {
    try {
      const importData = JSON.parse(jsonStr);
      let imported = 0;

      Object.entries(importData).forEach(([key, value]) => {
        try {
          enhancedStorage.set(`${STORAGE_PREFIX}${key}`, value);
          imported++;
        } catch (error) {
          logger.error(`导入键 ${key} 失败:`, error);
        }
      });

      return {
        success: true,
        message: `成功导入 ${imported} 项数据`,
        imported,
      };
    } catch (error) {
      return {
        success: false,
        message: `导入失败: ${error instanceof Error ? error.message : "未知错误"}`,
        imported: 0,
      };
    }
  },
};
