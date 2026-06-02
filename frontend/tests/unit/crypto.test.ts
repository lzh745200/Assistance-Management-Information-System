import { describe, it, expect } from 'vitest'
import { md5, sha256 } from '@/utils/crypto'

describe('crypto', () => {
  describe('md5', () => {
    it('返回 8 位十六进制字符串', () => {
      const result = md5('hello')
      expect(result).toMatch(/^[0-9a-f]{8,}$/)
    })

    it('相同输入返回相同结果', () => {
      expect(md5('test')).toBe(md5('test'))
    })

    it('不同输入返回不同结果', () => {
      expect(md5('hello')).not.toBe(md5('world'))
    })

    it('空字符串返回有效哈希', () => {
      const result = md5('')
      expect(result).toMatch(/^[0-9a-f]+$/)
    })
  })

  describe('sha256', () => {
    it('返回 64 位十六进制字符串', async () => {
      const result = await sha256('hello')
      expect(result).toMatch(/^[0-9a-f]{64}$/)
    })

    it('相同输入返回相同结果', async () => {
      const a = await sha256('test')
      const b = await sha256('test')
      expect(a).toBe(b)
    })

    it('不同输入返回不同结果', async () => {
      const a = await sha256('hello')
      const b = await sha256('world')
      expect(a).not.toBe(b)
    })
  })
})
