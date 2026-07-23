/**
 * 后台任务 API
 * 提供系统后台任务的状态查询、控制和监控功能
 */

import { get, post, del } from '@/api/request'

// ==================== 类型定义 ====================

/** 任务状态 */
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

/** 任务信息 */
export interface TaskInfo {
  task_id: string
  task_type: string
  task_name: string
  status: TaskStatus
  progress: number
  message: string
  created_at: string
  started_at?: string
  completed_at?: string
  created_by?: string
  result?: Record<string, any>
  params?: Record<string, any>
}

/** 任务列表响应 */
export interface TaskListResponse {
  items: TaskInfo[]
  total: number
  page: number
  page_size: number
}

/** 任务统计 */
export interface TaskStats {
  total: number
  by_status: Record<string, number>
  by_type: Record<string, number>
  active_count: number
}

/** 运行中任务计数 */
export interface RunningTaskCount {
  running: number
  pending: number
  total_active: number
}

// ==================== API 函数 ====================

/** 获取任务列表 */
export async function listTasks(params?: {
  status?: TaskStatus
  task_type?: string
  page?: number
  page_size?: number
}): Promise<{ success: boolean; data: TaskListResponse }> {
  return get('/system/tasks', params)
}

/** 获取任务统计 */
export async function getTaskStats(): Promise<{
  success: boolean
  data: TaskStats
}> {
  return get('/system/tasks/stats')
}

/** 获取任务详情 */
export async function getTask(taskId: string): Promise<{ success: boolean; data: TaskInfo }> {
  return get(`/system/tasks/${taskId}`)
}

/** 创建后台任务 */
export async function createTask(data: {
  task_type?: string
  task_name: string
  params?: Record<string, any>
}): Promise<{
  success: boolean
  message: string
  data: { task_id: string }
}> {
  return post('/system/tasks', data)
}

/** 取消任务 */
export async function cancelTask(taskId: string): Promise<{ success: boolean; message: string }> {
  return post(`/system/tasks/${taskId}/cancel`)
}

/** 删除任务记录 */
export async function deleteTask(taskId: string): Promise<{ success: boolean; message: string }> {
  return del(`/system/tasks/${taskId}`)
}

/** 获取运行中任务数 */
export async function getRunningTaskCount(): Promise<{
  success: boolean
  data: RunningTaskCount
}> {
  return get('/system/tasks/running/count')
}

// ==================== 分组导出 ====================

export const tasksApi = {
  listTasks,
  getStats: getTaskStats,
  getTask,
  createTask,
  cancelTask,
  deleteTask,
  getRunningCount: getRunningTaskCount,
}
