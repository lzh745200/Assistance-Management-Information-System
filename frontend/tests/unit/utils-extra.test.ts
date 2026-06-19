import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// 全局 teardown：排空 microtask 队列，消除 RequestDeduplicator 竞态
afterEach(async () => {
  await new Promise((r) => setTimeout(r, 0));
});

// ==================== RequestDeduplicator ====================
describe('RequestDeduplicator', () => {
  let RequestDeduplicator: any

  beforeEach(async () => {
    const mod = await import('@/utils/requestDeduplicator')
    RequestDeduplicator = mod.RequestDeduplicator
  })

  it('dedupe 正常执行', async () => {
    const dd = new RequestDeduplicator()
    const result = await dd.dedupe('k1', async () => 'hello')
    expect(result).toBe('hello')
  })

  it('dedupe 合并并发请求', async () => {
    const dd = new RequestDeduplicator()
    const fn = vi.fn(async () => 'result')
    const [r1, r2, r3] = await Promise.all([
      dd.dedupe('k', fn),
      dd.dedupe('k', fn),
      dd.dedupe('k', fn),
    ])
    expect(fn).toHaveBeenCalledTimes(1)
    expect(r1).toBe('result')
    expect(r2).toBe('result')
    expect(r3).toBe('result')
  })

  it('dedupe 不同 key 独立执行', async () => {
    const dd = new RequestDeduplicator()
    const fn = vi.fn(async () => 'ok')
    await Promise.all([dd.dedupe('a', fn), dd.dedupe('b', fn)])
    expect(fn).toHaveBeenCalledTimes(2)
  })

  it('dedupe 失败时所有订阅者收到错误', async () => {
    const dd = new RequestDeduplicator()
    const err = new Error('fail')
    const fn = async () => { throw err }
    const results = await Promise.allSettled([
      dd.dedupe('k', fn),
      dd.dedupe('k', fn),
    ])
    expect(results[0].status).toBe('rejected')
    expect(results[1].status).toBe('rejected')
  })

  it('getPendingCount', async () => {
    const dd = new RequestDeduplicator()
    expect(dd.getPendingCount()).toBe(0)
    let resolve: any
    const promise = dd.dedupe('k', () => new Promise(r => { resolve = r }))
    expect(dd.getPendingCount()).toBe(1)
    resolve('done')
    await promise
    expect(dd.getPendingCount()).toBe(0)
  })

  it('isPending', async () => {
    const dd = new RequestDeduplicator()
    let resolve: any
    const promise = dd.dedupe('k', () => new Promise(r => { resolve = r }))
    expect(dd.isPending('k')).toBe(true)
    expect(dd.isPending('other')).toBe(false)
    resolve('done')
    await promise
  })

  it('getPendingKeys', async () => {
    const dd = new RequestDeduplicator()
    let r1: any, r2: any
    const p1 = dd.dedupe('a', () => new Promise(r => { r1 = r }))
    const p2 = dd.dedupe('b', () => new Promise(r => { r2 = r }))
    expect(dd.getPendingKeys().sort()).toEqual(['a', 'b'])
    r1(''); r2('')
    await Promise.all([p1, p2])
  })

  it('cancel 取消请求', async () => {
    const dd = new RequestDeduplicator()
    // 不 await dedupe（因为 request 永不完成），只验证 cancel 行为
    dd.dedupe('k', () => new Promise(() => {})).catch(() => {})
    expect(dd.cancel('k')).toBe(true)
    expect(dd.isPending('k')).toBe(false)
    // 重复 cancel 返回 false
    expect(dd.cancel('k')).toBe(false)
  })

  it('cancelAll', async () => {
    const dd = new RequestDeduplicator()
    dd.dedupe('a', () => new Promise(() => {})).catch(() => {})
    dd.dedupe('b', () => new Promise(() => {})).catch(() => {})
    dd.cancelAll()
    expect(dd.getPendingCount()).toBe(0)
  })

  it('getConfig 返回配置副本', () => {
    const dd = new RequestDeduplicator({ maxConcurrent: 5, timeout: 10000 })
    const cfg = dd.getConfig()
    expect(cfg.maxConcurrent).toBe(5)
    expect(cfg.timeout).toBe(10000)
  })
})

// ==================== createDedupedRequest ====================
describe('createDedupedRequest', () => {
  it('生成带去重的请求函数', async () => {
    const { createDedupedRequest, RequestDeduplicator } = await import('@/utils/requestDeduplicator')
    const dd = new RequestDeduplicator()
    const fn = vi.fn(async (id: number) => ({ id }))
    const deduped = createDedupedRequest(
      (id: number) => `user:${id}`,
      fn,
      dd
    )
    const [r1, r2] = await Promise.all([deduped(1), deduped(1)])
    expect(fn).toHaveBeenCalledTimes(1)
    expect(r1).toEqual({ id: 1 })
    expect(r2).toEqual({ id: 1 })
  })
})

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

// ==================== StateManager ====================
describe('StateManager', () => {
  let StateManager: any

  beforeEach(async () => {
    localStorage.clear()
    const mod = await import('@/utils/stateManager')
    StateManager = mod.StateManager
  })

  it('setState / getState', () => {
    const sm = new StateManager()
    sm.setState('key', 'value')
    expect(sm.getState('key')).toBe('value')
  })

  it('getState 默认值', () => {
    const sm = new StateManager()
    expect(sm.getState('none', 'def')).toBe('def')
  })

  it('setState ttl 过期', () => {
    const sm = new StateManager()
    const now = Date.now()
    vi.spyOn(Date, 'now')
      .mockReturnValueOnce(now) // setState timestamp
      .mockReturnValueOnce(now + 500) // getState (未过期)
      .mockReturnValueOnce(now + 2000) // getState (已过期)
      .mockReturnValueOnce(now + 2000) // getState localStorage fallback
    sm.setState('k', 'v', { ttl: 1000 })
    expect(sm.getState('k')).toBe('v')
    expect(sm.getState('k', 'expired')).toBe('expired')
    vi.restoreAllMocks()
  })

  it('removeState', () => {
    const sm = new StateManager()
    sm.setState('k', 'v')
    sm.removeState('k')
    expect(sm.getState('k')).toBeUndefined()
  })

  it('subscribe / notify', () => {
    const sm = new StateManager()
    const callback = vi.fn()
    const unsub = sm.subscribe('k', callback)
    sm.setState('k', 42)
    expect(callback).toHaveBeenCalledWith(42)
    unsub()
    sm.setState('k', 99)
    expect(callback).toHaveBeenCalledTimes(1)
  })

  it('batchSetState / batchGetState', () => {
    const sm = new StateManager()
    sm.batchSetState({ a: 1, b: 2 })
    const result = sm.batchGetState(['a', 'b'])
    expect(result.a).toBe(1)
    expect(result.b).toBe(2)
  })

  it('hasState', () => {
    const sm = new StateManager()
    expect(sm.hasState('k')).toBe(false)
    sm.setState('k', 'v')
    expect(sm.hasState('k')).toBe(true)
  })

  it('clearState', () => {
    const sm = new StateManager()
    sm.setState('a', 1)
    sm.setState('b', 2)
    sm.clearState()
    expect(sm.getState('a')).toBeUndefined()
    expect(sm.getState('b')).toBeUndefined()
  })

  it('exportState / importState', () => {
    const sm = new StateManager()
    sm.setState('x', 'hello')
    const exported = sm.exportState()
    expect(Object.values(exported)).toContain('hello')
    // import into new manager
    const sm2 = new StateManager()
    sm2.importState(exported)
    // verify keys are present
    const keys = sm2.getStateKeys()
    expect(keys.length).toBeGreaterThan(0)
  })

  it('getStateKeys', () => {
    const sm = new StateManager()
    sm.setState('a', 1)
    sm.setState('b', 2)
    const keys = sm.getStateKeys()
    expect(keys.length).toBe(2)
  })

  it('persist: false 不写 localStorage', () => {
    const sm = new StateManager()
    sm.setState('mem', 'only', { persist: false })
    expect(sm.getState('mem')).toBe('only')
    // 直接从 localStorage 不应找到
    const allKeys: string[] = []
    for (let i = 0; i < localStorage.length; i++) {
      allKeys.push(localStorage.key(i)!)
    }
    expect(allKeys.some(k => k.includes('mem'))).toBe(false)
  })
})
