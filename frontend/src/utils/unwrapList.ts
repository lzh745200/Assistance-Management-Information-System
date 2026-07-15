/** API 响应解包工具 — 处理后端多种响应格式 */

import type { ListResponse } from '@/types/api'

export interface UnwrappedList<T = unknown> {
  items: T[]
  total: number
}

/**
 * 从 axios 解包后的 data 中提取 items + total
 *
 * 兼容格式:
 *   { items, total }              — 直接分页格式（Pattern B 自动解包后）
 *   { code, data: { items, total } } — 标准 API 响应（Pattern A 原始响应）
 */
export function unwrapList<T = unknown>(res: any): UnwrappedList<T> {
  if (res?.items) return { items: res.items as T[], total: res.total ?? res.items.length }
  if (res?.data?.items)
    return {
      items: res.data.items as T[],
      total: res.data.total ?? res.data.items.length,
    }
  return { items: [] as T[], total: 0 }
}

/**
 * 类型安全的列表响应解包
 * 适用于已通过 apiRequest/get/post 自动解包的响应
 */
export function unwrapListTyped<T>(res: ListResponse<T> | any): UnwrappedList<T> {
  return unwrapList<T>(res)
}
