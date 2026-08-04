import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, enableAutoUnmount } from '@vue/test-utils'
import PrintDialog from '@/components/common/PrintDialog.vue'

enableAutoUnmount(afterEach)

const authMock = vi.hoisted(() => ({ user: { username: 'tester' } as { username: string } | null }))
vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({ user: authMock.user }),
}))

const stubs = {
  'el-dialog': {
    name: 'ElDialog',
    props: ['modelValue', 'title', 'beforeClose'],
    emits: ['update:modelValue'],
    template:
      '<div v-if="modelValue" class="el-dialog"><slot /></div><div v-if="modelValue" class="el-dialog-footer"><slot name="footer" /></div>',
  },
  'el-button': {
    name: 'ElButton',
    props: ['type'],
    emits: ['click'],
    template: '<button class="el-btn" @click="$emit(\'click\')"><slot /></button>',
  },
  'el-table': {
    name: 'ElTable',
    props: ['data', 'showHeader'],
    template: '<table class="el-table"><slot /></table>',
  },
  'el-table-column': {
    name: 'ElTableColumn',
    props: ['prop', 'label', 'minWidth'],
    template: '<th class="el-table-col" />',
  },
}

const columns = [
  { key: 'name', label: '名称' },
  { key: 'amount', label: '金额' },
]
const data = [
  { name: 'A', amount: 1 },
  { name: 'B', amount: 2 },
]

function makeFakeIframe(fakeWin: any) {
  const realCreate = document.createElement.bind(document)
  vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
    const el = realCreate(tag)
    if (tag === 'iframe') {
      Object.defineProperty(el, 'contentWindow', { value: fakeWin, configurable: true })
      Object.defineProperty(el, 'contentDocument', {
        value: fakeWin?.document ?? null,
        configurable: true,
      })
    }
    return el
  })
}

describe('common/PrintDialog.vue', () => {
  beforeEach(() => {
    authMock.user = { username: 'tester' }
    vi.restoreAllMocks()
  })

  it('renders dialog with title, printer and table when visible', () => {
    const wrapper = mount(PrintDialog, {
      props: { data, columns, title: '打印报表', visible: true },
      global: { stubs },
    })
    expect(wrapper.find('.el-dialog').exists()).toBe(true)
    expect(wrapper.find('.print-header h2').text()).toBe('打印报表')
    expect(wrapper.find('.print-info').text()).toContain('tester')
    expect(wrapper.findAll('.el-table-col').length).toBe(2)
    expect(wrapper.find('.print-info').text()).toContain('打印时间')
  })

  it('does not render content when visible=false', () => {
    const wrapper = mount(PrintDialog, {
      props: { data, columns, title: 'T', visible: false },
      global: { stubs },
    })
    expect(wrapper.find('.print-content').exists()).toBe(false)
  })

  it('shows 未知用户 when authStore user is missing', () => {
    authMock.user = null
    const wrapper = mount(PrintDialog, {
      props: { data, columns, title: 'T', visible: true },
      global: { stubs },
    })
    expect(wrapper.find('.print-info').text()).toContain('未知用户')
  })

  it('handleUpdateVisible emits update:visible and close when false', async () => {
    const wrapper = mount(PrintDialog, {
      props: { data, columns, title: 'T', visible: true },
      global: { stubs },
    })
    const dialog = wrapper.findComponent({ name: 'ElDialog' })
    dialog.vm.$emit('update:modelValue', false)
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('update:visible')).toBeTruthy()
    expect(wrapper.emitted('update:visible')![0][0]).toBe(false)
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('handleUpdateVisible only emits update:visible when true', async () => {
    const wrapper = mount(PrintDialog, {
      props: { data, columns, title: 'T', visible: true },
      global: { stubs },
    })
    const dialog = wrapper.findComponent({ name: 'ElDialog' })
    dialog.vm.$emit('update:modelValue', true)
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('update:visible')![0][0]).toBe(true)
    expect(wrapper.emitted('close')).toBeFalsy()
  })

  it('handleClose emits update:visible false and close via 关闭 button', async () => {
    const wrapper = mount(PrintDialog, {
      props: { data, columns, title: 'T', visible: true },
      global: { stubs },
    })
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[0].trigger('click')
    expect(wrapper.emitted('update:visible')![0][0]).toBe(false)
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('handlePrint full flow writes into iframe and prints', async () => {
    vi.useFakeTimers()
    const doc = { open: vi.fn(), write: vi.fn(), close: vi.fn() }
    const fakeWin = { document: doc, focus: vi.fn(), print: vi.fn(), onafterprint: null }
    makeFakeIframe(fakeWin)

    const wrapper = mount(PrintDialog, {
      props: { data, columns, title: '报表', visible: true },
      global: { stubs },
    })
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[1].trigger('click')

    vi.advanceTimersByTime(100)
    expect(fakeWin.focus).toHaveBeenCalled()
    expect(fakeWin.print).toHaveBeenCalled()
    expect(doc.open).toHaveBeenCalled()
    expect(doc.close).toHaveBeenCalled()
    const html = doc.write.mock.calls[0][0] as string
    expect(html).toContain('print-table')
    expect(fakeWin.onafterprint).toBeTypeOf('function')

    vi.advanceTimersByTime(5000)
    vi.useRealTimers()
  })

  it('handlePrint cleans up when print throws', async () => {
    vi.useFakeTimers()
    const doc = { open: vi.fn(), write: vi.fn(), close: vi.fn() }
    const fakeWin = {
      document: doc,
      focus: vi.fn(),
      print: vi.fn(() => {
        throw new Error('print denied')
      }),
      onafterprint: null,
    }
    makeFakeIframe(fakeWin)

    const wrapper = mount(PrintDialog, {
      props: { data, columns, title: 'T', visible: true },
      global: { stubs },
    })
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[1].trigger('click')

    vi.advanceTimersByTime(100)
    expect(fakeWin.print).toHaveBeenCalled()
    vi.advanceTimersByTime(5000)
    vi.useRealTimers()
  })

  it('handlePrint returns early when iframe doc is unavailable', async () => {
    vi.useFakeTimers()
    const doc = { open: vi.fn(), write: vi.fn(), close: vi.fn() }
    makeFakeIframe(null)

    const wrapper = mount(PrintDialog, {
      props: { data, columns, title: 'T', visible: true },
      global: { stubs },
    })
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[1].trigger('click')
    vi.advanceTimersByTime(100)
    expect(doc.write).not.toHaveBeenCalled()
    vi.useRealTimers()
  })

  it('handlePrint returns early when printContent ref is missing', () => {
    const wrapper = mount(PrintDialog, {
      props: { data, columns, title: 'T', visible: false },
      global: { stubs },
    })
    const createSpy = vi.spyOn(document, 'createElement')
    ;(wrapper.vm as any).handlePrint()
    expect(createSpy).not.toHaveBeenCalled()
  })

  it('handlePrint removes iframe when contentWindow is missing but contentDocument exists', async () => {
    vi.useFakeTimers()
    const doc = { open: vi.fn(), write: vi.fn(), close: vi.fn() }
    const fakeWin = { document: doc, focus: vi.fn(), print: vi.fn(), onafterprint: null }
    const realCreate = document.createElement.bind(document)
    vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
      const el = realCreate(tag)
      if (tag === 'iframe') {
        Object.defineProperty(el, 'contentWindow', { value: undefined, configurable: true })
        Object.defineProperty(el, 'contentDocument', { value: doc, configurable: true })
      }
      return el
    })

    const wrapper = mount(PrintDialog, {
      props: { data, columns, title: 'T', visible: true },
      global: { stubs },
    })
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[1].trigger('click')
    vi.advanceTimersByTime(100)
    expect(doc.write).toHaveBeenCalled()
    expect(fakeWin.focus).not.toHaveBeenCalled()
    vi.useRealTimers()
  })
})
