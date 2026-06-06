import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { CacheManager, cacheManager, serialize, deserialize } from '@/utils/cacheManager'

vi.mock('@/utils/logger', () => ({
  logger: { warn: vi.fn(), info: vi.fn(), error: vi.fn() },
}))

describe('utils/cacheManager', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('CacheManager basics', () => {
    it('默认配置 maxSize=100, defaultTTL=5min, prefix=cache:', () => {
      const c = new CacheManager()
      const cfg = (c as any).config
      expect(cfg.maxSize).toBe(100)
      expect(cfg.defaultTTL).toBe(5 * 60 * 1000)
      expect(cfg.storagePrefix).toBe('cache:')
    })

    it('merge config', () => {
      const c = new CacheManager({ maxSize: 5, defaultTTL: 1000, storagePrefix: 'p:' })
      const cfg = (c as any).config
      expect(cfg.maxSize).toBe(5)
      expect(cfg.defaultTTL).toBe(1000)
      expect(cfg.storagePrefix).toBe('p:')
    })

    it('set + get + has + size + keys', () => {
      const c = new CacheManager()
      c.set('a', 1)
      c.set('b', 2)
      expect(c.get('a')).toBe(1)
      expect(c.has('a')).toBe(true)
      expect(c.size()).toBe(2)
      expect(c.keys()).toEqual(['a', 'b'])
    })

    it('get 缺失返回 undefined + miss+1', () => {
      const c = new CacheManager()
      expect(c.get('nope')).toBeUndefined()
      expect(c.getStats().misses).toBe(1)
    })

    it('get 命中 +1', () => {
      const c = new CacheManager()
      c.set('k', 'v')
      c.get('k')
      expect(c.getStats().hits).toBe(1)
    })

    it('delete 成功返回 true', () => {
      const c = new CacheManager()
      c.set('k', 'v')
      expect(c.delete('k')).toBe(true)
      expect(c.has('k')).toBe(false)
    })

    it('delete 不存在返回 false', () => {
      const c = new CacheManager()
      expect(c.delete('nope')).toBe(false)
    })
  })

  describe('TTL expiry', () => {
    it('TTL 到期后 get 返回 undefined', () => {
      vi.useFakeTimers()
      const c = new CacheManager()
      c.set('k', 'v', 1000)
      vi.advanceTimersByTime(1001)
      expect(c.get('k')).toBeUndefined()
      expect(c.getStats().misses).toBe(1)
      vi.useRealTimers()
    })

    it('TTL 0 = 永不过期', () => {
      vi.useFakeTimers()
      const c = new CacheManager()
      c.set('k', 'v', 0)
      vi.advanceTimersByTime(100000)
      expect(c.get('k')).toBe('v')
      vi.useRealTimers()
    })

    it('has 检查过期', () => {
      vi.useFakeTimers()
      const c = new CacheManager()
      c.set('k', 'v', 100)
      vi.advanceTimersByTime(200)
      expect(c.has('k')).toBe(false)
      vi.useRealTimers()
    })
  })

  describe('LRU eviction', () => {
    it('超过 maxSize 触发 evictLRU (淘汰最旧 lastAccess)', () => {
      vi.useFakeTimers()
      const c = new CacheManager({ maxSize: 2 })
      c.set('a', 1)
      vi.advanceTimersByTime(10)
      c.set('b', 2)
      vi.advanceTimersByTime(10)
      // Touch 'a' to make it more recent
      c.get('a')
      c.set('c', 3)  // triggers eviction of 'b' (older lastAccess)
      expect(c.has('a')).toBe(true)
      expect(c.has('b')).toBe(false)
      expect(c.has('c')).toBe(true)
      expect(c.getStats().evictions).toBe(1)
      vi.useRealTimers()
    })

    it('overwrite existing key 不触发 eviction', () => {
      const c = new CacheManager({ maxSize: 1 })
      c.set('a', 1)
      c.set('a', 2)  // overwrites, no eviction
      expect(c.get('a')).toBe(2)
      expect(c.getStats().evictions).toBe(0)
    })
  })

  describe('invalidate', () => {
    it('精确字符串匹配', () => {
      const c = new CacheManager()
      c.set('user:1', { name: 'a' })
      c.set('user:2', { name: 'b' })
      c.set('item:1', { name: 'c' })
      const n = c.invalidate('user:1')
      expect(n).toBe(1)
      expect(c.has('user:1')).toBe(false)
      expect(c.has('user:2')).toBe(true)
    })

    it('字符串前缀匹配', () => {
      const c = new CacheManager()
      c.set('user:1', 1)
      c.set('user:2', 2)
      c.set('item:1', 3)
      const n = c.invalidate('user:')
      expect(n).toBe(2)
      expect(c.has('item:1')).toBe(true)
    })

    it('正则匹配', () => {
      const c = new CacheManager()
      c.set('user:1', 1)
      c.set('user:2', 2)
      c.set('item:1', 3)
      const n = c.invalidate(/^user:\d+$/)
      expect(n).toBe(2)
    })

    it('无匹配返回 0', () => {
      const c = new CacheManager()
      c.set('a', 1)
      expect(c.invalidate('nope')).toBe(0)
    })
  })

  describe('clear', () => {
    it('清空 + 重置 stats', () => {
      const c = new CacheManager()
      c.set('a', 1)
      c.get('a')  // hit
      c.clear()
      expect(c.size()).toBe(0)
      expect(c.getStats().hits).toBe(0)
      expect(c.getStats().misses).toBe(0)
    })
  })

  describe('getStats', () => {
    it('hitRate 计算', () => {
      const c = new CacheManager()
      c.set('a', 1)
      c.get('a')  // hit
      c.get('a')  // hit
      c.get('nope')  // miss
      const s = c.getStats()
      expect(s.hits).toBe(2)
      expect(s.misses).toBe(1)
      expect(s.hitRate).toBeCloseTo(2/3)
    })

    it('hitRate 0/0 = 0', () => {
      const c = new CacheManager()
      expect(c.getStats().hitRate).toBe(0)
    })
  })

  describe('persistence', () => {
    it('persistKeys 含 * 触发通配符匹配', () => {
      const c = new CacheManager({ persistKeys: ['user:*'], storagePrefix: 't1:' })
      c.set('user:1', { name: 'A' })
      const stored = localStorage.getItem('t1:data')
      expect(stored).toBeTruthy()
      const data = JSON.parse(stored!)
      expect(data.version).toBe(1)
      expect(data.entries.length).toBe(1)
    })

    it('非 persistKey 不持久化', () => {
      const c = new CacheManager({ persistKeys: ['user:'], storagePrefix: 't2:' })
      c.set('item:1', 1)
      expect(localStorage.getItem('t2:data')).toBeNull()
    })

    it('restoreFromStorage 恢复持久化条目', () => {
      localStorage.setItem('t3:data', JSON.stringify({
        version: 1,
        entries: [['k', { value: 42, timestamp: Date.now(), ttl: 60000, accessCount: 1, lastAccess: Date.now() }]],
      }))
      const c = new CacheManager({ storagePrefix: 't3:' })
      expect(c.get('k')).toBe(42)
    })

    it('restoreFromStorage 版本不匹配清空', () => {
      localStorage.setItem('t4:data', JSON.stringify({ version: 999, entries: [] }))
      const c = new CacheManager({ storagePrefix: 't4:' })
      // Logger was called
      expect((c as any).cache.size).toBe(0)
    })

    it('restoreFromStorage JSON.parse fail', () => {
      localStorage.setItem('t5:data', 'not-json')
      const c = new CacheManager({ storagePrefix: 't5:' })
      expect((c as any).cache.size).toBe(0)
    })

    it('restoreFromStorage 跳过过期条目', () => {
      localStorage.setItem('t6:data', JSON.stringify({
        version: 1,
        entries: [['old', { value: 1, timestamp: 1, ttl: 1000, accessCount: 1, lastAccess: 1 }]],
      }))
      const c = new CacheManager({ storagePrefix: 't6:' })
      expect(c.has('old')).toBe(false)
    })

    it('persistToStorage 跳过过期条目', () => {
      localStorage.setItem('t7:data', JSON.stringify({
        version: 1,
        entries: [
          ['expired', { value: 1, timestamp: 1, ttl: 1000, accessCount: 1, lastAccess: 1 }],
          ['fresh', { value: 2, timestamp: Date.now(), ttl: 60000, accessCount: 1, lastAccess: Date.now() }],
        ],
      }))
      const c = new CacheManager({ persistKeys: ['expired', 'fresh'], storagePrefix: 't7:' })
      // trigger persist by setting
      c.set('fresh', 99)
      const stored = JSON.parse(localStorage.getItem('t7:data')!)
      const keys = stored.entries.map((e: any) => e[0])
      expect(keys).toContain('fresh')
      expect(keys).not.toContain('expired')
    })

    it('persistToStorage JSON.stringify 失败 (quota?)', () => {
      const c = new CacheManager({ persistKeys: ['*'], storagePrefix: 't8:' })
      const orig = (localStorage as any).setItem
      ;(localStorage as any).setItem = vi.fn(() => { throw new Error('quota') })
      c.set('k', 1)
      ;(localStorage as any).setItem = orig
    })

    it('clearStorage 失败也不报错', () => {
      const c = new CacheManager({ storagePrefix: 't9:' })
      const orig = (localStorage as any).removeItem
      ;(localStorage as any).removeItem = vi.fn(() => { throw new Error('quota') })
      c.clear()
      ;(localStorage as any).removeItem = orig
    })
  })

  describe('serialize / deserialize', () => {
    it('serialize', () => {
      expect(serialize({ a: 1 })).toBe('{"a":1}')
    })
    it('deserialize', () => {
      expect(deserialize<{ a: number }>('{"a":2}')).toEqual({ a: 2 })
    })
  })

  describe('default cacheManager instance', () => {
    it('cacheManager 可用', () => {
      cacheManager.set('__test_key', 'X')
      expect(cacheManager.get('__test_key')).toBe('X')
      cacheManager.delete('__test_key')
    })
  })
})
