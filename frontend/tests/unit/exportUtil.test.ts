/**
 * exportUtil 单元测试
 * 覆盖: src/utils/exportUtil.ts
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { exportUtil } from '@/utils/exportUtil'

describe('exportUtil', () => {
  // ==================== exportToCSV ====================

  describe('exportToCSV', () => {
    let mockCreateElement: any
    let mockAppendChild: any
    let mockRemoveChild: any
    let clickSpy: ReturnType<typeof vi.fn>

    beforeEach(() => {
      clickSpy = vi.fn()
      mockCreateElement = vi.spyOn(document, 'createElement').mockReturnValue({
        href: '',
        download: '',
        style: {},
        click: clickSpy,
      } as any)
      mockAppendChild = vi.spyOn(document.body, 'appendChild').mockImplementation((n) => n)
      mockRemoveChild = vi.spyOn(document.body, 'removeChild').mockImplementation((n) => n)
    })

    it('should do nothing for empty data', () => {
      exportUtil.exportToCSV([], 'test')
      expect(mockCreateElement).not.toHaveBeenCalled()
    })

    it('should create download link for data', () => {
      const data = [
        { name: '张三', age: 25 },
        { name: '李四', age: 30 },
      ]
      exportUtil.exportToCSV(data, 'users')

      expect(mockCreateElement).toHaveBeenCalledWith('a')
      expect(clickSpy).toHaveBeenCalled()
      expect(mockAppendChild).toHaveBeenCalled()
      expect(mockRemoveChild).toHaveBeenCalled()
    })

    it('should use custom headers', () => {
      const data = [
        { name: '张三', age: 25 },
      ]
      const headers = { name: '姓名', age: '年龄' }

      exportUtil.exportToCSV(data, 'users', headers)
      expect(mockCreateElement).toHaveBeenCalledWith('a')
      expect(clickSpy).toHaveBeenCalled()
    })

    it('should handle values with commas', () => {
      const data = [
        { name: '张三,Jr', age: 25 },
      ]
      // Should not throw
      exportUtil.exportToCSV(data, 'test')
      expect(clickSpy).toHaveBeenCalled()
    })

    it('should handle null/undefined values', () => {
      const data = [
        { name: null, age: undefined },
      ] as any
      exportUtil.exportToCSV(data, 'test')
      expect(clickSpy).toHaveBeenCalled()
    })
  })

  // ==================== downloadBlob → triggerDownload migration ====================

  describe('downloadBlob → triggerDownload', () => {
    it('triggerDownload is available from @/api/export', async () => {
      const mod = await import('@/api/export')
      expect(mod.triggerDownload).toBeDefined()
      expect(typeof mod.triggerDownload).toBe('function')
    })
  })
})
