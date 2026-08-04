import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
}))

import { getReminders, triggerReminderScan } from '@/api/reminders'

describe('api/reminders', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getReminders → GET /reminders', async () => {
    const body = {
      items: [
        {
          id: 1,
          type: 'approval_timeout',
          title: '审批超时',
          content: 'x',
          created_at: '2026-01-01T00:00:00',
          is_read: false,
        },
      ],
      total: 1,
      unread: 1,
    }
    mockGet.mockResolvedValueOnce(body)
    const result = await getReminders()
    expect(mockGet).toHaveBeenCalledWith('/reminders')
    expect(result).toBe(body)
  })

  it('triggerReminderScan → POST /reminders/scan', async () => {
    const body = { created: 3 }
    mockPost.mockResolvedValueOnce(body)
    const result = await triggerReminderScan()
    expect(mockPost).toHaveBeenCalledWith('/reminders/scan')
    expect(result).toBe(body)
  })

  it('reminder 项支持缺失 created_at', async () => {
    mockGet.mockResolvedValueOnce({
      items: [{ id: 2, type: 'budget_warning', title: '预算预警', content: 'y', is_read: true }],
      total: 1,
      unread: 0,
    })
    const result = await getReminders()
    expect(result.items[0].created_at).toBeUndefined()
    expect(result.unread).toBe(0)
  })
})
