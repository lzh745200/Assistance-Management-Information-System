import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BatchOperationBar from '@/components/common/BatchOperationBar.vue'

describe('common/BatchOperationBar.vue', () => {
  it('renders nothing when selectedCount is 0', () => {
    const wrapper = mount(BatchOperationBar, { props: { selectedCount: 0 } })
    expect(wrapper.find('.batch-bar').exists()).toBe(false)
  })

  it('renders nothing when selectedCount is undefined', () => {
    const wrapper = mount(BatchOperationBar)
    expect(wrapper.find('.batch-bar').exists()).toBe(false)
  })

  it('renders bar with count and slot when selectedCount > 0', () => {
    const wrapper = mount(BatchOperationBar, {
      props: { selectedCount: 3 },
      slots: { default: '<button class="act">删除</button>' },
    })
    expect(wrapper.find('.batch-bar').exists()).toBe(true)
    expect(wrapper.find('.batch-bar').text()).toContain('已选 3 项')
    expect(wrapper.find('.act').exists()).toBe(true)
  })
})
