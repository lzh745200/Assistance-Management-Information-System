import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import NetworkStatusIndicator from '@/components/common/NetworkStatusIndicator.vue'

describe('NetworkStatusIndicator.vue', () => {
  it('renders offline when online is not provided', () => {
    const w = mount(NetworkStatusIndicator)
    expect(w.classes()).toContain('net-dot')
    expect(w.classes()).toContain('offline')
    expect(w.attributes('title')).toBe('离线')
  })

  it('renders offline when online=false', () => {
    const w = mount(NetworkStatusIndicator, { props: { online: false } })
    expect(w.classes()).toContain('offline')
    expect(w.attributes('title')).toBe('离线')
  })

  it('renders online when online=true', () => {
    const w = mount(NetworkStatusIndicator, { props: { online: true } })
    expect(w.classes()).toContain('online')
    expect(w.attributes('title')).toBe('在线')
  })
})
