import { describe, it, expect, beforeEach } from 'vitest'
import { LocalStorageManager, STORAGE_KEYS, localStorageManager } from '@/utils/LocalStorageManager'

describe('utils/LocalStorageManager', () => {
  let mgr: LocalStorageManager
  beforeEach(() => { localStorage.clear(); mgr = new LocalStorageManager() })

  describe('STORAGE_KEYS', () => {
    it('exports 10 keys', () => {
      expect(Object.keys(STORAGE_KEYS).length).toBe(9)
      expect(STORAGE_KEYS.AUTH_TOKEN).toBe('military_rural_auth_token')
    })
  })

  describe('saveData', () => {
    it('object', () => { expect(mgr.saveData('a', { x: 1 })).toBe(true); expect(JSON.parse(localStorage.getItem('a')!)).toEqual({ x: 1 }) })
    it('string', () => { mgr.saveData('a', 'hello'); expect(localStorage.getItem('a')).toBe('"hello"') })
    it('array', () => { mgr.saveData('a', [1, 2, 3]); expect(JSON.parse(localStorage.getItem('a')!)).toEqual([1, 2, 3]) })
    it('null', () => { mgr.saveData('a', null); expect(localStorage.getItem('a')).toBe('null') })
    it('serialize error -> false', () => {
      const circular: any = {}
      circular.self = circular
      expect(mgr.saveData('a', circular)).toBe(false)
    })
  })

  describe('getData', () => {
    it('exists', () => { localStorage.setItem('a', '"x"'); expect(mgr.getData('a')).toBe('x') })
    it('not exists -> null', () => { expect(mgr.getData('a')).toBeNull() })
    it('invalid JSON -> null', () => { localStorage.setItem('a', 'not-json'); expect(mgr.getData('a')).toBeNull() })
  })

  describe('removeData', () => {
    it('removes', () => { localStorage.setItem('a', '"x"'); expect(mgr.removeData('a')).toBe(true); expect(localStorage.getItem('a')).toBeNull() })
    it('non-existent -> true', () => { expect(mgr.removeData('a')).toBe(true) })
  })

  describe('clearAllData', () => {
    it('removes all STORAGE_KEYS', () => {
      localStorage.setItem(STORAGE_KEYS.USERS, 'x')
      localStorage.setItem(STORAGE_KEYS.PROJECTS, 'y')
      expect(mgr.clearAllData()).toBe(true)
      expect(localStorage.getItem(STORAGE_KEYS.USERS)).toBeNull()
      expect(localStorage.getItem(STORAGE_KEYS.PROJECTS)).toBeNull()
    })
  })

  describe('getStorageInfo', () => {
    it('returns sizes for all keys', () => {
      localStorage.setItem(STORAGE_KEYS.USERS, '{"x":1}')
      const info = mgr.getStorageInfo()
      expect(typeof info.USERS).toBe('number')
      expect(info.USERS).toBeGreaterThan(0)
      expect(info.PROJECTS).toBe(0)
    })
  })

  describe('bulkSave', () => {
    it('saves multiple', () => { expect(mgr.bulkSave({ a: 1, b: 2 })).toBe(true); expect(JSON.parse(localStorage.getItem('a')!)).toBe(1) })
  })

  describe('hasEnoughStorage', () => {
    it('under threshold -> true', () => { expect(mgr.hasEnoughStorage(100)).toBe(true) })
    it('over threshold -> false', () => { expect(mgr.hasEnoughStorage(10 * 1024 * 1024)).toBe(false) })
  })

  describe('initializeDefaultData', () => {
    it('writes missing keys', () => {
      mgr.initializeDefaultData({ a: 'defaultA', b: 'defaultB' })
      expect(JSON.parse(localStorage.getItem('a')!)).toBe('defaultA')
      expect(JSON.parse(localStorage.getItem('b')!)).toBe('defaultB')
    })
    it('preserves existing', () => {
      localStorage.setItem('a', '"existing"')
      mgr.initializeDefaultData({ a: 'defaultA' })
      expect(JSON.parse(localStorage.getItem('a')!)).toBe('existing')
    })
  })

  describe('storage unavailable', () => {
    it('saveData returns false', () => {
      const orig = localStorage.setItem
      ;(localStorage as any).setItem = () => { throw new Error('quota') }
      expect(mgr.saveData('a', 1)).toBe(false)
      ;(localStorage as any).setItem = orig
    })
    it('getData returns null', () => {
      const orig = localStorage.setItem
      ;(localStorage as any).setItem = () => { throw new Error('quota') }
      expect(mgr.getData('a')).toBeNull()
      ;(localStorage as any).setItem = orig
    })
  })

  it('singleton localStorageManager works', () => {
    expect(localStorageManager.saveData('a', 1)).toBe(true)
    expect(localStorageManager.getData('a')).toBe(1)
  })
})
