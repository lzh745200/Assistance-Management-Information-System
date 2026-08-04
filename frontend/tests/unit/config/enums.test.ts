import { describe, it, expect } from 'vitest'
import {
  FUND_TYPES,
  FUND_STATUS,
  PROJECT_STATUS,
  PROJECT_TYPES,
  POLICY_LEVELS,
  POLICY_STATUS,
  getFundTypeLabel,
  getFundStatusLabel,
  getProjectStatusLabel,
  getProjectTypeLabel,
} from '@/config/enums'

describe('config/enums', () => {
  it('FUND_TYPES 常量', () => {
    expect(FUND_TYPES.project).toBe('项目经费')
    expect(FUND_TYPES.operation).toBe('运营经费')
    expect(FUND_TYPES.education).toBe('教育经费')
    expect(FUND_TYPES.infrastructure).toBe('基建经费')
    expect(FUND_TYPES.emergency).toBe('应急经费')
  })

  it('FUND_STATUS 常量', () => {
    expect(FUND_STATUS.pending).toBe('待审批')
    expect(FUND_STATUS.approved).toBe('已审批')
    expect(FUND_STATUS.allocated).toBe('已拨付')
    expect(FUND_STATUS.in_use).toBe('使用中')
    expect(FUND_STATUS.completed).toBe('已完成')
    expect(FUND_STATUS.cancelled).toBe('已取消')
  })

  it('PROJECT_STATUS 常量', () => {
    expect(PROJECT_STATUS.planning).toBe('规划中')
    expect(PROJECT_STATUS.in_progress).toBe('进行中')
    expect(PROJECT_STATUS.completed).toBe('已完成')
    expect(PROJECT_STATUS.suspended).toBe('已暂停')
    expect(PROJECT_STATUS.cancelled).toBe('已取消')
  })

  it('PROJECT_TYPES 常量', () => {
    expect(PROJECT_TYPES.infrastructure).toBe('基础设施')
    expect(PROJECT_TYPES.industry).toBe('产业发展')
    expect(PROJECT_TYPES.education).toBe('教育帮扶')
    expect(PROJECT_TYPES.medical).toBe('医疗帮扶')
    expect(PROJECT_TYPES.ecology).toBe('生态建设')
    expect(PROJECT_TYPES.party_building).toBe('党建引领')
  })

  it('POLICY_LEVELS 常量', () => {
    expect(POLICY_LEVELS.national).toBe('国家级')
    expect(POLICY_LEVELS.provincial).toBe('省级')
    expect(POLICY_LEVELS.municipal).toBe('市级')
    expect(POLICY_LEVELS.county).toBe('县级')
    expect(POLICY_LEVELS.department).toBe('部门级')
  })

  it('POLICY_STATUS 常量', () => {
    expect(POLICY_STATUS.draft).toBe('草稿')
    expect(POLICY_STATUS.published).toBe('已发布')
    expect(POLICY_STATUS.expired).toBe('已过期')
    expect(POLICY_STATUS.revoked).toBe('已撤销')
  })

  describe('getFundTypeLabel', () => {
    it('已知类型返回中文标签', () => {
      expect(getFundTypeLabel('project')).toBe('项目经费')
    })
    it('未知类型原样返回', () => {
      expect(getFundTypeLabel('unknown')).toBe('unknown')
    })
  })

  describe('getFundStatusLabel', () => {
    it('已知状态返回中文标签', () => {
      expect(getFundStatusLabel('allocated')).toBe('已拨付')
    })
    it('未知状态原样返回', () => {
      expect(getFundStatusLabel('weird')).toBe('weird')
    })
  })

  describe('getProjectStatusLabel', () => {
    it('已知状态返回中文标签', () => {
      expect(getProjectStatusLabel('in_progress')).toBe('进行中')
    })
    it('未知状态原样返回', () => {
      expect(getProjectStatusLabel('x')).toBe('x')
    })
  })

  describe('getProjectTypeLabel', () => {
    it('已知类型返回中文标签', () => {
      expect(getProjectTypeLabel('medical')).toBe('医疗帮扶')
    })
    it('未知类型原样返回', () => {
      expect(getProjectTypeLabel('y')).toBe('y')
    })
  })
})
