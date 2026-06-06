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
  getDataReports,
  getReportStatistics,
  getSubordinateDashboard,
  getPendingReports,
  getDataReport,
  createDataReport,
  submitReport,
  reviewReport,
  cancelReport,
  resubmitReport,
  getReportPackage,
  previewReportData,
  downloadReportPackage,
} from '@/api/dataReport'

describe('api/dataReport', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getDataReports GET /data-reports', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [], total: 0 } })
    await getDataReports({ status: 'pending' })
    expect(mockGet).toHaveBeenCalledWith('/data-reports', { params: { status: 'pending' } })
  })

  it('getReportStatistics GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { total: 0 } })
    await getReportStatistics()
    expect(mockGet).toHaveBeenCalledWith('/data-reports/statistics')
  })

  it('getSubordinateDashboard GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { pending: 0 } })
    await getSubordinateDashboard()
    expect(mockGet).toHaveBeenCalledWith('/data-reports/dashboard')
  })

  it('getPendingReports GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [], total: 0 } })
    await getPendingReports({ page: 1 })
    expect(mockGet).toHaveBeenCalledWith('/data-reports/pending', { params: { page: 1 } })
  })

  it('getDataReport GET /data-reports/{id}', async () => {
    mockGet.mockResolvedValueOnce({ data: { id: 1 } })
    await getDataReport(1)
    expect(mockGet).toHaveBeenCalledWith('/data-reports/1')
  })

  it('createDataReport POST /data-reports', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await createDataReport({ title: 'X' } as any)
    expect(mockPost).toHaveBeenCalledWith('/data-reports', { title: 'X' })
  })

  it('submitReport 无 comment', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await submitReport(1)
    expect(mockPost).toHaveBeenCalledWith('/data-reports/1/submit', null, { params: undefined })
  })

  it('submitReport 含 comment', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await submitReport(1, 'ok')
    expect(mockPost).toHaveBeenCalledWith('/data-reports/1/submit', null, { params: { comment: 'ok' } })
  })

  it('reviewReport POST /data-reports/{id}/review', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await reviewReport(1, { status: 'approved' } as any)
    expect(mockPost).toHaveBeenCalledWith('/data-reports/1/review', { status: 'approved' })
  })

  it('cancelReport 无 reason', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await cancelReport(1)
    expect(mockPost).toHaveBeenCalledWith('/data-reports/1/cancel', null, { params: undefined })
  })

  it('cancelReport 含 reason', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await cancelReport(1, 'wrong data')
    expect(mockPost).toHaveBeenCalledWith('/data-reports/1/cancel', null, { params: { reason: 'wrong data' } })
  })

  it('resubmitReport 无 comment', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await resubmitReport(1)
    expect(mockPost).toHaveBeenCalledWith('/data-reports/1/resubmit', null, { params: undefined })
  })

  it('resubmitReport 含 comment', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await resubmitReport(1, 'fixed')
    expect(mockPost).toHaveBeenCalledWith('/data-reports/1/resubmit', null, { params: { comment: 'fixed' } })
  })

  it('getReportPackage GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { report_id: 1, package_id: 5 } })
    await getReportPackage(1)
    expect(mockGet).toHaveBeenCalledWith('/data-reports/1/package')
  })

  it('previewReportData GET', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await previewReportData(1)
    expect(mockGet).toHaveBeenCalledWith('/data-reports/1/preview')
  })

  it('downloadReportPackage GET blob', async () => {
    mockGet.mockResolvedValueOnce({ data: new Blob(['x']) })
    const blob = await downloadReportPackage(1)
    expect(mockGet).toHaveBeenCalledWith('/data-reports/1/download', { responseType: 'blob' })
    expect(blob).toBeInstanceOf(Blob)
  })
})
