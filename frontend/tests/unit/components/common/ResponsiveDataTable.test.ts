import { describe, it, expect, afterEach, vi } from 'vitest'
import { mount, enableAutoUnmount } from '@vue/test-utils'
import ResponsiveDataTable from '@/components/common/ResponsiveDataTable.vue'

enableAutoUnmount(afterEach)

const stubs = {
  'el-table': {
    name: 'ElTable',
    props: ['data'],
    template: '<table class="el-table"><slot /></table>',
  },
  'el-pagination': {
    name: 'ElPagination',
    props: ['currentPage', 'pageSize', 'total', 'pageSizes', 'small'],
    emits: ['update:currentPage', 'update:pageSize'],
    template: '<div class="el-pagination" />',
  },
  'el-icon': { name: 'ElIcon', template: '<i class="el-icon"><slot /></i>' },
}

function setViewport(width: number) {
  Object.defineProperty(window, 'innerWidth', { value: width, configurable: true, writable: true })
}

describe('common/ResponsiveDataTable.vue', () => {
  it('renders desktop table when viewport >= 768', () => {
    setViewport(1200)
    const wrapper = mount(ResponsiveDataTable, {
      props: { data: [{ id: 1, name: 'a' }] },
      slots: { default: '<el-table-column label="x" />' },
      global: { stubs },
    })
    expect(wrapper.find('.desktop-table').exists()).toBe(true)
    expect(wrapper.find('.mobile-card-list').exists()).toBe(false)
  })

  it('renders mobile card list when viewport < 768 and emits row-click', async () => {
    setViewport(500)
    const wrapper = mount(ResponsiveDataTable, {
      props: {
        data: [{ id: 1, name: '项目一', status: '已完成' }],
        cardFields: [
          { key: 'amount', label: '金额' },
          { key: 'ratio', label: '比例', format: 'currency' },
          { key: 'pct', label: '百分比', format: 'percent' },
          { key: 'date', label: '日期', format: 'date' },
          { key: 'plain', label: '文本' },
        ],
        cardTitleKey: 'name',
        cardBadgeKey: 'status',
      },
      global: { stubs },
    })
    expect(wrapper.find('.mobile-card-list').exists()).toBe(true)
    expect(wrapper.find('.card-title').text()).toBe('项目一')
    expect(wrapper.find('.card-badge').text()).toBe('已完成')
    expect(wrapper.find('.card-badge').classes()).toContain('badge-success')

    await wrapper.find('.data-card').trigger('click')
    expect(wrapper.emitted('row-click')).toBeTruthy()
    expect(wrapper.emitted('row-click')![0][0]).toEqual({
      id: 1,
      name: '项目一',
      status: '已完成',
    })
  })

  it('formats card fields: currency, percent, date, null and plain', () => {
    setViewport(500)
    const wrapper = mount(ResponsiveDataTable, {
      props: {
        data: [
          {
            id: 2,
            amount: 12345.6,
            ratio: 0.5,
            pct: 12.345,
            date: '2024-01-15T10:00:00Z',
            plain: 'text',
            none: null,
          },
        ],
        cardFields: [
          { key: 'amount', label: '金额', format: 'currency' },
          { key: 'ratio', label: '比例', format: 'percent' },
          { key: 'pct', label: '百分比', format: 'percent' },
          { key: 'date', label: '日期', format: 'date' },
          { key: 'plain', label: '文本' },
          { key: 'none', label: '空值' },
        ],
      },
      global: { stubs },
    })
    const values = wrapper.findAll('.field-value').map((v) => v.text())
    expect(values[0]).toBe('¥12,345.6')
    expect(values[1]).toBe('0.5%')
    expect(values[2]).toBe('12.3%')
    expect(values[3]).toBe('2024-01-15')
    expect(values[4]).toBe('text')
    expect(values[5]).toBe('-')
  })

  it('falls back title/badge and badge classes for danger/warning/info', () => {
    setViewport(500)
    const wrapper = mount(ResponsiveDataTable, {
      props: {
        data: [
          { id: 3, status: '已超期' },
          { id: 4, label: '标签名', badge: 'pending' },
          { id: 5, status: '进行中' },
        ],
      },
      global: { stubs },
    })
    const titles = wrapper.findAll('.card-title').map((t) => t.text())
    expect(titles[0]).toBe('#3')
    expect(titles[1]).toBe('标签名')
    expect(titles[2]).toBe('#5')
    const badges = wrapper.findAll('.card-badge')
    expect(badges[0].classes()).toContain('badge-danger')
    expect(badges[1].classes()).toContain('badge-warning')
    expect(badges[2].classes()).toContain('badge-info')
  })

  it('falls back to # with empty id when no title fields present', () => {
    setViewport(500)
    const wrapper = mount(ResponsiveDataTable, {
      props: { data: [{ status: 'x' }, { id: 0, status: 'y' }] },
      global: { stubs },
    })
    const titles = wrapper.findAll('.card-title').map((t) => t.text())
    expect(titles[0]).toBe('#')
    expect(titles[1]).toBe('#')
  })

  it('renders empty state when data prop is undefined', () => {
    setViewport(500)
    const wrapper = mount(ResponsiveDataTable, {
      props: { data: undefined },
      global: { stubs },
    })
    expect(wrapper.find('.empty-state').text()).toContain('暂无数据')
  })

  it('falls back to 暂无数据 when emptyText prop is empty string', () => {
    setViewport(500)
    const wrapper = mount(ResponsiveDataTable, {
      props: { data: [], emptyText: '' },
      global: { stubs },
    })
    expect(wrapper.find('.empty-state').text()).toContain('暂无数据')
  })

  it('forward table events from computed tableEvents map', async () => {
    setViewport(1200)
    const wrapper = mount(ResponsiveDataTable, {
      props: { data: [{ id: 1, name: 'x' }] },
      global: { stubs },
    })
    const table = wrapper.findComponent({ name: 'ElTable' })
    const attrs: any = table.vm.$attrs
    expect(Object.keys(attrs)).toContain('class')
  })

  it('renders card-actions slot', () => {
    setViewport(500)
    const wrapper = mount(ResponsiveDataTable, {
      props: { data: [{ id: 1, name: 'x' }] },
      slots: {
        'card-actions': '<template #default="{ row }"><button class="act">{{ row.name }}</button></template>',
      },
      global: { stubs },
    })
    expect(wrapper.find('.act').text()).toBe('x')
  })

  it('renders empty state on mobile when no data', () => {
    setViewport(500)
    const wrapper = mount(ResponsiveDataTable, {
      props: { data: [], emptyText: '没有数据' },
      global: { stubs },
    })
    expect(wrapper.find('.empty-state').text()).toContain('没有数据')
  })

  it('renders empty state with default text and no pagination when total 0', () => {
    setViewport(500)
    const wrapper = mount(ResponsiveDataTable, {
      props: { data: [], showPagination: true, total: 0 },
      global: { stubs },
    })
    expect(wrapper.find('.empty-state').text()).toContain('暂无数据')
    expect(wrapper.find('.el-pagination').exists()).toBe(false)
  })

  it('renders pagination when showPagination and total > 0, forwards page events', async () => {
    setViewport(1200)
    const wrapper = mount(ResponsiveDataTable, {
      props: { data: [{ id: 1 }], showPagination: true, total: 50 },
      global: { stubs },
    })
    const pagination = wrapper.findComponent({ name: 'ElPagination' })
    expect(pagination.exists()).toBe(true)
    expect(pagination.props('small')).toBe(false)

    pagination.vm.$emit('update:currentPage', 3)
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('page-change')).toBeTruthy()
    expect(wrapper.emitted('page-change')![0][0]).toBe(3)

    pagination.vm.$emit('update:pageSize', 20)
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('size-change')).toBeTruthy()
    expect(wrapper.emitted('size-change')![0][0]).toBe(20)
  })

  it('switches from mobile to desktop on resize', async () => {
    setViewport(500)
    const wrapper = mount(ResponsiveDataTable, {
      props: { data: [{ id: 1, name: 'x' }] },
      global: { stubs },
    })
    expect(wrapper.find('.mobile-card-list').exists()).toBe(true)

    setViewport(1000)
    window.dispatchEvent(new Event('resize'))
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.desktop-table').exists()).toBe(true)
  })
})
