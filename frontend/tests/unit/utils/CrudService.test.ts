import { describe, it, expect, vi, beforeEach } from 'vitest'
import crudService from '@/utils/CrudService'
import { localDatabase } from '@/utils/LocalDatabase'

vi.mock('@/utils/LocalDatabase', () => ({
  localDatabase: {
    query: vi.fn(),
    get: vi.fn(),
    set: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('@/utils/logger', () => ({
  logger: { info: vi.fn(), warn: vi.fn(), error: vi.fn() },
}))

describe('utils/CrudService', () => {
  beforeEach(() => { vi.clearAllMocks() })

  describe('getAll', () => {
    it('no options -> calls query with empty filters', async () => {
      ;(localDatabase.query as any).mockResolvedValue([{ id: 1 }])
      const r = await crudService.getAll('users')
      expect(r).toEqual([{ id: 1 }])
      expect(localDatabase.query).toHaveBeenCalledWith('users', {})
    })

    it('applies sort asc by field', async () => {
      ;(localDatabase.query as any).mockResolvedValue([{ id: 3 }, { id: 1 }, { id: 2 }])
      const r = await crudService.getAll('x', { sort: { field: 'id', order: 'asc' } })
      expect(r.map((x: any) => x.id)).toEqual([1, 2, 3])
    })

    it('applies sort desc by field', async () => {
      ;(localDatabase.query as any).mockResolvedValue([{ id: 1 }, { id: 3 }, { id: 2 }])
      const r = await crudService.getAll('x', { sort: { field: 'id', order: 'desc' } })
      expect(r.map((x: any) => x.id)).toEqual([3, 2, 1])
    })

    it('sort is no-op on empty array', async () => {
      ;(localDatabase.query as any).mockResolvedValue([])
      const r = await crudService.getAll('x', { sort: { field: 'id', order: 'asc' } })
      expect(r).toEqual([])
    })

    it('applies pagination', async () => {
      const data = Array.from({ length: 10 }, (_, i) => ({ id: i }))
      ;(localDatabase.query as any).mockResolvedValue(data)
      const r = await crudService.getAll('x', { page: 2, pageSize: 3 })
      expect(r).toEqual([{ id: 3 }, { id: 4 }, { id: 5 }])
    })

    it('throws on query failure', async () => {
      ;(localDatabase.query as any).mockRejectedValue(new Error('db fail'))
      await expect(crudService.getAll('x')).rejects.toThrow('db fail')
    })
  })

  describe('getById', () => {
    it('returns record', async () => {
      ;(localDatabase.get as any).mockResolvedValue({ id: 1, name: 'A' })
      const r = await crudService.getById('users', 1)
      expect(r).toEqual({ id: 1, name: 'A' })
      expect(localDatabase.get).toHaveBeenCalledWith('users', '1')
    })

    it('string id converted', async () => {
      ;(localDatabase.get as any).mockResolvedValue({ id: 'abc' })
      await crudService.getById('users', 'abc')
      expect(localDatabase.get).toHaveBeenCalledWith('users', 'abc')
    })

    it('returns null when not found', async () => {
      ;(localDatabase.get as any).mockResolvedValue(null)
      const r = await crudService.getById('users', 99)
      expect(r).toBeNull()
    })

    it('throws on get failure', async () => {
      ;(localDatabase.get as any).mockRejectedValue(new Error('boom'))
      await expect(crudService.getById('x', 1)).rejects.toThrow('boom')
    })
  })

  describe('create', () => {
    it('creates with id (timestamp) + createdAt + updatedAt', async () => {
      ;(localDatabase.set as any).mockResolvedValue(undefined)
      const r = await crudService.create<any>('users', { name: 'X' })
      expect(r.name).toBe('X')
      expect(r.id).toBeDefined()
      expect(r.createdAt).toMatch(/T/)
      expect(r.updatedAt).toBe(r.createdAt)
      expect(localDatabase.set).toHaveBeenCalledWith('users', r)
    })

    it('preserves provided id', async () => {
      ;(localDatabase.set as any).mockResolvedValue(undefined)
      const r = await crudService.create<any>('x', { id: 'CUSTOM' })
      expect(r.id).toBe('CUSTOM')
    })

    it('throws on set failure', async () => {
      ;(localDatabase.set as any).mockRejectedValue(new Error('fail'))
      await expect(crudService.create('x', {})).rejects.toThrow('fail')
    })
  })

  describe('update', () => {
    it('updates existing record', async () => {
      ;(localDatabase.get as any).mockResolvedValue({ id: '1', name: 'old' })
      ;(localDatabase.update as any).mockResolvedValue(undefined)
      const r = await crudService.update('users', '1', { name: 'new' })
      expect(r.name).toBe('new')
      expect(r.id).toBe('1')
      expect(r.updatedAt).toBeDefined()
    })

    it('throws when id missing', async () => {
      await expect(crudService.update('x', undefined, {})).rejects.toThrow('ID is required')
      await expect(crudService.update('x', '', {})).rejects.toThrow('ID is required')
    })

    it('throws when record not found', async () => {
      ;(localDatabase.get as any).mockResolvedValue(null)
      await expect(crudService.update('x', 1, {})).rejects.toThrow('not found')
    })

    it('throws on update failure', async () => {
      ;(localDatabase.get as any).mockResolvedValue({ id: '1' })
      ;(localDatabase.update as any).mockRejectedValue(new Error('db'))
      await expect(crudService.update('x', '1', {})).rejects.toThrow('db')
    })
  })

  describe('delete', () => {
    it('deletes by id', async () => {
      ;(localDatabase.delete as any).mockResolvedValue(undefined)
      const r = await crudService.delete('users', '1')
      expect(r).toBe(true)
      expect(localDatabase.delete).toHaveBeenCalledWith('users', '1')
    })

    it('throws when id missing', async () => {
      await expect(crudService.delete('x', undefined)).rejects.toThrow('ID is required')
    })

    it('throws on delete failure', async () => {
      ;(localDatabase.delete as any).mockRejectedValue(new Error('boom'))
      await expect(crudService.delete('x', '1')).rejects.toThrow('boom')
    })
  })

  describe('batchDelete', () => {
    it('deletes multiple ids', async () => {
      ;(localDatabase.delete as any).mockResolvedValue(undefined)
      const r = await crudService.batchDelete('users', [1, 2, 3])
      expect(r).toBe(true)
      expect(localDatabase.delete).toHaveBeenCalledTimes(3)
    })

    it('stops on first failure', async () => {
      ;(localDatabase.delete as any)
        .mockResolvedValueOnce(undefined)
        .mockRejectedValueOnce(new Error('fail'))
      await expect(crudService.batchDelete('x', [1, 2])).rejects.toThrow('fail')
    })
  })

  describe('search', () => {
    it('no keyword returns all', async () => {
      ;(localDatabase.query as any).mockResolvedValue([{ id: 1 }])
      const r = await crudService.search('x', '', ['name'])
      expect(r).toEqual([{ id: 1 }])
    })

    it('matches string fields case-insensitive', async () => {
      ;(localDatabase.query as any).mockResolvedValue([
        { name: 'Alice' },
        { name: 'Bob' },
        { name: 'Alicia' },
      ])
      const r = await crudService.search('x', 'ali', ['name'])
      expect(r).toEqual([{ name: 'Alice' }, { name: 'Alicia' }])
    })

    it('non-string fields ignored (only string fields searched)', async () => {
      ;(localDatabase.query as any).mockResolvedValue([
        { name: 'A' },
        { count: 5 },
      ])
      const r = await crudService.search('x', '5', ['count'])
      // Non-string fields return false in filter, so nothing matches
      expect(r).toEqual([])
    })
  })

  describe('count', () => {
    it('returns length', async () => {
      ;(localDatabase.query as any).mockResolvedValue([1, 2, 3])
      const r = await crudService.count('x')
      expect(r).toBe(3)
    })

    it('returns 0 for empty', async () => {
      ;(localDatabase.query as any).mockResolvedValue([])
      expect(await crudService.count('x')).toBe(0)
    })
  })
})
