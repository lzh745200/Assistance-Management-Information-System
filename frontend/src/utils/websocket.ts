import { logger } from '@/utils/logger'

/**
 * WebSocket 工具（预留）
 * 单机版暂不使用 WebSocket
 */

export class WebSocketManager {
  private ws: WebSocket | null = null

  constructor(private _url: string) {}

  connect() {
    logger.info(`[WebSocket] 单机版暂不启用 WebSocket 连接 (url: ${this._url})`)
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(_data: any) {
    logger.warn('[WebSocket] 单机版暂不支持 WebSocket')
  }
}

export default WebSocketManager
