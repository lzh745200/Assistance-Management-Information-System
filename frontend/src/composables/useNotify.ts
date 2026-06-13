/**
 * 统一通知工具 — 四级通知体系
 *
 * Tier 0: 静默 — 下载/导出等浏览器已反馈的操作，不弹任何提示
 * Tier 1: 轻提示 — CRUD 成功 (2s, ElMessage)
 * Tier 2: 结果提示 — 导入/批量结果 (5s, ElMessage)
 * Tier 3: 系统通知 — 备份/恢复/加密 (5s, ElNotification 角标)
 *
 * 用法：
 *   import { notify } from '@/composables/useNotify'
 *   notify.success('已保存')
 *   notify.error('操作失败')
 *   notify.done('导入完成：成功 42 条')
 *   notify.system('备份已完成')
 */

import { ElMessage, ElNotification } from 'element-plus'

/** 从 Axios 错误提取后端返回的 detail 消息 */
function extractError(e: any, fallback = '操作失败，请重试'): string {
  return e?.response?.data?.detail || e?.message || fallback
}

export const notify = {
  /** Tier 0: 显式跳过 — 用于标记"这里不需要通知"（代码可读性） */
  silent() {},

  /** Tier 1: 操作成功 — 2s 自动消失 */
  success(msg: string) {
    ElMessage({ type: 'success', message: msg, duration: 2000 })
  },

  /** Tier 1: 操作失败 — 5s */
  error(msgOrErr: any, fallback?: string) {
    const msg = typeof msgOrErr === 'string' ? msgOrErr : extractError(msgOrErr, fallback)
    ElMessage({ type: 'error', message: msg, duration: 5000 })
  },

  /** Tier 1: 警告 */
  warn(msg: string) {
    ElMessage({ type: 'warning', message: msg, duration: 3000 })
  },

  /** Tier 2: 含统计结果提示 — 5s */
  done(msg: string) {
    ElMessage({ type: 'success', message: msg, duration: 5000 })
  },

  /** Tier 3: 系统级角标通知 */
  system(title: string, message: string, type: 'success' | 'error' | 'warning' | 'info' = 'success') {
    ElNotification({ title, message, type, duration: 5000, showClose: true })
  },
}
