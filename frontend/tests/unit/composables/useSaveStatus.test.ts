import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useSaveStatus } from '@/composables/useSaveStatus'

describe('useSaveStatus', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('初始 state 为 idle, errorMessage 为空', () => {
    const { state, errorMessage, statusText, isSaving, isSaved, isError } =
      useSaveStatus()
    expect(state.value).toBe('idle')
    expect(errorMessage.value).toBe('')
    expect(statusText.value).toBe('')
    expect(isSaving.value).toBe(false)
    expect(isSaved.value).toBe(false)
    expect(isError.value).toBe(false)
  })

  it('startSaving 后 isSaving 为 true', () => {
    const { isSaving, startSaving } = useSaveStatus()
    startSaving()
    expect(isSaving.value).toBe(true)
  })

  it('markSaved 后 isSaved 为 true 且 autoReset 后变 idle', () => {
    const { isSaved, markSaved, state } = useSaveStatus(1000)
    markSaved()
    expect(isSaved.value).toBe(true)
    vi.advanceTimersByTime(1000)
    expect(state.value).toBe('idle')
  })

  it('markError 后 isError 为 true 且显示错误消息', () => {
    const { isError, errorMessage, statusText, markError } = useSaveStatus(1000)
    markError('保存失败: 字段 X 必填')
    expect(isError.value).toBe(true)
    expect(errorMessage.value).toBe('保存失败: 字段 X 必填')
    expect(statusText.value).toBe('保存失败: 字段 X 必填')
  })

  it('markError 默认消息为 "保存失败"', () => {
    const { errorMessage, markError } = useSaveStatus(1000)
    markError()
    expect(errorMessage.value).toBe('保存失败')
  })

  it('wrapSave 成功时 markSaved', async () => {
    const { wrapSave, isSaved, isSaving } = useSaveStatus(1000)
    const fn = vi.fn().mockResolvedValue('ok')
    const result = await wrapSave(fn)
    expect(result).toBe('ok')
    expect(isSaved.value).toBe(true)
    expect(isSaving.value).toBe(false)
  })

  it('wrapSave 失败时 markError 并重新抛出', async () => {
    const { wrapSave, isError, errorMessage } = useSaveStatus(1000)
    const err = new Error('网络错误')
    const fn = vi.fn().mockRejectedValue(err)
    await expect(wrapSave(fn)).rejects.toThrow('网络错误')
    expect(isError.value).toBe(true)
    expect(errorMessage.value).toBe('网络错误')
  })

  it('wrapSave 失败时优先从 err.response.data.error.message 取消息', async () => {
    const { wrapSave, errorMessage } = useSaveStatus(1000)
    const err = {
      response: { data: { error: { message: '后端业务错误' } } },
    }
    const fn = vi.fn().mockRejectedValue(err)
    await expect(wrapSave(fn)).rejects.toBe(err)
    expect(errorMessage.value).toBe('后端业务错误')
  })

  it('startSaving 取消先前的 reset 定时器', () => {
    const { markSaved, startSaving, isSaving, isSaved } = useSaveStatus(1000)
    markSaved()
    expect(isSaved.value).toBe(true)
    startSaving()
    expect(isSaving.value).toBe(true)
    expect(isSaved.value).toBe(false)
    vi.advanceTimersByTime(2000)
    expect(isSaving.value).toBe(true)
  })

  it('markSaved 后 statusText 为 "已保存"', () => {
    const { markSaved, statusText } = useSaveStatus()
    markSaved()
    expect(statusText.value).toBe('已保存')
  })

  it('startSaving 后 statusText 为 "正在保存..."', () => {
    const { startSaving, statusText } = useSaveStatus()
    startSaving()
    expect(statusText.value).toBe('正在保存...')
  })

  it('markError 无消息时 statusText 回退为 "保存失败"', () => {
    const { markError, statusText } = useSaveStatus()
    markError('')
    expect(statusText.value).toBe('保存失败')
  })

  it('markError 覆盖先前定时器并在 2 倍延迟后重置为 idle', () => {
    const { markSaved, markError, state, errorMessage } = useSaveStatus(1000)
    markSaved()
    markError('出错了')
    expect(state.value).toBe('error')
    expect(errorMessage.value).toBe('出错了')
    vi.advanceTimersByTime(1999)
    expect(state.value).toBe('error')
    vi.advanceTimersByTime(1)
    expect(state.value).toBe('idle')
    expect(errorMessage.value).toBe('')
  })

  it('markSaved 覆盖先前 error 的 reset 定时器', () => {
    const { markError, markSaved, state } = useSaveStatus(1000)
    markError('出错了')
    expect(state.value).toBe('error')
    markSaved()
    expect(state.value).toBe('saved')
    vi.advanceTimersByTime(3000)
    expect(state.value).toBe('idle')
  })

  it('wrapSave 失败且错误无任何消息时回退默认文案', async () => {
    const { wrapSave, errorMessage } = useSaveStatus(1000)
    const err = {}
    const fn = vi.fn().mockRejectedValue(err)
    await expect(wrapSave(fn)).rejects.toBe(err)
    expect(errorMessage.value).toBe('保存失败')
  })

  it('wrapSave 成功时返回结果并进入 saved 状态', async () => {
    const { wrapSave, statusText } = useSaveStatus(1000)
    const result = await wrapSave(() => Promise.resolve('data'))
    expect(result).toBe('data')
    expect(statusText.value).toBe('已保存')
  })
})
