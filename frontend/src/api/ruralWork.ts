import api from './request'

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
  api.get('/rural-works', { params }).then((r: any) => r.data)

export const createRuralWork = (data: any) =>
  api.post('/rural-works', data).then((r: any) => r.data)

export const updateRuralWork = (id: number, data: any) =>
  api.put('/rural-works/' + id, data).then((r: any) => r.data)

export const deleteRuralWork = (id: number) =>
  api.delete('/rural-works/' + id).then((r: any) => r.data)

export const generateWorkReport = (params?: any) =>
  api.get('/rural-works/report/generate', { params }).then((r: any) => r.data)

// Backward-compatible object form
export const ruralWorkApi = {
  list: (params?: any) => api.get('/rural-works', { params }).then((r: any) => r.data),
  get: (id: number) => api.get('/rural-works/' + id).then((r: any) => r.data),
  getById: (id: number) => api.get('/rural-works/' + id).then((r: any) => r.data),
  create: (data: any) => api.post('/rural-works', data).then((r: any) => r.data),
  update: (id: number, data: any) => api.put('/rural-works/' + id, data).then((r: any) => r.data),
  delete: deleteRuralWork,
  getRuralWorks,
  createRuralWork,
  updateRuralWork,
  deleteRuralWork,
  generateWorkReport,
  getStatistics: () => api.get('/rural-works/statistics/summary'),
  getVillagesForSelect: () => api.get('/rural-works/villages'),
  getAvailableYears: () => api.get('/rural-works/years'),
  batchDelete: (ids: number[]) => api.post('/rural-works/batch-delete', { ids }),
}
