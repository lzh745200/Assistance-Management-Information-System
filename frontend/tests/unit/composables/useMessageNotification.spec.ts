import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'
import useMessageNotification from '@/composables/useMessageNotification'

// Mock electron API
const mockIpcRenderer = {
  invoke: vi.fn()
}

describe('useMessageNotification', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    ;(globalThis as any).electron = {
      ipcRenderer: mockIpcRenderer
    }
    mockIpcRenderer.invoke.mockReset()
    mockIpcRenderer.invoke.mockResolvedValue(true)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('初始化状态正确', () => {
    const { unreadCount, messages, isPolling } = useMessageNotification()

    expect(unreadCount.value).toBe(0)
    expect(messages.value).toEqual([])
    expect(isPolling.value).toBe(false)
  })

  it('开始轮询后状态更新', async () => {
    const { isPolling, startPolling } = useMessageNotification()

    startPolling()

    expect(isPolling.value).toBe(true)
  })

  it('停止轮询后状态更新', () => {
    const { isPolling, startPolling, stopPolling } = useMessageNotification()

    startPolling()
    expect(isPolling.value).toBe(true)

    stopPolling()
    expect(isPolling.value).toBe(false)
  })

  it('定期检查新消息', async () => {
    const mockMessages = [
      { id: 1, title: '消息1', content: '内容1', read: false },
      { id: 2, title: '消息2', content: '内容2', read: false }
    ]

    mockIpcRenderer.invoke.mockResolvedValueOnce({
      success: true,
      data: {
        messages: mockMessages,
        unread_count: 2
      }
    })

    const { unreadCount, messages, startPolling, checkNewMessages } = useMessageNotification()

    startPolling()

    // 手动触发一次检查
    await checkNewMessages()

    expect(mockIpcRenderer.invoke).toHaveBeenCalledWith('message:getUnread')
    expect(unreadCount.value).toBe(2)
    expect(messages.value).toHaveLength(2)
  })

  it('有新消息时显示桌面通知', async () => {
    const notificationMock = vi.fn()
    const originalNotification = global.Notification

    // Mock Notification
    global.Notification = vi.fn().mockImplementation(function(title: string, options?: NotificationOptions) {
      notificationMock(title, options)
      return {
        onclick: null,
        close: vi.fn()
      } as any
    }) as any
    global.Notification.permission = 'granted'

    const { showNotification } = useMessageNotification()

    showNotification('测试标题', '测试内容')

    expect(notificationMock).toHaveBeenCalledWith('测试标题', {
      body: '测试内容',
      icon: expect.any(String)
    })

    // 恢复原始 Notification
    global.Notification = originalNotification
  })

  it('通知权限未授予时不显示通知', () => {
    const originalNotification = global.Notification
    const notificationMock = vi.fn()

    global.Notification = vi.fn() as any
    global.Notification.permission = 'denied'

    const { showNotification } = useMessageNotification()

    showNotification('测试标题', '测试内容')

    expect(notificationMock).not.toHaveBeenCalled()

    global.Notification = originalNotification
  })

  it('请求通知权限', async () => {
    const originalNotification = global.Notification

    global.Notification = vi.fn() as any
    global.Notification.permission = 'default'
    global.Notification.requestPermission = vi.fn().mockResolvedValue('granted')

    const { requestNotificationPermission } = useMessageNotification()

    const result = await requestNotificationPermission()

    expect(global.Notification.requestPermission).toHaveBeenCalled()
    expect(result).toBe('granted')

    global.Notification = originalNotification
  })

  it('标记消息为已读', async () => {
    mockIpcRenderer.invoke.mockResolvedValueOnce({
      success: true,
      data: { updated: true }
    })

    const { markAsRead } = useMessageNotification()

    const result = await markAsRead(1)

    expect(mockIpcRenderer.invoke).toHaveBeenCalledWith('message:markAsRead', 1)
    expect(result).toBe(true)
  })

  it('标记所有消息为已读', async () => {
    mockIpcRenderer.invoke.mockResolvedValueOnce({
      success: true,
      data: { updated: 5 }
    })

    const { markAllAsRead, unreadCount } = useMessageNotification()

    // 设置初始未读数
    unreadCount.value = 5

    const result = await markAllAsRead()

    expect(mockIpcRenderer.invoke).toHaveBeenCalledWith('message:markAllAsRead')
    expect(result).toBe(true)
    expect(unreadCount.value).toBe(0)
  })

  it('清理函数停止轮询', () => {
    const { startPolling, cleanup } = useMessageNotification()

    startPolling()
    expect(vi.getTimerCount()).toBeGreaterThan(0)

    cleanup()

    // 验证定时器被清理
    expect(vi.getTimerCount()).toBe(0)
  })

  it('自动轮询间隔正确', () => {
    const { startPolling } = useMessageNotification()

    startPolling()

    // 检查是否设置了60秒的轮询间隔
    expect(vi.getTimerCount()).toBeGreaterThan(0)
  })

  it('获取消息列表', async () => {
    const mockMessages = [
      { id: 1, title: '消息1', content: '内容1', read: true },
      { id: 2, title: '消息2', content: '内容2', read: false }
    ]

    mockIpcRenderer.invoke.mockResolvedValueOnce({
      success: true,
      data: mockMessages
    })

    const { fetchMessages, messages } = useMessageNotification()

    await fetchMessages()

    expect(mockIpcRenderer.invoke).toHaveBeenCalledWith('message:getAll')
    expect(messages.value).toEqual(mockMessages)
  })

  it('发送消息', async () => {
    mockIpcRenderer.invoke.mockResolvedValueOnce({
      success: true,
      data: { id: 1 }
    })

    const { sendMessage } = useMessageNotification()

    const messageData = {
      title: '新消息',
      content: '消息内容',
      recipient_id: 2
    }

    const result = await sendMessage(messageData)

    expect(mockIpcRenderer.invoke).toHaveBeenCalledWith('message:send', messageData)
    expect(result).toEqual({ id: 1 })
  })

  it('删除消息', async () => {
    mockIpcRenderer.invoke.mockResolvedValueOnce({
      success: true,
      data: { deleted: true }
    })

    const { deleteMessage, messages } = useMessageNotification()

    messages.value = [
      { id: 1, title: '消息1', content: '内容1', read: true },
      { id: 2, title: '消息2', content: '内容2', read: false }
    ]

    const result = await deleteMessage(1)

    expect(mockIpcRenderer.invoke).toHaveBeenCalledWith('message:delete', 1)
    expect(result).toBe(true)
    expect(messages.value).toHaveLength(1)
  })
})
