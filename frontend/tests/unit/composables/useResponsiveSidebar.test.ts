import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockOnMounted, mockOnUnmounted } = vi.hoisted(() => ({
  mockOnMounted: vi.fn((fn) => { fn() }),
  mockOnUnmounted: vi.fn((fn) => { fn() }),
}))

vi.mock('vue', async () => {
  const actual = await vi.importActual<any>('vue')
  return { ...actual, onMounted: mockOnMounted, onUnmounted: mockOnUnmounted }
})

import { useResponsiveSidebar } from '@/composables/useResponsiveSidebar'

describe('composables/useResponsiveSidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    ;(globalThis as any).window = { innerWidth: 1280, addEventListener: vi.fn(), removeEventListener: vi.fn() }
  })

  it('initial state', () => {
    const s = useResponsiveSidebar()
    expect(s.isCollapsed.value).toBe(false)
    expect(s.isMobile.value).toBe(false)
  })

  it('onMounted/onUnmounted registered', () => {
    useResponsiveSidebar()
    expect(mockOnMounted).toHaveBeenCalled()
    expect(mockOnUnmounted).toHaveBeenCalled()
  })

  it('restoreState from localStorage = "true"', () => {
    localStorage.setItem('sidebar_collapsed', 'true')
    const s = useResponsiveSidebar()
    // Run the onMounted callback (it's auto-called via our mock)
    // But we need to trigger it
    mockOnMounted.mock.calls[0][0]()  // call the registered fn
    expect(s.isCollapsed.value).toBe(true)
  })

  it('restoreState from localStorage = "false"', () => {
    localStorage.setItem('sidebar_collapsed', 'false')
    const s = useResponsiveSidebar()
    mockOnMounted.mock.calls[0][0]()
    expect(s.isCollapsed.value).toBe(false)
  })

  it('restoreState with no localStorage -> unchanged', () => {
    const s = useResponsiveSidebar()
    mockOnMounted.mock.calls[0][0]()
    expect(s.isCollapsed.value).toBe(false)
  })

  it('restoreState handles localStorage error', () => {
    const orig = localStorage.getItem
    ;(localStorage as any).getItem = () => { throw new Error('quota') }
    const s = useResponsiveSidebar()
    expect(() => mockOnMounted.mock.calls[0][0]()).not.toThrow()
    ;(localStorage as any).getItem = orig
  })

  it('toggleCollapse', () => {
    const s = useResponsiveSidebar()
    s.toggleCollapse()
    expect(s.isCollapsed.value).toBe(true)
    expect(localStorage.getItem('sidebar_collapsed')).toBe('true')
    s.toggleCollapse()
    expect(s.isCollapsed.value).toBe(false)
    expect(localStorage.getItem('sidebar_collapsed')).toBe('false')
  })

  it('setCollapsed(true)', () => {
    const s = useResponsiveSidebar()
    s.setCollapsed(true)
    expect(s.isCollapsed.value).toBe(true)
    expect(localStorage.getItem('sidebar_collapsed')).toBe('true')
  })

  it('setCollapsed(false)', () => {
    const s = useResponsiveSidebar()
    s.setCollapsed(false)
    expect(s.isCollapsed.value).toBe(false)
    expect(localStorage.getItem('sidebar_collapsed')).toBe('false')
  })

  it('handleResize mobile (< 768) -> isMobile=true + collapse', () => {
    ;(globalThis as any).window.innerWidth = 600
    const s = useResponsiveSidebar()
    // simulate onMounted
    s.toggleCollapse()  // collapse=true first
    s.toggleCollapse()  // back to false
    // call registered onMounted
    mockOnMounted.mock.calls[mockOnMounted.mock.calls.length - 1][0]()
    expect(s.isMobile.value).toBe(true)
    expect(s.isCollapsed.value).toBe(true)
  })

  it('handleResize tablet (768-1024) -> isMobile=false + collapse', () => {
    ;(globalThis as any).window.innerWidth = 900
    const s = useResponsiveSidebar()
    s.setCollapsed(false)
    mockOnMounted.mock.calls[mockOnMounted.mock.calls.length - 1][0]()
    expect(s.isMobile.value).toBe(false)
    expect(s.isCollapsed.value).toBe(true)
  })

  it('handleResize desktop (>= 1024) -> not collapsed', () => {
    ;(globalThis as any).window.innerWidth = 1280
    const s = useResponsiveSidebar()
    s.setCollapsed(false)
    mockOnMounted.mock.calls[mockOnMounted.mock.calls.length - 1][0]()
    expect(s.isMobile.value).toBe(false)
    expect(s.isCollapsed.value).toBe(false)
  })

  it('window resize listener added/removed', () => {
    const add = vi.fn()
    const remove = vi.fn()
    ;(globalThis as any).window.addEventListener = add
    ;(globalThis as any).window.removeEventListener = remove
    useResponsiveSidebar()
    // Our mock auto-calls onMounted fn, which calls window.addEventListener
    expect(add).toHaveBeenCalledWith('resize', expect.any(Function))
  })

  it('persistState error -> swallow', () => {
    const s = useResponsiveSidebar()
    const orig = localStorage.setItem
    ;(localStorage as any).setItem = () => { throw new Error('quota') }
    expect(() => s.setCollapsed(true)).not.toThrow()
    ;(localStorage as any).setItem = orig
  })
})
