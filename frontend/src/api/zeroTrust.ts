/**
 * 零信任安全 API
 * 提供零信任安全策略管理、访问评估和信任评分功能
 */

import { get, post } from '@/api/request'

// ==================== 类型定义 ====================

/** 信任评估因子 */
export interface TrustFactor {
  factor: string
  score: number
  status: string
  detail: string
}

/** 信任评估结果 */
export interface TrustAssessment {
  level: string
  score: number
  factors: TrustFactor[]
  recommendations: string[]
  assessed_at: string
}

/** 安全策略 */
export interface SecurityPolicy {
  id: string
  name: string
  description: string
  category: string
  enabled: boolean
  severity: string
  conditions?: Record<string, any>
  actions?: string[]
}

/** 安全策略列表响应 */
export interface SecurityPolicyList {
  policies: SecurityPolicy[]
  total: number
  enabled_count: number
}

/** 访问评估请求 */
export interface AccessEvaluationRequest {
  resource: string
  action: string
  context?: Record<string, any>
}

/** 访问评估结果 */
export interface AccessEvaluationResult {
  resource: string
  action: string
  username: string
  result: 'allowed' | 'denied'
  message: string
  evaluated_at: string
}

/** 安全事件 */
export interface SecurityEvent {
  id: number
  event_type: string
  source: string
  severity: string
  message: string
  details?: Record<string, any>
  timestamp: string
}

/** 安全事件列表响应 */
export interface SecurityEventList {
  items: SecurityEvent[]
  total: number
  page: number
  page_size: number
}

/** 安全事件统计 */
export interface SecurityEventStats {
  total_events: number
  high_severity_count: number
  by_severity: Record<string, number>
  by_type: Record<string, number>
  security_posture: 'secure' | 'normal' | 'warning'
}

// ==================== API 函数 ====================

/** 获取信任评估 */
export async function getTrustAssessment(): Promise<{
  success: boolean
  data: TrustAssessment
}> {
  return get('/zero-trust/assessment')
}

/** 获取安全策略列表 */
export async function listSecurityPolicies(params?: {
  category?: string
  enabled_only?: boolean
}): Promise<{ success: boolean; data: SecurityPolicyList }> {
  return get('/zero-trust/policies', params)
}

/** 获取安全策略详情 */
export async function getSecurityPolicy(
  policyId: string
): Promise<{ success: boolean; data: SecurityPolicy }> {
  return get(`/zero-trust/policies/${policyId}`)
}

/** 评估访问请求 */
export async function evaluateAccessRequest(
  data: AccessEvaluationRequest
): Promise<{ success: boolean; data: AccessEvaluationResult }> {
  return post('/zero-trust/evaluate', data)
}

/** 获取安全事件列表 */
export async function listSecurityEvents(params?: {
  severity?: string
  event_type?: string
  page?: number
  page_size?: number
}): Promise<{ success: boolean; data: SecurityEventList }> {
  return get('/zero-trust/events', params)
}

/** 记录安全事件 */
export async function reportSecurityEvent(data: {
  event_type: string
  source: string
  severity?: string
  message: string
  details?: Record<string, any>
}): Promise<{
  success: boolean
  message: string
  data: { event_id: number }
}> {
  return post('/zero-trust/events', data)
}

/** 获取安全事件统计 */
export async function getSecurityEventStats(): Promise<{
  success: boolean
  data: SecurityEventStats
}> {
  return get('/zero-trust/events/stats')
}

// ==================== 分组导出 ====================

export const zeroTrustApi = {
  getAssessment: getTrustAssessment,
  listPolicies: listSecurityPolicies,
  getPolicy: getSecurityPolicy,
  evaluateAccess: evaluateAccessRequest,
  listEvents: listSecurityEvents,
  reportEvent: reportSecurityEvent,
  getEventStats: getSecurityEventStats,
}
