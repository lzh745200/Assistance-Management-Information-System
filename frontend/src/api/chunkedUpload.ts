/**
 * 分片上传 API
 * 实现大文件分片上传功能
 */

import { get, post, del } from '@/api/request'

// ==================== 类型定义 ====================

/** 初始化上传响应 */
export interface InitUploadResult {
  session_id: string
  file_name: string
  file_size: number
  chunk_size: number
  total_chunks: number
  status: string
}

/** 上传进度响应 */
export interface UploadProgress {
  session_id: string
  file_name: string
  total_chunks: number
  uploaded_chunks: number
  progress: number
  status: string
}

/** 合并响应 */
export interface MergeResult {
  session_id: string
  file_path: string
  file_name: string
  status: string
}

// ==================== API 函数 ====================

/** 初始化分片上传会话 */
export async function initChunkedUpload(data: {
  file_name: string
  file_size: number
  chunk_size?: number
  file_hash?: string
}): Promise<InitUploadResult> {
  return post<InitUploadResult>('/chunked-upload/init', data)
}

/** 上传单个分片（使用 FormData） */
export async function uploadChunk(
  sessionId: string,
  chunkIndex: number,
  chunkData: Blob,
  chunkHash?: string
): Promise<{ success: boolean; chunk_index: number }> {
  const formData = new FormData()
  formData.append('file', chunkData)
  let url = `/chunked-upload/chunk/${sessionId}/${chunkIndex}`
  if (chunkHash) {
    url += `?chunk_hash=${encodeURIComponent(chunkHash)}`
  }
  return post(url, formData)
}

/** 获取上传进度 */
export async function getChunkedUploadProgress(sessionId: string): Promise<UploadProgress> {
  return get<UploadProgress>(`/chunked-upload/progress/${sessionId}`)
}

/** 合并所有分片 */
export async function mergeChunkedUpload(sessionId: string): Promise<MergeResult> {
  return post<MergeResult>(`/chunked-upload/merge/${sessionId}`)
}

/** 取消上传并清理 */
export async function cancelChunkedUpload(
  sessionId: string
): Promise<{ success: boolean; message: string }> {
  return del(`/chunked-upload/${sessionId}`)
}

// ==================== 分组导出 ====================

export const chunkedUploadApi = {
  initUpload: initChunkedUpload,
  uploadChunk,
  getProgress: getChunkedUploadProgress,
  mergeChunks: mergeChunkedUpload,
  cancelUpload: cancelChunkedUpload,
}
