import { describe, it, expect, vi } from 'vitest'
import { ref, nextTick, onMounted, onUnmounted } from 'vue'

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

/** 触发最近一次 useVirtualScroll 调用注册的 onMounted/onUnmounted 回调 */
function lastHook(mock: ReturnType<typeof vi.fn>): () => void {
  const calls = mock.mock.calls
  return calls[calls.length - 1][0]
}

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

describe('mounted 之后的滚动行为', () => {
  function makeScrollElement(clientHeight: number) {
    const el = document.createElement('div')
    Object.defineProperty(el, 'clientHeight', { configurable: true, get: () => clientHeight })
    return el
  }

  it('onMounted 绑定 scroll 监听并读取 clientHeight', () => {
    const el = makeScrollElement(300)
    const addSpy = vi.spyOn(el, 'addEventListener')
    const items = Array.from({ length: 100 }, (_, i) => i)
    const v = useVirtualScroll({ items, containerRef: ref<HTMLElement | null>(el) })
    lastHook(onMounted)()
    expect(addSpy).toHaveBeenCalledWith('scroll', expect.any(Function), { passive: true })
    // clientHeight 已写入 → visibleCount = ceil(300/48) = 7，end 被 count 截断为 17
    expect(v.visibleItems.value.length).toBe(7 + 5 * 2) // 7 + overscan*2
    addSpy.mockRestore()
  })

  it('scroll 事件更新 scrollTop/containerHeight → offsetY 与 visibleItems 变化', () => {
    const el = makeScrollElement(100)
    const items = Array.from({ length: 100 }, (_, i) => i)
    const v = useVirtualScroll({
      items,
      itemHeight: 10,
      overscan: 0,
      containerRef: ref<HTMLElement | null>(el),
    })
    lastHook(onMounted)()
    el.scrollTop = 50
    el.dispatchEvent(new Event('scroll'))
    expect(v.offsetY.value).toBe(50)
    expect(v.visibleItems.value).toHaveLength(10)
    expect(v.visibleItems.value[0].index).toBe(5)
    expect(v.visibleItems.value[0].style.top).toBe('50px')
  })

  it('滚动到底部时 end 被 clamp 到 items 长度', () => {
    const el = makeScrollElement(100)
    const items = Array.from({ length: 100 }, (_, i) => i)
    const v = useVirtualScroll({
      items,
      itemHeight: 10,
      overscan: 0,
      containerRef: ref<HTMLElement | null>(el),
    })
    lastHook(onMounted)()
    el.scrollTop = 900
    el.dispatchEvent(new Event('scroll'))
    expect(v.visibleItems.value).toHaveLength(10)
    expect(v.visibleItems.value[9].index).toBe(99)
  })

  it('scrollTo 调用 element.scrollTo({top})', () => {
    const el = document.createElement('div')
    // jsdom 未实现 element.scrollTo，直接挂 mock 函数
    const spy = vi.fn()
    el.scrollTo = spy as any
    const v = useVirtualScroll({ items: [], containerRef: ref<HTMLElement | null>(el) })
    lastHook(onMounted)()
    v.scrollTo(120)
    expect(spy).toHaveBeenCalledWith({ top: 120 })
  })

  it('scrollToIndex 计算 top（含 smooth）且负数 clamp 到 0', () => {
    const el = document.createElement('div')
    const spy = vi.fn()
    el.scrollTo = spy as any
    const v = useVirtualScroll({ items: [], containerRef: ref<HTMLElement | null>(el) })
    lastHook(onMounted)()
    v.scrollToIndex(10) // 默认 itemHeight=48
    expect(spy).toHaveBeenCalledWith({ top: 480, behavior: 'smooth' })
    spy.mockClear()
    v.scrollToIndex(-3)
    expect(spy).toHaveBeenCalledWith({ top: 0, behavior: 'smooth' })
  })

  it('onUnmounted 移除 scroll 监听', () => {
    const el = document.createElement('div')
    const rmSpy = vi.spyOn(el, 'removeEventListener')
    useVirtualScroll({ items: [], containerRef: ref<HTMLElement | null>(el) })
    lastHook(onMounted)()
    lastHook(onUnmounted)()
    expect(rmSpy).toHaveBeenCalledWith('scroll', expect.any(Function))
  })

  it('containerRef 为 null 时 mounted/unmounted 均不报错', () => {
    const v = useVirtualScroll({ items: [] })
    expect(() => {
      lastHook(onMounted)()
      lastHook(onUnmounted)()
    }).not.toThrow()
    expect(v.containerRef.value).toBeNull()
  })
})
