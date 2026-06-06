import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTaskQueueStore } from '@/stores/taskQueue'
import { useRouteStore } from '@/stores/route'

describe('useTaskQueueStore', () => {
  let store: ReturnType<typeof useTaskQueueStore>
  beforeEach(() => {
    setActivePinia(createPinia())
    store = useTaskQueueStore()
  })

  it('初始: tasks=[]', () => {
    expect(store.tasks).toEqual([])
  })

  it('add 添加 task', () => {
    store.add({ id: '1', name: 'A' })
    store.add({ id: '2', name: 'B' })
    expect(store.tasks).toHaveLength(2)
  })

  it('remove 按 id 过滤', () => {
    store.add({ id: '1', name: 'A' })
    store.add({ id: '2', name: 'B' })
    store.remove('1')
    expect(store.tasks).toHaveLength(1)
    expect(store.tasks[0].id).toBe('2')
  })

  it('remove 不存在的 id 不报错', () => {
    store.add({ id: '1' })
    store.remove('99')
    expect(store.tasks).toHaveLength(1)
  })

  it('clear 清空所有 tasks', () => {
    store.add({ id: '1' })
    store.add({ id: '2' })
    store.clear()
    expect(store.tasks).toEqual([])
  })
})

describe('useRouteStore', () => {
  let store: ReturnType<typeof useRouteStore>
  beforeEach(() => {
    setActivePinia(createPinia())
    store = useRouteStore()
  })

  it('初始: routes=[], addRoutes=[]', () => {
    expect(store.routes).toEqual([])
    expect(store.addRoutes).toEqual([])
  })

  it('setRoutes 设置 routes', () => {
    store.setRoutes([{ path: '/a' }, { path: '/b' }])
    expect(store.routes).toHaveLength(2)
  })

  it('setAddRoutes 设置 addRoutes', () => {
    store.setAddRoutes([{ path: '/admin' }])
    expect(store.addRoutes).toHaveLength(1)
  })

  it('setRoutes 支持清空为 []', () => {
    store.setRoutes([{ path: '/a' }])
    expect(store.routes).toHaveLength(1)
    store.setRoutes([])
    expect(store.routes).toHaveLength(0)
  })
})
