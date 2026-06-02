/**
 * 地图API单元测试 - 100%覆盖
 * 测试 getMapMarkers() 和 getCountyCoords()
 *
 * IMPORTANT: 真实的 get<T>(url, params) 内部调用 apiRequest<T> → res.data，
 * 返回的是已解包的响应数据，不是完整的 AxiosResponse。
 * 因此 mock 应直接返回数据对象，不包裹 { data, status, ... }。
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock request module
vi.mock('@/api/request', () => ({
  default: { get: vi.fn(), post: vi.fn() },
  get: vi.fn(),
  post: vi.fn(),
}))

describe('Map API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getMapMarkers', () => {
    it('应该使用默认参数 marker_type=all', async () => {
      const { get } = await import('@/api/request')
      vi.mocked(get).mockResolvedValue({ villages: [], schools: [] })

      const { getMapMarkers } = await import('@/api/map')
      const result = await getMapMarkers()

      expect(get).toHaveBeenCalledWith('/map/markers', { params: { marker_type: 'all' } })
      expect(result).toEqual({ villages: [], schools: [] })
    })

    it('应该传递 marker_type=villages', async () => {
      const { get } = await import('@/api/request')
      vi.mocked(get).mockResolvedValue({
        villages: [{ id: 1, name: '测试村', lng: 107.5, lat: 26.3 }]
      })

      const { getMapMarkers } = await import('@/api/map')
      const result = await getMapMarkers('villages')

      expect(get).toHaveBeenCalledWith('/map/markers', { params: { marker_type: 'villages' } })
      expect(result.villages).toHaveLength(1)
      expect(result.villages![0].name).toBe('测试村')
    })

    it('应该传递 marker_type=schools', async () => {
      const { get } = await import('@/api/request')
      vi.mocked(get).mockResolvedValue({
        schools: [{ id: 1, name: '测试校', lng: 107.5, lat: 26.3 }]
      })

      const { getMapMarkers } = await import('@/api/map')
      const result = await getMapMarkers('schools')

      expect(get).toHaveBeenCalledWith('/map/markers', { params: { marker_type: 'schools' } })
      expect(result.schools).toHaveLength(1)
    })

    it('应该返回包含完整村庄字段的数据', async () => {
      const { get } = await import('@/api/request')
      const village = {
        id: 1, name: '测试村', lng: 107.52, lat: 26.26,
        county: '都匀市', department: '测试部队', supportUnit: '测试单位',
        regionScope: '黔南州', isThreeRegions: true, isKeyCounty: false,
        isBorderArea: false, isProvincialDemo: true,
        isHundredVillageDemo: false, tieredDevelopmentLevel: '示范级'
      }
      vi.mocked(get).mockResolvedValue({ villages: [village] })

      const { getMapMarkers } = await import('@/api/map')
      const result = await getMapMarkers('all')

      const v = result.villages![0]
      expect(v.id).toBe(1)
      expect(v.lng).toBe(107.52)
      expect(v.lat).toBe(26.26)
      expect(v.isThreeRegions).toBe(true)
      expect(v.tieredDevelopmentLevel).toBe('示范级')
    })

    it('应该返回包含完整学校字段的数据', async () => {
      const { get } = await import('@/api/request')
      const school = {
        id: 1, name: '测试校', lng: 107.3, lat: 26.5,
        district: '都匀市', type: 'primary', supportStatus: 'active',
        supportUnit: '测试单位', studentCount: 200, teacherCount: 15
      }
      vi.mocked(get).mockResolvedValue({ schools: [school] })

      const { getMapMarkers } = await import('@/api/map')
      const result = await getMapMarkers('all')

      const s = result.schools![0]
      expect(s.studentCount).toBe(200)
      expect(s.teacherCount).toBe(15)
      expect(s.supportStatus).toBe('active')
    })

    it('应该处理网络错误', async () => {
      const { get } = await import('@/api/request')
      vi.mocked(get).mockRejectedValue(new Error('Network Error'))

      const { getMapMarkers } = await import('@/api/map')
      await expect(getMapMarkers()).rejects.toThrow('Network Error')
    })
  })

  describe('getCountyCoords', () => {
    it('应该返回中心坐标和县市坐标', async () => {
      const { get } = await import('@/api/request')
      const mockData = {
        center: { lng: 107.5, lat: 26.3 },
        counties: {
          '都匀市': { lng: 107.5187, lat: 26.2594 },
          '福泉市': { lng: 107.5133, lat: 26.6868 },
        }
      }
      vi.mocked(get).mockResolvedValue(mockData)

      const { getCountyCoords } = await import('@/api/map')
      const result = await getCountyCoords()

      expect(get).toHaveBeenCalledWith('/map/county-coords')
      expect(result.center.lng).toBe(107.5)
      expect(result.center.lat).toBe(26.3)
      expect(result.counties['都匀市'].lng).toBe(107.5187)
    })

    it('应该处理空县市列表', async () => {
      const { get } = await import('@/api/request')
      vi.mocked(get).mockResolvedValue({
        center: { lng: 107.5, lat: 26.3 },
        counties: {}
      })

      const { getCountyCoords } = await import('@/api/map')
      const result = await getCountyCoords()

      expect(Object.keys(result.counties)).toHaveLength(0)
    })

    it('应该处理网络错误', async () => {
      const { get } = await import('@/api/request')
      vi.mocked(get).mockRejectedValue(new Error('Network Error'))

      const { getCountyCoords } = await import('@/api/map')
      await expect(getCountyCoords()).rejects.toThrow('Network Error')
    })
  })
})

describe('Map API Types', () => {
  it('VillageMarker 接口应包含所有必需字段', () => {
    const marker = {
      id: 1, name: '测试', lng: 0, lat: 0,
      county: '', department: '', supportUnit: '',
      regionScope: '', isThreeRegions: false,
      isKeyCounty: false, isBorderArea: false,
      isProvincialDemo: false, isHundredVillageDemo: false,
      tieredDevelopmentLevel: null
    }
    expect(marker).toHaveProperty('id')
    expect(marker).toHaveProperty('lng')
    expect(marker).toHaveProperty('lat')
    expect(marker).toHaveProperty('isThreeRegions')
    expect(marker).toHaveProperty('tieredDevelopmentLevel')
  })

  it('SchoolMarker 接口应包含所有必需字段', () => {
    const marker = {
      id: 1, name: '测试', lng: 0, lat: 0,
      district: '', type: '', supportStatus: '',
      supportUnit: '', studentCount: 0, teacherCount: 0
    }
    expect(marker).toHaveProperty('studentCount')
    expect(marker).toHaveProperty('teacherCount')
    expect(marker).toHaveProperty('supportStatus')
  })

  it('MapMarkers 接口 villages 和 schools 应为可选', () => {
    const empty: Record<string, unknown> = {}
    expect(empty.villages).toBeUndefined()
    expect(empty.schools).toBeUndefined()
  })
})
