import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Skeleton from '@/components/common/Skeleton/Skeleton.vue'

describe('common/Skeleton/Skeleton.vue', () => {
  it('renders rect variant by default with loading state', () => {
    const wrapper = mount(Skeleton)
    expect(wrapper.find('.skeleton__rect').exists()).toBe(true)
    expect(wrapper.classes()).toContain('skeleton--rect')
    expect(wrapper.classes()).toContain('skeleton--pulse')
    expect(wrapper.classes()).toContain('skeleton--loading')
    expect(wrapper.attributes('role')).toBe('status')
    expect(wrapper.attributes('aria-busy')).toBe('true')
  })

  it('renders slot content when loading=false (rect skeleton still rendered)', () => {
    const wrapper = mount(Skeleton, {
      props: { loading: false },
      slots: { default: '<p class="content">ready</p>' },
    })
    expect(wrapper.find('.content').text()).toBe('ready')
    expect(wrapper.find('.skeleton__rect').exists()).toBe(true)
    expect(wrapper.classes()).not.toContain('skeleton--loading')
    expect(wrapper.attributes('aria-busy')).toBe('false')
  })

  it('renders circle variant with numeric width', () => {
    const wrapper = mount(Skeleton, { props: { variant: 'circle', width: 80 } })
    const circle = wrapper.find('.skeleton__circle')
    expect(circle.exists()).toBe(true)
    expect(circle.attributes('style')).toContain('width: 80px')
    expect(circle.attributes('style')).toContain('height: 80px')
  })

  it('renders circle variant with string width fallback', () => {
    const wrapper = mount(Skeleton, { props: { variant: 'circle' } })
    const circle = wrapper.find('.skeleton__circle')
    expect(circle.attributes('style')).toContain('width: 40px')
  })

  it('renders text variant with rows and last-row width 60%', () => {
    const wrapper = mount(Skeleton, { props: { variant: 'text', rows: 3 } })
    const lines = wrapper.findAll('.skeleton__text-line')
    expect(lines.length).toBe(3)
    expect(lines[0].attributes('style')).toContain('width: 100%')
    expect(lines[2].attributes('style')).toContain('width: 60%')
  })

  it('renders text variant when row index equals rows count', () => {
    const wrapper = mount(Skeleton, { props: { variant: 'text', rows: 1 } })
    const lines = wrapper.findAll('.skeleton__text-line')
    expect(lines[0].attributes('style')).toContain('width: 60%')
  })

  it('renders list variant with avatar', () => {
    const wrapper = mount(Skeleton, { props: { variant: 'list', rows: 2, avatar: true } })
    expect(wrapper.findAll('.skeleton__list-item').length).toBe(2)
    expect(wrapper.find('.skeleton__avatar').exists()).toBe(true)
  })

  it('renders list variant without avatar', () => {
    const wrapper = mount(Skeleton, { props: { variant: 'list', avatar: false } })
    expect(wrapper.find('.skeleton__avatar').exists()).toBe(false)
  })

  it('renders list variant with string avatarSize', () => {
    const wrapper = mount(Skeleton, { props: { variant: 'list', avatar: true, avatarSize: '56px' } })
    expect(wrapper.find('.skeleton__avatar').attributes('style')).toContain('width: 56px')
  })

  it('renders card variant with image and without image', () => {
    const withImage = mount(Skeleton, { props: { variant: 'card', image: true } })
    expect(withImage.find('.skeleton__image').exists()).toBe(true)

    const withoutImage = mount(Skeleton, { props: { variant: 'card', image: false } })
    expect(withoutImage.find('.skeleton__image').exists()).toBe(false)
  })

  it('renders form variant with rows', () => {
    const wrapper = mount(Skeleton, { props: { variant: 'form', rows: 2 } })
    expect(wrapper.findAll('.skeleton__form-item').length).toBe(2)
  })

  it('renders table variant with columns and rows', () => {
    const wrapper = mount(Skeleton, { props: { variant: 'table', rows: 3, columns: 4 } })
    expect(wrapper.findAll('.skeleton__table-row').length).toBe(3)
    expect(wrapper.findAll('.skeleton__table-header .skeleton__table-cell').length).toBe(4)
  })

  it('applies numeric width/height and animation wave', () => {
    const wrapper = mount(Skeleton, {
      props: { variant: 'rect', width: 100, height: 50, animation: 'wave' },
    })
    const rect = wrapper.find('.skeleton__rect')
    expect(rect.attributes('style')).toContain('width: 100px')
    expect(rect.attributes('style')).toContain('height: 50px')
    expect(wrapper.classes()).toContain('skeleton--wave')
  })

  it('applies string width/height with fallbacks', () => {
    const wrapper = mount(Skeleton, { props: { variant: 'rect', width: '200px', height: '' } })
    const rect = wrapper.find('.skeleton__rect')
    expect(rect.attributes('style')).toContain('width: 200px')
    expect(rect.attributes('style')).toContain('height: 20px')
  })

  it('applies numeric borderRadius as px and string as-is', () => {
    const num = mount(Skeleton, { props: { borderRadius: 8 } })
    expect(num.attributes('style')).toContain('--skeleton-border-radius: 8px')

    const str = mount(Skeleton, { props: { borderRadius: '12px' } })
    expect(str.attributes('style')).toContain('--skeleton-border-radius: 12px')
  })

  it('renders animation none variant', () => {
    const wrapper = mount(Skeleton, { props: { animation: 'none' } })
    expect(wrapper.classes()).toContain('skeleton--none')
  })
})
