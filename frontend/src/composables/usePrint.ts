import { logger } from '@/utils/logger'
import { sanitizeHtml } from '@/utils/sanitize'

/**
 * 打印功能 composable
 * 提供打印预览和直接打印能力
 */

/**
 * 打印指定区域的内容
 * @param elementId 要打印的 DOM 元素 ID
 * @param title 打印页面标题
 */
export function printElement(elementId: string, title?: string) {
  const el = document.getElementById(elementId)
  if (!el) {
    logger.warn(`[usePrint] 找不到元素: #${elementId}`)
    return
  }

  const printWindow = window.open('', '_blank', 'width=900,height=700')
  if (!printWindow) return

  const content = sanitizeHtml(el.innerHTML)
  const pageTitle = title || document.title

  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <title>${pageTitle}</title>
      <style>
        ${PRINT_CSS}
      </style>
    </head>
    <body>
      <div class="print-header">
        <h1>${pageTitle}</h1>
        <p class="print-date">打印时间: ${new Date().toLocaleString('zh-CN')}</p>
      </div>
      <div class="print-content">
        ${content}
      </div>
      <div class="print-footer">
        <p>帮扶管理信息系统 — 内部资料，注意保密</p>
      </div>
    </body>
    </html>
  `)
  printWindow.document.close()
  // 等待资源加载后触发打印
  printWindow.onload = () => {
    printWindow.focus()
    printWindow.print()
  }
}

/**
 * 直接打印当前页面（使用媒体查询隐藏非打印区域）
 */
export function printCurrentPage() {
  window.print()
}

/** 打印专用 CSS */
const PRINT_CSS = `
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: "SimSun", "宋体", serif; font-size: 12pt; color: #000; padding: 20mm; }
  .print-header { text-align: center; margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 10px; }
  .print-header h1 { font-size: 18pt; margin-bottom: 4px; }
  .print-date { font-size: 10pt; color: #666; }
  .print-content { margin: 16px 0; }
  .print-footer { margin-top: 30px; text-align: center; font-size: 9pt; color: #999; border-top: 1px solid #ccc; padding-top: 8px; }
  table { width: 100%; border-collapse: collapse; margin: 10px 0; }
  table th, table td { border: 1px solid #333; padding: 6px 8px; text-align: left; font-size: 10pt; }
  table th { background: #f0f0f0; font-weight: bold; }
  .el-tag, .el-button, .el-input, .el-select { display: none !important; }
  .el-table { border: 1px solid #333; }
  .el-table th.el-table__cell { background: #f0f0f0 !important; border: 1px solid #333 !important; }
  .el-table td.el-table__cell { border: 1px solid #333 !important; }
  @page { size: A4; margin: 15mm; }
`

/** 在 composable 形式中使用 */
export function usePrint() {
  return {
    printElement,
    printCurrentPage,
  }
}
