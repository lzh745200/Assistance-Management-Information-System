import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useRouteStore } from '@/stores/route'
import { useProjectStore } from '@/stores/project'
import { useTaskQueueStore } from '@/stores/taskQueue'
import { useDataStore } from '@/stores/data'
import { useIndustryStore } from '@/stores/industry'
import { useRuralWorkStore } from '@/stores/ruralWork'

describe('stores misc (route, project, taskQueue, data, industry, ruralWork)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('useRouteStore', () => {
    it('initial empty', () => {
      const s = useRouteStore()
      expect(s.routes).toEqual([])
      expect(s.addRoutes).toEqual([])
    })
    it('setRoutes', () => {
      const s = useRouteStore()
      s.setRoutes([{ path: '/a' }])
      expect(s.routes).toEqual([{ path: '/a' }])
    })
    it('setAddRoutes', () => {
      const s = useRouteStore()
      s.setAddRoutes([{ path: '/b' }])
      expect(s.addRoutes).toEqual([{ path: '/b' }])
    })
  })

  describe('useProjectStore', () => {
    it('initial empty', () => {
      const s = useProjectStore()
      expect(s.projects).toEqual([])
      expect(s.currentProject).toBeNull()
    })
    it('setProjects', () => {
      const s = useProjectStore()
      s.setProjects([{ id: 1 }])
      expect(s.projects).toEqual([{ id: 1 }])
    })
    it('setCurrent', () => {
      const s = useProjectStore()
      s.setCurrent({ id: 1 })
      expect(s.currentProject).toEqual({ id: 1 })
    })
  })

  describe('useTaskQueueStore', () => {
    it('initial empty', () => {
      const s = useTaskQueueStore()
      expect(s.tasks).toEqual([])
    })
    it('add', () => {
      const s = useTaskQueueStore()
      s.add({ id: '1' })
      s.add({ id: '2' })
      expect(s.tasks).toHaveLength(2)
    })
    it('remove by id', () => {
      const s = useTaskQueueStore()
      s.add({ id: '1' })
      s.add({ id: '2' })
      s.remove('1')
      expect(s.tasks).toHaveLength(1)
      expect(s.tasks[0].id).toBe('2')
    })
    it('remove missing id noop', () => {
      const s = useTaskQueueStore()
      s.add({ id: '1' })
      s.remove('nope')
      expect(s.tasks).toHaveLength(1)
    })
    it('clear', () => {
      const s = useTaskQueueStore()
      s.add({ id: '1' })
      s.clear()
      expect(s.tasks).toEqual([])
    })
  })

  describe('useDataStore', () => {
    it('initial state', () => {
      const s = useDataStore()
      expect(s.dataList).toEqual([])
      expect(s.currentData).toBeNull()
      expect(s.loading).toBe(false)
      expect(s.error).toBeNull()
      expect(s.total).toBe(0)
    })
    it('fetchData: stub sets total=0 + loading flips', async () => {
      const s = useDataStore()
      const p = s.fetchData()
      // before await: loading should be true (sync part)
      // after await: loading false
      await p
      expect(s.loading).toBe(false)
      expect(s.total).toBe(0)
    })
    it('setCurrentData', () => {
      const s = useDataStore()
      s.setCurrentData({ id: 1 })
      expect(s.currentData).toEqual({ id: 1 })
    })
  })

  describe('useIndustryStore', () => {
    it('initial state', () => {
      const s = useIndustryStore()
      expect(s.industryList).toEqual([])
      expect(s.loading).toBe(false)
      expect(s.error).toBeNull()
    })
    it('fetchIndustries stub', async () => {
      const s = useIndustryStore()
      await s.fetchIndustries()
      expect(s.loading).toBe(false)
    })
  })

  describe('useRuralWorkStore', () => {
    it('initial state', () => {
      const s = useRuralWorkStore()
      expect(s.works).toEqual([])
      expect(s.currentWork).toBeNull()
      expect(s.loading).toBe(false)
      expect(s.error).toBeNull()
    })
    it('fetchWorks stub', async () => {
      const s = useRuralWorkStore()
      await s.fetchWorks()
      expect(s.loading).toBe(false)
    })
  })
})
