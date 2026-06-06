import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('element-plus', () => ({
  ElMessage: vi.fn(),
}))

import { ElMessage } from 'element-plus'
import { useErrorHandler } from '@/composables/useErrorHandler'

describe('composables/useErrorHandler', () => {
  let h: ReturnType<typeof useErrorHandler>

  beforeEach(() => {
    vi.clearAllMocks()
    h = useErrorHandler()
  })

  describe('handleError', () => {
    it('extracts message from err.response.data.message', () => {
      const err = { response: { data: { message: 'invalid input' }, status: 400 } }
      h.handleError(err, '保存数据')
      expect(h.errorState.value?.message).toBe('保存数据失败: invalid input')
      expect(h.errorState.value?.code).toBe(400)
    })

    it('falls back to err.response.data.detail', () => {
      const err = { response: { data: { detail: 'detail msg' }, status: 500 } }
      h.handleError(err)
      expect(h.errorState.value?.message).toBe('操作失败: detail msg')
    })

    it('falls back to err.message', () => {
      h.handleError(new Error('boom'))
      expect(h.errorState.value?.message).toBe('操作失败: boom')
    })

    it('falls back to err as truthy', () => {
      h.handleError('string error')
      expect(h.errorState.value?.message).toBe('操作失败: string error')
    })

    it('falls back to 未知错误', () => {
      h.handleError(null)
      expect(h.errorState.value?.message).toBe('操作失败: 未知错误')
    })

    it('uses err.code when no response.status', () => {
      const err = { code: 'E001' }
      h.handleError(err)
      expect(h.errorState.value?.code).toBe('E001')
    })

    it('showNotification=false 跳过 ElMessage', () => {
      h.handleError(new Error('x'), 'ctx', false)
      expect(ElMessage).not.toHaveBeenCalled()
    })

    it('showNotification=true 调 ElMessage', () => {
      h.handleError(new Error('x'))
      expect(ElMessage).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'error', duration: 5000, showClose: true }),
      )
    })

    it('console.error 总是触发', () => {
      const errSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      h.handleError(new Error('test'))
      expect(errSpy).toHaveBeenCalled()
      errSpy.mockRestore()
    })

    it('returns errorState', () => {
      const r = h.handleError(new Error('x'))
      expect(r).toBe(h.errorState.value)
    })
  })

  describe('handleWarning', () => {
    it('调 ElMessage warning', () => {
      h.handleWarning('careful')
      expect(ElMessage).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'warning', duration: 3000, showClose: true, message: 'careful' }),
      )
    })
    it('console.warn 触发', () => {
      const w = vi.spyOn(console, 'warn').mockImplementation(() => {})
      h.handleWarning('w')
      expect(w).toHaveBeenCalled()
      w.mockRestore()
    })
  })

  describe('handleSuccess', () => {
    it('调 ElMessage success', () => {
      h.handleSuccess('done')
      expect(ElMessage).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'success', duration: 2000, message: 'done' }),
      )
    })
  })

  describe('clearError', () => {
    it('清空 errorState', () => {
      h.handleError(new Error('x'))
      expect(h.errorState.value).not.toBeNull()
      h.clearError()
      expect(h.errorState.value).toBeNull()
    })
  })
})
