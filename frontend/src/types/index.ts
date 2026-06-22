/**
 * 类型定义统一导出
 *
 * 所有共享类型从此文件集中导出
 * 使用方式: import { User, ApiResponse, TableProps } from '@/types'
 */

// API响应类型
export * from './api'

// 实体类型
export * from './entities'

// 组件Props类型
export * from './components'

// 数据分析类型
export * from './analytics'

// ============================================================================
// 兼容性类型别名（保持向后兼容）
// ============================================================================

import type { User as UserType } from './entities'

/**
 * 登录请求参数
 */
export interface LoginRequest {
  /** 用户名 */
  username: string
  /** 密码 */
  password: string
  /** 是否记住登录 */
  remember?: boolean
}

/**
 * 登录响应数据
 */
export interface LoginResponse {
  /** 访问令牌 */
  accessToken: string
  /** 刷新令牌 */
  refreshToken?: string
  /** 令牌类型 */
  tokenType: string
  /** 过期时间（秒） */
  expiresIn: number
  /** 用户信息 */
  user: UserType
}

/**
 * 分页参数（简化版）
 */
export interface PaginationParams {
  /** 页码 */
  page: number
  /** 每页大小 */
  pageSize: number
}

/**
 * 排序参数
 */
export interface SortParams {
  /** 排序字段 */
  sortBy?: string
  /** 排序方向 */
  sortOrder?: 'asc' | 'desc'
}

/**
 * 列表查询参数（组合分页和排序）
 */
export interface ListParams extends PaginationParams, SortParams {
  /** 搜索关键词 */
  search?: string
  /** 过滤条件 */
  filters?: Record<string, unknown>
}

// ============================================================================
// 通用工具类型
// ============================================================================

/**
 * 可空类型
 */
export type Nullable<T> = T | null

/**
 * 可选类型
 */
export type Optional<T> = T | undefined

/**
 * 深度只读类型
 */
export type DeepReadonly<T> = {
  readonly [P in keyof T]: T[P] extends object ? DeepReadonly<T[P]> : T[P]
}

/**
 * 深度可选类型
 */
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

/**
 * 提取Promise返回类型
 */
export type UnwrapPromise<T> = T extends Promise<infer U> ? U : T

/**
 * 提取数组元素类型
 */
export type ArrayElement<T> = T extends (infer U)[] ? U : never

/**
 * 键值对类型
 */
export type KeyValue<K extends string | number | symbol = string, V = unknown> = Record<K, V>

/**
 * 函数类型
 */
export type AnyFunction = (...args: unknown[]) => unknown

/**
 * 异步函数类型
 */
export type AsyncFunction<T = unknown> = (...args: unknown[]) => Promise<T>

/**
 * 搜索表单（通用）
 */
export interface SearchForm {
  [key: string]: any
}

/**
 * 分页信息
 */
export interface Pagination {
  page?: number
  page_size?: number
  current?: number
  size?: number
  total: number
}
