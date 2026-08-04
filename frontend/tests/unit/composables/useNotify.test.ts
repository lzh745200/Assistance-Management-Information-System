import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('element-plus', () => ({
  ElMessage: vi.fn(),
  ElNotification: vi.fn(),
}))

import { ElMessage, ElNotification } from 'element-plus'
import { notify } from '@/composables/useNotify'

describe('useNotify/notify', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('silent() 不产生任何通知', () => {
    expect(() => notify.silent()).not.toThrow()
    expect(ElMessage).not.toHaveBeenCalled()
    expect(ElNotification).not.toHaveBeenCalled()
  })

  it('success() 使用 2s 成功提示', () => {
    notify.success('已保存')
    expect(ElMessage).toHaveBeenCalledWith({
      type: 'success',
      message: '已保存',
      duration: 2000,
    })
  })

  it('error(string) 使用 5s 错误提示', () => {
    notify.error('操作失败')
    expect(ElMessage).toHaveBeenCalledWith({
      type: 'error',
      message: '操作失败',
      duration: 5000,
    })
  })

  it('error(axios err) 优先提取 response.data.detail', () => {
    notify.error({ response: { data: { detail: '后端返回的错误详情' } } })
    expect(ElMessage).toHaveBeenCalledWith(
      expect.objectContaining({ message: '后端返回的错误详情' })
    )
  })

  it('error(err with message) 使用 err.message', () => {
    notify.error(new Error('网络异常'))
    expect(ElMessage).toHaveBeenCalledWith(
      expect.objectContaining({ message: '网络异常' })
    )
  })

  it('error(err 无 detail/message) 使用 fallback', () => {
    notify.error({ foo: 'bar' }, '自定义回退文案')
    expect(ElMessage).toHaveBeenCalledWith(
      expect.objectContaining({ message: '自定义回退文案' })
    )
  })

  it('error(err 无 detail/message 且无 fallback) 使用默认文案', () => {
    notify.error({ foo: 'bar' })
    expect(ElMessage).toHaveBeenCalledWith(
      expect.objectContaining({ message: '操作失败，请重试' })
    )
  })

  it('warn() 使用 3s 警告提示', () => {
    notify.warn('注意')
    expect(ElMessage).toHaveBeenCalledWith({
      type: 'warning',
      message: '注意',
      duration: 3000,
    })
  })

  it('done() 使用 5s 成功提示', () => {
    notify.done('导入完成：成功 42 条')
    expect(ElMessage).toHaveBeenCalledWith({
      type: 'success',
      message: '导入完成：成功 42 条',
      duration: 5000,
    })
  })

  it('system() 默认 type 为 success 且带关闭按钮', () => {
    notify.system('备份已完成', '备份数据已保存')
    expect(ElNotification).toHaveBeenCalledWith({
      title: '备份已完成',
      message: '备份数据已保存',
      type: 'success',
      duration: 5000,
      showClose: true,
    })
  })

  it('system() 支持自定义 type', () => {
    notify.system('加密失败', '密钥错误', 'error')
    expect(ElNotification).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'error' })
    )
  })
})
