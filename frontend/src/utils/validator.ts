/**
 * 前端数据校验引擎
 * 从后端动态加载校验规则并执行实时校验
 */
import { apiRequest } from '@/api/request'

export interface ValidationRule {
  id: number
  module: string
  field: string
  rule_type: string
  params: string | null
  error_message: string
  is_active: boolean
  priority: number
}

export interface ValidationError {
  field: string
  rule_type: string
  message: string
}

export interface ValidationResult {
  valid: boolean
  errors: ValidationError[]
}

// 规则缓存
const rulesCache: Map<string, { rules: ValidationRule[]; timestamp: number }> = new Map()
const CACHE_TTL = 5 * 60 * 1000 // 5分钟缓存

/**
 * 获取指定模块的校验规则（带缓存）
 */
export async function fetchRules(module: string): Promise<ValidationRule[]> {
  const cached = rulesCache.get(module)
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.rules
  }
  try {
    const { data } = await apiRequest({
      method: 'GET',
      url: '/validation/rules',
      params: { module, is_active: true },
    })
    const rules = data as ValidationRule[]
    rulesCache.set(module, { rules, timestamp: Date.now() })
    return rules
  } catch {
    return cached?.rules || []
  }
}

/**
 * 清除规则缓存
 */
export function clearRulesCache(module?: string): void {
  if (module) {
    rulesCache.delete(module)
  } else {
    rulesCache.clear()
  }
}

/**
 * 前端本地校验（不调用后端）
 */
export function validateLocally(
  rules: ValidationRule[],
  data: Record<string, any>
): ValidationResult {
  const errors: ValidationError[] = []

  for (const rule of rules) {
    if (!rule.is_active) continue
    const value = data[rule.field]
    const params = rule.params ? JSON.parse(rule.params) : {}
    const failed = checkRule(rule.rule_type, value, params, data)
    if (failed) {
      errors.push({
        field: rule.field,
        rule_type: rule.rule_type,
        message: rule.error_message,
      })
    }
  }

  return { valid: errors.length === 0, errors }
}

/**
 * 校验单条规则
 */
function checkRule(
  ruleType: string,
  value: any,
  params: Record<string, any>,
  fullData: Record<string, any>
): boolean {
  if (ruleType === 'required') {
    return (
      value === null || value === undefined || (typeof value === 'string' && value.trim() === '')
    )
  }

  // 非必填字段为空时跳过
  if (value === null || value === undefined || value === '') return false

  switch (ruleType) {
    case 'positive':
      return isNaN(Number(value)) || Number(value) <= 0

    case 'non_negative':
      return isNaN(Number(value)) || Number(value) < 0

    case 'max_length':
      return String(value).length > (params.max ?? 255)

    case 'min_length':
      return String(value).length < (params.min ?? 0)

    case 'range': {
      const num = Number(value)
      if (isNaN(num)) return true
      if (params.min !== undefined && num < Number(params.min)) return true
      if (params.max !== undefined && num > Number(params.max)) return true
      return false
    }

    case 'regex': {
      const pattern = params.pattern || ''
      try {
        return !new RegExp(pattern).test(String(value))
      } catch {
        return true
      }
    }

    case 'date_format': {
      // 简单日期格式验证
      const fmt = params.format || 'YYYY-MM-DD'
      if (fmt === '%Y-%m-%d' || fmt === 'YYYY-MM-DD') {
        return !/^\d{4}-\d{2}-\d{2}$/.test(String(value))
      }
      return false
    }

    case 'file_type': {
      const allowed: string[] = params.allowed || []
      const ext = String(value).split('.').pop()?.toLowerCase() || ''
      return !allowed.includes(ext)
    }

    case 'enum_values': {
      const allowed: any[] = params.values || []
      return !allowed.map(String).includes(String(value))
    }

    case 'cross_field': {
      const otherField = params.other_field
      const operator = params.operator || '<='
      if (!otherField || !(otherField in fullData)) return false
      const v1 = Number(value)
      const v2 = Number(fullData[otherField])
      if (isNaN(v1) || isNaN(v2)) return true
      switch (operator) {
        case '<=':
          return v1 > v2
        case '>=':
          return v1 < v2
        case '<':
          return v1 >= v2
        case '>':
          return v1 <= v2
        case '==':
          return v1 !== v2
        default:
          return false
      }
    }

    default:
      return false
  }
}

/**
 * 获取字段的错误信息
 */
export function getFieldErrors(errors: ValidationError[], field: string): string[] {
  return errors.filter((e) => e.field === field).map((e) => e.message)
}

/**
 * 完整校验流程：获取规则 + 本地校验
 */
export async function validateModule(
  module: string,
  data: Record<string, any>
): Promise<ValidationResult> {
  const rules = await fetchRules(module)
  return validateLocally(rules, data)
}
