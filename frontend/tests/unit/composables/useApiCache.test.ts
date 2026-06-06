import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useApiCache } from '@/composables/useApiCache'

describe('useApiCache', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })
  afterEach(() => {
    vi.useRealTimers()
  })

  it('初始状态 cache 为空', () => {
    const { get } = useApiCache<number>()
    expect(get('missing')).toBeNull()
  })

  it('set 后 get 能取到值', () => {
    const { set, get } = useApiCache<number>()
    set('key1', 42)
    expect(get('key1')).toBe(42)
  })

  it('不同 key 互不干扰', () => {
    const { set, get } = useApiCache<string>()
    set('a', 'foo')
    set('b', 'bar')
    expect(get('a')).toBe('foo')
    expect(get('b')).toBe('bar')
  })

  it('覆盖已有 key 的值', () => {
    const { set, get } = useApiCache<string>()
    set('key', 'v1')
    set('key', 'v2')
    expect(get('key')).toBe('v2')
  })

  it('TTL 过期后 get 返回 null 并清除缓存', () => {
    const { set, get } = useApiCache<number>(1000)
    set('key', 1)
    expect(get('key')).toBe(1)
    vi.advanceTimersByTime(1001)
    expect(get('key')).toBeNull()
  })

  it('未过期则正常返回', () => {
    const { set, get } = useApiCache<number>(1000)
    set('key', 1)
    vi.advanceTimersByTime(500)
    expect(get('key')).toBe(1)
  })

  it('invalidate(key) 只删除指定 key', () => {
    const { set, get, invalidate } = useApiCache<number>()
    set('a', 1)
    set('b', 2)
    invalidate('a')
    expect(get('a')).toBeNull()
    expect(get('b')).toBe(2)
  })

  it('invalidate() 无参清空全部', () => {
    const { set, get, invalidate } = useApiCache<number>()
    set('a', 1)
    set('b', 2)
    invalidate()
    expect(get('a')).toBeNull()
    expect(get('b')).toBeNull()
  })

  it('支持对象作为缓存值', () => {
    interface User {
      id: number
      name: string
    }
    const { set, get } = useApiCache<User>()
    const user: User = { id: 1, name: 'alice' }
    set('user:1', user)
    expect(get('user:1')).toEqual(user)
  })
})
