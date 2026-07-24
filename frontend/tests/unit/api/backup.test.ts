import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockDel } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockDel: vi.fn(),
}))

// src/api/backup.ts 实际 import：import { get, post, del } from '@/api/request'
vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  del: mockDel,
}))

import {
  getBackupList,
  createBackup,
  restoreBackup,
  deleteBackup,
  getBackupStats,
} from '@/api/backup'

describe('api/backup', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getBackupList 调用 GET /system/backup 并透传分页参数与返回值', async () => {
    const body = { items: [], total: 0 }
    mockGet.mockResolvedValue(body)
    const result = await getBackupList({ page: 1, page_size: 20 })
    expect(mockGet).toHaveBeenCalledWith('/system/backup', { page: 1, page_size: 20 })
    expect(result).toBe(body)
  })

  it('createBackup 调用 POST /system/backup 并透传载荷', async () => {
    const body = { success: true }
    mockPost.mockResolvedValue(body)
    const data = { description: '手动备份', include_uploads: true }
    const result = await createBackup(data)
    expect(mockPost).toHaveBeenCalledWith('/system/backup', data)
    expect(result).toBe(body)
  })

  it('restoreBackup 调用 POST /system/backup/restore 带 filename 与 password', async () => {
    const body = { success: true }
    mockPost.mockResolvedValue(body)
    const result = await restoreBackup('backup-2024.zip', 'secret')
    expect(mockPost).toHaveBeenCalledWith('/system/backup/restore', {
      filename: 'backup-2024.zip',
      password: 'secret',
    })
    expect(result).toBe(body)
  })

  it('deleteBackup 调用 DELETE /system/backup/{filename}', async () => {
    mockDel.mockResolvedValue({ success: true })
    await deleteBackup('backup-2024.zip')
    expect(mockDel).toHaveBeenCalledWith('/system/backup/backup-2024.zip')
  })

  it('getBackupStats 调用 GET /system/backup/stats 并透传返回值', async () => {
    const body = { total_backups: 3, total_size: 1024, auto_backup_enabled: true }
    mockGet.mockResolvedValue(body)
    const result = await getBackupStats()
    expect(mockGet).toHaveBeenCalledWith('/system/backup/stats')
    expect(result).toBe(body)
  })
})
