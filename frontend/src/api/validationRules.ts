/**
 * 数据校验规则API服务
 * 管理员可配置字段级校验规则，前端动态读取并实时校验
 */

import api from './request'

const BASE_URL = '/validation'

/** 获取校验规则列表 */
export function listRules(params?: { module?: string; is_active?: boolean }): Promise<any> {
  return api.get(`${BASE_URL}/rules`, { params })
}

/** 创建校验规则（管理员） */
export function createRule(data: {
  module: string
  field: string
  rule_type: string
  params?: string
  error_message?: string
  description?: string
  is_active?: boolean
  priority?: number
}): Promise<any> {
  return api.post(`${BASE_URL}/rules`, data)
}

/** 更新校验规则 */
export function updateRule(
  ruleId: number,
  data: {
    module?: string
    field?: string
    rule_type?: string
    params?: string
    error_message?: string
    description?: string
    is_active?: boolean
    priority?: number
  }
): Promise<any> {
  return api.put(`${BASE_URL}/rules/${ruleId}`, data)
}

/** 删除校验规则 */
export function deleteRule(ruleId: number): Promise<any> {
  return api.delete(`${BASE_URL}/rules/${ruleId}`)
}

/** 对提交数据执行校验 */
export function runValidation(module: string, data: Record<string, any>): Promise<any> {
  return api.post(`${BASE_URL}/validate`, data, { params: { module } })
}
