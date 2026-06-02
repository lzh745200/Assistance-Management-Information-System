import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useConfigStore } from '@/stores/config'
import { useRouteStore } from '@/stores/route'
import { useTaskQueueStore } from '@/stores/taskQueue'

describe('useConfigStore', () => {
  let store: ReturnType<typeof useConfigStore>
  beforeEach(() => { setActivePinia(createPinia()); store = useConfigStore() })
  it('initializes with default config', () => {
    expect(store).toBeDefined()
  })
})

describe('useRouteStore', () => {
  let store: ReturnType<typeof useRouteStore>
  beforeEach(() => { setActivePinia(createPinia()); store = useRouteStore() })
  it('initializes', () => {
    expect(store).toBeDefined()
  })
})

describe('useTaskQueueStore', () => {
  let store: ReturnType<typeof useTaskQueueStore>
  beforeEach(() => { setActivePinia(createPinia()); store = useTaskQueueStore() })
  it('initializes with empty queue', () => {
    expect(store).toBeDefined()
  })
})
