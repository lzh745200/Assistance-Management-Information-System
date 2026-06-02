import { logger } from "@/utils/logger";

// 类型仅在泛型方法中使用，无需显式导入

// 本地存储键名常量
export const STORAGE_KEYS = {
  USERS: "military_rural_users",
  ARMY_PERSONNEL: "military_rural_army_personnel",
  PROJECTS: "military_rural_projects",
  RURAL_WORKS: "military_rural_rural_works",
  AUTH_TOKEN: "military_rural_auth_token",
  CURRENT_USER: "military_rural_current_user",
  USER_PERMISSIONS: "military_rural_user_permissions",
  LAST_SYNC_TIME: "military_rural_last_sync_time",
  APP_SETTINGS: "military_rural_app_settings",
};

// 本地存储管理器类
export class LocalStorageManager {
  // 检查localStorage是否可用
  private isStorageAvailable(): boolean {
    try {
      const testKey = "__storage_test__";
      localStorage.setItem(testKey, testKey);
      localStorage.removeItem(testKey);
      return true;
    } catch (e) {
      logger.error("LocalStorage is not available:", e);
      return false;
    }
  }

  // 存储数据到localStorage
  saveData<T>(key: string, data: T): boolean {
    if (!this.isStorageAvailable()) return false;

    try {
      const jsonData = JSON.stringify(data);
      localStorage.setItem(key, jsonData);
      return true;
    } catch (e) {
      logger.error(`Failed to save data for key ${key}:`, e);
      return false;
    }
  }

  // 从localStorage读取数据
  getData<T>(key: string): T | null {
    if (!this.isStorageAvailable()) return null;

    try {
      const jsonData = localStorage.getItem(key);
      if (!jsonData) return null;
      return JSON.parse(jsonData) as T;
    } catch (e) {
      logger.error(`Failed to get data for key ${key}:`, e);
      return null;
    }
  }

  // 删除localStorage中的数据
  removeData(key: string): boolean {
    if (!this.isStorageAvailable()) return false;

    try {
      localStorage.removeItem(key);
      return true;
    } catch (e) {
      logger.error(`Failed to remove data for key ${key}:`, e);
      return false;
    }
  }

  // 清空所有相关数据
  clearAllData(): boolean {
    if (!this.isStorageAvailable()) return false;

    try {
      Object.values(STORAGE_KEYS).forEach((key) => {
        localStorage.removeItem(key);
      });
      return true;
    } catch (e) {
      logger.error("Failed to clear all data:", e);
      return false;
    }
  }

  // 获取所有存储的数据的大小信息
  getStorageInfo(): { [key: string]: number } {
    const info: { [key: string]: number } = {};

    Object.entries(STORAGE_KEYS).forEach(([name, key]) => {
      const data = localStorage.getItem(key);
      info[name] = data ? new Blob([data]).size : 0;
    });

    return info;
  }

  // 批量保存多个数据
  bulkSave(data: { [key: string]: any }): boolean {
    if (!this.isStorageAvailable()) return false;

    try {
      Object.entries(data).forEach(([key, value]) => {
        this.saveData(key, value);
      });
      return true;
    } catch (e) {
      logger.error("Failed to bulk save data:", e);
      return false;
    }
  }

  // 检查存储空间是否充足
  hasEnoughStorage(estimatedSizeInBytes: number): boolean {
    try {
      // 简单估计，实际localStorage通常有5-10MB限制
      const totalSize = Object.values(STORAGE_KEYS)
        .map((key) => localStorage.getItem(key) || "")
        .reduce((size, item) => size + item.length, 0);

      // 假设预留500KB空间
      return totalSize + estimatedSizeInBytes < 4 * 1024 * 1024; // 4MB阈值
    } catch (e) {
      return false;
    }
  }

  // 初始化默认数据（如果不存在）
  initializeDefaultData(defaultData: { [key: string]: any }): void {
    Object.entries(defaultData).forEach(([key, defaultValue]) => {
      if (!localStorage.getItem(key)) {
        this.saveData(key, defaultValue);
      }
    });
  }
}

// 创建单例实例
export const localStorageManager = new LocalStorageManager();
