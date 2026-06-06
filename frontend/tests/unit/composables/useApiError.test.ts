import { describe, it, expect } from 'vitest'
import { useApiError } from '@/composables/useApiError'

describe('useApiError', () => {
  it('初始 error 为 null', () => {
    const { error, clearError } = useApiError()
    expect(error.value).toBeNull()
  })

  it('处理 axios 响应错误 (4xx/5xx)', () => {
    const { error, handleError } = useApiError()
    const result = handleError({
      response: {
        status: 500,
        data: { message: '服务器内部错误' },
      },
    })
    expect(error.value?.code).toBe(500)
    expect(error.value?.message).toBe('服务器内部错误')
    expect(result).toEqual(error.value)
  })

  it('处理 axios 响应错误但无 message 字段', () => {
    const { error, handleError } = useApiError()
    handleError({ response: { status: 404, data: {} } })
    expect(error.value?.code).toBe(404)
    expect(error.value?.message).toBe('请求失败')
  })

  it('处理网络错误 (有 request 无 response)', () => {
    const { error, handleError } = useApiError()
    handleError({ request: {} })
    expect(error.value?.code).toBe(0)
    expect(error.value?.message).toBe('网络连接失败，请检查网络')
  })

  it('处理其他错误 (无 response 无 request)', () => {
    const { error, handleError } = useApiError()
    handleError(new Error('Something went wrong'))
    expect(error.value?.code).toBe(-1)
    expect(error.value?.message).toBe('Something went wrong')
  })

  it('处理 null/undefined 错误', () => {
    const { error, handleError } = useApiError()
    handleError(null)
    expect(error.value?.code).toBe(-1)
    expect(error.value?.message).toBe('未知错误')
  })

  it('clearError() 重置 error 为 null', () => {
    const { error, handleError, clearError } = useApiError()
    handleError({ response: { status: 500, data: {} } })
    expect(error.value).not.toBeNull()
    clearError()
    expect(error.value).toBeNull()
  })
})
