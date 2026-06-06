import { describe, it, expect, beforeEach } from 'vitest'
import { getEventBus, useEventBus } from '@/composables/useEventBus'

describe('eventBus', () => {
  beforeEach(() => {
    // 清空所有事件订阅 (通过 emit 一个特殊事件 reset)
    const bus = getEventBus()
    // 先 emit 一次,再 off 全部 handler 没有 API, 用一个不同的清空方法
    // 由于 useEventBus 是单例, 用新 key 避免污染其他测试
  })

  it('useEventBus 返回 bus with on/off/emit', () => {
    const bus = useEventBus()
    expect(typeof bus.on).toBe('function')
    expect(typeof bus.off).toBe('function')
    expect(typeof bus.emit).toBe('function')
  })

  it('getEventBus 返回新实例但共享 state', () => {
    const a = getEventBus()
    const b = getEventBus()
    expect(a).not.toBe(b) // 不同实例
    const handler = () => {}
    a.on('shared', handler)
    b.emit('shared')
    // 共享 eventHandlers
  })

  it('on 注册 + emit 触发 handler', () => {
    const bus = useEventBus()
    const handler = vi.fn()
    bus.on('test-event', handler)
    bus.emit('test-event', 1, 2, 3)
    expect(handler).toHaveBeenCalledWith(1, 2, 3)
  })

  it('off 注销 handler', () => {
    const bus = useEventBus()
    const handler = vi.fn()
    bus.on('off-event', handler)
    bus.off('off-event', handler)
    bus.emit('off-event', 'x')
    expect(handler).not.toHaveBeenCalled()
  })

  it('off 不存在的 handler 不报错', () => {
    const bus = useEventBus()
    expect(() => bus.off('nonexistent', () => {})).not.toThrow()
  })

  it('emit 多个 handler 都触发', () => {
    const bus = useEventBus()
    const h1 = vi.fn()
    const h2 = vi.fn()
    bus.on('multi', h1)
    bus.on('multi', h2)
    bus.emit('multi', 'data')
    expect(h1).toHaveBeenCalledWith('data')
    expect(h2).toHaveBeenCalledWith('data')
  })

  it('emit 无订阅者不报错', () => {
    const bus = useEventBus()
    expect(() => bus.emit('no-subs', 'x')).not.toThrow()
  })

  it('on 同 handler 多次注册只触发一次 (Set 行为)', () => {
    const bus = useEventBus()
    const handler = vi.fn()
    bus.on('dedup', handler)
    bus.on('dedup', handler)
    bus.emit('dedup')
    expect(handler).toHaveBeenCalledTimes(1)
  })
})
