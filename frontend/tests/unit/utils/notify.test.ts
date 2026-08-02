import { describe, it, expect, vi, beforeEach } from 'vitest'

const { elNotificationMock } = vi.hoisted(() => {
  const fn = vi.fn((opts: any) => opts)
  fn.success = vi.fn((opts: any) => opts)
  fn.error = vi.fn((opts: any) => opts)
  fn.warning = vi.fn((opts: any) => opts)
  fn.info = vi.fn((opts: any) => opts)
  fn.closeAll = vi.fn()
  return { elNotificationMock: fn }
})

vi.mock('element-plus', () => ({
  ElNotification: elNotificationMock,
}))

import { notify } from '@/utils/notify'
import notifyDefault from '@/utils/notify'

const DEFAULTS = { showClose: true, duration: 5000 }

describe('utils/notify', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('默认导出即 notify 函数', () => {
    expect(notifyDefault).toBe(notify)
  })

  describe('notify', () => {
    it('字符串参数转换为 message', () => {
      notify('操作成功')
      expect(elNotificationMock).toHaveBeenCalledWith({ ...DEFAULTS, message: '操作成功' })
    })

    it('对象参数合并全局默认值', () => {
      notify({ type: 'error', title: '错误', message: 'x' })
      expect(elNotificationMock).toHaveBeenCalledWith({
        ...DEFAULTS,
        type: 'error',
        title: '错误',
        message: 'x',
      })
    })

    it('空参数仅使用默认值', () => {
      notify()
      expect(elNotificationMock).toHaveBeenCalledWith({ ...DEFAULTS, message: undefined })
    })
  })

  describe('notify.success', () => {
    it('字符串参数', () => {
      notify.success('成功')
      expect(elNotificationMock.success).toHaveBeenCalledWith({ ...DEFAULTS, message: '成功' })
    })

    it('对象参数', () => {
      notify.success({ title: 't' })
      expect(elNotificationMock.success).toHaveBeenCalledWith({ ...DEFAULTS, title: 't' })
    })
  })

  describe('notify.error', () => {
    it('字符串参数', () => {
      notify.error('失败')
      expect(elNotificationMock.error).toHaveBeenCalledWith({ ...DEFAULTS, message: '失败' })
    })

    it('对象参数', () => {
      notify.error({ message: 'm' })
      expect(elNotificationMock.error).toHaveBeenCalledWith({ ...DEFAULTS, message: 'm' })
    })
  })

  describe('notify.warning', () => {
    it('字符串参数', () => {
      notify.warning('警告')
      expect(elNotificationMock.warning).toHaveBeenCalledWith({ ...DEFAULTS, message: '警告' })
    })

    it('对象参数', () => {
      notify.warning({ title: 'w' })
      expect(elNotificationMock.warning).toHaveBeenCalledWith({ ...DEFAULTS, title: 'w' })
    })
  })

  describe('notify.info', () => {
    it('字符串参数', () => {
      notify.info('提示')
      expect(elNotificationMock.info).toHaveBeenCalledWith({ ...DEFAULTS, message: '提示' })
    })

    it('对象参数', () => {
      notify.info({ title: 'i' })
      expect(elNotificationMock.info).toHaveBeenCalledWith({ ...DEFAULTS, title: 'i' })
    })
  })

  it('closeAll 委托 ElNotification.closeAll', () => {
    notify.closeAll()
    expect(elNotificationMock.closeAll).toHaveBeenCalled()
  })
})
