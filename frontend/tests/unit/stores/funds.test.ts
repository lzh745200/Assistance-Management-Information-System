import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFundsStore } from '@/stores/funds'

describe('useFundsStore', () => {
  let store: ReturnType<typeof useFundsStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useFundsStore()
  })

  it('initializes with default values', () => {
    expect(store.fundList).toEqual([])
    expect(store.current).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.total).toBe(0)
    expect(store.totalFunds).toBe(0)
    expect(store.usedFunds).toBe(0)
    expect(store.remainFunds).toBe(0)
  })

  it('totalFunds computes sum of fund amounts', () => {
    store.fundList = [
      { id: 1, amount: 100, used_amount: 30 },
      { id: 2, amount: 200, used_amount: 50 },
    ] as any[]
    expect(store.totalFunds).toBe(300)
    expect(store.usedFunds).toBe(80)
    expect(store.remainFunds).toBe(220)
  })

  it('handles empty fundList gracefully', () => {
    store.fundList = []
    expect(store.totalFunds).toBe(0)
    expect(store.usedFunds).toBe(0)
    expect(store.remainFunds).toBe(0)
  })

  it('handles missing amount fields as zero', () => {
    store.fundList = [{ id: 1 }, { id: 2, amount: 50 }] as any[]
    expect(store.totalFunds).toBe(50)
    expect(store.usedFunds).toBe(0)
  })
})
