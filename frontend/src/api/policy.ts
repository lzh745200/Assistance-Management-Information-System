import { get, post, put, del, apiRequest, downloadBlob, parseContentDisposition } from '@/api/request'

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
export const getLevelOptions = () => get('/policies/options/levels')
export const getStatusOptions = () => get('/policies/options/statuses')
export const getPolicyTypes = () => get('/policies/options/levels')
export const searchPolicies = (query: string) =>
  get('/policies/search', { q: query })

// ── Categories ──
export const getPolicyCategories = () => get('/policies/categories')
export const getCategoryTree = () => get('/policies/categories/tree')
export const createCategory = (data: any) => post('/policies/categories', data)
export const updateCategory = (id: number, data: any) => put(`/policies/categories/${id}`, data)
export const deleteCategory = (id: number) => del(`/policies/categories/${id}`)

// ── Statistics ──
export const getPolicyStats = () => get('/policies/statistics')

// ── CRUD ──
export const getPolicies = (params?: any) => get('/policies', { params })
export const getPolicy = (id: number) => get('/policies/' + id)
export const createPolicy = (data: any) => post('/policies', data)
export const updatePolicy = (id: number, data: any) => put('/policies/' + id, data)
export const deletePolicy = (id: number) => del('/policies/' + id)

// ── Publish / Archive ──
export const publishPolicy = (id: number) => post(`/policies/${id}/publish`)
export const archivePolicy = (id: number) => post(`/policies/${id}/archive`)

// ── File upload / preview / download ──
export const uploadPolicyFile = (policyId: number, file: File) => {
  const fd = new FormData()
  fd.append('file', file)
  return post(`/policies/${policyId}/upload`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const previewPolicyFile = (policyId: number) => get(`/policies/${policyId}/preview`)
export const downloadPolicyFile = (policyId: number) =>
  apiRequest({ method: 'GET', url: `/policies/${policyId}/download`, responseType: 'blob' })

// ── Favorites ──
export const addPolicyFavorite = (policyId: number) => post(`/policies/${policyId}/favorite`)
export const removePolicyFavorite = (policyId: number) =>
  del(`/policies/${policyId}/favorite`)
export const getPolicyFavorites = (userId: number | string) =>
  get(`/policies/user/${userId}/favorites`)

// ── Related ──
export const getPolicyRelated = (policyId: number) => get(`/policies/${policyId}/related`)

// ── Batch delete ──
export const batchDeletePolicies = (ids: number[]) => post('/policies/batch-delete', { ids })

// ── Import/export ──
export const importPolicies = (file: File) => {
  const fd = new FormData()
  fd.append('file', file)
  return post('/policies/import', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const exportPolicies = (params?: any) =>
  apiRequest({ method: 'GET', url: '/policies/export/excel', params, responseType: 'blob' }).then((r) => {
    const filename = parseContentDisposition(
      r.headers as Record<string, string>,
      '政策法规导出.xlsx'
    )
    downloadBlob(r.data, filename)
  })
export const exportPoliciesPDF = (params?: any) =>
  apiRequest({ method: 'GET', url: '/policies/export/pdf', params, responseType: 'blob' }).then((r) => {
    const filename = parseContentDisposition(
      r.headers as Record<string, string>,
      `政策法规_${new Date().getTime()}.pdf`
    )
    downloadBlob(r.data, filename)
  })
export const exportPoliciesWPS = (params?: any) =>
  apiRequest({ method: 'GET', url: '/policies/export/wps', params, responseType: 'blob' }).then((r) => {
    const filename = parseContentDisposition(
      r.headers as Record<string, string>,
      `政策法规_${new Date().getTime()}.wps`
    )
    downloadBlob(r.data, filename)
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
