import { get, post, put, del } from '@/api/request'

// Types
export type WorkStatus = 'pending' | 'in_progress' | 'completed' | 'delayed' | 'cancelled'

export type WorkType =
  | 'industry'
  | 'infrastructure'
  | 'education'
  | 'medical'
  | 'party'
  | 'consumption'
  | 'employment'
  | 'other'
  | 'party_building'
  | 'ecommerce'
  | 'talent'

export interface WorkReportData {
  summary: Record<string, any>
  details: any[]
  generated_at: string
}

// Named functions — unwrap AxiosResponse，返回 res.data
export const getRuralWorks = (params?: any) =>
  get('/rural-works', { params })

export const createRuralWork = (data: any) =>
  post('/rural-works', data)

export const updateRuralWork = (id: number, data: any) =>
  put('/rural-works/' + id, data)

export const deleteRuralWork = (id: number) =>
  del('/rural-works/' + id)

export const generateWorkReport = (params?: any) =>
  get('/rural-works/report/generate', { params })

// Backward-compatible object form
export const ruralWorkApi = {
  list: (params?: any) => get('/rural-works', { params }),
  get: (id: number) => get('/rural-works/' + id),
  getById: (id: number) => get('/rural-works/' + id),
  create: (data: any) => post('/rural-works', data),
  update: (id: number, data: any) => put('/rural-works/' + id, data),
  delete: deleteRuralWork,
  getRuralWorks,
  createRuralWork,
  updateRuralWork,
  deleteRuralWork,
  generateWorkReport,
  getStatistics: () => get('/rural-works/statistics/summary'),
  getVillagesForSelect: () => get('/rural-works/villages'),
  getAvailableYears: () => get('/rural-works/years'),
  batchDelete: (ids: number[]) => post('/rural-works/batch-delete', { ids }),
}
