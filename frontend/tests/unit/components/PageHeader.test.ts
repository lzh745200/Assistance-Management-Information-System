import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PageHeader from '@/components/PageHeader.vue'

describe('PageHeader.vue', () => {
  it('renders title and slot', () => {
    const w = mount(PageHeader, { props: { title: '测试标题' }, slots: { default: '<button>按钮</button>' } })
    expect(w.text()).toContain('测试标题')
    expect(w.find('button').exists()).toBe(true)
    expect(w.find('p.page-desc').exists()).toBe(false)
  })

  it('renders description when provided', () => {
    const w = mount(PageHeader, { props: { title: '标题', description: '描述文本' } })
    expect(w.find('p.page-desc').text()).toBe('描述文本')
  })

  it('default description is empty string', () => {
    const w = mount(PageHeader, { props: { title: '标题' } })
    expect(w.props('description')).toBe('')
    expect(w.text()).toContain('标题')
  })
})
