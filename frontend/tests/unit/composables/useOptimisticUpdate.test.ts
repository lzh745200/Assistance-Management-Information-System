import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn() },
}))

import { ElMessage } from 'element-plus'
import { useOptimisticUpdate, useOptimisticRemove } from '@/composables/useOptimisticUpdate'

describe('composables/useOptimisticUpdate', () => {
  beforeEach(() => { vi.clearAllMocks() })

  describe('useOptimisticUpdate', () => {
    it('isPending/error/reset 暴露', () => {
      const u = useOptimisticUpdate(async () => {})
      expect(u.isPending.value).toBe(false)
      expect(u.error.value).toBeNull()
      u.reset()
    })

    it('execute 成功: returns true, isPending 翻转, onSuccess 调', async () => {
      const onSuccess = vi.fn()
      const fn = vi.fn(async () => 'ok')
      const u = useOptimisticUpdate(fn, { onSuccess, successMessage: 'Saved' })
      const r = await u.execute({ x: 1 })
      expect(r).toBe(true)
      expect(fn).toHaveBeenCalledWith({ x: 1 })
      expect(u.isPending.value).toBe(false)
      expect(onSuccess).toHaveBeenCalledWith({ x: 1 })
      expect(ElMessage.success).toHaveBeenCalledWith('Saved')
    })

    it('execute 失败: returns false, error 设置, onError 调, ElMessage.error', async () => {
      const onError = vi.fn()
      const fn = vi.fn(async () => { throw new Error('api down') })
      const u = useOptimisticUpdate(fn, { onError })
      const r = await u.execute({ y: 2 })
      expect(r).toBe(false)
      expect(u.error.value?.message).toBe('api down')
      expect(onError).toHaveBeenCalled()
      expect(ElMessage.error).toHaveBeenCalledWith('操作失败，请重试')
    })

    it('非 Error 抛出 转换为 Error', async () => {
      const fn = vi.fn(async () => { throw 'string' })
      const u = useOptimisticUpdate(fn)
      await u.execute({})
      expect(u.error.value).toBeInstanceOf(Error)
      expect(u.error.value?.message).toBe('string')
    })

    it('isPending 在执行时为 true (异步微任务前)', async () => {
      let resolveFn: any
      const fn = vi.fn(() => new Promise(r => { resolveFn = r }))
      const u = useOptimisticUpdate(fn)
      const p = u.execute({})
      expect(u.isPending.value).toBe(true)
      resolveFn()
      await p
      expect(u.isPending.value).toBe(false)
    })

    it('并发 execute 第二个返回 false', async () => {
      const fn = vi.fn(() => new Promise(r => setTimeout(r, 100)))
      const u = useOptimisticUpdate(fn)
      const p1 = u.execute({ a: 1 })
      const r2 = await u.execute({ b: 2 })
      expect(r2).toBe(false)
      await p1
    })

    it('beforeExecute 返回 false 取消', async () => {
      const fn = vi.fn()
      const before = vi.fn(() => false)
      const u = useOptimisticUpdate(fn, { beforeExecute: before })
      const r = await u.execute({})
      expect(r).toBe(false)
      expect(fn).not.toHaveBeenCalled()
    })

    it('beforeExecute 返回 true 继续', async () => {
      const fn = vi.fn(async () => 'ok')
      const u = useOptimisticUpdate(fn, { beforeExecute: () => true })
      const r = await u.execute({})
      expect(r).toBe(true)
    })

    it('beforeExecute async 抛错取消', async () => {
      const fn = vi.fn()
      const u = useOptimisticUpdate(fn, { beforeExecute: async () => { throw new Error('cancel') } })
      const r = await u.execute({})
      expect(r).toBe(false)
      expect(fn).not.toHaveBeenCalled()
    })

    it('无 successMessage 跳过 ElMessage.success', async () => {
      const fn = vi.fn(async () => 'ok')
      const u = useOptimisticUpdate(fn)
      await u.execute({})
      expect(ElMessage.success).not.toHaveBeenCalled()
    })

    it('自定义 errorMessage', async () => {
      const fn = vi.fn(async () => { throw new Error('x') })
      const u = useOptimisticUpdate(fn, { errorMessage: 'failed badly' })
      await u.execute({})
      expect(ElMessage.error).toHaveBeenCalledWith('failed badly')
    })

    it('reset 清空 error', async () => {
      const fn = vi.fn(async () => { throw new Error('e') })
      const u = useOptimisticUpdate(fn)
      await u.execute({})
      expect(u.error.value).not.toBeNull()
      u.reset()
      expect(u.error.value).toBeNull()
    })
  })

  describe('useOptimisticRemove', () => {
    it('removes 立即从列表移除', async () => {
      const list = ref([{ id: 1, n: 'A' }, { id: 2, n: 'B' }, { id: 3, n: 'C' }])
      const fn = vi.fn(async () => 'ok')
      const u = useOptimisticRemove(list, fn)
      // Don't await
      const p = u.remove(2)
      expect(list.value).toEqual([{ id: 1, n: 'A' }, { id: 3, n: 'C' }])
      expect(u.removingIds.value.has(2)).toBe(true)
      await p
      expect(u.removingIds.value.has(2)).toBe(false)
    })

    it('失败回滚 (rollbackOnError default true)', async () => {
      const list = ref([{ id: 1, n: 'A' }, { id: 2, n: 'B' }, { id: 3, n: 'C' }])
      const fn = vi.fn(async () => { throw new Error('fail') })
      const u = useOptimisticRemove(list, fn)
      const r = await u.remove(2)
      expect(r).toBe(false)
      expect(list.value).toEqual([{ id: 1, n: 'A' }, { id: 2, n: 'B' }, { id: 3, n: 'C' }])
    })

    it('rollbackOnError=false 失败不回滚', async () => {
      const list = ref([{ id: 1, n: 'A' }, { id: 2, n: 'B' }])
      const fn = vi.fn(async () => { throw new Error('fail') })
      const u = useOptimisticRemove(list, fn, { rollbackOnError: false })
      await u.remove(1)
      expect(list.value).toEqual([{ id: 2, n: 'B' }])
    })

    it('removing id 不在原列表中也能操作', async () => {
      const list = ref([{ id: 1, n: 'A' }])
      const fn = vi.fn(async () => 'ok')
      const u = useOptimisticRemove(list, fn)
      const r = await u.remove(999)
      expect(r).toBe(true)
      expect(list.value).toEqual([{ id: 1, n: 'A' }])
    })
  })
})
