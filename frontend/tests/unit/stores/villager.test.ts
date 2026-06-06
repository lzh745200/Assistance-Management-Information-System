import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useVillagerStore } from '@/stores/villager'

describe('stores/villager', () => {
  beforeEach(() => { setActivePinia(createPinia()) })

  it('initial state', () => {
    const s = useVillagerStore()
    expect(s.villagerList).toEqual([])
    expect(s.current).toBeNull()
    expect(s.loading).toBe(false)
    expect(s.total).toBe(0)
  })

  it('fetchVillagers', async () => {
    const s = useVillagerStore()
    s.loading = true
    await s.fetchVillagers()
    expect(s.loading).toBe(false)
  })

  it('fetchVillager', async () => {
    const s = useVillagerStore()
    s.loading = true
    await s.fetchVillager(1)
    expect(s.loading).toBe(false)
  })

  it('createVillager returns 200', async () => {
    const s = useVillagerStore()
    const r = await s.createVillager({ name: 'X' })
    expect(r).toEqual({ code: 200 })
  })

  it('updateVillager returns 200', async () => {
    const s = useVillagerStore()
    const r = await s.updateVillager(1, { name: 'X' })
    expect(r).toEqual({ code: 200 })
  })

  it('deleteVillager returns 200', async () => {
    const s = useVillagerStore()
    const r = await s.deleteVillager(1)
    expect(r).toEqual({ code: 200 })
  })
})
