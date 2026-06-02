/**
 * 备份 API
 */
import request from "./request";

export interface BackupItem {
  id: number;
  filename: string;
  file_size: number;
  status: string;
  created_at: string;
  type?: string;
}

export interface BackupStats {
  total_backups: number;
  total_size: number;
  last_backup_time?: string;
  auto_backup_enabled: boolean;
}

const BASE = "/system/backup";

export async function getBackupList(params?: { page?: number; page_size?: number }) {
  const res = await request.get(BASE, { params });
  return res.data;
}

export async function createBackup(type?: string) {
  const res = await request.post(BASE, { type });
  return res.data;
}

export async function restoreBackup(id: number) {
  const res = await request.post(`${BASE}/${id}/restore`);
  return res.data;
}

export async function deleteBackup(id: number) {
  const res = await request.delete(`${BASE}/${id}`);
  return res.data;
}

export async function verifyBackup(id: number) {
  const res = await request.post(`${BASE}/${id}/verify`);
  return res.data;
}

export async function getBackupStats(): Promise<BackupStats> {
  const res = await request.get(`${BASE}/stats`);
  return res.data;
}

export async function cleanupOldBackups(retentionDays?: number) {
  const res = await request.delete(`${BASE}/cleanup`, {
    params: { retention_days: retentionDays || 30 },
  });
  return res.data;
}
