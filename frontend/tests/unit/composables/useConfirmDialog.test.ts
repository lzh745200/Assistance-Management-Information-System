import { describe, it, expect } from 'vitest'
import { useConfirmDialog } from '@/composables/useConfirmDialog'

describe('composables/useConfirmDialog', () => {
  it('initial state', () => {
    const d = useConfirmDialog()
    expect(d.isVisible.value).toBe(false)
    expect(d.options.title).toBe('确认')
    expect(d.options.confirmText).toBe('确定')
    expect(d.options.cancelText).toBe('取消')
    expect(d.options.showCancel).toBe(true)
    expect(d.options.type).toBe('info')
  })

  it('confirm sets visible + merges options', async () => {
    const d = useConfirmDialog()
    const p = d.confirm({ message: 'Are you sure?', type: 'warning', title: 'T', confirmText: 'OK' })
    expect(d.isVisible.value).toBe(true)
    expect(d.options.message).toBe('Are you sure?')
    expect(d.options.type).toBe('warning')
    expect(d.options.title).toBe('T')
    expect(d.options.confirmText).toBe('OK')
    d.handleCancel()  // resolve to clean up
    await p
  })

  it('handleConfirm resolves true', async () => {
    const d = useConfirmDialog()
    const p = d.confirm({ message: 'm' })
    d.handleConfirm()
    expect(d.isVisible.value).toBe(false)
    expect(await p).toBe(true)
  })

  it('handleCancel resolves false', async () => {
    const d = useConfirmDialog()
    const p = d.confirm({ message: 'm' })
    d.handleCancel()
    expect(d.isVisible.value).toBe(false)
    expect(await p).toBe(false)
  })

  it('handleConfirm/Cancel without pending -> no error', () => {
    const d = useConfirmDialog()
    d.handleConfirm()
    d.handleCancel()
  })
})
