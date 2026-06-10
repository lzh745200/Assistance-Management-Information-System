import { describe, it, expect } from 'vitest'
import { useRoutePreload } from '@/composables/useRoutePreload'

describe('composables/useRoutePreload', () => {
  it('preloadRoute is a function that does nothing', () => {
    const r = useRoutePreload()
    expect(typeof r.preloadRoute).toBe('function')
    expect(() => r.preloadRoute('/any')).not.toThrow()
  })
})
