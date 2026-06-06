import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const { mockRequest } = vi.hoisted(() => ({
  mockRequest: { get: vi.fn(), post: vi.fn() },
}))

vi.mock('@/api/request', () => ({ default: mockRequest }))
vi.mock('@/utils/logger', () => ({
  logger: { error: vi.fn(), warn: vi.fn(), info: vi.fn(), debug: vi.fn() },
}))

import {
  checkUnique,
  checkUniqueBatch,
  createUniqueValidator,
  createDebouncedUniqueValidator,
  UniqueValidators,
} from '@/utils/uniqueValidation'

describe('utils/uniqueValidation', () => {
  beforeEach(() => { vi.clearAllMocks() })

  describe('checkUnique', () => {
    it('available=true', async () => {
      mockRequest.get.mockResolvedValue({ data: { available: true, message: 'ok' } })
      const r = await checkUnique({ model: 'm', field: 'f', value: 'v' })
      expect(r).toEqual({ available: true, message: 'ok' })
      expect(mockRequest.get).toHaveBeenCalledWith('/validation/check-unique', {
        params: { model: 'm', field: 'f', value: 'v', exclude_id: undefined },
      })
    })

    it('with excludeId', async () => {
      mockRequest.get.mockResolvedValue({ data: { available: true, message: 'ok' } })
      await checkUnique({ model: 'm', field: 'f', value: 'v', excludeId: 7 })
      expect(mockRequest.get).toHaveBeenCalledWith('/validation/check-unique', {
        params: { model: 'm', field: 'f', value: 'v', exclude_id: 7 },
      })
    })

    it('error -> default to available=true', async () => {
      mockRequest.get.mockRejectedValue(new Error('net'))
      const r = await checkUnique({ model: 'm', field: 'f', value: 'v' })
      expect(r.available).toBe(true)
      expect(r.message).toContain('验证失败')
    })
  })

  describe('checkUniqueBatch', () => {
    it('success', async () => {
      mockRequest.post.mockResolvedValue({ data: [{ available: true, message: 'a' }] })
      const r = await checkUniqueBatch([{ model: 'm', field: 'f', value: 'v' }])
      expect(r).toEqual([{ available: true, message: 'a' }])
    })

    it('error -> fallback', async () => {
      mockRequest.post.mockRejectedValue(new Error('net'))
      const r = await checkUniqueBatch([
        { model: 'm', field: 'f', value: 'v1' },
        { model: 'm', field: 'f', value: 'v2' },
      ])
      expect(r).toHaveLength(2)
      expect(r.every((x) => x.available)).toBe(true)
    })
  })

  describe('createUniqueValidator', () => {
    it('empty value -> resolve', async () => {
      const v = createUniqueValidator('m', 'f', 'msg')
      await expect(v.asyncValidator({}, '')).resolves.toBeUndefined()
    })

    it('available -> resolve', async () => {
      mockRequest.get.mockResolvedValue({ data: { available: true, message: 'ok' } })
      const v = createUniqueValidator('m', 'f', 'msg')
      await expect(v.asyncValidator({}, 'val')).resolves.toBeUndefined()
    })

    it('!available -> reject with msg', async () => {
      mockRequest.get.mockResolvedValue({ data: { available: false, message: 'taken' } })
      const v = createUniqueValidator('m', 'f', 'customErr')
      await expect(v.asyncValidator({}, 'val')).rejects.toBe('customErr')
    })

    it('with excludeIdGetter', async () => {
      mockRequest.get.mockResolvedValue({ data: { available: true, message: 'ok' } })
      const v = createUniqueValidator('m', 'f', 'msg', () => 99)
      await v.asyncValidator({}, 'val')
      expect(mockRequest.get).toHaveBeenCalledWith('/validation/check-unique', {
        params: { model: 'm', field: 'f', value: 'val', exclude_id: 99 },
      })
    })

    it('default trigger is blur', () => {
      const v = createUniqueValidator('m', 'f', 'msg')
      expect(v.trigger).toBe('blur')
    })
  })

  describe('createDebouncedUniqueValidator', () => {
    beforeEach(() => { vi.useFakeTimers() })
    afterEach(async () => { vi.useRealTimers() })

    it('empty value -> resolve immediately', async () => {
      const v = createDebouncedUniqueValidator('m', 'f', 'msg', 100)
      await expect(v.asyncValidator({}, '')).resolves.toBeUndefined()
    })

    it('debounced + available -> resolve', async () => {
      mockRequest.get.mockResolvedValue({ data: { available: true, message: 'ok' } })
      const v = createDebouncedUniqueValidator('m', 'f', 'msg', 100)
      const p = v.asyncValidator({}, 'val')
      await vi.advanceTimersByTimeAsync(150)
      await expect(p).resolves.toBeUndefined()
    })

    it('debounced + !available -> reject', async () => {
      mockRequest.get.mockResolvedValue({ data: { available: false, message: 'taken' } })
      const v = createDebouncedUniqueValidator('m', 'f', 'msg', 100)
      const p = v.asyncValidator({}, 'val')
      p.catch(() => {})  // suppress unhandled
      await vi.advanceTimersByTimeAsync(150)
      await expect(p).rejects.toBe('msg')
    })

    it('with excludeIdGetter', async () => {
      mockRequest.get.mockResolvedValue({ data: { available: true, message: 'ok' } })
      const v = createDebouncedUniqueValidator('m', 'f', 'msg', 100, () => 5)
      const p = v.asyncValidator({}, 'val')
      await vi.advanceTimersByTimeAsync(150)
      await p
      expect(mockRequest.get.mock.calls[0][1].params.exclude_id).toBe(5)
    })

    it('trigger is blur', () => {
      const v = createDebouncedUniqueValidator('m', 'f', 'msg', 100)
      expect(v.trigger).toBe('blur')
    })
  })

  describe('UniqueValidators', () => {
    it('villageCode', () => {
      const v = UniqueValidators.villageCode()
      expect(v.trigger).toBe('blur')
    })
    it('organizationCode', () => {
      const v = UniqueValidators.organizationCode()
      expect(v.trigger).toBe('blur')
    })
    it('schoolCode', () => {
      const v = UniqueValidators.schoolCode()
      expect(v.trigger).toBe('blur')
    })
    it('userEmail', () => {
      const v = UniqueValidators.userEmail()
      expect(v.trigger).toBe('blur')
    })
    it('policyCode', () => {
      const v = UniqueValidators.policyCode()
      expect(v.trigger).toBe('blur')
    })
    it('roleName', () => {
      const v = UniqueValidators.roleName()
      expect(v.trigger).toBe('blur')
    })
    it('villagerIdCard', () => {
      const v = UniqueValidators.villagerIdCard()
      expect(v.trigger).toBe('blur')
    })

    it('all with excludeIdGetter', () => {
      const getter = () => 1
      expect(UniqueValidators.villageCode(getter).trigger).toBe('blur')
      expect(UniqueValidators.organizationCode(getter).trigger).toBe('blur')
      expect(UniqueValidators.schoolCode(getter).trigger).toBe('blur')
      expect(UniqueValidators.userEmail(getter).trigger).toBe('blur')
      expect(UniqueValidators.policyCode(getter).trigger).toBe('blur')
      expect(UniqueValidators.roleName(getter).trigger).toBe('blur')
      expect(UniqueValidators.villagerIdCard(getter).trigger).toBe('blur')
    })
  })
})
