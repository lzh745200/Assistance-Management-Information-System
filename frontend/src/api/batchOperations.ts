/**
 * 批量操作API服务
 * 提供批量更新、删除、导出和验证功能
 */

import api from './request'

const BASE_URL = '/batch'

/** 批量更新 */
export function batchUpdate(data: {
  table_name: string
  ids: number[]
  updates: Record<string, any>
}): Promise<any> {
  return api.post(`${BASE_URL}/update`, data)
}

/** 批量删除 */
export function batchDelete(data: {
  table_name: string
  ids: number[]
  soft_delete?: boolean
}): Promise<any> {
  return api.post(`${BASE_URL}/delete`, data)
}

/** 批量导出 */
export function batchExport(data: {
  table_name: string
  ids: number[]
  format?: string
}): Promise<any> {
  return api.post(`${BASE_URL}/export`, data)
}

/** 验证批量操作 */
export function validateBatch(tableName: string, ids: number[]): Promise<any> {
  return api.post(`${BASE_URL}/validate`, null, {
    params: { table_name: tableName, ids },
  })
}

/** 获取批量操作状态 */
export function getBatchStatus(): Promise<any> {
  return api.get(`${BASE_URL}/status`)
}
