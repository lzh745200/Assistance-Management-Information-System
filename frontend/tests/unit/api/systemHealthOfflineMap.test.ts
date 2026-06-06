import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockDelete = vi.fn()

vi.mock('@/utils/request', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
    delete: (...args: any[]) => mockDelete(...args),
  },
}))

vi.mock('@/api/request', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
    delete: (...args: any[]) => mockDelete(...args),
  },
}))

import { systemHealthApi } from '@/api/systemHealth'
import {
  offlineMapApi,
  clearTiles,
  downloadTiles,
  getMapStatus,
} from '@/api/offlineMap'

describe('api/systemHealth', () => {
  beforeEach(() => vi.clearAllMocks())

  it('overview', () => {
    systemHealthApi.overview()
    expect(mockGet).toHaveBeenCalledWith('/system/health/overview')
  })
  it('liveness', () => {
    systemHealthApi.liveness()
    expect(mockGet).toHaveBeenCalledWith('/system/health/liveness')
  })
  it('readiness', () => {
    systemHealthApi.readiness()
    expect(mockGet).toHaveBeenCalledWith('/system/health/readiness')
  })
  it('metrics', () => {
    systemHealthApi.metrics()
    expect(mockGet).toHaveBeenCalledWith('/system/health/metrics')
  })
})

describe('api/offlineMap', () => {
  beforeEach(() => vi.clearAllMocks())

  it('offlineMapApi.getTiles', () => {
    offlineMapApi.getTiles()
    expect(mockGet).toHaveBeenCalledWith('/offline-map/tiles')
  })
  it('offlineMapApi.getStatus', () => {
    offlineMapApi.getStatus()
    expect(mockGet).toHaveBeenCalledWith('/offline-map/status')
  })
  it('clearTiles DELETE', () => {
    clearTiles()
    expect(mockDelete).toHaveBeenCalledWith('/offline-map/tiles')
  })
  it('downloadTiles POST area', () => {
    downloadTiles('北京')
    expect(mockPost).toHaveBeenCalledWith('/offline-map/tiles/download', { area: '北京' })
  })
  it('getMapStatus GET', () => {
    getMapStatus()
    expect(mockGet).toHaveBeenCalledWith('/offline-map/status')
  })
})
