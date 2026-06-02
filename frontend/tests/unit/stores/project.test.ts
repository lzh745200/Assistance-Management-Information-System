import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useProjectStore } from '@/stores/project'

describe('useProjectStore', () => {
  let store: ReturnType<typeof useProjectStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useProjectStore()
  })

  it('should initialize with empty projects', () => {
    expect(store.projects).toEqual([])
    expect(store.currentProject).toBeNull()
  })

  it('setProjects should update projects list', () => {
    store.setProjects([{ id: 1, name: 'Test' }])
    expect(store.projects).toHaveLength(1)
  })

  it('setCurrent should update current project', () => {
    store.setCurrent({ id: 1, name: 'Test' })
    expect(store.currentProject).toEqual({ id: 1, name: 'Test' })
  })
})
