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
  verifyBackup,
  getBackupStats,
  cleanupOldBackups,
} from '@/api/backup'
import { projectMilestonesApi } from '@/api/projectMilestones'

describe('api/backup', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getBackupList GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [] } })
    await getBackupList({ page: 1 })
    expect(mockGet).toHaveBeenCalledWith('/system/backup', { params: { page: 1 } })
  })

  it('createBackup POST 含 type', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await createBackup('full')
    expect(mockPost).toHaveBeenCalledWith('/system/backup', { type: 'full' })
  })

  it('restoreBackup POST', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true } })
    await restoreBackup(1)
    expect(mockPost).toHaveBeenCalledWith('/system/backup/1/restore')
  })

  it('deleteBackup DELETE', async () => {
    mockDelete.mockResolvedValueOnce({ data: { success: true } })
    await deleteBackup(1)
    expect(mockDelete).toHaveBeenCalledWith('/system/backup/1')
  })

  it('verifyBackup POST', async () => {
    mockPost.mockResolvedValueOnce({ data: { valid: true } })
    await verifyBackup(1)
    expect(mockPost).toHaveBeenCalledWith('/system/backup/1/verify')
  })

  it('getBackupStats GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { total_backups: 5 } })
    await getBackupStats()
    expect(mockGet).toHaveBeenCalledWith('/system/backup/stats')
  })

  it('cleanupOldBackups 默认 retention 30', async () => {
    mockDelete.mockResolvedValueOnce({ data: { deleted: 3 } })
    await cleanupOldBackups()
    expect(mockDelete).toHaveBeenCalledWith('/system/backup/cleanup', { params: { retention_days: 30 } })
  })

  it('cleanupOldBackups 自定义 retention', async () => {
    mockDelete.mockResolvedValueOnce({ data: { deleted: 3 } })
    await cleanupOldBackups(60)
    expect(mockDelete).toHaveBeenCalledWith('/system/backup/cleanup', { params: { retention_days: 60 } })
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
