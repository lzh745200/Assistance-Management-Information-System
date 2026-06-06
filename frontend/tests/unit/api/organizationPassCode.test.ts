import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()

vi.mock('@/utils/request', () => ({
  default: { get: (...args: any[]) => mockGet(...args), post: (...args: any[]) => mockPost(...args) },
}))

vi.mock('@/api/request', () => ({
  default: { get: (...args: any[]) => mockGet(...args), post: (...args: any[]) => mockPost(...args) },
}))

import {
  orgPassCodeApi,
  getOrganizationVerificationCode,
  createOrganizationPassCode,
  getOrganizationPassCodeList,
  exportOrganizationPassCodes,
} from '@/api/organizationPassCode'

describe('api/organizationPassCode', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('orgPassCodeApi.generate POST /organizations/{id}/passcode', () => {
    orgPassCodeApi.generate(5)
    expect(mockPost).toHaveBeenCalledWith('/organizations/5/passcode')
  })

  it('orgPassCodeApi.verify POST /organizations/passcode/verify with code', () => {
    orgPassCodeApi.verify('ABC123')
    expect(mockPost).toHaveBeenCalledWith('/organizations/passcode/verify', { code: 'ABC123' })
  })

  it('getOrganizationVerificationCode GET /organizations/{id}/verification-code', () => {
    getOrganizationVerificationCode(3)
    expect(mockGet).toHaveBeenCalledWith('/organizations/3/verification-code')
  })

  it('createOrganizationPassCode POST /organizations/passcodes', () => {
    createOrganizationPassCode({
      organization_id: 1,
      verification_code: 'VC',
      allow_subordinate_generation: true,
    })
    expect(mockPost).toHaveBeenCalledWith('/organizations/passcodes', {
      organization_id: 1,
      verification_code: 'VC',
      allow_subordinate_generation: true,
    })
  })

  it('getOrganizationPassCodeList GET /organizations/passcodes with params', () => {
    getOrganizationPassCodeList({ organization_id: 1, status: 'active', page: 1, page_size: 10 })
    expect(mockGet).toHaveBeenCalledWith('/organizations/passcodes', {
      params: { organization_id: 1, status: 'active', page: 1, page_size: 10 },
    })
  })

  it('getOrganizationPassCodeList 无参', () => {
    getOrganizationPassCodeList()
    expect(mockGet).toHaveBeenCalledWith('/organizations/passcodes', { params: undefined })
  })

  it('exportOrganizationPassCodes 触发下载', async () => {
    mockGet.mockResolvedValueOnce({ data: new Blob(['test']) })
    const createObjectURL = vi.fn(() => 'blob:fake')
    const revokeObjectURL = vi.fn()
    const click = vi.fn()
    URL.createObjectURL = createObjectURL
    URL.revokeObjectURL = revokeObjectURL
    const a = document.createElement('a')
    a.click = click
    const realCreate = document.createElement.bind(document)
    vi.spyOn(document, 'createElement').mockImplementation((tag: any) => {
      if (tag === 'a') return a
      return realCreate(tag)
    })
    await exportOrganizationPassCodes({ status: 'active' })
    expect(mockGet).toHaveBeenCalledWith('/organizations/passcodes/export', {
      params: { status: 'active' },
      responseType: 'blob',
    })
    expect(click).toHaveBeenCalled()
  })
})
