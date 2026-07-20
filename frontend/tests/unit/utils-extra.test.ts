import { describe, it, expect, vi, beforeEach } from 'vitest'

// ==================== EnhancedStorage ====================
describe('EnhancedStorage', () => {
  let EnhancedStorage: any

  beforeEach(async () => {
    localStorage.clear()
    sessionStorage.clear()
    const mod = await import('@/utils/enhancedStorage')
    EnhancedStorage = mod.EnhancedStorage
  })

  it('set / get 基本读写', () => {
    const s = new EnhancedStorage('test_')
    s.set('name', 'value')
    expect(s.get('name')).toBe('value')
  })

  it('get 默认值', () => {
    const s = new EnhancedStorage('test_')
    expect(s.get('nope', 'fallback')).toBe('fallback')
  })

  it('set 带过期时间', () => {
    const s = new EnhancedStorage('test_')
    const now = Date.now()
    vi.spyOn(Date, 'now')
      .mockReturnValueOnce(now) // set
      .mockReturnValueOnce(now + 100) // get (未过期)
      .mockReturnValueOnce(now + 2000) // get (已过期)
    s.set('k', 'v', { expiry: 1000 })
    expect(s.get('k')).toBe('v')
    expect(s.get('k', 'expired')).toBe('expired')
    vi.restoreAllMocks()
  })

  it('remove 删除', () => {
    const s = new EnhancedStorage('test_')
    s.set('k', 'v')
    s.remove('k')
    expect(s.get('k')).toBeUndefined()
  })

  it('has 检查存在', () => {
    const s = new EnhancedStorage('test_')
    expect(s.has('k')).toBe(false)
    s.set('k', 1)
    expect(s.has('k')).toBe(true)
  })

  it('clear 只清除带前缀的', () => {
    const s = new EnhancedStorage('test_')
    s.set('a', 1)
    s.set('b', 2)
    localStorage.setItem('other', 'keep')
    s.clear()
    expect(s.get('a')).toBeUndefined()
    expect(localStorage.getItem('other')).toBe('keep')
  })

  it('keys 返回所有键', () => {
    const s = new EnhancedStorage('test_')
    s.set('x', 1)
    s.set('y', 2)
    expect(s.keys().sort()).toEqual(['x', 'y'])
  })

  it('setMany / getMany', () => {
    const s = new EnhancedStorage('test_')
    s.setMany({ a: 1, b: 2 })
    const result = s.getMany(['a', 'b', 'c'])
    expect(result.a).toBe(1)
    expect(result.b).toBe(2)
    expect(result.c).toBeUndefined()
  })

  it('getUsage 返回使用情况', () => {
    const s = new EnhancedStorage('test_')
    s.set('k', 'v')
    const usage = s.getUsage()
    expect(usage.used).toBeGreaterThan(0)
    expect(usage.total).toBe(5 * 1024 * 1024)
    expect(typeof usage.percentage).toBe('number')
  })

  it('sessionStorage 模式', () => {
    const s = new EnhancedStorage('sess_', true)
    s.set('k', 'v')
    expect(s.get('k')).toBe('v')
    expect(sessionStorage.getItem('sess_k')).toBeTruthy()
    expect(localStorage.getItem('sess_k')).toBeNull()
  })

  it('clearExpired 清理过期数据', () => {
    const s = new EnhancedStorage('test_')
    const now = Date.now()
    // 手动写入一条过期数据
    localStorage.setItem('test_old', JSON.stringify({
      value: 'stale',
      timestamp: now - 10000,
      expiry: 1000,
    }))
    s.clearExpired()
    expect(localStorage.getItem('test_old')).toBeNull()
  })
})

// ==================== STORAGE_KEYS ====================
describe('STORAGE_KEYS', () => {
  it('导出常量', async () => {
    const { STORAGE_KEYS } = await import('@/utils/enhancedStorage')
    expect(STORAGE_KEYS.TOKEN).toBe('token')
    expect(STORAGE_KEYS.USER_INFO).toBe('user_info')
  })
})
