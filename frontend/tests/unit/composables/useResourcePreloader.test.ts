import { describe, it, expect } from 'vitest'
import { useResourcePreloader } from '@/composables/useResourcePreloader'

describe('composables/useResourcePreloader', () => {
  it('initial state', () => {
    const p = useResourcePreloader()
    expect(p.loaded.value).toBe(false)
    expect(p.progress.value).toBe(0)
  })

  it('preloadImages empty -> loaded=true, progress=0', async () => {
    const p = useResourcePreloader()
    await p.preloadImages([])
    expect(p.loaded.value).toBe(true)
    expect(p.progress.value).toBe(0)
  })

  it('preloadImages all onload -> progress=100, loaded=true', async () => {
    class MockImg {
      onload: any
      onerror: any
      src = ''
      constructor() { setTimeout(() => this.onload?.(), 0) }
    }
    ;(globalThis as any).Image = MockImg
    const p = useResourcePreloader()
    await p.preloadImages(['a.png', 'b.png', 'c.png'])
    expect(p.loaded.value).toBe(true)
    expect(p.progress.value).toBe(100)
  })

  it('preloadImages all onerror -> still progress=100', async () => {
    class MockImg {
      onload: any
      onerror: any
      src = ''
      constructor() { setTimeout(() => this.onerror?.(), 0) }
    }
    ;(globalThis as any).Image = MockImg
    const p = useResourcePreloader()
    await p.preloadImages(['a.png'])
    expect(p.loaded.value).toBe(true)
    expect(p.progress.value).toBe(100)
  })
})
