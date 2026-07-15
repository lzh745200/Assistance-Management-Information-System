/**
 * 审计管理 API
 */
import { get, post, del } from '@/api/request'
import type { PaginatedResponse } from '@/types/api'

/** 审计日志 */
export interface AuditLog {
  id: number
  user_id?: number
  username?: string
  action: string
  resource_type?: string
  resource_id?: string
  detail?: string
  status?: string
  level?: string
  ip_address?: string
  user_agent?: string
  created_at?: string
}

/** 登录尝试记录 */
export interface LoginAttempt {
  id: number
  username: string
  ip_address?: string
  user_agent?: string
  success: boolean
  failure_reason?: string
  attempt_time?: string
}

/** 安全事件 */
export interface SecurityEvent {
  id: number
  event_type: string
  severity: string
  description?: string
  source_ip?: string
  resolved: boolean
  resolved_by?: number
  resolution_notes?: string
  created_at?: string
}

/** 审计统计 */
export interface AuditStats {
  today_operations?: number
  total_operations?: number
  active_users?: number
  failed_operations?: number
  warnings?: number
  period_days?: number
  by_action?: Array<{ action: string; count: number }>
  by_resource?: Array<{ resource_type: string; count: number }>
}

/** 审计日志查询参数 */
export interface AuditLogQuery {
  user_id?: number
  action?: string
  resource_type?: string
  status?: string
  level?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

/** 登录尝试查询参数 */
export interface LoginAttemptQuery {
  username?: string
  ip_address?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

/** 安全事件查询参数 */
export interface SecurityEventQuery {
  severity?: string
  event_type?: string
  resolved?: boolean
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

const BASE = '/system/audit'

export const auditApi = {
  /** 获取审计日志列表 */
  async getLogs(params?: AuditLogQuery): Promise<PaginatedResponse<AuditLog>> {
    const res = await get(`${BASE}/logs`, { params })
    return res.data
  },

  /** 获取审计统计 */
  async getStats(params?: { start_date?: string; end_date?: string }): Promise<AuditStats> {
    const res = await get(`${BASE}/stats`, { params })
    return res.data
  },

  /** 获取登录尝试记录 */
  async getLoginAttempts(params?: LoginAttemptQuery): Promise<PaginatedResponse<LoginAttempt>> {
    const res = await get(`${BASE}/login-attempts`, { params })
    return res.data
  },

  /** 获取安全事件列表 */
  async getSecurityEvents(params?: SecurityEventQuery): Promise<PaginatedResponse<SecurityEvent>> {
    const res = await get(`${BASE}/security/events`, { params })
    return res.data
  },

  /** 获取安全统计 */
  async getSecurityStats(): Promise<Record<string, any>> {
    const res = await get(`${BASE}/security/stats`)
    return res.data
  },

  /** 处理安全事件 */
  async resolveSecurityEvent(eventId: number, notes: string) {
    const res = await post(`${BASE}/security/events/${eventId}/resolve`, null, {
      params: { resolution_notes: notes },
    })
    return res.data
  },

  /** 删除审计日志 */
  async deleteLog(logId: number) {
    const res = await del(`${BASE}/logs/${logId}`)
    return res.data
  },
}
