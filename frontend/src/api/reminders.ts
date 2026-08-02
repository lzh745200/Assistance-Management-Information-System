/**
 * 提醒中心 API（审批超时/项目截止/预算预警等聚合）
 */
import { get, post } from '@/api/request'

const BASE = '/reminders'

export interface ReminderItem {
  id: number
  type: string
  title: string
  content: string
  created_at?: string | null
  is_read: boolean
}

/** 获取提醒列表 */
export async function getReminders(): Promise<{
  items: ReminderItem[]
  total: number
  unread: number
}> {
  return get(BASE)
}

/** 手动触发一次提醒扫描 */
export async function triggerReminderScan(): Promise<{ created: number }> {
  return post(`${BASE}/scan`)
}
