import { describe, it, expect, vi, beforeEach } from 'vitest'
import { logger, tryCatch, tryCatchAsync, withErrorBoundary, LogLevel, type LogEntry } from '@/utils/logger'

describe('logger', () => {
  beforeEach(() => {
    logger.clear()
    vi.spyOn(console, 'log').mockImplementation(() => {})
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.spyOn(console, 'debug').mockImplementation(() => {})
  })

  describe('logger methods', () => {
    it('debug 记录日志条目', () => {
      logger.debug('test debug')
      const logs = logger.getLogs()
      expect(logs).toHaveLength(1)
      expect(logs[0].level).toBe(LogLevel.DEBUG)
      expect(logs[0].message).toBe('test debug')
    })

    it('debug 传入 context 对象', () => {
      logger.debug('msg', { key: 'value' })
      expect(logger.getLogs()[0].context).toEqual({ key: 'value' })
    })

    it('debug 传入基本类型 context 会被包装', () => {
      logger.debug('msg', 42)
      expect(logger.getLogs()[0].context).toEqual({ value: 42 })
    })

    it('info 记录日志', () => {
      logger.info('info msg')
      expect(logger.getLogs(LogLevel.INFO)).toHaveLength(1)
    })

    it('warn 记录日志', () => {
      logger.warn('warn msg')
      expect(logger.getLogs(LogLevel.WARN)).toHaveLength(1)
    })

    it('error 记录日志 + stack', () => {
      const err = new Error('boom')
      logger.error('failed', err)
      const logs = logger.getLogs(LogLevel.ERROR)
      expect(logs[0].stack).toBe(err.stack)
    })

    it('error 传入非 Error 对象时 stack=undefined', () => {
      logger.error('failed', 'string error')
      expect(logger.getLogs(LogLevel.ERROR)[0].stack).toBeUndefined()
    })

    it('fatal 记录日志 + stack', () => {
      const err = new Error('fatal')
      logger.fatal('crashed', err)
      expect(logger.getLogs(LogLevel.FATAL)[0].stack).toBe(err.stack)
    })

    it('getLogs 无 level 返回全部', () => {
      logger.info('a')
      logger.warn('b')
      expect(logger.getLogs()).toHaveLength(2)
    })

    it('getLogs(level) 过滤', () => {
      logger.info('a')
      logger.warn('b')
      expect(logger.getLogs(LogLevel.WARN)).toHaveLength(1)
    })

    it('clear 清空日志', () => {
      logger.info('a')
      logger.clear()
      expect(logger.getLogs()).toHaveLength(0)
    })

    it('exportLogs 返回 JSON 字符串', () => {
      logger.info('a')
      const json = logger.exportLogs()
      expect(typeof json).toBe('string')
      const parsed = JSON.parse(json)
      expect(Array.isArray(parsed)).toBe(true)
    })
  })

  describe('tryCatch', () => {
    it('同步函数成功时返回结果', () => {
      const result = tryCatch(() => 42, 'err')
      expect(result).toBe(42)
    })

    it('同步函数异常时返回 defaultValue', () => {
      const result = tryCatch(
        () => { throw new Error('boom') },
        'caught',
        'fallback',
      )
      expect(result).toBe('fallback')
    })

    it('无 defaultValue 时返回 undefined', () => {
      const result = tryCatch(() => { throw new Error('boom') }, 'caught')
      expect(result).toBeUndefined()
    })
  })

  describe('tryCatchAsync', () => {
    it('异步函数成功时返回结果', async () => {
      const result = await tryCatchAsync(async () => 100, 'err')
      expect(result).toBe(100)
    })

    it('异步函数 reject 时返回 defaultValue', async () => {
      const result = await tryCatchAsync(
        async () => { throw new Error('async boom') },
        'caught',
        'fb',
      )
      expect(result).toBe('fb')
    })
  })

  describe('withErrorBoundary', () => {
    it('成功时透传结果', async () => {
      const fn = async (x: number) => x * 2
      const wrapped = withErrorBoundary(fn)
      expect(await wrapped(5)).toBe(10)
    })

    it('失败时记录日志并 rethrow', async () => {
      const fn = async () => { throw new Error('wrapped boom') }
      const wrapped = withErrorBoundary(fn, 'wrap msg')
      await expect(wrapped()).rejects.toThrow('wrapped boom')
      expect(logger.getLogs(LogLevel.ERROR)).toHaveLength(1)
    })
  })
})
