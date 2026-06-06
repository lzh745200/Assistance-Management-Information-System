import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  logError,
  logWarn,
  logInfo,
  getErrorLogs,
  clearErrorLogs,
  exportErrorLogs,
  type ErrorLogEntry,
} from '@/utils/errorLogger'

describe('errorLogger', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('logError 写入 entry 到 localStorage', () => {
    logError('TestComp', 'something broke', { code: 500 })
    const logs = JSON.parse(localStorage.getItem('app_error_logs')!)
    expect(logs).toHaveLength(1)
    expect(logs[0].level).toBe('error')
    expect(logs[0].source).toBe('TestComp')
    expect(logs[0].message).toBe('something broke')
    expect(logs[0].context).toEqual({ code: 500 })
    expect(logs[0].timestamp).toMatch(/T/)
  })

  it('logWarn 写入 level=warn', () => {
    logWarn('API', 'slow response')
    const logs = JSON.parse(localStorage.getItem('app_error_logs')!)
    expect(logs[0].level).toBe('warn')
  })

  it('logInfo 写入 level=info', () => {
    logInfo('Init', 'app started')
    const logs = JSON.parse(localStorage.getItem('app_error_logs')!)
    expect(logs[0].level).toBe('info')
  })

  it('logError 不带 context 时 context 字段为 undefined', () => {
    logError('X', 'msg')
    const logs = JSON.parse(localStorage.getItem('app_error_logs')!)
    expect(logs[0].context).toBeUndefined()
  })

  it('getErrorLogs 返回已记录日志', () => {
    logError('A', 'e1')
    logWarn('B', 'w1')
    const logs = getErrorLogs()
    expect(logs).toHaveLength(2)
    expect(logs[0].source).toBe('A')
    expect(logs[1].source).toBe('B')
  })

  it('clearErrorLogs 清空 localStorage', () => {
    logError('A', 'e1')
    expect(getErrorLogs()).toHaveLength(1)
    clearErrorLogs()
    expect(getErrorLogs()).toHaveLength(0)
    expect(localStorage.getItem('app_error_logs')).toBeNull()
  })

  it('localStorage 损坏 JSON 时 getErrorLogs 返回 []', () => {
    localStorage.setItem('app_error_logs', '{not json')
    expect(getErrorLogs()).toEqual([])
  })

  it('环形缓冲区: 超出 MAX_ENTRIES 时只保留最新 200 条', () => {
    for (let i = 0; i < 250; i++) logError('Burst', `e${i}`)
    const logs = getErrorLogs()
    expect(logs).toHaveLength(200)
    expect(logs[0].message).toBe('e50')
    expect(logs[199].message).toBe('e249')
  })

  it('exportErrorLogs 创建 a 标签并触发点击', () => {
    logError('X', 'e1')
    const createObjectURL = vi.fn(() => 'blob:fake')
    const revokeObjectURL = vi.fn()
    const click = vi.fn()
    const originalCreate = URL.createObjectURL
    const originalRevoke = URL.revokeObjectURL
    URL.createObjectURL = createObjectURL
    URL.revokeObjectURL = revokeObjectURL
    const a = document.createElement('a')
    a.click = click
    const realCreate = document.createElement.bind(document)
    vi.spyOn(document, 'createElement').mockImplementation((tag: any) => {
      if (tag === 'a') return a
      return realCreate(tag)
    })

    exportErrorLogs()

    expect(createObjectURL).toHaveBeenCalled()
    expect(click).toHaveBeenCalled()
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:fake')
    URL.createObjectURL = originalCreate
    URL.revokeObjectURL = originalRevoke
  })
})
