/**
 * FormValidator 单元测试
 * 覆盖: src/utils/formValidator.ts
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  validateValue,
  FormValidator,
  createFormValidator,
  emailRule,
  phoneRule,
  idCardRule,
  urlRule,
  requiredRule,
  lengthRule,
  type ValidationRule,
} from '@/utils/formValidator'

// ==================== validateValue 测试 ====================

describe('validateValue', () => {
  it('should pass when no rules', async () => {
    const result = await validateValue('anything', [])
    expect(result.valid).toBe(true)
    expect(result.message).toBe('')
  })

  describe('required rule', () => {
    const rules: ValidationRule[] = [{ required: true, message: '必填' }]

    it('should fail for undefined', async () => {
      const result = await validateValue(undefined, rules)
      expect(result.valid).toBe(false)
      expect(result.message).toBe('必填')
    })

    it('should fail for null', async () => {
      const result = await validateValue(null, rules)
      expect(result.valid).toBe(false)
    })

    it('should fail for empty string', async () => {
      const result = await validateValue('', rules)
      expect(result.valid).toBe(false)
    })

    it('should fail for empty array', async () => {
      const result = await validateValue([], rules)
      expect(result.valid).toBe(false)
    })

    it('should pass for non-empty string', async () => {
      const result = await validateValue('hello', rules)
      expect(result.valid).toBe(true)
    })

    it('should use default message', async () => {
      const result = await validateValue(undefined, [{ required: true }])
      expect(result.message).toBe('此字段为必填项')
    })
  })

  describe('min/max length rules', () => {
    it('should fail when too short', async () => {
      const result = await validateValue('ab', [{ min: 3 }])
      expect(result.valid).toBe(false)
      expect(result.message).toContain('3')
    })

    it('should fail when too long', async () => {
      const result = await validateValue('abcdef', [{ max: 3 }])
      expect(result.valid).toBe(false)
      expect(result.message).toContain('3')
    })

    it('should pass when within range', async () => {
      const result = await validateValue('abc', [{ min: 2, max: 5 }])
      expect(result.valid).toBe(true)
    })

    it('should check array length for min', async () => {
      const result = await validateValue([1], [{ min: 2 }])
      expect(result.valid).toBe(false)
    })

    it('should check array length for max', async () => {
      const result = await validateValue([1, 2, 3, 4], [{ max: 2 }])
      expect(result.valid).toBe(false)
    })

    it('should skip min/max for empty non-required value', async () => {
      const result = await validateValue('', [{ min: 3 }])
      expect(result.valid).toBe(true) // empty + not required => skip
    })

    it('should use custom message', async () => {
      const result = await validateValue('a', [{ min: 3, message: '太短了' }])
      expect(result.message).toBe('太短了')
    })
  })

  describe('pattern rule', () => {
    it('should pass matching pattern', async () => {
      const result = await validateValue('hello123', [{ pattern: /^[a-z0-9]+$/ }])
      expect(result.valid).toBe(true)
    })

    it('should fail non-matching pattern', async () => {
      const result = await validateValue('Hello!', [{ pattern: /^[a-z0-9]+$/ }])
      expect(result.valid).toBe(false)
    })

    it('should use default pattern message', async () => {
      const result = await validateValue('bad', [{ pattern: /^\d+$/ }])
      expect(result.message).toBe('格式不正确')
    })
  })

  describe('custom validator', () => {
    it('should pass when validator returns true', async () => {
      const result = await validateValue('good', [{ validator: () => true }])
      expect(result.valid).toBe(true)
    })

    it('should fail when validator returns false', async () => {
      const result = await validateValue('bad', [{ validator: () => false, message: '自定义失败' }])
      expect(result.valid).toBe(false)
      expect(result.message).toBe('自定义失败')
    })

    it('should fail with string message from validator', async () => {
      const result = await validateValue('bad', [{ validator: () => '自定义错误消息' }])
      expect(result.valid).toBe(false)
      expect(result.message).toBe('自定义错误消息')
    })

    it('should handle async validator', async () => {
      const result = await validateValue('value', [{
        validator: async () => true,
      }])
      expect(result.valid).toBe(true)
    })

    it('should handle validator exception', async () => {
      const result = await validateValue('value', [{
        validator: () => { throw new Error('oops') },
        message: '出错了',
      }])
      expect(result.valid).toBe(false)
      expect(result.message).toBe('出错了')
    })

    it('should use default message on exception', async () => {
      const result = await validateValue('value', [{
        validator: () => { throw new Error('oops') },
      }])
      expect(result.message).toBe('校验出错')
    })

    it('should use default message on false return', async () => {
      const result = await validateValue('value', [{
        validator: () => false,
      }])
      expect(result.message).toBe('校验失败')
    })
  })

  describe('multiple rules', () => {
    it('should stop at first failure', async () => {
      const result = await validateValue('', [
        { required: true, message: '必填' },
        { min: 3, message: '太短' },
      ])
      expect(result.message).toBe('必填')
    })
  })
})

// ==================== FormValidator 类测试 ====================

describe('FormValidator', () => {
  let validator: FormValidator

  beforeEach(() => {
    validator = new FormValidator({ debounceDelay: 0 })
  })

  describe('addField / removeField', () => {
    it('should add field rules', () => {
      validator.addField('name', [{ required: true }])
      const state = validator.getFieldState('name')
      expect(state).toBeDefined()
      expect(state!.valid).toBe(true)
      expect(state!.touched).toBe(false)
    })

    it('should remove field rules', () => {
      validator.addField('name', [{ required: true }])
      validator.removeField('name')
      expect(validator.getFieldState('name')).toBeUndefined()
    })
  })

  describe('validateField', () => {
    it('should validate a field', async () => {
      validator.addField('name', [{ required: true, message: '必填' }])
      const result = await validator.validateField('name', '')
      expect(result.valid).toBe(false)
      expect(result.message).toBe('必填')
    })

    it('should update field state', async () => {
      validator.addField('name', [{ required: true }])
      await validator.validateField('name', '')
      const state = validator.getFieldState('name')
      expect(state!.valid).toBe(false)
      expect(state!.touched).toBe(true)
      expect(state!.validating).toBe(false)
    })

    it('should pass for unknown field', async () => {
      const result = await validator.validateField('unknown', 'value')
      expect(result.valid).toBe(true)
    })

    it('should increment validate call count', async () => {
      validator.addField('name', [{ required: true }])
      validator.resetValidateCallCount()
      await validator.validateField('name', 'test')
      expect(validator.getValidateCallCount()).toBe(1)
    })
  })

  describe('validateAll', () => {
    it('should validate all fields', async () => {
      validator.addField('name', [{ required: true, message: '名称必填' }])
      validator.addField('email', [{ required: true, message: '邮箱必填' }])

      const result = await validator.validateAll({ name: '', email: '' })
      expect(result.valid).toBe(false)
      expect(result.errors.name).toBe('名称必填')
      expect(result.errors.email).toBe('邮箱必填')
    })

    it('should pass when all valid', async () => {
      validator.addField('name', [{ required: true }])
      validator.addField('email', [{ required: true }])

      const result = await validator.validateAll({ name: 'Test', email: 'a@b.com' })
      expect(result.valid).toBe(true)
      expect(Object.keys(result.errors)).toHaveLength(0)
    })
  })

  describe('getAllStates', () => {
    it('should return copy of all states', () => {
      validator.addField('a', [{ required: true }])
      validator.addField('b', [{ required: true }])
      const states = validator.getAllStates()
      expect(states.size).toBe(2)
    })
  })

  describe('reset', () => {
    it('should reset specific field', async () => {
      validator.addField('name', [{ required: true }])
      await validator.validateField('name', '')
      validator.reset('name')
      const state = validator.getFieldState('name')
      expect(state!.valid).toBe(true)
      expect(state!.touched).toBe(false)
      expect(state!.message).toBe('')
    })

    it('should reset all fields', async () => {
      validator.addField('a', [{ required: true }])
      validator.addField('b', [{ required: true }])
      await validator.validateField('a', '')
      await validator.validateField('b', '')
      validator.reset()
      expect(validator.getFieldState('a')!.valid).toBe(true)
      expect(validator.getFieldState('b')!.valid).toBe(true)
    })
  })

  describe('destroy', () => {
    it('should clear everything', () => {
      validator.addField('name', [{ required: true }])
      validator.destroy()
      expect(validator.getFieldState('name')).toBeUndefined()
    })
  })
})

// ==================== createFormValidator 便捷函数 ====================

describe('createFormValidator', () => {
  it('should create a FormValidator instance', () => {
    const v = createFormValidator()
    expect(v).toBeInstanceOf(FormValidator)
  })

  it('should accept options', () => {
    const v = createFormValidator({ debounceDelay: 500 })
    expect(v).toBeInstanceOf(FormValidator)
  })
})

// ==================== 预置校验规则测试 ====================

describe('preset validation rules', () => {
  it('emailRule: valid email', async () => {
    const result = await validateValue('test@example.com', [emailRule])
    expect(result.valid).toBe(true)
  })

  it('emailRule: invalid email', async () => {
    const result = await validateValue('invalid', [emailRule])
    expect(result.valid).toBe(false)
  })

  it('phoneRule: valid phone', async () => {
    const result = await validateValue('13812345678', [phoneRule])
    expect(result.valid).toBe(true)
  })

  it('phoneRule: invalid phone', async () => {
    const result = await validateValue('12345', [phoneRule])
    expect(result.valid).toBe(false)
  })

  it('idCardRule: valid id', async () => {
    const result = await validateValue('110101199001011234', [idCardRule])
    expect(result.valid).toBe(true)
  })

  it('idCardRule: invalid id', async () => {
    const result = await validateValue('123', [idCardRule])
    expect(result.valid).toBe(false)
  })

  it('urlRule: valid url', async () => {
    const result = await validateValue('https://example.com', [urlRule])
    expect(result.valid).toBe(true)
  })

  it('urlRule: invalid url', async () => {
    const result = await validateValue('not-a-url', [urlRule])
    expect(result.valid).toBe(false)
  })

  it('requiredRule: with custom message', () => {
    const rule = requiredRule('自定义')
    expect(rule.required).toBe(true)
    expect(rule.message).toBe('自定义')
  })

  it('requiredRule: with default message', () => {
    const rule = requiredRule()
    expect(rule.message).toBe('此字段为必填项')
  })

  it('lengthRule: creates correct rule', () => {
    const rule = lengthRule(3, 10)
    expect(rule.min).toBe(3)
    expect(rule.max).toBe(10)
  })

  it('lengthRule: with custom message', () => {
    const rule = lengthRule(3, 10, '自定义')
    expect(rule.message).toBe('自定义')
  })

  it('lengthRule: with default message', () => {
    const rule = lengthRule(3, 10)
    expect(rule.message).toContain('3')
    expect(rule.message).toContain('10')
  })
})
