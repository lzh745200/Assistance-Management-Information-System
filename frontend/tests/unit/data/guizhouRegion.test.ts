import { describe, it, expect } from 'vitest'
import {
  GUIZHOU_REGION_FULL,
  GUIZHOU_REGION,
  GUIZHOU_ALL_COUNTIES,
  GUIZHOU_ALL_CITIES,
  QIANNAN_COUNTIES,
  DEFAULT_PROVINCE,
  DEFAULT_CITY,
  DEFAULT_PREFECTURE,
  getCountiesByCity,
  getTownshipsByCityCounty,
  isValidCounty,
  getFullRegionInfo,
} from '@/data/guizhouRegion'

describe('data/guizhouRegion', () => {
  it('GUIZHOU_REGION_FULL 包含 9 个市州且结构完整', () => {
    expect(GUIZHOU_REGION_FULL).toHaveLength(9)
    for (const city of GUIZHOU_REGION_FULL) {
      expect(city.name).toBeTruthy()
      expect(city.counties.length).toBeGreaterThan(0)
      for (const county of city.counties) {
        expect(county.name).toBeTruthy()
        expect(Array.isArray(county.townships)).toBe(true)
        expect(county.townships.length).toBeGreaterThan(0)
      }
    }
    expect(GUIZHOU_REGION_FULL.map((c) => c.name)).toEqual([
      '贵阳市',
      '六盘水市',
      '遵义市',
      '安顺市',
      '毕节市',
      '铜仁市',
      '黔西南布依族苗族自治州',
      '黔东南苗族侗族自治州',
      '黔南布依族苗族自治州',
    ])
  })

  it('GUIZHOU_REGION 旧接口只含县区名（无乡镇）', () => {
    expect(GUIZHOU_REGION).toHaveLength(9)
    for (const city of GUIZHOU_REGION) {
      expect(typeof city.name).toBe('string')
      expect(city.counties.every((c) => typeof c === 'string')).toBe(true)
    }
    expect(GUIZHOU_REGION[0].name).toBe('贵阳市')
    expect(GUIZHOU_REGION[0].counties).toContain('南明区')
    expect(GUIZHOU_REGION[0].counties).not.toContain('新华路街道')
  })

  it('GUIZHOU_ALL_COUNTIES 为全部县区 flat 列表且与 full 一致', () => {
    const expected = GUIZHOU_REGION_FULL.flatMap((c) => c.counties.map((co) => co.name))
    expect(GUIZHOU_ALL_COUNTIES).toEqual(expected)
    expect(GUIZHOU_ALL_COUNTIES).toHaveLength(expected.length)
    expect(GUIZHOU_ALL_COUNTIES).toContain('都匀市')
    expect(GUIZHOU_ALL_COUNTIES).toContain('三都水族自治县')
    expect(new Set(GUIZHOU_ALL_COUNTIES).size).toBe(GUIZHOU_ALL_COUNTIES.length)
  })

  it('GUIZHOU_ALL_CITIES 为 9 个市州名称', () => {
    expect(GUIZHOU_ALL_CITIES).toHaveLength(9)
    expect(GUIZHOU_ALL_CITIES).toContain('黔南布依族苗族自治州')
    expect(GUIZHOU_ALL_CITIES).toContain('贵阳市')
  })

  it('DEFAULT_PROVINCE / DEFAULT_CITY / DEFAULT_PREFECTURE 常量', () => {
    expect(DEFAULT_PROVINCE).toBe('贵州省')
    expect(DEFAULT_CITY).toBe('黔南布依族苗族自治州')
    expect(DEFAULT_PREFECTURE).toBe(DEFAULT_CITY)
  })

  it('getCountiesByCity 返回下属县区', () => {
    const counties = getCountiesByCity('黔南布依族苗族自治州')
    expect(counties).toHaveLength(QIANNAN_COUNTIES.length)
    for (const c of QIANNAN_COUNTIES) {
      expect(counties).toContain(c)
    }
  })

  it('getCountiesByCity 未知市州返回空数组', () => {
    expect(getCountiesByCity('不存在市')).toEqual([])
  })

  it('getTownshipsByCityCounty 返回乡镇列表', () => {
    const townships = getTownshipsByCityCounty('黔南布依族苗族自治州', '都匀市')
    expect(townships).toContain('匀东镇')
    expect(townships).toContain('归兰水族乡')
  })

  it('getTownshipsByCityCounty 未知市州返回空数组', () => {
    expect(getTownshipsByCityCounty('不存在市', '都匀市')).toEqual([])
  })

  it('getTownshipsByCityCounty 未知县区返回空数组', () => {
    expect(getTownshipsByCityCounty('黔南布依族苗族自治州', '不存在县')).toEqual([])
  })

  it('isValidCounty 校验黔南州县区', () => {
    expect(isValidCounty('都匀市')).toBe(true)
    expect(isValidCounty('三都水族自治县')).toBe(true)
    expect(isValidCounty('贵阳市')).toBe(false)
    expect(isValidCounty('')).toBe(false)
  })

  it('getFullRegionInfo 返回完整地区信息', () => {
    expect(getFullRegionInfo('都匀市')).toEqual({
      province: '贵州省',
      city: '黔南布依族苗族自治州',
      county: '都匀市',
    })
  })

  it('getFullRegionInfo 非法县区 county 置空', () => {
    expect(getFullRegionInfo('南明区')).toEqual({
      province: '贵州省',
      city: '黔南布依族苗族自治州',
      county: '',
    })
  })

  it('QIANNAN_COUNTIES 覆盖黔南州 12 县市且无重复', () => {
    expect(QIANNAN_COUNTIES).toHaveLength(12)
    expect(new Set(QIANNAN_COUNTIES).size).toBe(12)
    for (const county of QIANNAN_COUNTIES) {
      expect(GUIZHOU_ALL_COUNTIES).toContain(county)
    }
  })
})
