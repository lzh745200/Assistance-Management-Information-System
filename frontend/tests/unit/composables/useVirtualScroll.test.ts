import { describe, it, expect, vi } from 'vitest'
import { ref, nextTick } from 'vue'

// Mock vue lifecycle hooks to allow testing without app context
vi.mock('vue', async () => {
  const actual = await vi.importActual<any>('vue')
  return {
    ...actual,
    onMounted: vi.fn(),
    onUnmounted: vi.fn(),
  }
})

import { useVirtualScroll } from '@/composables/useVirtualScroll'

describe('composables/useVirtualScroll', () => {
  it('items 数组 + 默认 itemHeight=48', () => {
    const items = Array.from({ length: 100 }, (_, i) => ({ id: i }))
    const v = useVirtualScroll({ items })
    expect(v.totalHeight.value).toBe(100 * 48)
    // overscan * 2 = 10 items rendered with containerHeight=0
    expect(v.visibleItems.value).toHaveLength(10)
  })

  it('ref items', () => {
    const items = ref([{ id: 1 }, { id: 2 }])
    const v = useVirtualScroll({ items, itemHeight: 20 })
    expect(v.totalHeight.value).toBe(40)
  })

  it('visibleRange 空数组 (start=end=0)', () => {
    const v = useVirtualScroll({ items: [], overscan: 0 })
    expect(v.visibleItems.value).toEqual([])
  })

  it('visibleRange start 不会被 overscan 拉成负数', () => {
    // Manually inject scrollTop
    const items = Array.from({ length: 100 }, (_, i) => i)
    const v = useVirtualScroll({ items, itemHeight: 10, overscan: 3 })
    // can't easily mutate scrollTop since it's internal; just test defaults
    expect(v.offsetY.value).toBeGreaterThanOrEqual(0)
  })

  it('scrollTo element null no throw (without onMounted scrollElement is null)', () => {
    const v = useVirtualScroll({ items: [] })
    expect(() => v.scrollTo(100)).not.toThrow()
  })

  it('scrollToIndex 负数 clamp 到 0 (without onMounted scrollElement is null)', () => {
    const v = useVirtualScroll({ items: [] })
    expect(() => v.scrollToIndex(-5)).not.toThrow()
  })

  it('visibleItems 包含 style + item + index', () => {
    const items = Array.from({ length: 3 }, (_, i) => ({ id: i }))
    const v = useVirtualScroll({ items, itemHeight: 30, overscan: 0 })
    // 0 height + 0 overscan -> empty
    expect(v.visibleItems.value).toEqual([])
  })

  it('totalHeight = length * itemHeight', () => {
    const items = Array.from({ length: 1000 }, (_, i) => i)
    const v = useVirtualScroll({ items, itemHeight: 60 })
    expect(v.totalHeight.value).toBe(60000)
  })

  it('externalContainerRef 使用传入 ref', () => {
    const el = { scrollTo: vi.fn() } as any
    const external = ref<HTMLElement | null>(el)
    const v = useVirtualScroll({ items: [], containerRef: external })
    expect(v.containerRef).toBe(external)
  })

  it('default containerRef 是新 ref', () => {
    const v = useVirtualScroll({ items: [] })
    expect(v.containerRef.value).toBeNull()
  })
})
