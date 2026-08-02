import { describe, it, expect } from 'vitest'
import { md5, sha256 } from '@/utils/crypto'

describe('utils/crypto', () => {
  describe('md5', () => {
    it('返回 8 位十六进制字符串', () => {
      expect(md5('hello')).toMatch(/^[0-9a-f]{8}$/)
    })

    it('相同输入返回相同结果', () => {
      expect(md5('test')).toBe(md5('test'))
    })

    it('不同输入返回不同结果', () => {
      expect(md5('hello')).not.toBe(md5('world'))
    })

    it('空字符串返回有效哈希', () => {
      expect(md5('')).toMatch(/^[0-9a-f]{8}$/)
    })
  })

  describe('sha256', () => {
    it('返回 64 位十六进制字符串', async () => {
      expect(await sha256('hello')).toMatch(/^[0-9a-f]{64}$/)
    })

    it('相同输入返回相同结果', async () => {
      expect(await sha256('test')).toBe(await sha256('test'))
    })

    it('不同输入返回不同结果', async () => {
      expect(await sha256('hello')).not.toBe(await sha256('world'))
    })

    it('中文输入可哈希', async () => {
      expect(await sha256('乡村振兴')).toMatch(/^[0-9a-f]{64}$/)
    })
  })
})
