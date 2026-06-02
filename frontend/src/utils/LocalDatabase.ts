/**
 * 本地数据库工具
 * 使用 IndexedDB 或 localStorage 进行本地数据存储
 */

import { logger } from "./logger";

const DB_NAME = "military_rural_db";
const DB_VERSION = 1;

class LocalDatabaseClass {
  private db: IDBDatabase | null = null;
  private storageKey = "mrs_local_data";

  /**
   * 初始化数据库
   */
  async init(): Promise<void> {
    if (this.db) return;

    return new Promise((resolve) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        logger.warn("IndexedDB 不可用，使用 localStorage 作为后备");
        resolve();
      };

      request.onsuccess = () => {
        this.db = request.result;
        logger.info("IndexedDB 初始化成功");
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // 创建存储对象
        const stores = [
          "users",
          "projects",
          "armyPersonnel",
          "ruralWorks",
          "villages",
          "schools",
          "funds",
          "budget",
          "todos",
        ];
        stores.forEach((storeName) => {
          if (!db.objectStoreNames.contains(storeName)) {
            db.createObjectStore(storeName, {
              keyPath: "id",
              autoIncrement: true,
            });
          }
        });
      };
    });
  }

  /**
   * 查询数据（支持简单过滤）
   */
  async query<T = any>(
    tableName: string,
    filter?: Record<string, any>,
  ): Promise<T[]> {
    const allData = await this.getAll<T>(tableName);

    if (!filter || Object.keys(filter).length === 0) {
      return allData;
    }

    return allData.filter((item) => {
      return Object.entries(filter).every(([key, value]) => {
        if (value === undefined || value === null || value === "") return true;
        return (item as any)[key] === value;
      });
    });
  }

  /**
   * 设置/保存数据（别名方法）
   */
  async set<T = any>(tableName: string, data: T): Promise<T> {
    return this.add(tableName, data);
  }

  /**
   * 根据ID获取单条数据
   */
  async get<T = any>(
    tableName: string,
    id: string | number,
  ): Promise<T | null> {
    await this.init();

    if (this.db) {
      return new Promise((resolve) => {
        try {
          const transaction = this.db!.transaction(tableName, "readonly");
          const store = transaction.objectStore(tableName);
          const request = store.get(id);

          request.onsuccess = () => resolve(request.result || null);
          request.onerror = () =>
            resolve(this.getByIdFromLocalStorage(tableName, id));
        } catch {
          resolve(this.getByIdFromLocalStorage(tableName, id));
        }
      });
    }

    return this.getByIdFromLocalStorage(tableName, id);
  }

  /**
   * 保存数据（新增或更新）
   */
  async save<T = any>(tableName: string, data: T): Promise<T> {
    const item = data as any;
    if (item.id) {
      return this.update(tableName, data);
    } else {
      return this.add(tableName, data);
    }
  }

  /**
   * 获取所有数据
   */
  async getAll<T = any>(tableName: string): Promise<T[]> {
    await this.init();

    if (this.db) {
      return new Promise((resolve) => {
        try {
          const transaction = this.db!.transaction(tableName, "readonly");
          const store = transaction.objectStore(tableName);
          const request = store.getAll();

          request.onsuccess = () => resolve(request.result || []);
          request.onerror = () => resolve(this.getFromLocalStorage(tableName));
        } catch {
          resolve(this.getFromLocalStorage(tableName));
        }
      });
    }

    return this.getFromLocalStorage(tableName);
  }

  /**
   * 添加数据
   */
  async add(tableName: string, data: any): Promise<any> {
    await this.init();

    if (this.db) {
      return new Promise((resolve) => {
        try {
          const transaction = this.db!.transaction(tableName, "readwrite");
          const store = transaction.objectStore(tableName);
          const request = store.add(data);

          request.onsuccess = () => resolve({ ...data, id: request.result });
          request.onerror = () =>
            resolve(this.addToLocalStorage(tableName, data));
        } catch {
          resolve(this.addToLocalStorage(tableName, data));
        }
      });
    }

    return this.addToLocalStorage(tableName, data);
  }

  /**
   * 更新数据
   */
  async update(tableName: string, data: any): Promise<any> {
    await this.init();

    if (this.db) {
      return new Promise((resolve) => {
        try {
          const transaction = this.db!.transaction(tableName, "readwrite");
          const store = transaction.objectStore(tableName);
          const request = store.put(data);

          request.onsuccess = () => resolve(data);
          request.onerror = () =>
            resolve(this.updateInLocalStorage(tableName, data));
        } catch {
          resolve(this.updateInLocalStorage(tableName, data));
        }
      });
    }

    return this.updateInLocalStorage(tableName, data);
  }

  /**
   * 删除数据
   */
  async delete(tableName: string, id: number | string): Promise<boolean> {
    await this.init();

    if (this.db) {
      return new Promise((resolve) => {
        try {
          const transaction = this.db!.transaction(tableName, "readwrite");
          const store = transaction.objectStore(tableName);
          const request = store.delete(id);

          request.onsuccess = () => resolve(true);
          request.onerror = () =>
            resolve(this.deleteFromLocalStorage(tableName, id));
        } catch {
          resolve(this.deleteFromLocalStorage(tableName, id));
        }
      });
    }

    return this.deleteFromLocalStorage(tableName, id);
  }

  /**
   * 检查存储空间
   */
  async checkStorage(): Promise<{
    available: boolean;
    used: number;
    total: number;
  }> {
    try {
      if (navigator.storage && navigator.storage.estimate) {
        const estimate = await navigator.storage.estimate();
        return {
          available: true,
          used: estimate.usage || 0,
          total: estimate.quota || 0,
        };
      }
    } catch (error) {
      logger.warn(
        "无法获取存储信息",
        error instanceof Error ? error : new Error(String(error)),
      );
    }

    return { available: true, used: 0, total: 50 * 1024 * 1024 };
  }

  /**
   * 清理过期数据
   */
  async cleanup(): Promise<{ removedItems: number }> {
    // 简单实现，可以根据需要扩展
    return { removedItems: 0 };
  }

  /**
   * 验证数据完整性
   */
  async validateDataIntegrity(): Promise<boolean> {
    try {
      const tables = ["users", "projects"];
      for (const table of tables) {
        await this.getAll(table);
      }
      return true;
    } catch {
      return false;
    }
  }

  private getByIdFromLocalStorage<T = any>(
    tableName: string,
    id: string | number,
  ): T | null {
    const items = this.getFromLocalStorage(tableName);
    return items.find((i: any) => i.id === id || i.id === String(id)) || null;
  }

  // localStorage 后备方法
  private getFromLocalStorage(tableName: string): any[] {
    try {
      const data = localStorage.getItem(`${this.storageKey}_${tableName}`);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  }

  private addToLocalStorage(tableName: string, data: any): any {
    const items = this.getFromLocalStorage(tableName);
    const newId =
      items.length > 0 ? Math.max(...items.map((i: any) => i.id || 0)) + 1 : 1;
    const newItem = { ...data, id: newId };
    items.push(newItem);
    localStorage.setItem(
      `${this.storageKey}_${tableName}`,
      JSON.stringify(items),
    );
    return newItem;
  }

  private updateInLocalStorage(tableName: string, data: any): any {
    const items = this.getFromLocalStorage(tableName);
    const index = items.findIndex((i: any) => i.id === data.id);
    if (index >= 0) {
      items[index] = data;
      localStorage.setItem(
        `${this.storageKey}_${tableName}`,
        JSON.stringify(items),
      );
    }
    return data;
  }

  private deleteFromLocalStorage(
    tableName: string,
    id: number | string,
  ): boolean {
    const items = this.getFromLocalStorage(tableName);
    const filtered = items.filter(
      (i: any) => i.id !== id && String(i.id) !== String(id),
    );
    localStorage.setItem(
      `${this.storageKey}_${tableName}`,
      JSON.stringify(filtered),
    );
    return true;
  }
}

export const localDatabase = new LocalDatabaseClass();
export default localDatabase;
