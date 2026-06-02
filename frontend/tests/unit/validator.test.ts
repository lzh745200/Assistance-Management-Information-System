import { describe, it, expect, vi, beforeEach } from 'vitest'
import { validateLocally, getFieldErrors, clearRulesCache, type ValidationRule } from '@/utils/validator'

function makeRule(overrides: Partial<ValidationRule> = {}): ValidationRule {
  return {
    id: 1,
    module: 'test',
    field: 'name',
    rule_type: 'required',
    params: null,
    error_message: '此字段必填',
    is_active: true,
    priority: 1,
    ...overrides,
  }
}

describe('validator - validateLocally', () => {
  beforeEach(() => {
    clearRulesCache()
  })

  it('required: 空字符串应失败', () => {
    const rules = [makeRule()]
    const result = validateLocally(rules, { name: '' })
    expect(result.valid).toBe(false)
    expect(result.errors).toHaveLength(1)
    expect(result.errors[0].rule_type).toBe('required')
  })

  it('required: null 应失败', () => {
    const result = validateLocally([makeRule()], { name: null })
    expect(result.valid).toBe(false)
  })

  it('required: undefined 应失败', () => {
    const result = validateLocally([makeRule()], { name: undefined })
    expect(result.valid).toBe(false)
  })

  it('required: 有值应通过', () => {
    const result = validateLocally([makeRule()], { name: '张三' })
    expect(result.valid).toBe(true)
    expect(result.errors).toHaveLength(0)
  })

  it('非激活规则应跳过', () => {
    const rules = [makeRule({ is_active: false })]
    const result = validateLocally(rules, { name: '' })
    expect(result.valid).toBe(true)
  })

  it('positive: 正数通过', () => {
    const rules = [makeRule({ rule_type: 'positive', field: 'amount', error_message: '必须为正数' })]
    expect(validateLocally(rules, { amount: 10 }).valid).toBe(true)
  })

  it('positive: 0 失败', () => {
    const rules = [makeRule({ rule_type: 'positive', field: 'amount', error_message: '必须为正数' })]
    expect(validateLocally(rules, { amount: 0 }).valid).toBe(false)
  })

  it('positive: 负数失败', () => {
    const rules = [makeRule({ rule_type: 'positive', field: 'amount', error_message: '必须为正数' })]
    expect(validateLocally(rules, { amount: -5 }).valid).toBe(false)
  })

  it('non_negative: 0 通过', () => {
    const rules = [makeRule({ rule_type: 'non_negative', field: 'count', error_message: '不能为负' })]
    expect(validateLocally(rules, { count: 0 }).valid).toBe(true)
  })

  it('non_negative: 负数失败', () => {
    const rules = [makeRule({ rule_type: 'non_negative', field: 'count', error_message: '不能为负' })]
    expect(validateLocally(rules, { count: -1 }).valid).toBe(false)
  })

  it('max_length: 超过限制失败', () => {
    const rules = [makeRule({ rule_type: 'max_length', field: 'name', params: '{"max":5}', error_message: '过长' })]
    expect(validateLocally(rules, { name: '超长的名字测试' }).valid).toBe(false)
  })

  it('max_length: 符合限制通过', () => {
    const rules = [makeRule({ rule_type: 'max_length', field: 'name', params: '{"max":10}', error_message: '过长' })]
    expect(validateLocally(rules, { name: '张三' }).valid).toBe(true)
  })

  it('min_length: 过短失败', () => {
    const rules = [makeRule({ rule_type: 'min_length', field: 'name', params: '{"min":3}', error_message: '过短' })]
    expect(validateLocally(rules, { name: '张' }).valid).toBe(false)
  })

  it('range: 在范围内通过', () => {
    const rules = [makeRule({ rule_type: 'range', field: 'age', params: '{"min":0,"max":150}', error_message: '超范围' })]
    expect(validateLocally(rules, { age: 25 }).valid).toBe(true)
  })

  it('range: 超出范围失败', () => {
    const rules = [makeRule({ rule_type: 'range', field: 'age', params: '{"min":0,"max":150}', error_message: '超范围' })]
    expect(validateLocally(rules, { age: 200 }).valid).toBe(false)
  })

  it('regex: 匹配通过', () => {
    const rules = [makeRule({ rule_type: 'regex', field: 'phone', params: '{"pattern":"^1[3-9]\\\\d{9}$"}', error_message: '格式错误' })]
    expect(validateLocally(rules, { phone: '13800138000' }).valid).toBe(true)
  })

  it('regex: 不匹配失败', () => {
    const rules = [makeRule({ rule_type: 'regex', field: 'phone', params: '{"pattern":"^1[3-9]\\\\d{9}$"}', error_message: '格式错误' })]
    expect(validateLocally(rules, { phone: '12345' }).valid).toBe(false)
  })

  it('date_format: YYYY-MM-DD 格式验证', () => {
    const rules = [makeRule({ rule_type: 'date_format', field: 'date', params: '{"format":"YYYY-MM-DD"}', error_message: '日期格式错误' })]
    expect(validateLocally(rules, { date: '2024-01-15' }).valid).toBe(true)
    expect(validateLocally(rules, { date: '20240115' }).valid).toBe(false)
  })

  it('enum_values: 在枚举中通过', () => {
    const rules = [makeRule({ rule_type: 'enum_values', field: 'status', params: '{"values":["active","inactive"]}', error_message: '无效值' })]
    expect(validateLocally(rules, { status: 'active' }).valid).toBe(true)
  })

  it('enum_values: 不在枚举中失败', () => {
    const rules = [makeRule({ rule_type: 'enum_values', field: 'status', params: '{"values":["active","inactive"]}', error_message: '无效值' })]
    expect(validateLocally(rules, { status: 'deleted' }).valid).toBe(false)
  })

  it('cross_field: <= 校验', () => {
    const rules = [makeRule({
      rule_type: 'cross_field',
      field: 'allocated',
      params: '{"other_field":"total","operator":"<="}',
      error_message: '不能超过总额',
    })]
    expect(validateLocally(rules, { allocated: 50, total: 100 }).valid).toBe(true)
    expect(validateLocally(rules, { allocated: 150, total: 100 }).valid).toBe(false)
  })

  it('file_type: 验证文件扩展名', () => {
    const rules = [makeRule({ rule_type: 'file_type', field: 'file', params: '{"allowed":["xlsx","csv"]}', error_message: '不支持的文件类型' })]
    expect(validateLocally(rules, { file: 'data.xlsx' }).valid).toBe(true)
    expect(validateLocally(rules, { file: 'image.png' }).valid).toBe(false)
  })

  it('空值字段（非 required）跳过校验', () => {
    const rules = [makeRule({ rule_type: 'positive', field: 'amount', error_message: '必须为正数' })]
    expect(validateLocally(rules, { amount: '' }).valid).toBe(true)
    expect(validateLocally(rules, { amount: null }).valid).toBe(true)
  })

  it('多条规则组合校验', () => {
    const rules = [
      makeRule({ id: 1, field: 'name', rule_type: 'required', error_message: '姓名必填' }),
      makeRule({ id: 2, field: 'amount', rule_type: 'positive', error_message: '金额必须为正数' }),
    ]
    const result = validateLocally(rules, { name: '', amount: -1 })
    expect(result.valid).toBe(false)
    expect(result.errors).toHaveLength(2)
  })
})

describe('validator - getFieldErrors', () => {
  it('返回指定字段的错误消息', () => {
    const errors = [
      { field: 'name', rule_type: 'required', message: '姓名必填' },
      { field: 'age', rule_type: 'range', message: '年龄超范围' },
      { field: 'name', rule_type: 'max_length', message: '姓名过长' },
    ]
    const nameErrors = getFieldErrors(errors, 'name')
    expect(nameErrors).toEqual(['姓名必填', '姓名过长'])
  })

  it('无匹配返回空数组', () => {
    const errors = [{ field: 'name', rule_type: 'required', message: '必填' }]
    expect(getFieldErrors(errors, 'phone')).toEqual([])
  })
})
