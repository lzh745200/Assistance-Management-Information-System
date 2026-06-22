/**
 * 数据类型常量
 * 用于数据包导出、上报等功能
 */

export const DATA_TYPES = {
  VILLAGES: 'villages',
  PROJECTS: 'projects',
  FUNDS: 'funds',
  SCHOOLS: 'schools',
  POLICIES: 'policies',
  ORGANIZATIONS: 'organizations',
} as const

export type DataType = (typeof DATA_TYPES)[keyof typeof DATA_TYPES]

/**
 * 数据类型显示名称映射
 */
export const DATA_TYPE_LABELS: Record<DataType, string> = {
  [DATA_TYPES.VILLAGES]: '帮扶村数据',
  [DATA_TYPES.PROJECTS]: '项目数据',
  [DATA_TYPES.FUNDS]: '资金数据',
  [DATA_TYPES.SCHOOLS]: '学校数据',
  [DATA_TYPES.POLICIES]: '政策法规',
  [DATA_TYPES.ORGANIZATIONS]: '组织数据',
}

/**
 * 导出字段常量
 */
export const EXPORT_FIELDS = {
  // 帮扶村字段
  VILLAGE: {
    NAME: 'name',
    CODE: 'code',
    PROVINCE: 'province',
    CITY: 'city',
    COUNTY: 'county',
    TOWNSHIP: 'township',
    POPULATION: 'population',
    AREA: 'area',
  },
  // 项目字段
  PROJECT: {
    NAME: 'name',
    CODE: 'code',
    TYPE: 'type',
    STATUS: 'status',
    BUDGET: 'budget',
    START_DATE: 'start_date',
    END_DATE: 'end_date',
  },
  // 资金字段
  FUND: {
    AMOUNT: 'amount',
    TYPE: 'type',
    SOURCE: 'source',
    DATE: 'date',
    PURPOSE: 'purpose',
  },
} as const
