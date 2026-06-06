import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPut = vi.fn()

vi.mock('@/utils/request', () => ({
  default: { get: (...args: any[]) => mockGet(...args), put: (...args: any[]) => mockPut(...args) },
}))

vi.mock('@/api/request', () => ({
  default: { get: (...args: any[]) => mockGet(...args), put: (...args: any[]) => mockPut(...args) },
  get: (...args: any[]) => mockGet(...args),
  put: (...args: any[]) => mockPut(...args),
}))

import {
  getMapMarkers,
  getCountyCoords,
  getRegions,
  updateMarkerCoordinates,
} from '@/api/map'

describe('api/map', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getMapMarkers 默认 all', async () => {
    mockGet.mockResolvedValueOnce({ villages: [], schools: [] })
    await getMapMarkers()
    expect(mockGet).toHaveBeenCalledWith('/map/markers', { params: { marker_type: 'all' } })
  })

  it('getMapMarkers 指定 villages', async () => {
    mockGet.mockResolvedValueOnce({ villages: [] })
    await getMapMarkers('villages')
    expect(mockGet).toHaveBeenCalledWith('/map/markers', { params: { marker_type: 'villages' } })
  })

  it('getMapMarkers 指定 schools', async () => {
    mockGet.mockResolvedValueOnce({ schools: [] })
    await getMapMarkers('schools')
    expect(mockGet).toHaveBeenCalledWith('/map/markers', { params: { marker_type: 'schools' } })
  })

  it('getCountyCoords GET /map/county-coords', async () => {
    mockGet.mockResolvedValueOnce({ center: { lng: 1, lat: 2 }, counties: {} })
    await getCountyCoords()
    expect(mockGet).toHaveBeenCalledWith('/map/county-coords')
  })

  it('getRegions 无参', async () => {
    mockGet.mockResolvedValueOnce({ total: 0, items: [] })
    await getRegions()
    expect(mockGet).toHaveBeenCalledWith('/map/regions', {})
  })

  it('getRegions level + parentCode', async () => {
    mockGet.mockResolvedValueOnce({ total: 0, items: [] })
    await getRegions('city', '110000')
    expect(mockGet).toHaveBeenCalledWith('/map/regions', { level: 'city', parent_code: '110000' })
  })

  it('getRegions 只传 level', async () => {
    mockGet.mockResolvedValueOnce({ total: 0, items: [] })
    await getRegions('province')
    expect(mockGet).toHaveBeenCalledWith('/map/regions', { level: 'province' })
  })

  it('updateMarkerCoordinates PUT /map/markers/{type}/{id}/coordinates', async () => {
    mockPut.mockResolvedValueOnce({ success: true })
    await updateMarkerCoordinates('village', 5, 40.0, 116.0)
    expect(mockPut).toHaveBeenCalledWith('/map/markers/village/5/coordinates', {
      latitude: 40.0,
      longitude: 116.0,
    })
  })
})
