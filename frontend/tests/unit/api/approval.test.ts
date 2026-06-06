import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPut = vi.fn()
const mockDel = vi.fn()

vi.mock('@/utils/request', () => ({
  get: (...args: any[]) => mockGet(...args),
  post: (...args: any[]) => mockPost(...args),
  put: (...args: any[]) => mockPut(...args),
  del: (...args: any[]) => mockDel(...args),
}))

vi.mock('@/api/request', () => ({
  get: (...args: any[]) => mockGet(...args),
  post: (...args: any[]) => mockPost(...args),
  put: (...args: any[]) => mockPut(...args),
  del: (...args: any[]) => mockDel(...args),
}))

import {
  createWorkflow,
  getWorkflows,
  getWorkflow,
  updateWorkflow,
  deleteWorkflow,
  submitApproval,
  approveTask,
  rejectTask,
  transferTask,
  withdrawTask,
  getAllTasks,
  getPendingTasks,
  batchApprove,
  getTaskDiff,
  getApprovalHistory,
  autoApproveSingleTask,
  autoApproveAll,
  submitAndAutoApprove,
  formatApprovalStatus,
  formatApprovalAction,
  formatEntityType,
} from '@/api/approval'

describe('api/approval', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('workflows', () => {
    it('createWorkflow POST /approval/workflows', async () => {
      mockPost.mockResolvedValueOnce({ id: 1, name: 'W', level_count: 3 })
      const result = await createWorkflow({
        name: 'W',
        entity_type: 'project',
        nodes: [],
      })
      expect(mockPost).toHaveBeenCalledWith('/approval/workflows', {
        name: 'W',
        entity_type: 'project',
        nodes: [],
      })
      expect(result.level_count).toBe(3)
    })

    it('getWorkflows GET /approval/workflows 带 params', async () => {
      mockGet.mockResolvedValueOnce([])
      await getWorkflows({ entity_type: 'project', skip: 0, limit: 20 })
      expect(mockGet).toHaveBeenCalledWith('/approval/workflows', {
        params: { entity_type: 'project', skip: 0, limit: 20 },
      })
    })

    it('getWorkflows 无参时 params=undefined', async () => {
      mockGet.mockResolvedValueOnce([])
      await getWorkflows()
      expect(mockGet).toHaveBeenCalledWith('/approval/workflows', { params: undefined })
    })

    it('getWorkflow GET /approval/workflows/{id}', async () => {
      mockGet.mockResolvedValueOnce({ id: 5, name: 'W' })
      await getWorkflow(5)
      expect(mockGet).toHaveBeenCalledWith('/approval/workflows/5')
    })

    it('updateWorkflow PUT /approval/workflows/{id}', async () => {
      mockPut.mockResolvedValueOnce({ id: 5 })
      await updateWorkflow(5, { is_active: false })
      expect(mockPut).toHaveBeenCalledWith('/approval/workflows/5', { is_active: false })
    })

    it('deleteWorkflow DELETE /approval/workflows/{id}', async () => {
      mockDel.mockResolvedValueOnce(undefined)
      await deleteWorkflow(5)
      expect(mockDel).toHaveBeenCalledWith('/approval/workflows/5')
    })
  })

  describe('tasks', () => {
    it('submitApproval POST /approval/submit', async () => {
      mockPost.mockResolvedValueOnce({ task_id: 1, status: 'pending', current_level: 1 })
      const result = await submitApproval({
        entity_type: 'project',
        entity_id: 100,
        change_data: { name: 'X' },
      })
      expect(mockPost).toHaveBeenCalledWith('/approval/submit', {
        entity_type: 'project',
        entity_id: 100,
        change_data: { name: 'X' },
      })
      expect(result.status).toBe('pending')
    })

    it('approveTask POST /approval/tasks/{id}/approve', async () => {
      mockPost.mockResolvedValueOnce({ task_id: 1, status: 'approved', current_level: 2 })
      await approveTask(1, 'looks good')
      expect(mockPost).toHaveBeenCalledWith('/approval/tasks/1/approve', { opinion: 'looks good' })
    })

    it('approveTask 无 opinion', async () => {
      mockPost.mockResolvedValueOnce({ task_id: 1, status: 'approved', current_level: 2 })
      await approveTask(1)
      expect(mockPost).toHaveBeenCalledWith('/approval/tasks/1/approve', { opinion: undefined })
    })

    it('rejectTask POST /approval/tasks/{id}/reject', async () => {
      mockPost.mockResolvedValueOnce({ task_id: 1, status: 'rejected' })
      await rejectTask(1, 'not good')
      expect(mockPost).toHaveBeenCalledWith('/approval/tasks/1/reject', { opinion: 'not good' })
    })

    it('transferTask POST /approval/tasks/{id}/transfer with reason', async () => {
      mockPost.mockResolvedValueOnce({ task_id: 1, current_approver_id: 99 })
      await transferTask(1, 99, 'out of office')
      expect(mockPost).toHaveBeenCalledWith('/approval/tasks/1/transfer', {
        transfer_to_id: 99,
        reason: 'out of office',
      })
    })

    it('withdrawTask POST /approval/tasks/{id}/withdraw', async () => {
      mockPost.mockResolvedValueOnce({ task_id: 1, status: 'withdrawn' })
      await withdrawTask(1)
      expect(mockPost).toHaveBeenCalledWith('/approval/tasks/1/withdraw', {})
    })

    it('getAllTasks 返回数组 (非数组时回退为空)', async () => {
      mockGet.mockResolvedValueOnce([{ id: 1 }])
      const result = await getAllTasks({ status: 'pending' })
      expect(result).toEqual([{ id: 1 }])
    })

    it('getAllTasks 响应非数组时返回 []', async () => {
      mockGet.mockResolvedValueOnce({ items: [] })
      const result = await getAllTasks()
      expect(result).toEqual([])
    })

    it('getPendingTasks GET /approval/tasks/pending', async () => {
      mockGet.mockResolvedValueOnce([])
      await getPendingTasks({ skip: 0 })
      expect(mockGet).toHaveBeenCalledWith('/approval/tasks/pending', { params: { skip: 0 } })
    })

    it('batchApprove POST /approval/tasks/batch with task_ids array', async () => {
      mockPost.mockResolvedValueOnce({ success: [1, 2], failed: [] })
      await batchApprove([1, 2, 3], 'OK')
      expect(mockPost).toHaveBeenCalledWith('/approval/tasks/batch', {
        task_ids: [1, 2, 3],
        opinion: 'OK',
      })
    })

    it('getTaskDiff GET /approval/tasks/{id}/diff', async () => {
      mockGet.mockResolvedValueOnce({ changes: [] })
      await getTaskDiff(5)
      expect(mockGet).toHaveBeenCalledWith('/approval/tasks/5/diff')
    })

    it('getApprovalHistory GET /approval/history', async () => {
      mockGet.mockResolvedValueOnce([{ id: 1 }])
      await getApprovalHistory({ entity_type: 'project' })
      expect(mockGet).toHaveBeenCalledWith('/approval/history', {
        params: { entity_type: 'project' },
      })
    })
  })

  describe('auto-approve (单机版)', () => {
    it('autoApproveSingleTask POST /approval/tasks/{id}/auto-approve', async () => {
      mockPost.mockResolvedValueOnce({ task_id: 1, status: 'approved' })
      await autoApproveSingleTask(1, 'fast')
      expect(mockPost).toHaveBeenCalledWith('/approval/tasks/1/auto-approve', { opinion: 'fast' })
    })

    it('autoApproveAll POST /approval/tasks/auto-approve-all', async () => {
      mockPost.mockResolvedValueOnce({ success: [1, 2], failed: [3] })
      const result = await autoApproveAll()
      expect(mockPost).toHaveBeenCalledWith('/approval/tasks/auto-approve-all', { opinion: undefined })
      expect(result.success).toEqual([1, 2])
    })

    it('submitAndAutoApprove POST /approval/submit-auto', async () => {
      mockPost.mockResolvedValueOnce({ task_id: 1, status: 'approved' })
      await submitAndAutoApprove({
        entity_type: 'project',
        entity_id: 1,
        change_data: {},
      })
      expect(mockPost).toHaveBeenCalledWith('/approval/submit-auto', {
        entity_type: 'project',
        entity_id: 1,
        change_data: {},
      })
    })
  })

  describe('formatters', () => {
    it('formatApprovalStatus 已知状态', () => {
      expect(formatApprovalStatus('pending')).toEqual({ text: '待审批', type: 'warning' })
      expect(formatApprovalStatus('approved')).toEqual({ text: '已通过', type: 'success' })
      expect(formatApprovalStatus('rejected')).toEqual({ text: '已拒绝', type: 'danger' })
      expect(formatApprovalStatus('withdrawn')).toEqual({ text: '已撤回', type: 'info' })
    })

    it('formatApprovalStatus 未知状态回退', () => {
      expect(formatApprovalStatus('xyz')).toEqual({ text: 'xyz', type: 'info' })
    })

    it('formatApprovalAction 已知操作', () => {
      expect(formatApprovalAction('approve')).toBe('通过')
      expect(formatApprovalAction('reject')).toBe('拒绝')
      expect(formatApprovalAction('transfer')).toBe('转交')
    })

    it('formatApprovalAction 未知操作回退原值', () => {
      expect(formatApprovalAction('xyz')).toBe('xyz')
    })

    it('formatEntityType 已知类型', () => {
      expect(formatEntityType('supported_village')).toBe('帮扶村')
      expect(formatEntityType('project')).toBe('项目')
      expect(formatEntityType('fund')).toBe('经费')
      expect(formatEntityType('school')).toBe('学校')
    })

    it('formatEntityType 未知类型回退原值', () => {
      expect(formatEntityType('xyz')).toBe('xyz')
    })
  })
})
