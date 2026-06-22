/**
 * 数据初始化工具
 * 用于初始化单机版默认数据
 */

import { localDatabase } from './LocalDatabase'
import { logger } from './logger'

export interface InitializationResult {
  success: boolean
  initialized: Record<string, number>
  errors: string[]
}

// 默认管理员用户（不包含明文密码，密码由后端初始化时生成）
const defaultUsers = [
  {
    id: 1,
    username: 'admin',
    name: '系统管理员',
    role: 'admin',
    email: 'admin@example.com',
    phone: '13800000000',
    status: 'active',
    createdAt: new Date().toISOString(),
  },
]

// 默认项目数据
const defaultProjects = [
  {
    id: 1,
    name: '示例乡村振兴项目',
    code: 'PRJ-2026-001',
    type: '基础设施',
    status: 'planning',
    description: '这是一个示例项目',
    budget: 100,
    progress: 0,
    createdAt: new Date().toISOString(),
  },
]

// 默认军队人员数据
const defaultArmyPersonnel: any[] = []

// 默认乡村工作数据
const defaultRuralWorks: any[] = []

/**
 * 初始化所有默认数据
 */
export async function initializeAllDefaultData(): Promise<InitializationResult> {
  const result: InitializationResult = {
    success: true,
    initialized: {},
    errors: [],
  }

  try {
    // 初始化用户数据
    const usersCount = await initializeTable('users', defaultUsers)
    result.initialized.users = usersCount

    // 初始化项目数据
    const projectsCount = await initializeTable('projects', defaultProjects)
    result.initialized.projects = projectsCount

    // 初始化军队人员数据
    const armyCount = await initializeTable('armyPersonnel', defaultArmyPersonnel)
    result.initialized.armyPersonnel = armyCount

    // 初始化乡村工作数据
    const ruralCount = await initializeTable('ruralWorks', defaultRuralWorks)
    result.initialized.ruralWorks = ruralCount

    logger.info('数据初始化完成', result.initialized)
  } catch (error) {
    result.success = false
    result.errors.push(error instanceof Error ? error.message : String(error))
    logger.error('数据初始化失败', error instanceof Error ? error : new Error(String(error)))
  }

  return result
}

/**
 * 初始化单个表的数据
 */
async function initializeTable(tableName: string, defaultData: any[]): Promise<number> {
  try {
    const existingData = await localDatabase.getAll(tableName)

    if (!existingData || existingData.length === 0) {
      for (const item of defaultData) {
        await localDatabase.add(tableName, item)
      }
      return defaultData.length
    }

    return 0
  } catch (error) {
    logger.error(
      `初始化表 ${tableName} 失败`,
      error instanceof Error ? error : new Error(String(error))
    )
    return 0
  }
}

export default {
  initializeAllDefaultData,
}
