import { describe, it, expect } from 'vitest'
import { sanitizeHtml, stripHtml, escapeHtml } from '@/utils/sanitize'
import sanitizeDefault from '@/utils/sanitize'

describe('sanitize', () => {
  describe('sanitizeHtml', () => {
    it('空字符串返回空字符串', () => {
      expect(sanitizeHtml('')).toBe('')
    })

    it('null/undefined/数字 返回空字符串', () => {
      expect(sanitizeHtml(null as any)).toBe('')
      expect(sanitizeHtml(undefined as any)).toBe('')
      expect(sanitizeHtml(123 as any)).toBe('')
    })

    it('保留允许的标签 (p, b, strong)', () => {
      const html = '<p>hello <b>world</b></p>'
      const result = sanitizeHtml(html)
      expect(result).toContain('<p>')
      expect(result).toContain('<b>')
    })

    it('移除 script 标签', () => {
      const html = '<p>safe</p><script>alert(1)</script>'
      const result = sanitizeHtml(html)
      expect(result).not.toContain('<script>')
      expect(result).not.toContain('alert(1)')
    })

    it('移除 onclick 等事件属性', () => {
      const html = '<p onclick="alert(1)">click me</p>'
      const result = sanitizeHtml(html)
      expect(result).not.toContain('onclick')
    })

    it('移除 javascript: 链接', () => {
      const html = '<a href="javascript:alert(1)">click</a>'
      const result = sanitizeHtml(html)
      expect(result).not.toContain('javascript:')
    })

    it('移除 data: 链接', () => {
      const html = '<a href="data:text/html,<script>alert(1)</script>">x</a>'
      const result = sanitizeHtml(html)
      expect(result).not.toContain('data:text/html')
    })

    it('保留正常 https 链接 + target=_blank + rel=noopener', () => {
      const html = '<a href="https://example.com">link</a>'
      const result = sanitizeHtml(html)
      expect(result).toContain('href="https://example.com"')
      expect(result).toContain('target="_blank"')
      expect(result).toContain('rel="noopener noreferrer"')
    })

    it('内部 # 链接不加 target', () => {
      const html = '<a href="#section">section</a>'
      const result = sanitizeHtml(html)
      expect(result).toContain('href="#section"')
      expect(result).not.toContain('target="_blank"')
    })

    it('内部 / 路径不加 target', () => {
      const html = '<a href="/page">page</a>'
      const result = sanitizeHtml(html)
      expect(result).not.toContain('target="_blank"')
    })
  })

  describe('stripHtml', () => {
    it('空字符串返回空字符串', () => {
      expect(stripHtml('')).toBe('')
    })

    it('null/undefined 返回空字符串', () => {
      expect(stripHtml(null as any)).toBe('')
      expect(stripHtml(undefined as any)).toBe('')
    })

    it('纯文本直接返回', () => {
      expect(stripHtml('hello world')).toBe('hello world')
    })

    it('移除所有 HTML 标签但保留文本', () => {
      expect(stripHtml('<p>hello <b>world</b></p>')).toContain('hello')
      expect(stripHtml('<p>hello <b>world</b></p>')).toContain('world')
    })

    it('完全移除 script 标签', () => {
      expect(stripHtml('<script>alert(1)</script>')).not.toContain('alert(1)')
    })
  })

  describe('escapeHtml', () => {
    it('空字符串返回空字符串', () => {
      expect(escapeHtml('')).toBe('')
    })

    it('null/undefined 返回空字符串', () => {
      expect(escapeHtml(null as any)).toBe('')
      expect(escapeHtml(undefined as any)).toBe('')
    })

    it('转义 < > & " \'', () => {
      expect(escapeHtml('<script>')).toBe('&lt;script&gt;')
      expect(escapeHtml('&')).toBe('&amp;')
      expect(escapeHtml('"hello"')).toBe('&quot;hello&quot;')
      expect(escapeHtml("it's")).toBe('it&#39;s')
    })

    it('混合文本正确转义', () => {
      const text = `<a href="evil">x & y</a>`
      const result = escapeHtml(text)
      expect(result).toContain('&lt;')
      expect(result).toContain('&gt;')
      expect(result).toContain('&quot;')
      expect(result).toContain('&amp;')
    })

    it('无特殊字符时不变', () => {
      expect(escapeHtml('hello world')).toBe('hello world')
    })
  })

  describe('危险协议补充（hook 分支）', () => {
    it('vbscript: / file: 协议被移除', () => {
      expect(sanitizeHtml('<a href="vbscript:msgbox(1)">x</a>')).not.toContain('vbscript:')
      expect(sanitizeHtml('<a href="file:///etc/passwd">x</a>')).not.toContain('file:')
    })

    it('协议大小写混合同样被拦截', () => {
      expect(sanitizeHtml('<a href="JaVaScRiPt:alert(1)">x</a>')).not.toContain('JaVaScRiPt')
      expect(sanitizeHtml('<a href="JaVaScRiPt:alert(1)">x</a>')).not.toContain('href=')
    })

    it('带前导空格的危险协议（DOMPurify 放行，自定义 hook 拦截）', () => {
      const a = sanitizeHtml('<a href=" file:///etc/passwd">x</a>')
      expect(a).not.toContain('href')
      const b = sanitizeHtml('<a href=" javascript:alert(1)">x</a>')
      expect(b).not.toContain('href')
      const c = sanitizeHtml('<img src=" vbscript:msgbox(1)" alt="i">')
      expect(c).not.toContain('src=')
    })

    it('img src data: URI（DOMPurify 默认放行 data URI 标签）被自定义 hook 移除', () => {
      const r = sanitizeHtml('<img src="data:image/png;base64,iVBORw0KGgo=" alt="x">')
      expect(r).not.toContain('src=')
    })

    it('img src 危险协议移除、正常 src 保留', () => {
      const evil = sanitizeHtml('<img src="javascript:alert(1)" alt="x">')
      expect(evil).not.toContain('javascript:')
      const ok = sanitizeHtml('<img src="/static/a.png" alt="y">')
      expect(ok).toContain('/static/a.png')
    })

    it('无 href 的 a 标签只加 rel，不加 target', () => {
      const r = sanitizeHtml('<a>plain</a>')
      expect(r).toContain('rel="noopener noreferrer"')
      expect(r).not.toContain('target="_blank"')
    })

    it('外部链接（非 # 非 /）加 target=_blank', () => {
      expect(sanitizeHtml('<a href="https://example.com/x">x</a>')).toContain(
        'target="_blank"'
      )
    })
  })

  describe('stripHtml 兜底分支', () => {
    it('无可见文本时 textContent 为空 → innerText 兜底，不抛错', () => {
      const r = stripHtml('<div></div>')
      expect(r).toBeFalsy()
    })
  })

  describe('default export', () => {
    it('包含三个函数', () => {
      expect(typeof sanitizeDefault.sanitizeHtml).toBe('function')
      expect(typeof sanitizeDefault.stripHtml).toBe('function')
      expect(typeof sanitizeDefault.escapeHtml).toBe('function')
      expect(sanitizeDefault.sanitizeHtml('<script>x</script>')).not.toContain('<script>')
      expect(sanitizeDefault.stripHtml('<b>t</b>')).toContain('t')
      expect(sanitizeDefault.escapeHtml('<')).toBe('&lt;')
    })
  })
})
