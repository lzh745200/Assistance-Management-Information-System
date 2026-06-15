/**
 * Local Storage 增强工具单元测试
 * 覆盖: src/utils/local-storage.ts
 */
import { describe, it, expect, beforeEach } from 'vitest'
import {
  enhancedStorage,
  STORAGE_KEYS,
  StorageError,
  setMultiple,
  getMultiple,
  initializeStorage,
  dataImportExport,
} from '@/utils/local-storage'

describe('EnhancedStorage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  // ==================== set / get ====================

  describe('set and get', () => {
    it('should store and retrieve a string', () => {
      enhancedStorage.set('test_key', 'hello')
      expect(enhancedStorage.get('test_key')).toBe('hello')
    })

    it('should store and retrieve an object', () => {
      const obj = { name: '张三', age: 25 }
      enhancedStorage.set('test_obj', obj)
      expect(enhancedStorage.get('test_obj')).toEqual(obj)
    })

    it('should store and retrieve an array', () => {
      const arr = [1, 2, 3]
      enhancedStorage.set('test_arr', arr)
      expect(enhancedStorage.get('test_arr')).toEqual(arr)
    })

    it('should store and retrieve a number', () => {
      enhancedStorage.set('test_num', 42)
      expect(enhancedStorage.get('test_num')).toBe(42)
    })

    it('should store and retrieve a boolean', () => {
      enhancedStorage.set('test_bool', true)
      expect(enhancedStorage.get('test_bool')).toBe(true)
    })

    it('should store and retrieve null', () => {
      enhancedStorage.set('test_null', null)
      expect(enhancedStorage.get('test_null')).toBeNull()
    })

    it('should return default value for missing key', () => {
      expect(enhancedStorage.get('nonexistent')).toBeNull()
      expect(enhancedStorage.get('nonexistent', 'default')).toBe('default')
    })

    it('should return default for corrupted data', () => {
      localStorage.setItem('corrupt_key', 'not-json')
      expect(enhancedStorage.get('corrupt_key', 'fallback')).toBe('fallback')
    })
  })

  // ==================== remove ====================

  describe('remove', () => {
    it('should remove a key', () => {
      enhancedStorage.set('to_remove', 'value')
      enhancedStorage.remove('to_remove')
      expect(enhancedStorage.get('to_remove')).toBeNull()
    })

    it('should not throw for non-existing key', () => {
      expect(() => enhancedStorage.remove('nonexistent')).not.toThrow()
    })
  })

  // ==================== has ====================

  describe('has', () => {
    it('should return true for existing key', () => {
      enhancedStorage.set('exists_key', 'value')
      expect(enhancedStorage.has('exists_key')).toBe(true)
    })

    it('should return false for missing key', () => {
      expect(enhancedStorage.has('no_key')).toBe(false)
    })
  })

  // ==================== clearAll ====================

  describe('clearAll', () => {
    it('should clear all storage keys', () => {
      enhancedStorage.set(STORAGE_KEYS.USER, { id: 1 })
      enhancedStorage.set(STORAGE_KEYS.TOKEN, 'tok')
      enhancedStorage.clearAll()
      expect(localStorage.getItem(STORAGE_KEYS.USER)).toBeNull()
      expect(localStorage.getItem(STORAGE_KEYS.TOKEN)).toBeNull()
    })
  })

  // ==================== getStorageInfo ====================

  describe('getStorageInfo', () => {
    it('should return storage info', () => {
      enhancedStorage.set(STORAGE_KEYS.USER, { id: 1 })
      const info = enhancedStorage.getStorageInfo()
      expect(info.used).toBeGreaterThan(0)
      expect(info.keys.length).toBeGreaterThan(0)
    })

    it('should return empty for clean storage', () => {
      const info = enhancedStorage.getStorageInfo()
      expect(info.keys).toEqual([])
    })
  })

  // ==================== optimizeStorage ====================

  describe('optimizeStorage', () => {
    it('should return freed and errors', () => {
      const result = enhancedStorage.optimizeStorage()
      expect(typeof result.freed).toBe('number')
      expect(Array.isArray(result.errors)).toBe(true)
    })
  })
})

// ==================== StorageError ====================

describe('StorageError', () => {
  it('should have correct name and code', () => {
    const err = new StorageError('test error', 'TEST_CODE')
    expect(err.name).toBe('StorageError')
    expect(err.code).toBe('TEST_CODE')
    expect(err.message).toBe('test error')
  })
})

// ==================== setMultiple / getMultiple ====================

describe('setMultiple', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('should set multiple items', () => {
    const result = setMultiple({
      'test_a': 'valueA',
      'test_b': 'valueB',
    })
    expect(result.success).toBe(true)
    expect(result.errors).toEqual([])
    expect(enhancedStorage.get('test_a')).toBe('valueA')
    expect(enhancedStorage.get('test_b')).toBe('valueB')
  })
})

describe('getMultiple', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('should get multiple items', () => {
    enhancedStorage.set('multi_a', 'A')
    enhancedStorage.set('multi_b', 'B')
    const result = getMultiple(['multi_a', 'multi_b', 'multi_c'])
    expect(result['multi_a']).toBe('A')
    expect(result['multi_b']).toBe('B')
    expect(result).not.toHaveProperty('multi_c')
  })
})

// ==================== initializeStorage ====================

describe('initializeStorage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('should return true and set initialized flag', () => {
    const result = initializeStorage()
    expect(result).toBe(true)
    expect(enhancedStorage.get(STORAGE_KEYS.INITIALIZED)).toBe(true)
  })

  it('should set last_sync', () => {
    initializeStorage()
    const sync = enhancedStorage.get(STORAGE_KEYS.LAST_SYNC)
    expect(sync).toBeTruthy()
  })
})

// ==================== STORAGE_KEYS ====================

describe('STORAGE_KEYS', () => {
  it('should have expected keys', () => {
    expect(STORAGE_KEYS.USER).toContain('assistance_management_')
    expect(STORAGE_KEYS.TOKEN).toContain('assistance_management_')
    expect(STORAGE_KEYS.PROJECTS).toContain('assistance_management_')
    expect(STORAGE_KEYS.SETTINGS).toContain('assistance_management_')
    expect(STORAGE_KEYS.INITIALIZED).toContain('assistance_management_')
  })
})

// ==================== dataImportExport ====================

describe('dataImportExport', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  describe('exportData', () => {
    it('should export non-sensitive data as JSON', () => {
      enhancedStorage.set(STORAGE_KEYS.SETTINGS, { theme: 'dark' })
      const json = dataImportExport.exportData()
      const parsed = JSON.parse(json)
      expect(parsed).toHaveProperty('settings')
    })

    it('should not export token or refresh_token', () => {
      enhancedStorage.set(STORAGE_KEYS.TOKEN, 'secret-token')
      enhancedStorage.set(STORAGE_KEYS.REFRESH_TOKEN, 'refresh-secret')
      const json = dataImportExport.exportData()
      const parsed = JSON.parse(json)
      expect(parsed).not.toHaveProperty('token')
      expect(parsed).not.toHaveProperty('refresh_token')
    })
  })

  describe('importData', () => {
    it('should import valid JSON data', () => {
      const json = JSON.stringify({ settings: { theme: 'light' } })
      const result = dataImportExport.importData(json)
      expect(result.success).toBe(true)
      expect(result.imported).toBe(1)
    })

    it('should handle invalid JSON', () => {
      const result = dataImportExport.importData('not-json')
      expect(result.success).toBe(false)
      expect(result.imported).toBe(0)
    })

    it('should handle empty JSON object', () => {
      const result = dataImportExport.importData('{}')
      expect(result.success).toBe(true)
      expect(result.imported).toBe(0)
    })
  })
})
