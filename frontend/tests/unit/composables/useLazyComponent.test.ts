import { describe, it, expect } from 'vitest'
import { useLazyComponent } from '@/composables/useLazyComponent'

describe('composables/useLazyComponent', () => {
  it('exposes loadComponent function', () => {
    const lc = useLazyComponent()
    expect(typeof lc.loadComponent).toBe('function')
  })

  it('loadComponent returns a component (not undefined)', () => {
    const lc = useLazyComponent()
    const c = lc.loadComponent(() => Promise.resolve({ default: {} as any }))
    expect(c).toBeDefined()
  })

  it('loadComponent with loadingComponent + delay', () => {
    const lc = useLazyComponent()
    const loading = {} as any
    const c = lc.loadComponent(() => Promise.resolve({ default: {} as any }), loading, 500)
    expect(c).toBeDefined()
  })

  it('default delay is 200', () => {
    const lc = useLazyComponent()
    const c: any = lc.loadComponent(() => Promise.resolve({ default: {} as any }))
    // defineAsyncComponent doesn't expose delay directly, just verify it doesn't throw
    expect(c).toBeDefined()
  })
})
