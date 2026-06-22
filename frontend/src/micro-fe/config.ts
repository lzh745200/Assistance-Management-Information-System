import { logger } from '@/utils/logger'
import { ElMessage } from 'element-plus'

// 微前端应用配置
export const MICRO_APPS = [
  {
    name: 'user-center',
    entry: '//localhost:3001',
    container: '#subapp-viewport',
    activeRule: '/user-center',
    // 添加超时配置
    props: {
      loading: true,
      timeout: 5000, // 5秒超时
    },
  },
  {
    name: 'data-analysis',
    entry: '//localhost:3002',
    container: '#subapp-viewport',
    activeRule: '/data-analysis',
    // 添加超时配置
    props: {
      loading: true,
      timeout: 5000, // 5秒超时
    },
  },
]

// 微前端应用错误处理函数
export const handleMicroAppError = (error: Error, appName: string) => {
  logger.error(`微前端应用 ${appName} 加载失败:`, error)
  ElMessage.error(`子系统 ${appName} 加载失败，请稍后重试`)
  // 可以在这里添加更多的错误处理逻辑，如上报错误等
}

// 微前端应用加载超时处理
export const handleMicroAppTimeout = (appName: string) => {
  logger.warn(`微前端应用 ${appName} 加载超时`)
  ElMessage.warning(`子系统 ${appName} 加载超时，请检查网络连接后重试`)
}
