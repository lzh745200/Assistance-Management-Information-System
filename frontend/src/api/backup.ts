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

const BASE = '/system'

export async function getBackupList(params?: { page?: number; page_size?: number }) {
  const res = await get(`${BASE}/backups`, { params })
  return res.data
}

export async function createBackup(type?: string) {
  const res = await post(`${BASE}/backup`, { type })
  return res.data
}

export async function restoreBackup(filename: string) {
  const res = await post(`${BASE}/backup/restore`, { filename })
  return res.data
}

export async function deleteBackup(filename: string) {
  const res = await del(`${BASE}/backups/${filename}`)
  return res.data
}

export async function getBackupStats(): Promise<BackupStats> {
  const res = await get(`${BASE}/backup/stats`)
  return res.data
}
