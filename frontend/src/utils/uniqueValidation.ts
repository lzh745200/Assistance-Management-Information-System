/**
 * 唯一性验证工具
 *
 * 提供表单字段唯一性异步验证
 */

import { logger } from '@/utils/logger'
import request from '@/api/request'

export interface UniqueCheckParams {
  model: string
  field: string
  value: string
  excludeId?: number
}

export interface UniqueCheckResult {
  available: boolean
  message: string
}

/**
 * 检查字段值是否唯一
 */
export async function checkUnique(params: UniqueCheckParams): Promise<UniqueCheckResult> {
  try {
    const response = await request.get<UniqueCheckResult>('/validation/check-unique', {
      params: {
        model: params.model,
        field: params.field,
        value: params.value,
        exclude_id: params.excludeId,
      },
    })

    return response.data
  } catch (error) {
    logger.error('唯一性检查失败:', error)
    return {
      available: true, // 验证失败时默认允许
      message: '验证失败，请稍后重试',
    }
  }
}

/**
 * 批量检查唯一性
 */
export async function checkUniqueBatch(checks: UniqueCheckParams[]): Promise<UniqueCheckResult[]> {
  try {
    const response = await request.post<UniqueCheckResult[]>(
      '/validation/check-unique-batch',
      checks
    )

    return response.data
  } catch (error) {
    logger.error('批量唯一性检查失败:', error)
    return checks.map(() => ({
      available: true,
      message: '验证失败',
    }))
  }
}

/**
 * 创建Element Plus表单验证规则
 *
 * 使用示例:
 * ```typescript
 * const rules = {
 *   code: [
 *     { required: true, message: '请输入编码' },
 *     createUniqueValidator('villages', 'code', '编码已存在')
 *   ]
 * }
 * ```
 */
export function createUniqueValidator(
  model: string,
  field: string,
  message: string = '该值已被使用',
  excludeIdGetter?: () => number | undefined
) {
  return {
    asyncValidator: async (_rule: any, value: string) => {
      if (!value) {
        return Promise.resolve()
      }

      const excludeId = excludeIdGetter ? excludeIdGetter() : undefined

      const result = await checkUnique({
        model,
        field,
        value,
        excludeId,
      })

      if (!result.available) {
        return Promise.reject(message)
      }

      return Promise.resolve()
    },
    trigger: 'blur',
  }
}

/**
 * 防抖的唯一性验证器
 *
 * 使用示例:
 * ```typescript
 * const validator = createDebouncedUniqueValidator('villages', 'code');
 * const rules = {
 *   code: [validator]
 * }
 * ```
 */
export function createDebouncedUniqueValidator(
  model: string,
  field: string,
  message: string = '该值已被使用',
  debounceMs: number = 500,
  excludeIdGetter?: () => number | undefined
) {
  let timeoutId: NodeJS.Timeout | null = null

  return {
    asyncValidator: async (_rule: any, value: string) => {
      if (!value) {
        return Promise.resolve()
      }

      // 清除之前的定时器
      if (timeoutId) {
        clearTimeout(timeoutId)
      }

      // 等待防抖时间
      await new Promise((resolve) => {
        timeoutId = setTimeout(resolve, debounceMs)
      })

      const excludeId = excludeIdGetter ? excludeIdGetter() : undefined

      const result = await checkUnique({
        model,
        field,
        value,
        excludeId,
      })

      if (!result.available) {
        return Promise.reject(message)
      }

      return Promise.resolve()
    },
    trigger: 'blur',
  }
}

/**
 * 常用模型的验证器工厂
 */
export const UniqueValidators = {
  /**
   * 村庄编码验证
   */
  villageCode: (excludeIdGetter?: () => number | undefined) =>
    createDebouncedUniqueValidator('villages', 'code', '村庄编码已存在', 500, excludeIdGetter),

  /**
   * 组织编码验证
   */
  organizationCode: (excludeIdGetter?: () => number | undefined) =>
    createDebouncedUniqueValidator('organizations', 'code', '组织编码已存在', 500, excludeIdGetter),

  /**
   * 学校编码验证
   */
  schoolCode: (excludeIdGetter?: () => number | undefined) =>
    createDebouncedUniqueValidator('schools', 'code', '学校编码已存在', 500, excludeIdGetter),

  /**
   * 用户邮箱验证
   */
  userEmail: (excludeIdGetter?: () => number | undefined) =>
    createDebouncedUniqueValidator('users', 'email', '邮箱已被使用', 500, excludeIdGetter),

  /**
   * 政策编码验证
   */
  policyCode: (excludeIdGetter?: () => number | undefined) =>
    createDebouncedUniqueValidator('policies', 'code', '政策编码已存在', 500, excludeIdGetter),

  /**
   * 角色名称验证
   */
  roleName: (excludeIdGetter?: () => number | undefined) =>
    createDebouncedUniqueValidator('roles', 'name', '角色名称已存在', 500, excludeIdGetter),

  /**
   * 村民身份证验证
   */
  villagerIdCard: (excludeIdGetter?: () => number | undefined) =>
    createDebouncedUniqueValidator('villagers', 'id_card', '身份证号已存在', 500, excludeIdGetter),
}

export default {
  checkUnique,
  checkUniqueBatch,
  createUniqueValidator,
  createDebouncedUniqueValidator,
  UniqueValidators,
}
