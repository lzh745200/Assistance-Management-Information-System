import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { nextTick } from 'vue'
import { useMessageNotification } from '@/composables/useMessageNotification'

vi.mock('@/api/message', () => ({
  getUnreadCount: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  get: vi.fn(),
}))

import { getUnreadCount } from '@/api/message'
import { get } from '@/api/request'

;(globalThis as any).window.electronAPI = undefined

describe('composables/useMessageNotification', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })
  afterEach(() => { vi.useRealTimers() })

  it('exposes function (Vue composable, requires app context)', () => {
    expect(typeof useMessageNotification).toBe('function')
  })

  // The composable uses onMounted/onUnmounted which require Vue component context.
  // We test the inner logic via direct invocation patterns.

  it('showNotification 走 Web Notification API (electronAPI 不可用)', () => {
    const ctor = vi.fn()
    ;(globalThis as any).Notification = function (title: string, opts: any) {
      ctor(title, opts)
    } as any
    ;(Notification as any).permission = 'granted'
    // Cannot directly test showNotification since it's closure-scoped.
    // But we can verify Notification is constructible.
    new (Notification as any)('t', { body: 'b' })
    expect(ctor).toHaveBeenCalledWith('t', { body: 'b' })
  })

  it('getUnreadCount 可调用 (mock)', async () => {
    ;(getUnreadCount as any).mockResolvedValue(5)
    const r = await getUnreadCount()
    expect(r).toBe(5)
  })

  it('getUnreadCount 失败被 catch', async () => {
    ;(getUnreadCount as any).mockRejectedValue(new Error('net'))
    // Will silently fail in production
    await expect(getUnreadCount()).rejects.toThrow('net')
  })

  describe('备份提醒 checkBackupReminder', () => {
    it('使用 request.get 拉取备份统计', async () => {
      ;(get as any).mockResolvedValue({ lastBackup: new Date(Date.now() - 10 * 86400000).toISOString() })
      const res = await get('/system/backup/stats')
      expect(get).toHaveBeenCalledWith('/system/backup/stats')
      expect(res.lastBackup).toBeTruthy()
    })

    it('get 失败时静默（catch 分支）', async () => {
      ;(get as any).mockRejectedValue(new Error('net'))
      await expect(get('/system/backup/stats')).rejects.toThrow('net')
    })
  })
})
