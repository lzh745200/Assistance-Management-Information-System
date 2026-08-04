import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, enableAutoUnmount } from '@vue/test-utils'
import PrintTable from '@/components/common/PrintTable.vue'

enableAutoUnmount(afterEach)

const stubs = {
  'el-button': {
    name: 'ElButton',
    props: ['type'],
    emits: ['click'],
    template: '<button class="el-btn" @click="$emit(\'click\')"><slot /></button>',
  },
  'el-icon': { name: 'ElIcon', template: '<i class="el-icon"><slot /></i>' },
}

const columns = [
  { key: 'name', label: '名称' },
  { key: 'detail.amount', label: '金额' },
]
const data = [
  { name: '项目A', detail: { amount: 100 } },
  { name: '项目B', detail: 5 },
  { name: '项目C' },
]

describe('common/PrintTable.vue', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders nothing when visible=false', () => {
    const wrapper = mount(PrintTable, { props: { data, columns, title: 'T', visible: false } })
    expect(wrapper.find('.print-overlay').exists()).toBe(false)
  })

  it('renders table with header, rows and footer when visible', () => {
    const wrapper = mount(PrintTable, {
      props: { data, columns, title: '打印标题', visible: true },
      global: { stubs },
    })
    expect(wrapper.find('.print-overlay').exists()).toBe(true)
    expect(wrapper.find('.print-header h2').text()).toBe('打印标题')
    const headers = wrapper.findAll('thead th').map((t) => t.text())
    expect(headers).toEqual(['名称', '金额'])
    const rows = wrapper.findAll('tbody tr')
    expect(rows.length).toBe(3)
    expect(rows[0].findAll('td').map((t) => t.text())).toEqual(['项目A', '100'])
    expect(rows[1].findAll('td')[1].text()).toBe('')
    expect(rows[2].findAll('td')[1].text()).toBe('')
    expect(wrapper.find('.print-footer').text()).toContain('共 3 条记录')
  })

  it('closes and emits close via 关闭 button', async () => {
    const wrapper = mount(PrintTable, {
      props: { data, columns, title: 'T', visible: true },
      global: { stubs },
    })
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[1].trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('returns early when window.open returns null', async () => {
    vi.spyOn(window, 'open').mockReturnValue(null)
    const wrapper = mount(PrintTable, {
      props: { data, columns, title: 'T', visible: true },
      global: { stubs },
    })
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[0].trigger('click')
    expect(window.open).toHaveBeenCalledWith('', '_blank')
  })

  it('writes print content into opened window', async () => {
    const write = vi.fn()
    const close = vi.fn()
    const fakeWin = { document: { write, close } }
    vi.spyOn(window, 'open').mockReturnValue(fakeWin as any)
    const wrapper = mount(PrintTable, {
      props: { data, columns, title: '<script>alert(1)</script>', visible: true },
      global: { stubs },
    })
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[0].trigger('click')
    expect(window.open).toHaveBeenCalledWith('', '_blank')
    const html = write.mock.calls[0][0] as string
    expect(html).toContain('print-table')
    expect(html).toContain('&lt;script&gt;alert(1)&lt;/script&gt;')
    expect(close).toHaveBeenCalled()
  })

  it('handles data with falsy values and nested keys', () => {
    const wrapper = mount(PrintTable, {
      props: {
        data: [{ name: '', detail: { amount: 0 } }],
        columns,
        title: 'T',
        visible: true,
      },
      global: { stubs },
    })
    const cells = wrapper.findAll('tbody td')
    expect(cells.length).toBe(2)
    expect(cells[0].text()).toBe('')
    expect(cells[1].text()).toBe('')
  })
})
