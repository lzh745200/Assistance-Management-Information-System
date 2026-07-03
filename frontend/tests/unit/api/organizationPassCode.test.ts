import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockApiRequest = vi.fn()

vi.mock('@/api/request', () => ({
  get: (...args: any[]) => mockGet(...args),
  post: (...args: any[]) => mockPost(...args),
  apiRequest: (...args: any[]) => mockApiRequest(...args),
}))

import {
  getOrganizationVerificationCode,
  createOrganizationPassCode,
  getOrganizationPassCodeList,
  exportOrganizationPassCodes,
} from '@/api/organizationPassCode'

describe('api/organizationPassCode', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getOrganizationVerificationCode GET /machine-code/organization/{id}/verification-code', () => {
    getOrganizationVerificationCode(3)
    expect(mockGet).toHaveBeenCalledWith('/machine-code/organization/3/verification-code')
  })

  it('createOrganizationPassCode POST /machine-code/organization/create', () => {
    createOrganizationPassCode({
      organization_id: 1,
      verification_code: 'VC',
      allow_subordinate_generation: true,
    })
    expect(mockPost).toHaveBeenCalledWith('/machine-code/organization/create', {
      organization_id: 1,
      verification_code: 'VC',
      allow_subordinate_generation: true,
    })
  })

  it('getOrganizationPassCodeList GET /machine-code/organization/list with params', () => {
    getOrganizationPassCodeList({ organization_id: 1, status: 'active', page: 1, page_size: 10 })
    expect(mockGet).toHaveBeenCalledWith('/machine-code/organization/list', {
      organization_id: 1,
      status: 'active',
      page: 1,
      page_size: 10,
    })
  })

  it('getOrganizationPassCodeList 无参', () => {
    getOrganizationPassCodeList()
    expect(mockGet).toHaveBeenCalledWith('/machine-code/organization/list', undefined)
  })

  it('exportOrganizationPassCodes 触发下载', async () => {
    mockApiRequest.mockResolvedValueOnce(new Blob(['test']))
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
    expect(mockApiRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/machine-code/organization/export',
      params: { status: 'active' },
      responseType: 'blob',
    })
    expect(click).toHaveBeenCalled()
  })
})
