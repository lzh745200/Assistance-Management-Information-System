import { describe, it, expect, vi } from 'vitest'

const { mockGet } = vi.hoisted(() => ({ mockGet: vi.fn() }))
vi.mock('@/api/request', () => ({ get: mockGet }))

import {
  getMonitorSnapshot,
  getDatabaseFileSize,
  getResources,
  getAlerts,
  getAlertHistory,
  getApiStats,
} from '@/api/systemMonitor'

describe('api/systemMonitor', () => {
  it('getMonitorSnapshot calls GET /system/monitor/snapshot', async () => {
    const resp = { success: true, data: { cpu_usage: 50, timestamp: '2026-01-01' } }
    mockGet.mockResolvedValue(resp)
    const r = await getMonitorSnapshot()
    expect(mockGet).toHaveBeenCalledWith('/system/monitor/snapshot')
    expect(r).toBe(resp)
  })

  it('getDatabaseFileSize calls GET /system/monitor/database-size', async () => {
    const resp = { success: true, data: { size_bytes: 1024, size_mb: 0.001 } }
    mockGet.mockResolvedValue(resp)
    const r = await getDatabaseFileSize()
    expect(mockGet).toHaveBeenCalledWith('/system/monitor/database-size')
    expect(r).toBe(resp)
  })

  it('getResources calls GET /system/monitor/resources', async () => {
    const resp = { success: true, data: { cpu: 1 } }
    mockGet.mockResolvedValue(resp)
    const r = await getResources()
    expect(mockGet).toHaveBeenCalledWith('/system/monitor/resources')
    expect(r).toBe(resp)
  })

  it('getAlerts calls GET /system/monitor/alerts', async () => {
    const resp = { success: true, data: [{ id: 1 }] }
    mockGet.mockResolvedValue(resp)
    const r = await getAlerts()
    expect(mockGet).toHaveBeenCalledWith('/system/monitor/alerts')
    expect(r).toBe(resp)
  })

  it('getAlertHistory calls GET /system/monitor/alerts/history with params', async () => {
    const resp = { success: true, data: [] }
    mockGet.mockResolvedValue(resp)
    const r = await getAlertHistory({ page: 2, page_size: 10 })
    expect(mockGet).toHaveBeenCalledWith('/system/monitor/alerts/history', {
      page: 2,
      page_size: 10,
    })
    expect(r).toBe(resp)
  })

  it('getAlertHistory 无参', async () => {
    mockGet.mockResolvedValue({ success: true, data: [] })
    await getAlertHistory()
    expect(mockGet).toHaveBeenCalledWith('/system/monitor/alerts/history', undefined)
  })

  it('getApiStats calls GET /system/monitor/api-stats', async () => {
    const resp = { success: true, data: { total: 100 } }
    mockGet.mockResolvedValue(resp)
    const r = await getApiStats()
    expect(mockGet).toHaveBeenCalledWith('/system/monitor/api-stats')
    expect(r).toBe(resp)
  })
})
