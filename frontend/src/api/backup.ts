/**
 * 备份 API
 */
import { get, post, del } from '@/api/request'

export interface BackupItem {
  filename: string
  size: number
  file_size: number
  created_at: string
  id?: string | number
}

export interface BackupStats {
  total_backups: number
  total_size: number
  auto_backup_enabled: boolean
  totalBackups?: number
  lastBackup?: string
  totalSize?: number
}

const BASE = '/system/backup'

export interface CreateBackupPayload {
  description?: string
  include_uploads?: boolean
  password?: string
}

export async function getBackupList(params?: { page?: number; page_size?: number }) {
  return get(BASE, params)
}

export async function createBackup(data: CreateBackupPayload) {
  return post(BASE, data)
}

export async function restoreBackup(filename: string, password?: string) {
  return post(`${BASE}/restore`, { filename, password })
}

export async function deleteBackup(filename: string) {
  return del(`${BASE}/${filename}`)
}

export async function getBackupStats(): Promise<BackupStats> {
  const res = await get(`${BASE}/stats`)
  return res.data
}
