import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPut = vi.fn()
const mockDelete = vi.fn()
const mockRequest = vi.fn()

vi.mock('@/utils/request', () => ({
  default: (...args: any[]) => mockRequest(...args),
}))
vi.mock('@/api/request', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
    put: (...args: any[]) => mockPut(...args),
    delete: (...args: any[]) => mockDelete(...args),
  },
  default_alt: undefined,
}))

import {
  getOrganizations,
  getOrganization,
  getOrganizationTree,
  createOrganization,
  updateOrganization,
  deleteOrganization,
  batchUpdateSortOrders,
} from '@/api/organization'
import { ruralTaskApi } from '@/api/ruralTask'
import {
  getMetricsDashboard,
  getHealthMetrics,
  getPrometheusMetrics,
  getBusinessMetrics,
} from '@/api/metrics'

describe('api/organization', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getOrganizations GET /organizations', () => {
    getOrganizations({ page: 1 })
    expect(mockGet).toHaveBeenCalledWith('/organizations', { params: { page: 1 } })
  })
  it('getOrganization GET /{id}', () => {
    getOrganization(5)
    expect(mockGet).toHaveBeenCalledWith('/organizations/5')
  })
  it('getOrganizationTree GET /organizations/tree', () => {
    getOrganizationTree()
    expect(mockGet).toHaveBeenCalledWith('/organizations/tree')
  })
  it('createOrganization POST', () => {
    createOrganization({ name: 'O' })
    expect(mockPost).toHaveBeenCalledWith('/organizations', { name: 'O' })
  })
  it('updateOrganization PUT', () => {
    updateOrganization(5, { name: 'O2' })
    expect(mockPut).toHaveBeenCalledWith('/organizations/5', { name: 'O2' })
  })
  it('deleteOrganization DELETE', () => {
    deleteOrganization(5)
    expect(mockDelete).toHaveBeenCalledWith('/organizations/5')
  })
  it('batchUpdateSortOrders PUT /organizations/sort', () => {
    batchUpdateSortOrders([{ id: 1, sort: 1 }])
    expect(mockPut).toHaveBeenCalledWith('/organizations/sort', [{ id: 1, sort: 1 }])
  })
})

describe('api/ruralTask', () => {
  beforeEach(() => vi.clearAllMocks())

  it('list GET /rural-tasks', () => {
    ruralTaskApi.list({ page: 1 })
    expect(mockGet).toHaveBeenCalledWith('/rural-tasks', { params: { page: 1 } })
  })
  it('get GET /{id}', () => {
    ruralTaskApi.get(5)
    expect(mockGet).toHaveBeenCalledWith('/rural-tasks/5')
  })
  it('create POST', () => {
    ruralTaskApi.create({ title: 'T' })
    expect(mockPost).toHaveBeenCalledWith('/rural-tasks', { title: 'T' })
  })
  it('update PUT', () => {
    ruralTaskApi.update(5, { title: 'T2' })
    expect(mockPut).toHaveBeenCalledWith('/rural-tasks/5', { title: 'T2' })
  })
  it('delete DELETE', () => {
    ruralTaskApi.delete(5)
    expect(mockDelete).toHaveBeenCalledWith('/rural-tasks/5')
  })
})

describe('api/metrics', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getMetricsDashboard GET /system/metrics/dashboard', () => {
    getMetricsDashboard()
    expect(mockRequest).toHaveBeenCalledWith({
      url: '/system/metrics/dashboard',
      method: 'get',
    })
  })
  it('getHealthMetrics GET /system/metrics/health', () => {
    getHealthMetrics()
    expect(mockRequest).toHaveBeenCalledWith({
      url: '/system/metrics/health',
      method: 'get',
    })
  })
  it('getPrometheusMetrics GET with text responseType', () => {
    getPrometheusMetrics()
    expect(mockRequest).toHaveBeenCalledWith({
      url: '/monitoring/metrics/prometheus',
      method: 'get',
      responseType: 'text',
    })
  })
  it('getBusinessMetrics GET /monitoring/metrics/business', () => {
    getBusinessMetrics()
    expect(mockRequest).toHaveBeenCalledWith({
      url: '/monitoring/metrics/business',
      method: 'get',
    })
  })
})
