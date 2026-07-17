/**
 * API 通用类型定义
 */

/** API 响应基础结构（匹配后端 success_response() 输出） */
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  success?: boolean
  data?: T
  [key: string]: unknown
}

/** 标准列表响应（后端 ok_list() 输出） */
export interface PaginatedResponse<T = unknown> {
  items: T[]
  total: number
  page: number
  page_size: number
}

/** 后端信封响应格式（{ code: 200, data: T, message: "成功" }） */
export interface EnvelopeResponse<T = unknown> {
  code: number
  data: T
  message: string
  success?: boolean
}

/** 单实体响应 — 自动解包后可直接访问实体字段 */
export type SingleResponse<T = unknown> = T & {
  code?: number
  message?: string
  success?: boolean
}

/** 列表响应 — 自动解包后可直接访问 items/total */
export type ListResponse<T = unknown> = PaginatedResponse<T> & {
  code?: number
  message?: string
  success?: boolean
}

/** 操作结果响应 */
export interface OperationResult {
  success: boolean
  message?: string
  id?: number | string
  [key: string]: unknown
}

/** 查询参数 */
export interface QueryParams {
  page?: number
  page_size?: number
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  [key: string]: unknown
}

/** 错误响应类型 */
export interface ApiError {
  response?: {
    status?: number
    data?: {
      detail?: string
      message?: string
    }
  }
  message?: string
}

/** Axios 配置扩展 */
export interface RequestConfig {
  showError?: boolean
  showLoading?: boolean
  timeout?: number
  [key: string]: unknown
}

/** 资金操作数据（工作流请求） */
export interface FundActionData {
  opinion?: string
  comment?: string
  reason?: string
  allocated_amount?: number
  allocation_method?: string
  audit_result?: string
  [key: string]: unknown
}
