/**
 * CRUD 服务�?
 *
 * 提供统一的增删改查操作接口，支持本地存储和API两种模式
 */

import { localDatabase } from './LocalDatabase'
import { logger } from './logger'

/**
 * 通用CRUD操作服务
 */
class CrudService {
  /**
   * 获取所有记�?
   * @param collection 集合/表名
   * @param options 查询选项
   */
  async getAll<T = any>(
    collection: string,
    options?: {
      page?: number
      pageSize?: number
      filters?: Record<string, any>
      sort?: { field: string; order: 'asc' | 'desc' }
    }
  ): Promise<T[]> {
    try {
      const result = await localDatabase.query(collection, options?.filters || {})

      // 应用排序
      if (options?.sort && result.length > 0) {
        result.sort((a: any, b: any) => {
          const aVal = a[options.sort!.field]
          const bVal = b[options.sort!.field]
          const order = options.sort!.order === 'asc' ? 1 : -1

          if (aVal < bVal) return -1 * order
          if (aVal > bVal) return 1 * order
          return 0
        })
      }

      // 应用分页
      if (options?.page && options?.pageSize) {
        const start = (options.page - 1) * options.pageSize
        const end = start + options.pageSize
        return result.slice(start, end) as T[]
      }

      return result as T[]
    } catch (error) {
      logger.error(`CrudService.getAll(${collection}) failed:`, error)
      throw error
    }
  }

  /**
   * 根据ID获取单条记录
   * @param collection 集合/表名
   * @param id 记录ID
   */
  async getById<T = any>(collection: string, id: string | number): Promise<T | null> {
    try {
      const result = await localDatabase.get(collection, String(id))
      return result as T | null
    } catch (error) {
      logger.error(`CrudService.getById(${collection}, ${id}) failed:`, error)
      throw error
    }
  }

  /**
   * 创建新记�?
   * @param collection 集合/表名
   * @param data 记录数据
   */
  async create<T = any>(collection: string, data: Partial<T>): Promise<T> {
    try {
      const now = new Date().toISOString()
      const record = {
        ...data,
        id: (data as any).id || String(Date.now()),
        createdAt: now,
        updatedAt: now,
      } as T

      await localDatabase.set(collection, record)
      logger.info(`CrudService.create(${collection}) succeeded`)
      return record
    } catch (error) {
      logger.error(`CrudService.create(${collection}) failed:`, error)
      throw error
    }
  }

  /**
   * 更新记录
   * @param collection 集合/表名
   * @param id 记录ID
   * @param data 更新数据
   */
  async update<T = any>(
    collection: string,
    id: string | number | undefined,
    data: Partial<T>
  ): Promise<T> {
    try {
      if (!id) {
        throw new Error('ID is required for update')
      }

      const existing = await this.getById<T>(collection, id)
      if (!existing) {
        throw new Error(`Record with id ${id} not found in ${collection}`)
      }

      const updated = {
        ...existing,
        ...data,
        id: String(id),
        updatedAt: new Date().toISOString(),
      } as T

      await localDatabase.update(collection, updated)
      logger.info(`CrudService.update(${collection}, ${id}) succeeded`)
      return updated
    } catch (error) {
      logger.error(`CrudService.update(${collection}, ${id}) failed:`, error)
      throw error
    }
  }

  /**
   * 删除记录
   * @param collection 集合/表名
   * @param id 记录ID
   */
  async delete(collection: string, id: string | number | undefined): Promise<boolean> {
    try {
      if (!id) {
        throw new Error('ID is required for delete')
      }

      await localDatabase.delete(collection, String(id))
      logger.info(`CrudService.delete(${collection}, ${id}) succeeded`)
      return true
    } catch (error) {
      logger.error(`CrudService.delete(${collection}, ${id}) failed:`, error)
      throw error
    }
  }

  /**
   * 批量删除
   * @param collection 集合/表名
   * @param ids 记录ID数组
   */
  async batchDelete(collection: string, ids: (string | number)[]): Promise<boolean> {
    try {
      for (const id of ids) {
        await this.delete(collection, id)
      }
      logger.info(`CrudService.batchDelete(${collection}) deleted ${ids.length} records`)
      return true
    } catch (error) {
      logger.error(`CrudService.batchDelete(${collection}) failed:`, error)
      throw error
    }
  }

  /**
   * 搜索记录
   * @param collection 集合/表名
   * @param keyword 搜索关键�?
   * @param fields 搜索字段
   */
  async search<T = any>(collection: string, keyword: string, fields: string[]): Promise<T[]> {
    try {
      const allRecords = await this.getAll<T>(collection)

      if (!keyword) {
        return allRecords
      }

      const lowerKeyword = keyword.toLowerCase()
      return allRecords.filter((record: any) => {
        return fields.some((field) => {
          const value = record[field]
          if (typeof value === 'string') {
            return value.toLowerCase().includes(lowerKeyword)
          }
          return false
        })
      })
    } catch (error) {
      logger.error(`CrudService.search(${collection}) failed:`, error)
      throw error
    }
  }

  /**
   * 获取记录数量
   * @param collection 集合/表名
   * @param filters 过滤条件
   */
  async count(collection: string, filters?: Record<string, any>): Promise<number> {
    try {
      const records = await this.getAll(collection, { filters })
      return records.length
    } catch (error) {
      logger.error(`CrudService.count(${collection}) failed:`, error)
      throw error
    }
  }
}

// 导出单例实例
export default new CrudService()
