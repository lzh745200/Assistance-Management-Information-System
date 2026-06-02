import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  ErrorType,
  parseError,
  handleError,
  createBusinessError,
  errorHandler,
  setupGlobalErrorHandler,
} from '@/utils/errorHandler'

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
  ElNotification: vi.fn(),
}))

describe('errorHandler', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('parseError', () => {
    it('解析 Axios response 错误 (400)', () => {
      const error = { response: { status: 400, data: { message: '验证失败' } } }
      const result = parseError(error)
      expect(result.type).toBe(ErrorType.VALIDATION)
      expect(result.message).toBe('验证失败')
      expect(result.code).toBe(400)
    })

    it('解析 422 错误', () => {
      const error = { response: { status: 422, data: { detail: 'invalid' } } }
      const result = parseError(error)
      expect(result.type).toBe(ErrorType.VALIDATION)
    })

    it('解析 401 错误', () => {
      const error = { response: { status: 401, data: {} } }
      const result = parseError(error)
      expect(result.type).toBe(ErrorType.AUTH)
      expect(result.retryable).toBe(false)
    })

    it('解析 403 错误', () => {
      const error = { response: { status: 403, data: {} } }
      const result = parseError(error)
      expect(result.type).toBe(ErrorType.PERMISSION)
    })

    it('解析 404 错误', () => {
      const error = { response: { status: 404, data: {} } }
      const result = parseError(error)
      expect(result.type).toBe(ErrorType.NOT_FOUND)
    })

    it('解析 408 超时错误', () => {
      const error = { response: { status: 408, data: {} } }
      const result = parseError(error)
      expect(result.type).toBe(ErrorType.TIMEOUT)
    })

    it('解析 504 网关超时', () => {
      const error = { response: { status: 504, data: {} } }
      const result = parseError(error)
      expect(result.type).toBe(ErrorType.TIMEOUT)
    })

    it('解析 500 服务器错误', () => {
      const error = { response: { status: 500, data: {} } }
      const result = parseError(error)
      expect(result.type).toBe(ErrorType.SERVER)
      expect(result.retryable).toBe(true)
    })

    it('解析其他状态码', () => {
      const error = { response: { status: 418, data: {} } }
      const result = parseError(error)
      expect(result.type).toBe(ErrorType.UNKNOWN)
    })

    it('response.data.message 非字符串时使用默认消息', () => {
      const error = { response: { status: 500, data: { message: { nested: true } } } }
      const result = parseError(error)
      expect(result.message).toBe('请求失败 (500)')
    })

    it('解析 ECONNABORTED 超时', () => {
      const error = { request: {}, code: 'ECONNABORTED', message: 'timeout of 5000ms exceeded' }
      const result = parseError(error)
      expect(result.type).toBe(ErrorType.TIMEOUT)
      expect(result.retryable).toBe(true)
    })

    it('解析 timeout 消息', () => {
      const error = { request: {}, message: 'Request timeout' }
      const result = parseError(error)
      expect(result.type).toBe(ErrorType.TIMEOUT)
    })

    it('解析网络错误 (has request, no response)', () => {
      const error = { request: {}, message: 'Network Error' }
      const result = parseError(error)
      expect(result.type).toBe(ErrorType.NETWORK)
      expect(result.retryable).toBe(true)
    })

    it('解析业务错误 (有 code 字符串)', () => {
      const error = { code: 'FUND_INSUFFICIENT', message: '经费不足', details: { amount: 100 } }
      const result = parseError(error)
      expect(result.type).toBe(ErrorType.BUSINESS)
      expect(result.code).toBe('FUND_INSUFFICIENT')
    })

    it('解析 Error 实例', () => {
      const result = parseError(new Error('test error'))
      expect(result.type).toBe(ErrorType.UNKNOWN)
      expect(result.message).toBe('test error')
    })

    it('解析字符串错误', () => {
      const result = parseError('something went wrong')
      expect(result.type).toBe(ErrorType.UNKNOWN)
      expect(result.message).toBe('something went wrong')
    })

    it('解析 null/undefined', () => {
      expect(parseError(null).message).toBe('未知错误')
      expect(parseError(undefined).message).toBe('未知错误')
    })

    it('解析数字错误', () => {
      const result = parseError(42)
      expect(result.message).toBe('42')
    })
  })

  describe('handleError', () => {
    it('处理网络错误并显示通知', async () => {
      const { ElNotification } = await import('element-plus')
      const error = { request: {}, message: 'Network Error' }
      const result = handleError(error)
      expect(result.type).toBe(ErrorType.NETWORK)
      expect(ElNotification).toHaveBeenCalled()
    })

    it('处理验证错误并显示消息', async () => {
      const { ElMessage } = await import('element-plus')
      const error = { response: { status: 400, data: { message: '字段错误' } } }
      handleError(error)
      expect(ElMessage.warning).toHaveBeenCalledWith('字段错误')
    })

    it('showMessage=false 时不显示', async () => {
      const { ElMessage } = await import('element-plus')
      vi.mocked(ElMessage.warning).mockClear()
      handleError({ response: { status: 400, data: {} } }, false)
      expect(ElMessage.warning).not.toHaveBeenCalled()
    })

    it('记录错误日志', () => {
      const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
      handleError({ response: { status: 500, data: {} } })
      expect(spy).toHaveBeenCalled()
      spy.mockRestore()
    })
  })

  describe('createBusinessError', () => {
    it('创建业务错误', () => {
      const err = createBusinessError('E001', '操作失败', { field: 'name' })
      expect(err.type).toBe(ErrorType.BUSINESS)
      expect(err.code).toBe('E001')
      expect(err.message).toBe('操作失败')
      expect(err.details).toEqual({ field: 'name' })
      expect(err.retryable).toBe(false)
    })
  })

  describe('ErrorHandler class', () => {
    it('getStrategy 返回默认策略', () => {
      const strategy = errorHandler.getStrategy(ErrorType.NETWORK)
      expect(strategy.shouldNotify).toBe(true)
      expect(strategy.retryable).toBe(true)
    })

    it('configureStrategy 覆盖策略', () => {
      errorHandler.configureStrategy(ErrorType.NETWORK, { shouldNotify: false })
      const strategy = errorHandler.getStrategy(ErrorType.NETWORK)
      expect(strategy.shouldNotify).toBe(false)
      // 重置
      errorHandler.configureStrategy(ErrorType.NETWORK, { shouldNotify: true })
    })

    it('handleAsyncOperation 成功', async () => {
      const result = await errorHandler.handleAsyncOperation(
        async () => 'ok',
        { successMessage: '成功' }
      )
      expect(result).toBe('ok')
    })

    it('handleAsyncOperation 失败返回 null', async () => {
      const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const result = await errorHandler.handleAsyncOperation(
        async () => { throw new Error('fail') },
        { showError: true }
      )
      expect(result).toBeNull()
      spy.mockRestore()
    })

    it('handleAsyncOperation 重试', async () => {
      const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
      let attempt = 0
      const onRetry = vi.fn()
      await errorHandler.handleAsyncOperation(
        async () => { attempt++; if (attempt < 3) throw new Error('fail'); return 'ok' },
        { retryCount: 3, retryDelay: 10, onRetry }
      )
      expect(onRetry).toHaveBeenCalled()
      spy.mockRestore()
    })

    it('handleAsyncOperation showError=false', async () => {
      const result = await errorHandler.handleAsyncOperation(
        async () => { throw new Error('fail') },
        { showError: false }
      )
      expect(result).toBeNull()
    })
  })

  describe('setupGlobalErrorHandler', () => {
    it('注册 unhandledrejection 监听器', () => {
      const addSpy = vi.spyOn(window, 'addEventListener')
      setupGlobalErrorHandler()
      expect(addSpy).toHaveBeenCalledWith('unhandledrejection', expect.any(Function))
      addSpy.mockRestore()
    })
  })
})
