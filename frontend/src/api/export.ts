/**
 * 导出 API
 */
import request from './request'

export interface ExportTask {
  id: string
  status: string
  filename: string
  file_size?: number
  created_at: string
  completed_at?: string
}

export interface ExportFilterParams {
  village_ids?: number[]
  date_from?: string
  date_to?: string
  type?: string
  format?: string
}

const EXPORT_BASE = '/export'
const ASYNC_EXPORT_BASE = '/async-export'

export async function exportVillages(params: ExportFilterParams) {
  const res = await request.get(`${EXPORT_BASE}/villages`, {
    params,
    responseType: 'blob',
  })
  return res.data
}

export async function getExportTasks(params?: { page?: number; page_size?: number }) {
  const res = await request.get(`${ASYNC_EXPORT_BASE}/tasks`, { params })
  return res.data
}

export async function getExportStatus(taskId: string) {
  const res = await request.get(`${ASYNC_EXPORT_BASE}/status/${taskId}`)
  return res.data
}

export async function getExportHistory(params?: { page?: number; page_size?: number }) {
  const res = await request.get(`${ASYNC_EXPORT_BASE}/tasks`, { params })
  return res.data
}

export async function downloadExportFile(taskId: string) {
  const res = await request.get(`${ASYNC_EXPORT_BASE}/download/${taskId}`, {
    responseType: 'blob',
  })
  return res.data
}

export function formatExportStatus(status: string): string {
  const map: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] || status
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${units[i]}`
}

export function triggerDownload(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

export async function exportReportWord(reportType: string, year?: number) {
  const res = await request.get(`${EXPORT_BASE}/report-word`, {
    params: { report_type: reportType, ...(year ? { year } : {}) },
    responseType: 'blob',
  })
  return res.data
}

export async function exportReportPdf(reportType: string, year?: number) {
  const res = await request.get(`${EXPORT_BASE}/report-pdf`, {
    params: { report_type: reportType, ...(year ? { year } : {}) },
    responseType: 'blob',
  })
  return res.data
}

export async function exportUsers(params?: ExportFilterParams) {
  const res = await request.get(`${EXPORT_BASE}/users`, {
    params,
    responseType: 'blob',
  })
  return res.data
}

export async function exportSchools(params?: ExportFilterParams) {
  const res = await request.get(`${EXPORT_BASE}/schools`, {
    params,
    responseType: 'blob',
  })
  return res.data
}

export async function exportProjects(params?: ExportFilterParams) {
  const res = await request.get(`${EXPORT_BASE}/projects`, {
    params,
    responseType: 'blob',
  })
  return res.data
}

export async function exportFunds(params?: ExportFilterParams) {
  const res = await request.get(`${EXPORT_BASE}/funds`, {
    params,
    responseType: 'blob',
  })
  return res.data
}

export async function exportComprehensive(params?: ExportFilterParams) {
  const res = await request.get(`${EXPORT_BASE}/comprehensive`, {
    params,
    responseType: 'blob',
  })
  return res.data
}
