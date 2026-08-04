import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockPut, mockDel } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockPut: vi.fn(),
  mockDel: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  put: mockPut,
  del: mockDel,
  getCsrfToken: vi.fn(() => Promise.resolve("test-csrf"))}))

import { listRules, createRule, updateRule, deleteRule, runValidation } from '@/api/validationRules'

describe('api/validationRules', () => {
  beforeEach(() => vi.clearAllMocks())

  it('listRules 无参 GET /validation/rules', async () => {
    const body = { items: [] }
    mockGet.mockResolvedValueOnce(body)
    const r = await listRules()
    expect(mockGet).toHaveBeenCalledWith('/validation/rules', undefined)
    expect(r).toBe(body)
  })

  it('listRules 带模块筛选', async () => {
    mockGet.mockResolvedValueOnce({ items: [] })
    await listRules({ module: 'funds', is_active: true })
    expect(mockGet).toHaveBeenCalledWith('/validation/rules', {
      module: 'funds',
      is_active: true,
    })
  })

  it('createRule POST /validation/rules', async () => {
    const body = { id: 1 }
    mockPost.mockResolvedValueOnce(body)
    const data = { module: 'funds', field: 'amount', rule_type: 'required' }
    const r = await createRule(data)
    expect(mockPost).toHaveBeenCalledWith('/validation/rules', data)
    expect(r).toBe(body)
  })

  it('updateRule PUT /validation/rules/:id', async () => {
    const body = { id: 1 }
    mockPut.mockResolvedValueOnce(body)
    const data = { is_active: false }
    const r = await updateRule(1, data)
    expect(mockPut).toHaveBeenCalledWith('/validation/rules/1', data)
    expect(r).toBe(body)
  })

  it('deleteRule DELETE /validation/rules/:id', async () => {
    const body = { deleted: true }
    mockDel.mockResolvedValueOnce(body)
    const r = await deleteRule(1)
    expect(mockDel).toHaveBeenCalledWith('/validation/rules/1')
    expect(r).toBe(body)
  })

  it('runValidation POST /validation/validate 带 module 参数', async () => {
    const body = { valid: false, errors: ['amount 必填'] }
    mockPost.mockResolvedValueOnce(body)
    const data = { amount: null }
    const r = await runValidation('funds', data)
    expect(mockPost).toHaveBeenCalledWith('/validation/validate', data, {
      params: { module: 'funds' },
    })
    expect(r).toBe(body)
  })
})
