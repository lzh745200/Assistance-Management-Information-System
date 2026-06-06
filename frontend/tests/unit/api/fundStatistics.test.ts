import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()

vi.mock('@/utils/request', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
  },
}))

vi.mock('@/api/request', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
  },
}))

import {
  getFundStatisticsByType,
  getYearlyFundComparison,
  getUtilizationRate,
  getFundSummary,
  FUND_TYPES,
  FUND_SOURCES,
  FUND_STATUSES,
} from '@/api/fundStatistics'

describe('api/fundStatistics', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('constants', () => {
    it('FUND_TYPES 包含 project/operation/education/infrastructure/emergency/other', () => {
      expect(FUND_TYPES.project).toBe('项目经费')
      expect(FUND_TYPES.operation).toBe('运营经费')
      expect(FUND_TYPES.education).toBe('教育帮扶')
      expect(FUND_TYPES.infrastructure).toBe('基础设施')
      expect(FUND_TYPES.emergency).toBe('应急经费')
      expect(FUND_TYPES.other).toBe('其他')
    })

    it('FUND_SOURCES 包含 military/government/donation/enterprise/other', () => {
      expect(FUND_SOURCES.military).toBe('军队')
      expect(FUND_SOURCES.government).toBe('政府')
      expect(FUND_SOURCES.donation).toBe('捐赠')
      expect(FUND_SOURCES.enterprise).toBe('企业')
    })

    it('FUND_STATUSES 包含 7 个状态', () => {
      expect(FUND_STATUSES.pending).toBe('待审批')
      expect(FUND_STATUSES.approved).toBe('已批准')
      expect(FUND_STATUSES.audited).toBe('已审计')
      expect(FUND_STATUSES.rejected).toBe('已驳回')
    })
  })

  describe('getFundStatisticsByType', () => {
    it('调用 GET /funds/supported-village/statistics/by-type', () => {
      getFundStatisticsByType({ year: 2024 })
      expect(mockGet).toHaveBeenCalledWith(
        '/funds/supported-village/statistics/by-type',
        { params: { year: 2024 } },
      )
    })

    it('无参时 params=undefined', () => {
      getFundStatisticsByType()
      expect(mockGet).toHaveBeenCalledWith(
        '/funds/supported-village/statistics/by-type',
        { params: undefined },
      )
    })
  })

  describe('getYearlyFundComparison', () => {
    it('调用 GET /funds/supported-village/statistics/yearly-comparison', () => {
      getYearlyFundComparison({ year_start: 2020, year_end: 2024 })
      expect(mockGet).toHaveBeenCalledWith(
        '/funds/supported-village/statistics/yearly-comparison',
        { params: { year_start: 2020, year_end: 2024 } },
      )
    })
  })

  describe('getUtilizationRate', () => {
    it('调用 GET /funds/supported-village/statistics/utilization-rate', () => {
      getUtilizationRate({ village_id: 5 })
      expect(mockGet).toHaveBeenCalledWith(
        '/funds/supported-village/statistics/utilization-rate',
        { params: { village_id: 5 } },
      )
    })
  })

  describe('getFundSummary', () => {
    it('调用 GET /funds/supported-village/statistics/summary', () => {
      getFundSummary({ department: 'finance' })
      expect(mockGet).toHaveBeenCalledWith(
        '/funds/supported-village/statistics/summary',
        { params: { department: 'finance' } },
      )
    })
  })
})
