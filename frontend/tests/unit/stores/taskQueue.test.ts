import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTaskQueueStore } from '@/stores/taskQueue'

describe('useTaskQueueStore', () => {
  let store: ReturnType<typeof useTaskQueueStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useTaskQueueStore()
  })

  it('initializes with empty tasks', () => {
    expect(store.tasks).toEqual([])
  })

  it('add pushes task to list', () => {
    store.add({ id: '1', name: 'Task 1' })
    expect(store.tasks).toHaveLength(1)
    expect(store.tasks[0].id).toBe('1')
  })

  it('remove filters task by id', () => {
    store.add({ id: '1', name: 'Task 1' })
    store.add({ id: '2', name: 'Task 2' })
    store.remove('1')
    expect(store.tasks).toHaveLength(1)
    expect(store.tasks[0].id).toBe('2')
  })

  it('clear empties all tasks', () => {
    store.add({ id: '1' })
    store.add({ id: '2' })
    store.clear()
    expect(store.tasks).toEqual([])
  })
})
