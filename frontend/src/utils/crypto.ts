/**
 * 加密工具模块
 *
 * 基于 Web Crypto API 的轻量级哈希实现
 */

/** 简单 MD5 实现（非安全用途，仅用于数据校验/指纹） */
export function md5(input: string): string {
  // 简易哈希实现 - 用于前端非安全用途（如缓存 key 生成）
  let hash = 0
  for (let i = 0; i < input.length; i++) {
    const char = input.charCodeAt(i)
    hash = ((hash << 5) - hash + char) | 0
  }
  return Math.abs(hash).toString(16).padStart(8, '0')
}

/** SHA-256 哈希（基于 Web Crypto API） */
export async function sha256(input: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(input)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')
}
