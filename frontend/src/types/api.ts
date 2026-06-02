/**
 * API 通用类型定义
 */

/** API 响应基础结构 */
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

/** 分页响应结构 */
export interface PaginatedResponse<T = unknown> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

/** 查询参数 */
export interface QueryParams {
  page?: number;
  page_size?: number;
  search?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  [key: string]: unknown;
}

/** 错误响应类型 */
export interface ApiError {
  response?: {
    status?: number;
    data?: {
      detail?: string;
      message?: string;
    };
  };
  message?: string;
}

/** Axios 配置扩展 */
export interface RequestConfig {
  showError?: boolean;
  showLoading?: boolean;
  timeout?: number;
  [key: string]: unknown;
}

/** 资金操作数据（工作流请求） */
export interface FundActionData {
  opinion?: string;
  comment?: string;
  reason?: string;
  allocated_amount?: number;
  allocation_method?: string;
  audit_result?: string;
  [key: string]: unknown;
}
