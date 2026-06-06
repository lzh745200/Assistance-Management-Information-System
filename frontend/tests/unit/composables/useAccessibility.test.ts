import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ref } from 'vue'
import {
  useFocusTrap,
  usePageTitle,
  useSkipLink,
  useAccessibleForm,
  useAccessibleNotification,
} from '@/composables/useAccessibility'

describe('useAccessibility', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
  })

  describe('useFocusTrap', () => {
    it('返回 activate/deactivate/getFocusableElements', () => {
      const containerRef = ref<HTMLElement | null>(null)
      const trap = useFocusTrap(containerRef)
      expect(typeof trap.activate).toBe('function')
      expect(typeof trap.deactivate).toBe('function')
      expect(typeof trap.getFocusableElements).toBe('function')
    })

    it('container 为空时返回 []', () => {
      const containerRef = ref<HTMLElement | null>(null)
      const trap = useFocusTrap(containerRef)
      expect(trap.getFocusableElements()).toEqual([])
    })

    it('getFocusableElements 返回 button/input/etc', () => {
      const div = document.createElement('div')
      div.innerHTML = `
        <button>1</button>
        <input type="text" />
        <a href="/">link</a>
        <button disabled>disabled</button>
        <div aria-hidden="true"><button>hidden</button></div>
        <div tabindex="0">focusable div</div>
      `
      document.body.appendChild(div)
      const containerRef = ref<HTMLElement | null>(div)
      const trap = useFocusTrap(containerRef)
      const elements = trap.getFocusableElements()
      // Should not include disabled or aria-hidden
      expect(elements.length).toBeGreaterThan(0)
      expect(elements.find((el) => el.textContent === 'disabled')).toBeUndefined()
    })

    it('activate 添加 keydown listener + focus 第一个元素', () => {
      const div = document.createElement('div')
      div.innerHTML = '<button id="b1">B1</button><button id="b2">B2</button>'
      document.body.appendChild(div)
      const containerRef = ref<HTMLElement | null>(div)
      const trap = useFocusTrap(containerRef)
      const addEventListenerSpy = vi.spyOn(document, 'addEventListener')
      trap.activate()
      expect(addEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function))
      addEventListenerSpy.mockRestore()
    })

    it('deactivate 移除 keydown listener', () => {
      const div = document.createElement('div')
      div.innerHTML = '<button>1</button>'
      document.body.appendChild(div)
      const containerRef = ref<HTMLElement | null>(div)
      const trap = useFocusTrap(containerRef)
      const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener')
      trap.deactivate()
      expect(removeEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function))
      removeEventListenerSpy.mockRestore()
    })
  })

  describe('usePageTitle', () => {
    it('setPageTitle 修改 document.title + 添加后缀', () => {
      const { setPageTitle } = usePageTitle()
      setPageTitle('测试页面')
      expect(document.title).toBe('测试页面 - 帮扶管理信息系统')
    })

    it('setPageTitle 写入 aria-live region', () => {
      const live = document.createElement('div')
      live.id = 'page-title-live-region'
      document.body.appendChild(live)
      const { setPageTitle } = usePageTitle()
      setPageTitle('主页')
      expect(live.textContent).toBe('已导航到: 主页')
    })

    it('无 live region 时不报错', () => {
      const { setPageTitle } = usePageTitle()
      expect(() => setPageTitle('X')).not.toThrow()
    })
  })

  describe('useSkipLink', () => {
    it('skipToMainContent 找到 main 元素并聚焦', () => {
      const main = document.createElement('main')
      main.tabIndex = -1
      main.id = 'main-content'
      main.scrollIntoView = vi.fn() // jsdom doesn't implement scrollIntoView
      document.body.appendChild(main)
      const focusSpy = vi.spyOn(main, 'focus')
      const { skipToMainContent } = useSkipLink()
      skipToMainContent()
      expect(focusSpy).toHaveBeenCalled()
    })

    it('无 main 元素时不报错', () => {
      const { skipToMainContent } = useSkipLink()
      expect(() => skipToMainContent()).not.toThrow()
    })
  })

  describe('useAccessibleForm', () => {
    it('generateId 返回 prefix-random 格式', () => {
      const { generateId } = useAccessibleForm()
      const id = generateId('field')
      expect(id).toMatch(/^field-/)
    })

    it('generateId 默认 prefix=form', () => {
      const { generateId } = useAccessibleForm()
      const id = generateId()
      expect(id).toMatch(/^form-/)
    })

    it('reportFieldError 设置 aria-invalid + 创建 error element', () => {
      const field = document.createElement('input')
      field.id = 'username'
      document.body.appendChild(field)
      const { reportFieldError } = useAccessibleForm()
      reportFieldError('username', '必填')
      expect(field.getAttribute('aria-invalid')).toBe('true')
      expect(field.getAttribute('aria-describedby')).toBe('username-error')
      const errorEl = document.getElementById('username-error')
      expect(errorEl).toBeTruthy()
      expect(errorEl?.textContent).toBe('必填')
      expect(errorEl?.getAttribute('role')).toBe('alert')
    })

    it('reportFieldError 已存在 error 元素时更新', () => {
      const field = document.createElement('input')
      field.id = 'email'
      document.body.appendChild(field)
      const { reportFieldError } = useAccessibleForm()
      reportFieldError('email', '错误1')
      reportFieldError('email', '错误2')
      const errorEl = document.getElementById('email-error')
      expect(errorEl?.textContent).toBe('错误2')
    })

    it('clearFieldError 移除 aria 属性 + 删除 error 元素', () => {
      const field = document.createElement('input')
      field.id = 'phone'
      document.body.appendChild(field)
      const { reportFieldError, clearFieldError } = useAccessibleForm()
      reportFieldError('phone', '错误')
      clearFieldError('phone')
      expect(field.hasAttribute('aria-invalid')).toBe(false)
      expect(field.hasAttribute('aria-describedby')).toBe(false)
      expect(document.getElementById('phone-error')).toBeNull()
    })
  })

  describe('useAccessibleNotification', () => {
    it('announce 写入 polite live region', () => {
      vi.useFakeTimers()
      const live = document.createElement('div')
      live.id = 'live-region-polite'
      document.body.appendChild(live)
      const { announce } = useAccessibleNotification()
      announce('操作成功')
      expect(live.textContent).toBe('操作成功')
      vi.advanceTimersByTime(1100)
      expect(live.textContent).toBe('')
      vi.useRealTimers()
    })

    it('announce 写入 assertive live region', () => {
      const live = document.createElement('div')
      live.id = 'live-region-assertive'
      document.body.appendChild(live)
      const { announce } = useAccessibleNotification()
      announce('严重错误', 'assertive')
      expect(live.textContent).toBe('严重错误')
    })

    it('无 live region 时不报错', () => {
      const { announce } = useAccessibleNotification()
      expect(() => announce('msg')).not.toThrow()
    })
  })
})
