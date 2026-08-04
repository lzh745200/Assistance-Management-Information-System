import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import SkipLink from '@/components/common/SkipLink.vue'

describe('common/SkipLink.vue', () => {
  it('renders skip link with href', () => {
    const wrapper = mount(SkipLink)
    expect(wrapper.find('.skip-link').text()).toContain('跳转到主要内容')
    expect(wrapper.attributes('href')).toBe('#main-content')
  })

  it('calls skipToMainContent on click and prevents default', async () => {
    const scrollSpy = vi.fn()
    Object.defineProperty(Element.prototype, 'scrollIntoView', {
      value: scrollSpy,
      writable: true,
      configurable: true,
    })
    const wrapper = mount(SkipLink)
    const main = document.createElement('main')
    main.setAttribute('tabindex', '-1')
    document.body.appendChild(main)

    await wrapper.find('.skip-link').trigger('click')
    expect(scrollSpy).toHaveBeenCalled()

    document.body.removeChild(main)
  })
})
