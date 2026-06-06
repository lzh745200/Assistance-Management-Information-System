import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { usePrint, printElement, printCurrentPage } from '@/composables/usePrint'

vi.mock('@/utils/logger', () => ({
  logger: { warn: vi.fn(), info: vi.fn(), error: vi.fn() },
}))
vi.mock('@/utils/sanitize', () => ({
  sanitizeHtml: (html: string) => html,
}))

describe('usePrint', () => {
  it('usePrint 返回 printElement 和 printCurrentPage', () => {
    const result = usePrint()
    expect(result.printElement).toBe(printElement)
    expect(result.printCurrentPage).toBe(printCurrentPage)
  })
})

describe('printElement', () => {
  let mockWindow: any
  let mockElement: any
  let originalGetElement: any
  let originalOpen: any

  beforeAll(() => {
    originalGetElement = document.getElementById
    originalOpen = window.open
  })
  afterAll(() => {
    document.getElementById = originalGetElement
    window.open = originalOpen
  })

  beforeEach(() => {
    mockWindow = {
      document: { write: vi.fn(), close: vi.fn() },
      onload: null as any,
      focus: vi.fn(),
      print: vi.fn(),
    }
    window.open = vi.fn(() => mockWindow) as any
    mockElement = { innerHTML: '<p>hello</p>' }
    document.getElementById = vi.fn(() => mockElement) as any
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('元素不存在时打印警告并不打开窗口', async () => {
    const { logger } = await import('@/utils/logger')
    document.getElementById = vi.fn(() => null) as any
    printElement('not-found')
    expect(logger.warn).toHaveBeenCalledWith(
      expect.stringContaining('找不到元素: #not-found')
    )
    expect(window.open).not.toHaveBeenCalled()
  })

  it('打开新窗口并写入 HTML', () => {
    printElement('test', 'My Title')
    expect(window.open).toHaveBeenCalledWith(
      '',
      '_blank',
      'width=900,height=700'
    )
    expect(mockWindow.document.write).toHaveBeenCalled()
    const html = mockWindow.document.write.mock.calls[0][0] as string
    expect(html).toContain('<!DOCTYPE html>')
    expect(html).toContain('My Title')
    expect(html).toContain('hello')
    expect(mockWindow.document.close).toHaveBeenCalled()
  })

  it('使用默认 title (document.title) 当未提供时', () => {
    Object.defineProperty(document, 'title', { value: 'Default Title', configurable: true })
    printElement('test')
    const html = mockWindow.document.write.mock.calls[0][0] as string
    expect(html).toContain('Default Title')
  })

  it('onload 触发后调用 focus 和 print', () => {
    printElement('test')
    mockWindow.onload()
    expect(mockWindow.focus).toHaveBeenCalled()
    expect(mockWindow.print).toHaveBeenCalled()
  })

  it('window.open 返回 null 时静默退出', () => {
    window.open = vi.fn(() => null) as any
    expect(() => printElement('test')).not.toThrow()
  })
})

describe('printCurrentPage', () => {
  it('直接调用 window.print()', () => {
    const printSpy = vi.spyOn(window, 'print').mockImplementation(() => {})
    printCurrentPage()
    expect(printSpy).toHaveBeenCalled()
  })
})
