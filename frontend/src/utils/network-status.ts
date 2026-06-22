/**
 * 网络状态管理工具
 * 单机版系统 - 默认为单机模式
 */
import { ref } from 'vue'

/** 当前是否为单机模式 */
export const isStandalone = ref(true)

/** 网络状态信息 */
export interface NetworkStatus {
  mode: 'offline' | 'online'
  lastCheck: number
  apiReachable: boolean
}

const _status = ref<NetworkStatus>({
  mode: 'offline',
  lastCheck: Date.now(),
  apiReachable: false,
})

/**
 * 获取网络状态
 */
export function getNetworkStatus(): NetworkStatus {
  return _status.value
}

/**
 * 设置网络模式
 */
export function setNetworkMode(mode: 'offline' | 'online'): void {
  _status.value.mode = mode
  isStandalone.value = mode === 'offline'
  localStorage.setItem('network_mode', mode)
}

/**
 * 测试 API 连通性
 * @param apiUrl API 基础地址
 * @returns 是否可达
 */
export async function testApiConnectivity(apiUrl: string): Promise<boolean> {
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 5000)
    const response = await fetch(`${apiUrl}/api/v1/health`, {
      method: 'GET',
      signal: controller.signal,
    })
    clearTimeout(timeout)
    _status.value.apiReachable = response.ok
    _status.value.lastCheck = Date.now()
    return response.ok
  } catch {
    _status.value.apiReachable = false
    _status.value.lastCheck = Date.now()
    return false
  }
}

// 初始化：从 localStorage 恢复模式设置
const savedMode = localStorage.getItem('network_mode')
if (savedMode === 'online') {
  isStandalone.value = false
  _status.value.mode = 'online'
}
