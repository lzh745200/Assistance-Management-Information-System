import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import WebSocketManager from '@/utils/websocket'

vi.mock('@/utils/logger', () => ({
  logger: { info: vi.fn(), warn: vi.fn(), error: vi.fn() },
}))

import { logger } from '@/utils/logger'

describe('utils/websocket', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('constructor 接收 url', () => {
    const w = new WebSocketManager('wss://x')
    expect((w as any)._url).toBe('wss://x')
  })

  it('connect 记录 info 日志 (无实际连接)', () => {
    const w = new WebSocketManager('wss://test')
    w.connect()
    expect(logger.info).toHaveBeenCalledWith(expect.stringContaining('WebSocket'))
  })

  it('disconnect 当 ws=null 时不报错', () => {
    const w = new WebSocketManager('wss://x')
    expect(() => w.disconnect()).not.toThrow()
  })

  it('disconnect 当 ws 存在时调用 close', () => {
    const w = new WebSocketManager('wss://x')
    const fakeClose = vi.fn()
    ;(w as any).ws = { close: fakeClose }
    w.disconnect()
    expect(fakeClose).toHaveBeenCalled()
    expect((w as any).ws).toBeNull()
  })

  it('send 记录 warn 日志 (单机版不支持)', () => {
    const w = new WebSocketManager('wss://x')
    w.send({ foo: 'bar' })
    expect(logger.warn).toHaveBeenCalledWith(expect.stringContaining('WebSocket'))
  })
})
