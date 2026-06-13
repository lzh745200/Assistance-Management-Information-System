import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPut = vi.fn()
const mockDelete = vi.fn()

vi.mock('@/utils/request', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
    put: (...args: any[]) => mockPut(...args),
    delete: (...args: any[]) => mockDelete(...args),
  },
}))
vi.mock('@/api/request', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
    put: (...args: any[]) => mockPut(...args),
    delete: (...args: any[]) => mockDelete(...args),
  },
}))

import {
  getBackupList,
  createBackup,
  restoreBackup,
  deleteBackup,
  getBackupStats,
} from '@/api/backup'
import { projectMilestonesApi } from '@/api/projectMilestones'

describe('api/backup', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getBackupList GET /system/backups', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [] } })
    await getBackupList({ page: 1 })
    expect(mockGet).toHaveBeenCalledWith('/system/backups', { params: { page: 1 } })
  })

  it('createBackup POST /system/backup', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await createBackup('full')
    expect(mockPost).toHaveBeenCalledWith('/system/backup', { type: 'full' })
  })

  it('restoreBackup POST /system/restore with filename param', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    await restoreBackup('backup_2024.db')
    expect(mockPost).toHaveBeenCalledWith('/system/restore', null, {
      params: { filename: 'backup_2024.db' },
    })
  })

  it('deleteBackup DELETE /system/backups/{filename}', async () => {
    mockDelete.mockResolvedValueOnce({ data: { success: true } })
    await deleteBackup('backup_2024.db')
    expect(mockDelete).toHaveBeenCalledWith('/system/backups/backup_2024.db')
  })

  it('getBackupStats GET /system/backup/stats', async () => {
    mockGet.mockResolvedValueOnce({ data: { total_backups: 5 } })
    await getBackupStats()
    expect(mockGet).toHaveBeenCalledWith('/system/backup/stats')
  })
})

describe('api/projectMilestones', () => {
  beforeEach(() => vi.clearAllMocks())

  it('list GET milestones', () => {
    projectMilestonesApi.list(5)
    expect(mockGet).toHaveBeenCalledWith('/projects/5/milestones')
  })

  it('create POST', () => {
    projectMilestonesApi.create(5, { name: 'M1' })
    expect(mockPost).toHaveBeenCalledWith('/projects/5/milestones', { name: 'M1' })
  })

  it('update PUT', () => {
    projectMilestonesApi.update(5, 1, { name: 'M2' })
    expect(mockPut).toHaveBeenCalledWith('/projects/5/milestones/1', { name: 'M2' })
  })

  it('delete DELETE', () => {
    projectMilestonesApi.delete(5, 1)
    expect(mockDelete).toHaveBeenCalledWith('/projects/5/milestones/1')
  })
})
