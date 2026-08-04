import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const { loggerMock } = vi.hoisted(() => ({
  loggerMock: { error: vi.fn(), warn: vi.fn(), info: vi.fn(), debug: vi.fn() },
}))

vi.mock('@/utils/logger', () => ({ logger: loggerMock }))

import {
  EnhancedStorage,
  enhancedStorage,
  sessionEnhancedStorage,
  STORAGE_KEYS,
  default as defaultStorage,
} from '@/utils/enhancedStorage'

function rawStorage(): Record<string, string> {
  const raw: Record<string, string> = {}
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key) raw[key] = localStorage.getItem(key) || ''
  }
  return raw
}

describe('utils/enhancedStorage', () => {
  let store: EnhancedStorage
  let dateNowSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    sessionStorage.clear()
    store = new EnhancedStorage('t_')
    dateNowSpy = vi.spyOn(Date, 'now').mockReturnValue(1_000_000)
  })

  afterEach(() => {
    dateNowSpy.mockRestore()
    vi.restoreAllMocks()
  })

  describe('常量与导出', () => {
    it('默认导出即 enhancedStorage 实例', () => {
      expect(defaultStorage).toBe(enhancedStorage)
    })

    it('STORAGE_KEYS 常量定义完整', () => {
      expect(STORAGE_KEYS.TOKEN).toBe('token')
      expect(STORAGE_KEYS.USER_INFO).toBe('user_info')
      expect(STORAGE_KEYS.DRAFT_DATA).toBe('draft_data')
    })

    it('默认实例前缀 assistance_management_，会话实例使用 sessionStorage', () => {
      enhancedStorage.set('_k', 1)
      expect(localStorage.getItem('assistance_management__k')).toBeTruthy()
      expect(sessionStorage.getItem('assistance_management__k')).toBeNull()
      sessionEnhancedStorage.set('_s', 2)
      expect(sessionStorage.getItem('assistance_management_session__s')).toBeTruthy()
      expect(localStorage.getItem('assistance_management_session__s')).toBeNull()
    })
  })

  describe('set / get', () => {
    it('set 后可通过 get 读回并保留选项', () => {
      store.set('user', { id: 1 }, { expiry: 5000, version: 'v2' })
      const raw = JSON.parse(localStorage.getItem('t_user')!)
      expect(raw.value).toEqual({ id: 1 })
      expect(raw.expiry).toBe(5000)
      expect(raw.version).toBe('v2')
      expect(raw.timestamp).toBe(1_000_000)
      expect(store.get('user')).toEqual({ id: 1 })
    })

    it('get 不存在的键返回 defaultValue', () => {
      expect(store.get('missing')).toBeUndefined()
      expect(store.get('missing', 'def')).toBe('def')
    })

    it('未过期数据正常返回', () => {
      store.set('k', 'v', { expiry: 1000 })
      dateNowSpy.mockReturnValue(1_000_999)
      expect(store.get('k')).toBe('v')
    })

    it('过期数据被删除并返回 defaultValue', () => {
      dateNowSpy.mockReturnValue(1_000_000)
      store.set('k', 'v', { expiry: 1000 })
      dateNowSpy.mockReturnValue(1_001_001)
      expect(store.get('k', 'gone')).toBe('gone')
      expect(localStorage.getItem('t_k')).toBeNull()
    })

    it('无过期时间的数据永不失效', () => {
      store.set('k', 'v')
      dateNowSpy.mockReturnValue(99_999_999)
      expect(store.get('k')).toBe('v')
    })

    it('损坏的 JSON 返回 defaultValue 并记录日志', () => {
      localStorage.setItem('t_bad', 'not-json')
      expect(store.get('bad', 'fb')).toBe('fb')
      expect(loggerMock.error).toHaveBeenCalledWith('读取存储数据失败:', expect.any(Error))
    })

    it('get 命中解析为 null 的条目 → 走异常兜底', () => {
      localStorage.setItem('t_null', 'null')
      expect(store.get('null', 'd')).toBe('d')
      expect(loggerMock.error).toHaveBeenCalled()
    })
  })

  describe('set 异常路径', () => {
    it('普通存储异常仅记录日志不重试', () => {
      const setSpy = vi.spyOn(localStorage, 'setItem').mockImplementationOnce(() => {
        throw new Error('disk full')
      })
      store.set('k', 1)
      expect(loggerMock.error).toHaveBeenCalledWith('存储数据失败:', expect.any(Error))
      expect(loggerMock.error).toHaveBeenCalledTimes(1)
      expect(setSpy).toHaveBeenCalledTimes(1)
    })

    it('QuotaExceededError 清理过期后重试成功', () => {
      const setSpy = vi
        .spyOn(localStorage, 'setItem')
        .mockImplementationOnce(() => {
          throw new DOMException('quota', 'QuotaExceededError')
        })
      store.set('k', 1)
      expect(setSpy).toHaveBeenCalledTimes(2)
      expect(loggerMock.error).toHaveBeenCalledTimes(1)
      expect(store.get('k')).toBe(1)
    })

    it('QuotaExceededError 重试仍失败则记录两次日志', () => {
      const setSpy = vi
        .spyOn(localStorage, 'setItem')
        .mockImplementationOnce(() => {
          throw new DOMException('quota', 'QuotaExceededError')
        })
        .mockImplementationOnce(() => {
          throw new DOMException('quota', 'QuotaExceededError')
        })
      store.set('k', 1)
      expect(setSpy).toHaveBeenCalledTimes(2)
      expect(loggerMock.error).toHaveBeenCalledTimes(2)
      expect(loggerMock.error).toHaveBeenNthCalledWith(2, '重试存储失败:', expect.any(DOMException))
      expect(localStorage.getItem('t_k')).toBeNull()
    })
  })

  describe('remove / has', () => {
    it('remove 删除键', () => {
      store.set('k', 1)
      store.remove('k')
      expect(localStorage.getItem('t_k')).toBeNull()
    })

    it('has 判断存在性', () => {
      expect(store.has('k')).toBe(false)
      store.set('k', 1)
      expect(store.has('k')).toBe(true)
    })
  })

  describe('clear', () => {
    it('仅清除带前缀的键', () => {
      store.set('a', 1)
      store.set('b', 2)
      localStorage.setItem('other_key', 'x')
      store.clear()
      expect(localStorage.getItem('t_a')).toBeNull()
      expect(localStorage.getItem('t_b')).toBeNull()
      expect(localStorage.getItem('other_key')).toBe('x')
    })
  })

  describe('clearExpired', () => {
    it('清除过期项与损坏项，保留有效项', () => {
      localStorage.setItem('t_expired', JSON.stringify({ value: 1, timestamp: 0, expiry: 100 }))
      localStorage.setItem('t_valid', JSON.stringify({ value: 2, timestamp: 999_900, expiry: 1000 }))
      localStorage.setItem('t_corrupt', '{{{')
      localStorage.setItem('t_noexpiry', JSON.stringify({ value: 3, timestamp: 0 }))
      localStorage.setItem('other', JSON.stringify({ value: 4, timestamp: 0, expiry: 1 }))
      store.clearExpired()
      expect(localStorage.getItem('t_expired')).toBeNull()
      expect(localStorage.getItem('t_corrupt')).toBeNull()
      expect(localStorage.getItem('t_valid')).not.toBeNull()
      expect(localStorage.getItem('t_noexpiry')).not.toBeNull()
      expect(localStorage.getItem('other')).not.toBeNull()
    })
  })

  describe('getUsage', () => {
    it('统计所有键的存储占用（不区分前缀）', () => {
      localStorage.setItem('k1', 'aaaa')
      localStorage.setItem('k2', 'bb')
      const usage = store.getUsage()
      const expectedUsed = 2 * (2 + 4 + 2 + 2)
      expect(usage.used).toBe(expectedUsed)
      expect(usage.total).toBe(5 * 1024 * 1024)
      expect(usage.percentage).toBe(Math.round((expectedUsed / usage.total) * 100))
    })
  })

  describe('keys', () => {
    it('仅返回带前缀的键并去除前缀', () => {
      store.set('a', 1)
      store.set('b', 2)
      localStorage.setItem('foreign', 'x')
      expect(store.keys().sort()).toEqual(['a', 'b'])
    })
  })

  describe('setMany / getMany', () => {
    it('批量写入共享选项', () => {
      store.setMany({ x: 1, y: '2' }, { expiry: 999, version: 'v1' })
      const rawX = JSON.parse(localStorage.getItem('t_x')!)
      expect(rawX.value).toBe(1)
      expect(rawX.expiry).toBe(999)
      expect(rawX.version).toBe('v1')
    })

    it('批量读取，缺失键为 undefined', () => {
      store.set('x', 1)
      store.set('y', 'two')
      const result = store.getMany<string | number>(['x', 'y', 'z'])
      expect(result).toEqual({ x: 1, y: 'two', z: undefined })
    })
  })

  describe('自定义存储边界（key() 返回 null / 值为空）', () => {
    it('遍历中空键与空值被安全跳过', () => {
      localStorage.setItem('p_a', JSON.stringify({ value: 1, timestamp: 0, expiry: 1 }))
      localStorage.setItem('p_b', JSON.stringify({ value: 2, timestamp: 999_999, expiry: 1000 }))
      localStorage.setItem('p_zzz', 'x')
      localStorage.setItem('foreign', 'y')

      const origKey = localStorage.key.bind(localStorage)
      const origGet = localStorage.getItem.bind(localStorage)
      const keySpy = vi
        .spyOn(localStorage, 'key')
        .mockImplementation((i: number) => {
          const k = origKey(i)
          return k === 'p_b' ? null : k
        })
      const getSpy = vi
        .spyOn(localStorage, 'getItem')
        .mockImplementation((k: string) => (k === 'p_zzz' ? null : origGet(k)))

      const s = new EnhancedStorage('p_')

      const usage = s.getUsage()
      expect(usage.used).toBe(94)
      expect(usage.percentage).toBe(Math.round((94 / (5 * 1024 * 1024)) * 100))

      s.clearExpired()
      expect(origGet('p_a')).toBeNull()
      expect(origGet('p_b')).not.toBeNull()
      expect(origGet('p_zzz')).not.toBeNull()
      expect(origGet('foreign')).toBe('y')

      const keys = s.keys()
      expect(keys).toEqual(['zzz'])
      expect(keys).not.toContain('foreign')

      s.clear()
      expect(origGet('p_zzz')).toBeNull()
      expect(origGet('foreign')).toBe('y')

      expect(keySpy).toHaveBeenCalled()
      expect(getSpy).toHaveBeenCalled()
    })

    it('原始存储内容不受污染', () => {
      expect(rawStorage()).toEqual({})
    })
  })
})
