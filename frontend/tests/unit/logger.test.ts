import { describe, it, expect, vi, beforeEach } from 'vitest'
import { logger, LogLevel, tryCatch, tryCatchAsync } from '@/utils/logger'

describe('Logger', () => {
  beforeEach(() => {
    logger.clear()
    vi.restoreAllMocks()
  })

  it('debug 记录日志', () => {
    vi.spyOn(console, 'debug').mockImplementation(() => {})
    logger.debug('调试信息')
    const logs = logger.getLogs()
    expect(logs).toHaveLength(1)
    expect(logs[0].level).toBe(LogLevel.DEBUG)
    expect(logs[0].message).toBe('调试信息')
  })

  it('info 记录日志', () => {
    vi.spyOn(console, 'log').mockImplementation(() => {})
    logger.info('普通信息', { key: 'value' })
    const logs = logger.getLogs(LogLevel.INFO)
    expect(logs).toHaveLength(1)
    expect(logs[0].context).toEqual({ key: 'value' })
  })

  it('warn 记录日志', () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    logger.warn('警告信息')
    expect(logger.getLogs(LogLevel.WARN)).toHaveLength(1)
  })

  it('error 记录日志并包含堆栈', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const error = new Error('测试错误')
    logger.error('错误信息', error)
    const logs = logger.getLogs(LogLevel.ERROR)
    expect(logs).toHaveLength(1)
    expect(logs[0].stack).toBeDefined()
  })

  it('fatal 记录日志', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    logger.fatal('致命错误')
    expect(logger.getLogs(LogLevel.FATAL)).toHaveLength(1)
  })

  it('clear 清空日志', () => {
    vi.spyOn(console, 'log').mockImplementation(() => {})
    logger.info('信息1')
    logger.info('信息2')
    expect(logger.getLogs()).toHaveLength(2)
    logger.clear()
    expect(logger.getLogs()).toHaveLength(0)
  })

  it('getLogs 按级别过滤', () => {
    vi.spyOn(console, 'log').mockImplementation(() => {})
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    logger.info('信息')
    logger.warn('警告')
    expect(logger.getLogs(LogLevel.INFO)).toHaveLength(1)
    expect(logger.getLogs(LogLevel.WARN)).toHaveLength(1)
    expect(logger.getLogs()).toHaveLength(2)
  })

  it('exportLogs 返回 JSON 字符串', () => {
    vi.spyOn(console, 'log').mockImplementation(() => {})
    logger.info('测试')
    const exported = logger.exportLogs()
    const parsed = JSON.parse(exported)
    expect(Array.isArray(parsed)).toBe(true)
    expect(parsed[0].message).toBe('测试')
  })

  it('日志数量超过限制时截断', () => {
    vi.spyOn(console, 'log').mockImplementation(() => {})
    for (let i = 0; i < 510; i++) {
      logger.info(`日志 ${i}`)
    }
    expect(logger.getLogs().length).toBeLessThanOrEqual(500)
  })
})

describe('tryCatch', () => {
  it('成功时返回结果', () => {
    const result = tryCatch(() => 42)
    expect(result).toBe(42)
  })

  it('异常时返回默认值并记录日志', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const result = tryCatch(() => { throw new Error('fail') }, '操作失败', -1)
    expect(result).toBe(-1)
  })

  it('异常时无默认值返回 undefined', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const result = tryCatch(() => { throw new Error('fail') })
    expect(result).toBeUndefined()
  })
})

describe('tryCatchAsync', () => {
  it('成功时返回结果', async () => {
    const result = await tryCatchAsync(async () => 'ok')
    expect(result).toBe('ok')
  })

  it('异常时返回默认值', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const result = await tryCatchAsync(async () => { throw new Error('fail') }, '异步失败', 'default')
    expect(result).toBe('default')
  })
})
