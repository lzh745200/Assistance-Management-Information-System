import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPut = vi.fn()
const mockDelete = vi.fn()

vi.mock('@/utils/request', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
    put: (...args: any[]) => mockPut(...args),
    delete: (...args: any[]) => mockDelete(...args),
  },
}))
vi.mock('@/api/request', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
    put: (...args: any[]) => mockPut(...args),
    delete: (...args: any[]) => mockDelete(...args),
  },
}))

import { fundLifecycleApi } from '@/api/fundLifecycle'

describe('api/fundLifecycle (30 methods)', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getPhases', async () => {
    mockGet.mockResolvedValueOnce({ data: { data: { phases: [] } } })
    await fundLifecycleApi.getPhases(1)
    expect(mockGet).toHaveBeenCalledWith('/fund-lifecycle/phases/1')
  })

  it('advancePhase POST 含 remarks', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    await fundLifecycleApi.advancePhase(1, 'ok')
    expect(mockPost).toHaveBeenCalledWith('/fund-lifecycle/phases/1/advance', { remarks: 'ok' })
  })

  it('rollbackPhase POST', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    await fundLifecycleApi.rollbackPhase(1, 'revert')
    expect(mockPost).toHaveBeenCalledWith('/fund-lifecycle/phases/1/rollback', { remarks: 'revert' })
  })

  it('initiate POST', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    await fundLifecycleApi.initiate(1)
    expect(mockPost).toHaveBeenCalledWith('/fund-lifecycle/initiate/1')
  })

  it('getReportTemplate GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { data: { tpl: 'x' } } })
    await fundLifecycleApi.getReportTemplate(1)
    expect(mockGet).toHaveBeenCalledWith('/fund-lifecycle/report-template/1')
  })

  it('lockBudget POST', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    await fundLifecycleApi.lockBudget(1)
    expect(mockPost).toHaveBeenCalledWith('/fund-lifecycle/budget-lock/1')
  })

  it('complianceCheck GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { data: { ok: true } } })
    await fundLifecycleApi.complianceCheck(1)
    expect(mockGet).toHaveBeenCalledWith('/fund-lifecycle/compliance-check/1')
  })

  it('budgetAggregation GET with params', async () => {
    mockGet.mockResolvedValueOnce({ data: { data: [] } })
    await fundLifecycleApi.budgetAggregation({ group_by: 'year' })
    expect(mockGet).toHaveBeenCalledWith('/fund-lifecycle/budget-aggregation', { params: { group_by: 'year' } })
  })

  it('quotaLock POST', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    await fundLifecycleApi.quotaLock(5)
    expect(mockPost).toHaveBeenCalledWith('/fund-lifecycle/quota-lock/5')
  })

  it('allocationPlan GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { data: { plan: {} } } })
    await fundLifecycleApi.allocationPlan(1)
    expect(mockGet).toHaveBeenCalledWith('/fund-lifecycle/allocation-plan/1')
  })

  it('listTransferVouchers GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { data: [] } })
    await fundLifecycleApi.listTransferVouchers({ page: 1 })
    expect(mockGet).toHaveBeenCalledWith('/fund-lifecycle/transfer-vouchers', { params: { page: 1 } })
  })

  it('createTransferVoucher POST', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await fundLifecycleApi.createTransferVoucher({ amount: 100 })
    expect(mockPost).toHaveBeenCalledWith('/fund-lifecycle/transfer-vouchers', { amount: 100 })
  })

  it('getTransferVoucher GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { id: 1 } })
    await fundLifecycleApi.getTransferVoucher(1)
    expect(mockGet).toHaveBeenCalledWith('/fund-lifecycle/transfer-vouchers/1')
  })

  it('updateTransferVoucher PUT', async () => {
    mockPut.mockResolvedValueOnce({ data: { success: true } })
    await fundLifecycleApi.updateTransferVoucher(1, { amount: 200 })
    expect(mockPut).toHaveBeenCalledWith('/fund-lifecycle/transfer-vouchers/1', { amount: 200 })
  })

  it('deleteTransferVoucher DELETE', async () => {
    mockDelete.mockResolvedValueOnce({ data: { success: true } })
    await fundLifecycleApi.deleteTransferVoucher(1)
    expect(mockDelete).toHaveBeenCalledWith('/fund-lifecycle/transfer-vouchers/1')
  })

  it('confirmTransferVoucher POST', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    await fundLifecycleApi.confirmTransferVoucher(1)
    expect(mockPost).toHaveBeenCalledWith('/fund-lifecycle/transfer-vouchers/1/confirm')
  })

  it('transferLedger GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { data: { ledger: [] } } })
    await fundLifecycleApi.transferLedger(1)
    expect(mockGet).toHaveBeenCalledWith('/fund-lifecycle/transfer-ledger/1')
  })

  it('listContracts GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { data: [] } })
    await fundLifecycleApi.listContracts({ status: 'active' })
    expect(mockGet).toHaveBeenCalledWith('/fund-lifecycle/contracts', { params: { status: 'active' } })
  })

  it('createContract POST', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await fundLifecycleApi.createContract({ name: 'c1' })
    expect(mockPost).toHaveBeenCalledWith('/fund-lifecycle/contracts', { name: 'c1' })
  })

  it('getContract GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { id: 1 } })
    await fundLifecycleApi.getContract(1)
    expect(mockGet).toHaveBeenCalledWith('/fund-lifecycle/contracts/1')
  })

  it('updateContract PUT', async () => {
    mockPut.mockResolvedValueOnce({ data: { success: true } })
    await fundLifecycleApi.updateContract(1, { name: 'c2' })
    expect(mockPut).toHaveBeenCalledWith('/fund-lifecycle/contracts/1', { name: 'c2' })
  })

  it('deleteContract DELETE', async () => {
    mockDelete.mockResolvedValueOnce({ data: { success: true } })
    await fundLifecycleApi.deleteContract(1)
    expect(mockDelete).toHaveBeenCalledWith('/fund-lifecycle/contracts/1')
  })

  it('createContractPayment POST', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    await fundLifecycleApi.createContractPayment(1, { amount: 100 })
    expect(mockPost).toHaveBeenCalledWith('/fund-lifecycle/contracts/1/payments', { amount: 100 })
  })

  it('monitoringDeviation GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { data: { dev: 0 } } })
    await fundLifecycleApi.monitoringDeviation(1)
    expect(mockGet).toHaveBeenCalledWith('/fund-lifecycle/monitoring/deviation/1')
  })

  it('fundFlow GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { data: { flow: [] } } })
    await fundLifecycleApi.fundFlow(1)
    expect(mockGet).toHaveBeenCalledWith('/fund-lifecycle/monitoring/fund-flow/1')
  })

  it('listAnomalies GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { data: [] } })
    await fundLifecycleApi.listAnomalies({ severity: 'high' })
    expect(mockGet).toHaveBeenCalledWith('/fund-lifecycle/anomalies', { params: { severity: 'high' } })
  })

  it('detectAnomalies POST', async () => {
    mockPost.mockResolvedValueOnce({ data: { anomalies: [] } })
    await fundLifecycleApi.detectAnomalies(1)
    expect(mockPost).toHaveBeenCalledWith('/fund-lifecycle/anomalies/detect/1')
  })

  it('resolveAnomaly POST', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    await fundLifecycleApi.resolveAnomaly(5, 'fixed')
    expect(mockPost).toHaveBeenCalledWith('/fund-lifecycle/anomalies/5/resolve', { resolution: 'fixed' })
  })

  it('createSettlement POST', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    await fundLifecycleApi.createSettlement(1, { amount: 1000 })
    expect(mockPost).toHaveBeenCalledWith('/fund-lifecycle/settlement/1', { amount: 1000 })
  })

  it('createSettlement 无 data 用 {}', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    await fundLifecycleApi.createSettlement(1)
    expect(mockPost).toHaveBeenCalledWith('/fund-lifecycle/settlement/1', {})
  })

  it('updateSettlement PUT', async () => {
    mockPut.mockResolvedValueOnce({ data: { success: true } })
    await fundLifecycleApi.updateSettlement(2, { amount: 2000 })
    expect(mockPut).toHaveBeenCalledWith('/fund-lifecycle/settlement/2', { amount: 2000 })
  })

  it('approveSettlement POST', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    await fundLifecycleApi.approveSettlement(2, { approved: true })
    expect(mockPost).toHaveBeenCalledWith('/fund-lifecycle/settlement/2/approve', { approved: true })
  })

  it('approveSettlement 无 data 用 {}', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    await fundLifecycleApi.approveSettlement(2)
    expect(mockPost).toHaveBeenCalledWith('/fund-lifecycle/settlement/2/approve', {})
  })

  it('getPerformance GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { data: { score: 90 } } })
    await fundLifecycleApi.getPerformance(1)
    expect(mockGet).toHaveBeenCalledWith('/fund-lifecycle/performance/1')
  })

  it('getHealth GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { data: { score: 85 } } })
    await fundLifecycleApi.getHealth(1)
    expect(mockGet).toHaveBeenCalledWith('/fund-lifecycle/health/1')
  })

  it('batchHealth POST with project_ids', async () => {
    mockPost.mockResolvedValueOnce({ data: { data: { 1: 80, 2: 90 } } })
    await fundLifecycleApi.batchHealth([1, 2])
    expect(mockPost).toHaveBeenCalledWith('/fund-lifecycle/health/batch', { project_ids: [1, 2] })
  })
})
