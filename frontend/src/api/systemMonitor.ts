/**
 * 系统监控快照 API
 *
 * 对应后端 /api/v1/system/monitor/snapshot 端点
 * 提供 CPU/内存/磁盘/数据库文件大小等系统资源信息
 */
import { get } from './request'

export interface MonitorSnapshot {
  timestamp: string
  host: string | null
  cpu_usage: number
  cpu_count: number
  memory_usage: number
  memory_used_mb: number
  memory_total_mb: number
  disk_usage: number
  disk_used_gb: number
  disk_total_gb: number
  network_sent_mb: number
  network_recv_mb: number
  process_cpu_percent: number
  process_memory_mb: number
  process_threads: number
  status: 'healthy' | 'limited' | 'error'
  message?: string
}

export interface MonitorSnapshotResponse {
  success: boolean
  data: MonitorSnapshot
}

/** 获取系统实时监控快照 */
export function getMonitorSnapshot(): Promise<MonitorSnapshotResponse> {
  return get<MonitorSnapshotResponse>('/system/monitor/snapshot')
}

/** 获取数据库文件大小（通过本地文件系统 API 或后端端点） */
export function getDatabaseFileSize(): Promise<{
  success: boolean
  data: { size_bytes: number; size_mb: number }
}> {
  return get<{
    success: boolean
    data: { size_bytes: number; size_mb: number }
  }>('/system/monitor/database-size')
}

/** 获取资源使用详情 */
export function getResources(): Promise<{
  success: boolean
  data: Record<string, any>
}> {
  return get<{ success: boolean; data: Record<string, any> }>('/system/monitor/resources')
}

/** 获取告警规则列表 */
export function getAlerts(): Promise<{ success: boolean; data: any[] }> {
  return get<{ success: boolean; data: any[] }>('/system/monitor/alerts')
}

/** 获取告警历史记录 */
export function getAlertHistory(params?: {
  page?: number
  page_size?: number
}): Promise<{ success: boolean; data: any[] }> {
  return get<{ success: boolean; data: any[] }>('/system/monitor/alerts/history', { params })
}

/** 获取 API 调用统计 */
export function getApiStats(): Promise<{
  success: boolean
  data: Record<string, any>
}> {
  return get<{ success: boolean; data: Record<string, any> }>('/system/monitor/api-stats')
}
