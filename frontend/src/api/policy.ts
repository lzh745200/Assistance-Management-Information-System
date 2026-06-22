import api from './request'

// ── Types ──
export type PolicyCategory = string
export type PolicyStatus = 'draft' | 'active' | 'archived' | 'expired'
export type LevelConfig = {
  value: string
  label: string
  description?: string
}
export type CategoriesConfig = Record<PolicyCategory, string>
export type Policy = {
  id: number
  title: string
  content: string
  category: PolicyCategory
  level: string
  status: PolicyStatus
  effective_date?: string
  expiry_date?: string
  created_at?: string
  updated_at?: string
}
export type PolicyQuery = {
  keyword?: string
  category?: PolicyCategory
  level?: string
  status?: PolicyStatus
  page?: number
  page_size?: number
}
export type PolicyCreate = Omit<Policy, 'id' | 'created_at' | 'updated_at'>
export type PolicyUpdate = Partial<PolicyCreate>
export type PolicyStatistics = {
  total: number
  by_category: Record<PolicyCategory, number>
  by_status: Record<PolicyStatus, number>
}

// ── Options ──
export const getLevelOptions = () => api.get('/policies/options/levels')
export const getStatusOptions = () => api.get('/policies/options/statuses')
export const getPolicyTypes = () => api.get('/policies/options/levels')
export const searchPolicies = (query: string) =>
  api.get('/policies/search', { params: { q: query } })

// ── Categories ──
export const getPolicyCategories = () => api.get('/policies/categories')
export const getCategoryTree = () => api.get('/policies/categories/tree')
export const createCategory = (data: any) => api.post('/policies/categories', data)
export const updateCategory = (id: number, data: any) => api.put(`/policies/categories/${id}`, data)
export const deleteCategory = (id: number) => api.delete(`/policies/categories/${id}`)

// ── Statistics ──
export const getPolicyStats = () => api.get('/policies/statistics')

// ── CRUD ──
export const getPolicies = (params?: any) => api.get('/policies', { params })
export const getPolicy = (id: number) => api.get('/policies/' + id)
export const createPolicy = (data: any) => api.post('/policies', data)
export const updatePolicy = (id: number, data: any) => api.put('/policies/' + id, data)
export const deletePolicy = (id: number) => api.delete('/policies/' + id)

// ── Publish / Archive ──
export const publishPolicy = (id: number) => api.post(`/policies/${id}/publish`)
export const archivePolicy = (id: number) => api.post(`/policies/${id}/archive`)

// ── File upload / preview / download ──
export const uploadPolicyFile = (policyId: number, file: File) => {
  const fd = new FormData()
  fd.append('file', file)
  return api.post(`/policies/${policyId}/upload`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const previewPolicyFile = (policyId: number) => api.get(`/policies/${policyId}/preview`)
export const downloadPolicyFile = (policyId: number) =>
  api.get(`/policies/${policyId}/download`, { responseType: 'blob' })

// ── Favorites ──
export const addPolicyFavorite = (policyId: number) => api.post(`/policies/${policyId}/favorite`)
export const removePolicyFavorite = (policyId: number) =>
  api.delete(`/policies/${policyId}/favorite`)
export const getPolicyFavorites = (userId: number | string) =>
  api.get(`/policies/user/${userId}/favorites`)

// ── Related ──
export const getPolicyRelated = (policyId: number) => api.get(`/policies/${policyId}/related`)

// ── Batch delete ──
export const batchDeletePolicies = (ids: number[]) => api.post('/policies/batch-delete', { ids })

// ── Import/export ──
export const importPolicies = (file: File) => {
  const fd = new FormData()
  fd.append('file', file)
  return api.post('/policies/import', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const exportPolicies = (params?: any) =>
  api.get('/policies/export/excel', { params, responseType: 'blob' })
export const exportPoliciesPDF = (params?: any) =>
  api.get('/policies/export/pdf', { params, responseType: 'blob' })
export const exportPoliciesWPS = (params?: any) =>
  api.get('/policies/export/wps', { params, responseType: 'blob' })
export const downloadImportTemplate = () =>
  api.get('/import/template', {
    params: { entity_type: 'policy' },
    responseType: 'blob',
  })

// ── Display helpers (used by views for status/label formatting) ──
const CATEGORY_LABELS: Record<string, string> = {}
const LEVEL_LABELS: Record<string, string> = {}
const STATUS_LABELS: Record<string, string> = {}
const STATUS_COLORS: Record<string, string> = {}

export const getCategoryLabel = (cat: string) => CATEGORY_LABELS[cat] || cat
export const getLevelLabel = (level: string) => LEVEL_LABELS[level] || level
export const getStatusLabel = (status: string) => STATUS_LABELS[status] || status
export const getStatusColor = (status: string) => STATUS_COLORS[status] || 'info'
