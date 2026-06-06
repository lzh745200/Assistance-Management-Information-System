import { describe, it, expect, vi } from 'vitest'
import { useConfirm } from '@/composables/useConfirm'

vi.mock('element-plus', () => ({
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

import { ElMessageBox } from 'element-plus'

describe('useConfirm', () => {
  it('用户在确认对话框中点击确定时返回 true', async () => {
    vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce({} as any)
    const { confirm } = useConfirm()
    const result = await confirm({ message: '确定执行?' })
    expect(result).toBe(true)
  })

  it('用户点击取消时返回 false', async () => {
    vi.mocked(ElMessageBox.confirm).mockRejectedValueOnce(new Error('cancel'))
    const { confirm } = useConfirm()
    const result = await confirm({ message: '确定执行?' })
    expect(result).toBe(false)
  })

  it('使用默认 title/buttons/type', async () => {
    vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce({} as any)
    const { confirm } = useConfirm()
    await confirm({ message: 'msg' })
    expect(ElMessageBox.confirm).toHaveBeenCalledWith(
      'msg',
      '确认',
      expect.objectContaining({
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
    )
  })

  it('支持自定义 title', async () => {
    vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce({} as any)
    const { confirm } = useConfirm()
    await confirm({ message: 'msg', title: 'Custom Title' })
    expect(ElMessageBox.confirm).toHaveBeenCalledWith(
      'msg',
      'Custom Title',
      expect.any(Object)
    )
  })

  it('支持自定义按钮文本', async () => {
    vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce({} as any)
    const { confirm } = useConfirm()
    await confirm({
      message: 'msg',
      confirmButtonText: 'OK',
      cancelButtonText: 'No',
    })
    expect(ElMessageBox.confirm).toHaveBeenCalledWith(
      'msg',
      '确认',
      expect.objectContaining({
        confirmButtonText: 'OK',
        cancelButtonText: 'No',
      })
    )
  })

  it('支持自定义 type', async () => {
    vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce({} as any)
    const { confirm } = useConfirm()
    await confirm({ message: 'msg', type: 'error' })
    expect(ElMessageBox.confirm).toHaveBeenCalledWith(
      'msg',
      '确认',
      expect.objectContaining({ type: 'error' })
    )
  })
})
