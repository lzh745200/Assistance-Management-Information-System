import { describe, it, expect } from 'vitest'
import { mount, enableAutoUnmount } from '@vue/test-utils'
import { afterEach } from 'vitest'
import VirtualList from '@/components/common/VirtualList.vue'

enableAutoUnmount(afterEach)

const items = Array.from({ length: 100 }, (_, i) => ({ id: i, label: `item-${i}` }))

describe('common/VirtualList.vue', () => {
  it('renders visible items with slot data and index', () => {
    const wrapper = mount(VirtualList, {
      props: { items, itemHeight: 40, containerHeight: 400, buffer: 5 },
      slots: { default: '<template #default="{ item, index }"><p class="vitem">{{ item.label }}-{{ index }}</p></template>' },
    })
    const rendered = wrapper.findAll('.vitem')
    expect(rendered.length).toBeGreaterThan(0)
    expect(rendered[0].text()).toBe('item-0-0')
  })

  it('renders default container height (400) and buffer (5)', () => {
    const wrapper = mount(VirtualList, {
      props: { items, itemHeight: 40 },
      slots: { default: '<template #default="{}"><p class="vitem">x</p></template>' },
    })
    expect(wrapper.attributes('style')).toContain('height: 400px')
    expect(wrapper.findAll('.vitem').length).toBeGreaterThan(0)
  })

  it('handles empty items', () => {
    const wrapper = mount(VirtualList, {
      props: { items: [], itemHeight: 40 },
      slots: { default: '<p class="vitem">x</p>' },
    })
    expect(wrapper.findAll('.vitem').length).toBe(0)
    const inner = wrapper.find('.virtual-list > div')
    expect(inner.attributes('style')).toContain('height: 0px')
  })

  it('updates visible window when scrolling', async () => {
    const wrapper = mount(VirtualList, {
      props: { items, itemHeight: 40, containerHeight: 400, buffer: 5 },
      slots: { default: '<template #default="{ item, index }"><p class="vitem">{{ item.id }}-{{ index }}</p></template>' },
    })
    const listEl = wrapper.find('.virtual-list').element as HTMLElement
    Object.defineProperty(listEl, 'scrollTop', { value: 2000, writable: true, configurable: true })
    listEl.dispatchEvent(new Event('scroll'))
    await wrapper.vm.$nextTick()

    const rendered = wrapper.findAll('.vitem')
    const first = Number(rendered[0].text().split('-')[0])
    expect(first).toBeGreaterThan(0)
    expect(first).toBe(45)
  })

  it('reads initial scrollTop on mount', async () => {
    const wrapper = mount(VirtualList, {
      props: { items, itemHeight: 40, containerHeight: 400, buffer: 5 },
      slots: { default: '<p class="vitem">x</p>' },
    })
    await wrapper.vm.$nextTick()
    expect(wrapper.findAll('.vitem').length).toBeGreaterThan(0)
  })

  it('caps endIndex at items length (scrolled to bottom)', async () => {
    const wrapper = mount(VirtualList, {
      props: { items, itemHeight: 40, containerHeight: 400, buffer: 5 },
      slots: { default: '<p class="vitem">x</p>' },
    })
    const listEl = wrapper.find('.virtual-list').element as HTMLElement
    Object.defineProperty(listEl, 'scrollTop', { value: 100000, writable: true, configurable: true })
    listEl.dispatchEvent(new Event('scroll'))
    await wrapper.vm.$nextTick()
    const last = wrapper.findAll('.vitem')
    expect(last.length).toBeLessThanOrEqual(items.length)
  })
})
