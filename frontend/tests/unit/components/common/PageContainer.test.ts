import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PageContainer from '@/components/common/PageContainer.vue'

describe('common/PageContainer.vue', () => {
  it('renders title, description, filter, footer and default slot', () => {
    const wrapper = mount(PageContainer, {
      props: { title: '页面标题', description: '页面描述' },
      slots: {
        default: '<p class="main">main content</p>',
        filter: '<input class="filter" />',
        footer: '<p class="footer">footer</p>',
        'header-actions': '<button class="action">导出</button>',
      },
    })
    expect(wrapper.find('.page-title').text()).toBe('页面标题')
    expect(wrapper.find('.page-description').text()).toBe('页面描述')
    expect(wrapper.find('.main').text()).toBe('main content')
    expect(wrapper.find('.filter').exists()).toBe(true)
    expect(wrapper.find('.footer').exists()).toBe(true)
    expect(wrapper.find('.action').exists()).toBe(true)
  })

  it('renders header when header slot provided (no title)', () => {
    const wrapper = mount(PageContainer, {
      slots: { header: '<div>custom header</div>', default: 'x' },
    })
    expect(wrapper.find('.page-header').exists()).toBe(true)
  })

  it('omits header/filter/footer when absent', () => {
    const wrapper = mount(PageContainer, { slots: { default: 'x' } })
    expect(wrapper.find('.page-header').exists()).toBe(false)
    expect(wrapper.find('.filter-section').exists()).toBe(false)
    expect(wrapper.find('.footer-section').exists()).toBe(false)
    expect(wrapper.find('.main-section').exists()).toBe(true)
  })

  it('renders header with title but no description', () => {
    const wrapper = mount(PageContainer, { props: { title: 'T' }, slots: { default: 'x' } })
    expect(wrapper.find('.page-header').exists()).toBe(true)
    expect(wrapper.find('.page-description').exists()).toBe(false)
  })
})
