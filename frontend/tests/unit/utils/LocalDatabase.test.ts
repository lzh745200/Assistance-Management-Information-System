import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

vi.mock('@/utils/logger', () => ({
  logger: { info: vi.fn(), warn: vi.fn(), error: vi.fn(), debug: vi.fn() },
}))

const mockStorageEstimate = vi.fn()
;(globalThis as any).navigator = (globalThis as any).navigator || {}
;(globalThis as any).navigator.storage = { estimate: mockStorageEstimate }

// Build fake IDB that resolves synchronously-ish via microtask
class FakeStore {
  data: Map<any, any> = new Map()
  _resolve(value: any) { return { result: value, error: null, onsuccess: null as any, onerror: null as any, set onsuccess(cb: any) { setTimeout(() => cb({ target: this }), 0); (this as any)._cb = cb }, get onsuccess() { return (this as any)._cb } } as any }
}

class FakeReq<T = any> {
  result: T
  onsuccess: ((e: any) => void) | null = null
  onerror: ((e: any) => void) | null = null
  constructor(result: T) { this.result = result }
  fireSuccess() { setTimeout(() => this.onsuccess?.({ target: this }), 0) }
  fireError() { setTimeout(() => this.onerror?.({ target: this }), 0) }
}

class FakeIDBStore {
  data: Map<any, any> = new Map()
  constructor() {}
  get(id: any): FakeReq<any> { const v = this.data.get(id) ?? null; const r = new FakeReq(v); r.fireSuccess(); return r }
  getAll(): FakeReq<any[]> { const r = new FakeReq(Array.from(this.data.values())); r.fireSuccess(); return r }
  add(data: any): FakeReq<number> {
    const id = data.id ?? (this.data.size + 1)
    this.data.set(id, { ...data, id })
    const r = new FakeReq(id)
    r.fireSuccess()
    return r
  }
  put(data: any): FakeReq<any> {
    this.data.set(data.id, { ...data })
    const r = new FakeReq(data.id)
    r.fireSuccess()
    return r
  }
  delete(id: any): FakeReq<undefined> { this.data.delete(id); const r = new FakeReq(undefined); r.fireSuccess(); return r }
}

class FakeTransaction {
  store: FakeIDBStore
  constructor(s: FakeIDBStore) { this.store = s }
  objectStore() { return this.store }
}

class FakeDB {
  stores: Map<string, FakeIDBStore> = new Map()
  objectStoreNames = { contains: (n: string) => this.stores.has(n) }
  transaction(name: string, _mode: string) {
    if (!this.stores.has(name)) this.stores.set(name, new FakeIDBStore())
    return new FakeTransaction(this.stores.get(name)!)
  }
  createObjectStore(name: string) {
    const s = new FakeIDBStore()
    this.stores.set(name, s)
    return s
  }
  close() {}
}

class FakeOpenReq extends FakeReq<FakeDB> {
  onupgradeneeded: ((e: any) => void) | null = null
  fireSuccess() { setTimeout(() => this.onsuccess?.({ target: this }), 0) }
}

let fakeDB: FakeDB
const fakeOpen = vi.fn()
;(globalThis as any).indexedDB = {
  open: (name: string, ver: number) => {
    fakeDB = new FakeDB()
    const req = new FakeOpenReq(fakeDB)
    fakeOpen(name, ver, req)
    setTimeout(() => {
      req.onupgradeneeded?.({ target: req })
      req.fireSuccess()
    }, 0)
    return req
  },
}

import { localDatabase } from '@/utils/LocalDatabase'

const wait = (ms = 5) => new Promise((r) => setTimeout(r, ms))

describe('utils/LocalDatabase', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    ;(localDatabase as any).db = null
  })

  afterEach(() => { (localDatabase as any).db = null })

  it('init 调用 indexedDB.open 并保存 db', async () => {
    await localDatabase.init()
    expect(fakeOpen).toHaveBeenCalledWith('military_rural_db', 1, expect.any(Object))
    expect((localDatabase as any).db).toBe(fakeDB)
  })

  it('init 二次调用直接返回', async () => {
    await localDatabase.init()
    fakeOpen.mockClear()
    await localDatabase.init()
    expect(fakeOpen).not.toHaveBeenCalled()
  })

  it('init onerror resolve 但 db 保持 null', async () => {
    ;(globalThis as any).indexedDB.open = () => {
      const req = new FakeOpenReq(new FakeDB())
      setTimeout(() => req.onerror?.({ target: req }), 0)
      return req
    }
    await localDatabase.init()
    expect((localDatabase as any).db).toBeNull()
  })

  it('init onupgradeneeded 创建 9 个 stores', async () => {
    let captured: any = null
    ;(globalThis as any).indexedDB.open = () => {
      const db = new FakeDB()
      captured = db
      const req = new FakeOpenReq(db)
      setTimeout(() => {
        req.onupgradeneeded?.({ target: req })
        req.fireSuccess()
      }, 0)
      return req
    }
    await localDatabase.init()
    const expected = ['users', 'projects', 'armyPersonnel', 'ruralWorks', 'villages', 'schools', 'funds', 'budget', 'todos']
    expected.forEach((n) => expect(captured.objectStoreNames.contains(n)).toBe(true))
  })

  it('add 通过 IDB 返回 data + id', async () => {
    await localDatabase.init()
    const r = await localDatabase.add('users', { name: 'A' })
    expect(r.id).toBeDefined()
    expect(r.name).toBe('A')
  })

  it('getAll 返回所有项', async () => {
    await localDatabase.init()
    await localDatabase.add('users', { name: 'A' })
    await localDatabase.add('users', { name: 'B' })
    const all = await localDatabase.getAll('users')
    expect(all).toHaveLength(2)
  })

  it('get 通过 id 找到', async () => {
    await localDatabase.init()
    const a = await localDatabase.add('users', { name: 'A' })
    const got = await localDatabase.get('users', a.id)
    expect(got).toMatchObject({ name: 'A' })
  })

  it('get 找不到返回 null', async () => {
    await localDatabase.init()
    const got = await localDatabase.get('users', 999)
    expect(got).toBeNull()
  })

  it('update 替换已有 id', async () => {
    await localDatabase.init()
    const a = await localDatabase.add('users', { name: 'A' })
    const r = await localDatabase.update('users', { ...a, name: 'B' })
    expect(r.name).toBe('B')
    const got = await localDatabase.get('users', a.id)
    expect((got as any).name).toBe('B')
  })

  it('delete 删除并返回 true', async () => {
    await localDatabase.init()
    const a = await localDatabase.add('users', { name: 'A' })
    const ok = await localDatabase.delete('users', a.id)
    expect(ok).toBe(true)
    expect(await localDatabase.get('users', a.id)).toBeNull()
  })

  it('query 无 filter 返回全部', async () => {
    await localDatabase.init()
    await localDatabase.add('users', { name: 'A', role: 'admin' })
    await localDatabase.add('users', { name: 'B', role: 'user' })
    const all = await localDatabase.query('users')
    expect(all).toHaveLength(2)
  })

  it('query filter 按字段过滤', async () => {
    await localDatabase.init()
    await localDatabase.add('users', { name: 'A', role: 'admin' })
    await localDatabase.add('users', { name: 'B', role: 'user' })
    const r = await localDatabase.query('users', { role: 'admin' })
    expect(r).toHaveLength(1)
    expect((r[0] as any).name).toBe('A')
  })

  it('query filter undefined/null/空 跳过', async () => {
    await localDatabase.init()
    await localDatabase.add('users', { name: 'A', role: 'admin' })
    await localDatabase.add('users', { name: 'B', role: 'user' })
    const r = await localDatabase.query('users', { role: undefined, name: null })
    expect(r).toHaveLength(2)
  })

  it('set 等价 add', async () => {
    await localDatabase.init()
    const r = await localDatabase.set('users', { name: 'A' })
    expect(r.id).toBeDefined()
  })

  it('save 无 id 走 add', async () => {
    await localDatabase.init()
    const r = await localDatabase.save('users', { name: 'A' })
    expect(r.id).toBeDefined()
  })

  it('save 有 id 走 update', async () => {
    await localDatabase.init()
    const a = await localDatabase.add('users', { name: 'A' })
    const u = await localDatabase.save('users', { ...a, name: 'B' })
    expect((u as any).name).toBe('B')
  })

  it('checkStorage 走 navigator.storage.estimate', async () => {
    mockStorageEstimate.mockResolvedValueOnce({ usage: 100, quota: 1000 })
    const r = await localDatabase.checkStorage()
    expect(r).toEqual({ available: true, used: 100, total: 1000 })
  })

  it('checkStorage 失败回退 50MB', async () => {
    mockStorageEstimate.mockRejectedValueOnce(new Error('boom'))
    const r = await localDatabase.checkStorage()
    expect(r.used).toBe(0)
    expect(r.total).toBe(50 * 1024 * 1024)
  })

  it('checkStorage 没有 estimate 时也回退', async () => {
    ;(globalThis as any).navigator.storage = {}
    const r = await localDatabase.checkStorage()
    expect(r.total).toBe(50 * 1024 * 1024)
  })

  it('cleanup 返回 removedItems=0', async () => {
    const r = await localDatabase.cleanup()
    expect(r).toEqual({ removedItems: 0 })
  })

  it('validateDataIntegrity 返回 true', async () => {
    await localDatabase.init()
    expect(await localDatabase.validateDataIntegrity()).toBe(true)
  })

  describe('localStorage 后备 (indexedDB 不可用)', () => {
    beforeEach(() => {
      ;(globalThis as any).indexedDB.open = () => {
        const req = new FakeOpenReq(new FakeDB())
        setTimeout(() => req.onerror?.({ target: req }), 0)
        return req
      }
    })

    it('getAll 走 localStorage 返回 []', async () => {
      const r = await localDatabase.getAll('villages')
      expect(r).toEqual([])
    })

    it('add 自动生成 numeric id', async () => {
      const a = await localDatabase.add('villages', { name: 'V1' })
      expect(a.id).toBe(1)
      const b = await localDatabase.add('villages', { name: 'V2' })
      expect(b.id).toBe(2)
    })

    it('add 含已有最大 id+1', async () => {
      await localDatabase.add('villages', { name: 'V1' })  // id=1
      await localDatabase.add('villages', { name: 'V2' })  // id=2
      const r = await localDatabase.add('villages', { name: 'V3' })
      expect(r.id).toBe(3)
    })

    it('get 用 id 查', async () => {
      const a = await localDatabase.add('villages', { name: 'V1' })
      const got = await localDatabase.get('villages', a.id)
      expect((got as any).name).toBe('V1')
    })

    it('get 字符串 id 不匹配 numeric (已知限制)', async () => {
      // getByIdFromLocalStorage 只做 === 比较, 字符串与数字不匹配
      const a = await localDatabase.add('items', { name: 'A' })
      const got = await localDatabase.get('items', String(a.id))
      expect(got).toBeNull()
      // numeric id 仍能匹配
      const got2 = await localDatabase.get('items', a.id)
      expect((got2 as any).name).toBe('A')
    })

    it('update 修改已有项', async () => {
      const a = await localDatabase.add('villages', { name: 'V1' })
      const r = await localDatabase.update('villages', { ...a, name: 'V2' })
      expect((r as any).name).toBe('V2')
      expect(((await localDatabase.get('villages', a.id)) as any).name).toBe('V2')
    })

    it('update 不存在的 id 直接返回', async () => {
      const r = await localDatabase.update('villages', { id: 999, name: 'X' })
      expect((r as any).name).toBe('X')
    })

    it('delete 走 localStorage 返回 true', async () => {
      const a = await localDatabase.add('villages', { name: 'V1' })
      const ok = await localDatabase.delete('villages', a.id)
      expect(ok).toBe(true)
      expect(await localDatabase.get('villages', a.id)).toBeNull()
    })

    it('delete 字符串 id 也匹配', async () => {
      const a = await localDatabase.add('items', { name: 'A' })
      const ok = await localDatabase.delete('items', String(a.id))
      expect(ok).toBe(true)
      expect(await localDatabase.get('items', a.id)).toBeNull()
    })

    it('getFromLocalStorage 解析失败返回 []', () => {
      localStorage.setItem('mrs_local_data_broken', 'not-json')
      const r = (localDatabase as any).getFromLocalStorage('broken')
      expect(r).toEqual([])
    })
  })
})
