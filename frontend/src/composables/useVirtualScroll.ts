/**
 * 虚拟滚动 Composable
 *
 * 仅渲染可视区域内的 DOM 节点，大幅降低大数据列表的内存占用和渲染开销。
 * 适用于村庄列表、经费记录、人员列表等万级数据的流畅渲染。
 *
 * @example
 * const {
 *   containerRef, totalHeight, offsetY, visibleItems,
 *   scrollTo, scrollToIndex,
 * } = useVirtualScroll({
 *   items: largeList,
 *   itemHeight: 48,
 *   overscan: 5,
 * })
 */

import { ref, computed, onMounted, onUnmounted, type Ref } from 'vue'

export interface VirtualScrollOptions<T = any> {
  /** 数据源 */
  items: Ref<T[]> | T[]
  /** 每项高度 (px)，固定高度场景 */
  itemHeight?: number
  /** 预渲染行数（可视区域外），提升滚动流畅度 */
  overscan?: number
  /** 容器元素（如果传入则不再自动检测 scroll 容器） */
  containerRef?: Ref<HTMLElement | null>
}

export interface VirtualScrollReturn<T = any> {
  /** 容器模板引用（绑定到滚动容器） */
  containerRef: Ref<HTMLElement | null>
  /** 总高度 (px) */
  totalHeight: Ref<number>
  /** Y 轴偏移 (px) */
  offsetY: Ref<number>
  /** 当前可见（含 overscan）的数据项 */
  visibleItems: Ref<Array<{ item: T; index: number; style: Record<string, string> }>>
  /** 滚动到指定位置 */
  scrollTo: (top: number) => void
  /** 滚动到指定索引 */
  scrollToIndex: (index: number) => void
}

export function useVirtualScroll<T = any>(
  options: VirtualScrollOptions<T>
): VirtualScrollReturn<T> {
  const {
    items: rawItems,
    itemHeight = 48,
    overscan = 5,
    containerRef: externalContainerRef,
  } = options

  // ── 响应式状态 ──
  const containerRef = externalContainerRef ?? ref<HTMLElement | null>(null)
  const scrollTop = ref(0)
  const containerHeight = ref(0)

  // 规一化 items 为 Ref
  const items = computed<T[]>(() => {
    if (Array.isArray(rawItems)) return rawItems
    return rawItems.value
  })

  // ── 可视范围计算 ──
  const visibleRange = computed(() => {
    const count = items.value.length
    if (count === 0) return { start: 0, end: 0 }

    const start = Math.max(0, Math.floor(scrollTop.value / itemHeight) - overscan)
    const visibleCount = Math.ceil(containerHeight.value / itemHeight)
    const end = Math.min(count, start + visibleCount + overscan * 2)

    return { start, end }
  })

  // ── 可见项 ──
  const visibleItems = computed(() => {
    const { start, end } = visibleRange.value
    const result: Array<{
      item: T
      index: number
      style: Record<string, string>
    }> = []

    for (let i = start; i < end; i++) {
      result.push({
        item: items.value[i],
        index: i,
        style: {
          position: 'absolute',
          top: `${i * itemHeight}px`,
          left: '0',
          right: '0',
          height: `${itemHeight}px`,
        },
      })
    }
    return result
  })

  // ── 总高度 ──
  const totalHeight = computed(() => items.value.length * itemHeight)

  // ── Y 偏移 ──
  const offsetY = computed(() => visibleRange.value.start * itemHeight)

  // ── 滚动处理 ──
  let scrollElement: HTMLElement | null = null

  function onScroll(e: Event) {
    const target = e.target as HTMLElement
    scrollTop.value = target.scrollTop
    containerHeight.value = target.clientHeight
  }

  onMounted(() => {
    scrollElement = containerRef.value
    if (scrollElement) {
      scrollElement.addEventListener('scroll', onScroll, { passive: true })
      containerHeight.value = scrollElement.clientHeight
    }
  })

  onUnmounted(() => {
    if (scrollElement) {
      scrollElement.removeEventListener('scroll', onScroll)
    }
  })

  // ── 方法 ──
  function scrollTo(top: number) {
    scrollElement?.scrollTo({ top })
  }

  function scrollToIndex(index: number) {
    const top = Math.max(0, index * itemHeight)
    scrollElement?.scrollTo({ top, behavior: 'smooth' })
  }

  return {
    containerRef,
    totalHeight,
    offsetY,
    visibleItems,
    scrollTo,
    scrollToIndex,
  }
}
