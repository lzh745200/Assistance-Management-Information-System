import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useRouteStore } from '@/stores/route'

describe('useRouteStore', () => {
  let store: ReturnType<typeof useRouteStore>
  beforeEach(() => { setActivePinia(createPinia()); store = useRouteStore() })

  it('initializes with defaults', () => {
    expect(store.routes).toEqual([])
    expect(store.addRoutes).toEqual([])
  })

  it('setRoutes updates routes', () => {
    store.setRoutes([{ path: '/a' }, { path: '/b' }])
    expect(store.routes).toHaveLength(2)
  })

  it('setAddRoutes updates addRoutes', () => {
    store.setAddRoutes([{ path: '/c' }])
    expect(store.addRoutes).toHaveLength(1)
  })
})
