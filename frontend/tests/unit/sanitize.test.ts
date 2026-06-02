import { describe, it, expect } from 'vitest'
import { sanitizeHtml, stripHtml, escapeHtml } from '@/utils/sanitize'

describe('sanitize', () => {
  describe('sanitizeHtml', () => {
    it('空值返回空字符串', () => {
      expect(sanitizeHtml('')).toBe('')
      expect(sanitizeHtml(null as any)).toBe('')
      expect(sanitizeHtml(undefined as any)).toBe('')
      expect(sanitizeHtml(123 as any)).toBe('')
    })

    it('保留允许的标签', () => {
      expect(sanitizeHtml('<p>hello</p>')).toBe('<p>hello</p>')
      expect(sanitizeHtml('<strong>bold</strong>')).toBe('<strong>bold</strong>')
      expect(sanitizeHtml('<em>italic</em>')).toBe('<em>italic</em>')
      expect(sanitizeHtml('<br>')).toContain('br')
    })

    it('移除危险标签及其内容', () => {
      // DOMPurify 完全移除 <script>/<iframe> 等危险标签及其内容
      expect(sanitizeHtml('<script>alert(1)</script>')).toBe('')
      // iframe 也被 DOMPurify 完全移除（包括内容）
      const iframeResult = sanitizeHtml('<iframe>test</iframe>')
      expect(iframeResult).not.toContain('iframe')
    })

    it('保留允许的属性', () => {
      const result = sanitizeHtml('<a href="https://example.com" title="link">test</a>')
      expect(result).toContain('href="https://example.com"')
      expect(result).toContain('title="link"')
    })

    it('移除不允许的属性', () => {
      const result = sanitizeHtml('<p onclick="alert(1)">text</p>')
      expect(result).not.toContain('onclick')
      expect(result).toContain('text')
    })

    it('移除危险协议', () => {
      const result = sanitizeHtml('<a href="javascript:alert(1)">click</a>')
      expect(result).not.toContain('javascript:')
    })

    it('移除 data: 协议', () => {
      // 配置了 ALLOWED_URI_REGEXP 拦截 data: 协议
      const result = sanitizeHtml('<img src="data:text/html,<script>alert(1)</script>">')
      expect(result).not.toContain('data:')
    })

    it('为外部链接添加安全属性', () => {
      const result = sanitizeHtml('<a href="https://external.com">link</a>')
      expect(result).toContain('rel="noopener noreferrer"')
      expect(result).toContain('target="_blank"')
    })

    it('内部链接不添加 target=_blank', () => {
      const result = sanitizeHtml('<a href="/internal">link</a>')
      expect(result).not.toContain('target="_blank"')
    })

    it('锚点链接不添加 target=_blank', () => {
      const result = sanitizeHtml('<a href="#section">link</a>')
      expect(result).not.toContain('target="_blank"')
    })

    it('保留 div/span class 属性', () => {
      const result = sanitizeHtml('<div class="highlight">text</div>')
      expect(result).toContain('class="highlight"')
    })

    it('保留 table 相关属性', () => {
      const result = sanitizeHtml('<table class="t"><tr><td colspan="2">cell</td></tr></table>')
      expect(result).toContain('colspan="2"')
    })

    it('保留 img 允许的属性', () => {
      const result = sanitizeHtml('<img src="https://img.com/a.jpg" alt="photo" width="100">')
      expect(result).toContain('src="https://img.com/a.jpg"')
      expect(result).toContain('alt="photo"')
    })
  })

  describe('stripHtml', () => {
    it('空值返回空字符串', () => {
      expect(stripHtml('')).toBe('')
      expect(stripHtml(null as any)).toBe('')
      expect(stripHtml(undefined as any)).toBe('')
      expect(stripHtml(123 as any)).toBe('')
    })

    it('移除所有 HTML 标签', () => {
      expect(stripHtml('<p>hello <strong>world</strong></p>')).toBe('hello world')
    })

    it('处理嵌套标签', () => {
      expect(stripHtml('<div><p>nested</p></div>')).toBe('nested')
    })
  })

  describe('escapeHtml', () => {
    it('空值返回空字符串', () => {
      expect(escapeHtml('')).toBe('')
      expect(escapeHtml(null as any)).toBe('')
      expect(escapeHtml(undefined as any)).toBe('')
      expect(escapeHtml(123 as any)).toBe('')
    })

    it('转义特殊字符', () => {
      expect(escapeHtml('&')).toBe('&amp;')
      expect(escapeHtml('<')).toBe('&lt;')
      expect(escapeHtml('>')).toBe('&gt;')
      expect(escapeHtml('"')).toBe('&quot;')
      expect(escapeHtml("'")).toBe('&#39;')
    })

    it('转义组合字符', () => {
      expect(escapeHtml('<script>"test" & \'val\'</script>')).toBe(
        '&lt;script&gt;&quot;test&quot; &amp; &#39;val&#39;&lt;/script&gt;'
      )
    })

    it('普通文本不变', () => {
      expect(escapeHtml('hello world')).toBe('hello world')
    })
  })
})
