import { describe, it, expect } from 'vitest'
import { SecurityLevel, getSecurityLevelTagType, getSecurityWeight, sanitizeInput } from '@/utils/security'

describe('utils/security', () => {
  describe('SecurityLevel enum', () => {
    it('TOP_SECRET = 绝密', () => {
      expect(SecurityLevel.TOP_SECRET).toBe('绝密')
    })
    it('SECRET = 机密', () => {
      expect(SecurityLevel.SECRET).toBe('机密')
    })
    it('CONFIDENTIAL = 秘密', () => {
      expect(SecurityLevel.CONFIDENTIAL).toBe('秘密')
    })
    it('INTERNAL = 内部', () => {
      expect(SecurityLevel.INTERNAL).toBe('内部')
    })
    it('PUBLIC = 公开', () => {
      expect(SecurityLevel.PUBLIC).toBe('公开')
    })
  })

  describe('getSecurityLevelTagType', () => {
    it('TOP_SECRET -> danger', () => {
      expect(getSecurityLevelTagType(SecurityLevel.TOP_SECRET)).toBe('danger')
    })
    it('SECRET -> warning', () => {
      expect(getSecurityLevelTagType(SecurityLevel.SECRET)).toBe('warning')
    })
    it('CONFIDENTIAL -> primary', () => {
      expect(getSecurityLevelTagType(SecurityLevel.CONFIDENTIAL)).toBe('primary')
    })
    it('INTERNAL -> info', () => {
      expect(getSecurityLevelTagType(SecurityLevel.INTERNAL)).toBe('info')
    })
    it('unknown level -> "" (default)', () => {
      expect(getSecurityLevelTagType('未知' as any)).toBe('')
    })
  })

  describe('getSecurityWeight', () => {
    it('TOP_SECRET -> 5', () => {
      expect(getSecurityWeight(SecurityLevel.TOP_SECRET)).toBe(5)
    })
    it('SECRET -> 4', () => {
      expect(getSecurityWeight(SecurityLevel.SECRET)).toBe(4)
    })
    it('CONFIDENTIAL -> 3', () => {
      expect(getSecurityWeight(SecurityLevel.CONFIDENTIAL)).toBe(3)
    })
    it('INTERNAL -> 2', () => {
      expect(getSecurityWeight(SecurityLevel.INTERNAL)).toBe(2)
    })
    it('PUBLIC -> 1', () => {
      expect(getSecurityWeight(SecurityLevel.PUBLIC)).toBe(1)
    })
    it('unknown -> 0', () => {
      expect(getSecurityWeight('unknown' as any)).toBe(0)
    })
  })

  describe('sanitizeInput', () => {
    it('escape <, >, &, ", \'', () => {
      expect(sanitizeInput('<script>alert("x")</script>'))
        .toBe('&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;')
    })
    it('escape & first to avoid double-escape', () => {
      expect(sanitizeInput('&amp;')).toBe('&amp;amp;')
    })
    it('escape single quote', () => {
      expect(sanitizeInput("it's")).toBe('it&#039;s')
    })
    it('plain text unchanged', () => {
      expect(sanitizeInput('hello world')).toBe('hello world')
    })
  })
})
