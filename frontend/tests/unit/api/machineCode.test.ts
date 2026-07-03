import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockApiRequest = vi.fn()

vi.mock('@/api/request', () => ({
  apiRequest: (...args: any[]) => mockApiRequest(...args),
}))

import {
  getMachineCode,
  createMachineCode,
  listMachineCodes,
  revokeMachineCode,
  verifyMachineCode,
  generateInitialPassword,
  resetPasswordWithMachineCode,
  getMachineInfo,
} from '@/api/machineCode'

describe('api/machineCode', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getMachineCode 调用 GET /machine-code/get-machine-code', () => {
    getMachineCode()
    expect(mockApiRequest).toHaveBeenCalledWith({
      url: '/machine-code/get-machine-code',
      method: 'get',
    })
  })

  it('createMachineCode 调用 POST /machine-code/admin/create', () => {
    const data = { machine_code: 'MC123', description: 'test' }
    createMachineCode(data)
    expect(mockApiRequest).toHaveBeenCalledWith({
      url: '/machine-code/admin/create',
      method: 'post',
      data,
    })
  })

  it('listMachineCodes 带 filter 参数', () => {
    listMachineCodes({ status_filter: 'active', skip: 0, limit: 10 })
    expect(mockApiRequest).toHaveBeenCalledWith({
      url: '/machine-code/admin/list',
      method: 'get',
      params: { status_filter: 'active', skip: 0, limit: 10 },
    })
  })

  it('listMachineCodes 无参数', () => {
    listMachineCodes()
    expect(mockApiRequest).toHaveBeenCalledWith({
      url: '/machine-code/admin/list',
      method: 'get',
      params: undefined,
    })
  })

  it('revokeMachineCode 调用 POST /machine-code/admin/revoke/{id}', () => {
    revokeMachineCode(42)
    expect(mockApiRequest).toHaveBeenCalledWith({
      url: '/machine-code/admin/revoke/42',
      method: 'post',
    })
  })

  it('verifyMachineCode 调用 POST /machine-code/verify-machine-code', () => {
    const data = { machine_code: 'MC', verification_code: 'VC' }
    verifyMachineCode(data)
    expect(mockApiRequest).toHaveBeenCalledWith({
      url: '/machine-code/verify-machine-code',
      method: 'post',
      data,
    })
  })

  it('generateInitialPassword 调用 POST /machine-code/generate-initial-password', () => {
    const data = { username: 'alice', verification_code: 'VC' }
    generateInitialPassword(data)
    expect(mockApiRequest).toHaveBeenCalledWith({
      url: '/machine-code/generate-initial-password',
      method: 'post',
      data,
    })
  })

  it('resetPasswordWithMachineCode 用 params 传 data', () => {
    const data = { username: 'a', machine_code: 'm', verification_code: 'v' }
    resetPasswordWithMachineCode(data)
    expect(mockApiRequest).toHaveBeenCalledWith({
      url: '/machine-code/reset-password-with-machine-code',
      method: 'post',
      params: data,
    })
  })

  it('getMachineInfo 调用 GET /machine-code/machine-info', () => {
    getMachineInfo()
    expect(mockApiRequest).toHaveBeenCalledWith({
      url: '/machine-code/machine-info',
      method: 'get',
    })
  })
})
