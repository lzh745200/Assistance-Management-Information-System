import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  getCsrfToken: vi.fn(() => Promise.resolve("test-csrf"))}))

import {
  enableTwoFactor,
  verifyAndEnableTwoFactor,
  disableTwoFactor,
  getTwoFactorStatus,
  verifyLoginTwoFactor,
  twoFactorApi,
} from '@/api/twoFactor'

describe('api/twoFactor', () => {
  beforeEach(() => vi.clearAllMocks())

  it('enableTwoFactor POST /two-factor/enable', async () => {
    const body = { secret: 'ABC', qr_code: 'data:image/png', backup_codes: ['1'] }
    mockPost.mockResolvedValueOnce(body)
    const r = await enableTwoFactor()
    expect(mockPost).toHaveBeenCalledWith('/two-factor/enable')
    expect(r).toBe(body)
  })

  it('verifyAndEnableTwoFactor POST /two-factor/verify 带 token', async () => {
    const body = { message: 'ok' }
    mockPost.mockResolvedValueOnce(body)
    const r = await verifyAndEnableTwoFactor('123456')
    expect(mockPost).toHaveBeenCalledWith('/two-factor/verify', { token: '123456' })
    expect(r).toBe(body)
  })

  it('disableTwoFactor POST /two-factor/disable', async () => {
    const body = { message: 'disabled' }
    mockPost.mockResolvedValueOnce(body)
    const r = await disableTwoFactor()
    expect(mockPost).toHaveBeenCalledWith('/two-factor/disable')
    expect(r).toBe(body)
  })

  it('getTwoFactorStatus GET /two-factor/status', async () => {
    const body = { enabled: true }
    mockGet.mockResolvedValueOnce(body)
    const r = await getTwoFactorStatus()
    expect(mockGet).toHaveBeenCalledWith('/two-factor/status')
    expect(r).toBe(body)
  })

  it('verifyLoginTwoFactor POST /auth/two-factor/verify-login', async () => {
    const body = { code: 200, data: { access_token: 't' }, message: 'success' }
    mockPost.mockResolvedValueOnce(body)
    const r = await verifyLoginTwoFactor('tmp-token', '654321')
    expect(mockPost).toHaveBeenCalledWith('/auth/two-factor/verify-login', {
      temp_token: 'tmp-token',
      code: '654321',
    })
    expect(r).toBe(body)
  })

  it('twoFactorApi 分组导出引用同一批函数', () => {
    expect(twoFactorApi.enable).toBe(enableTwoFactor)
    expect(twoFactorApi.verifyAndEnable).toBe(verifyAndEnableTwoFactor)
    expect(twoFactorApi.disable).toBe(disableTwoFactor)
    expect(twoFactorApi.getStatus).toBe(getTwoFactorStatus)
    expect(twoFactorApi.verifyLogin).toBe(verifyLoginTwoFactor)
  })
})
