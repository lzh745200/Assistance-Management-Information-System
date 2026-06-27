/**
 * Property Test: Auth State Persistence Round-Trip
 *
 * Feature: frontend-architecture-enhancement
 * Property 1: 认证状态持久化往返一致性
 *
 * 对于任意有效的用户认证信息，将其设置到AuthStore后，
 * 从localStorage恢复应产生等价的认证状态。
 *
 * 验证: 需求 1.5
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import * as fc from 'fast-check'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore, type User, type AuthState } from '@/stores/auth'

// 用户数据生成器
const userArbitrary = fc.record({
  id: fc.string({ minLength: 1, maxLength: 36 }),
  username: fc.string({ minLength: 1, maxLength: 50 }),
  name: fc.option(fc.string({ minLength: 1, maxLength: 100 }), { nil: undefined }),
  realName: fc.option(fc.string({ minLength: 1, maxLength: 100 }), { nil: undefined }),
  role: fc.constantFrom('admin', 'user', 'guest', 'operator', 'viewer'),
  permissions: fc.option(fc.array(fc.string({ minLength: 1, maxLength: 50 }), { maxLength: 20 }), { nil: undefined }),
  avatar: fc.option(fc.webUrl(), { nil: undefined }),
  email: fc.option(fc.emailAddress(), { nil: undefined })
})

// Token生成器 - 模拟JWT格式
const tokenArbitrary = fc.string({ minLength: 20, maxLength: 500 })

// 刷新Token生成器
const refreshTokenArbitrary = fc.option(fc.string({ minLength: 20, maxLength: 500 }), { nil: null })

// Token过期时间生成器（秒）
const expiresInArbitrary = fc.integer({ min: 60, max: 86400 }) // 1分钟到24小时

describe('Feature: frontend-architecture-enhancement, Property 1: Auth state persistence round-trip', () => {
  beforeEach(() => {
    // 清理localStorage
    localStorage.clear()
    // 创建新的Pinia实例
    setActivePinia(createPinia())
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('should persist and restore user correctly for any valid user data', () => {
    fc.assert(
      fc.property(
        userArbitrary,
        (user) => {
          // Setup: 创建store并设置用户
          setActivePinia(createPinia())
          const store = useAuthStore()
          localStorage.clear()

          // Act: 设置用户并持久化
          store.setUser(user as User)
          store.persist()

          // 创建新的store实例并恢复
          setActivePinia(createPinia())
          const newStore = useAuthStore()
          newStore.restore()

          // Assert: 验证用户数据一致
          expect(newStore.user).toEqual(user)
        }
      ),
      { numRuns: 100 }
    )
  })

  it('should persist and restore token correctly for any valid token', () => {
    fc.assert(
      fc.property(
        tokenArbitrary,
        expiresInArbitrary,
        (token, expiresIn) => {
          // Setup
          setActivePinia(createPinia())
          const store = useAuthStore()
          localStorage.clear()

          // Act: 设置token并持久化
          store.setToken(token, expiresIn)
          const originalExpiry = store.tokenExpiry
          store.persist()

          // 创建新的store实例并恢复
          setActivePinia(createPinia())
          const newStore = useAuthStore()
          newStore.restore()

          // Assert: 验证token一致
          expect(newStore.token).toEqual(token)
          expect(newStore.tokenExpiry).toEqual(originalExpiry)
        }
      ),
      { numRuns: 100 }
    )
  })

  it('should persist and restore refresh token correctly', () => {
    fc.assert(
      fc.property(
        refreshTokenArbitrary,
        (refreshToken) => {
          // Setup
          setActivePinia(createPinia())
          const store = useAuthStore()
          localStorage.clear()

          // Act: 设置刷新token并持久化
          store.setRefreshToken(refreshToken)
          store.persist()

          // 创建新的store实例并恢复
          setActivePinia(createPinia())
          const newStore = useAuthStore()
          newStore.restore()

          // Assert: 验证刷新token一致
          expect(newStore.refreshToken).toEqual(refreshToken)
        }
      ),
      { numRuns: 100 }
    )
  })

  it('should persist and restore complete auth state correctly', () => {
    fc.assert(
      fc.property(
        userArbitrary,
        tokenArbitrary,
        refreshTokenArbitrary,
        expiresInArbitrary,
        (user, token, refreshToken, expiresIn) => {
          // Setup
          setActivePinia(createPinia())
          const store = useAuthStore()
          localStorage.clear()

          // Act: 设置完整认证状态
          store.setUser(user as User)
          store.setToken(token, expiresIn)
          store.setRefreshToken(refreshToken)

          const originalState: AuthState = {
            user: store.user,
            token: store.token,
            refreshToken: store.refreshToken,
            tokenExpiry: store.tokenExpiry
          }

          store.persist()

          // 创建新的store实例并恢复
          setActivePinia(createPinia())
          const newStore = useAuthStore()
          newStore.restore()

          // Assert: 验证完整状态一致
          expect(newStore.state).toEqual(originalState)
        }
      ),
      { numRuns: 100 }
    )
  })

  it('should handle null values correctly during persistence', () => {
    fc.assert(
      fc.property(
        fc.boolean(),
        fc.boolean(),
        fc.boolean(),
        userArbitrary,
        tokenArbitrary,
        refreshTokenArbitrary,
        (hasUser, hasToken, hasRefreshToken, user, token, refreshToken) => {
          // Setup
          setActivePinia(createPinia())
          const store = useAuthStore()
          localStorage.clear()

          // Act: 根据标志设置状态
          if (hasUser) {
            store.setUser(user as User)
          }
          if (hasToken) {
            store.setToken(token)
          }
          if (hasRefreshToken && refreshToken) {
            store.setRefreshToken(refreshToken)
          }

          const originalState: AuthState = {
            user: store.user,
            token: store.token,
            refreshToken: store.refreshToken,
            tokenExpiry: store.tokenExpiry
          }

          store.persist()

          // 创建新的store实例并恢复
          setActivePinia(createPinia())
          const newStore = useAuthStore()
          newStore.restore()

          // Assert: 验证状态一致（包括null值）
          expect(newStore.state).toEqual(originalState)
        }
      ),
      { numRuns: 100 }
    )
  })
})

describe('Feature: frontend-architecture-enhancement, Property 1: Permission checking consistency', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('should correctly check single permission for any user', () => {
    fc.assert(
      fc.property(
        userArbitrary,
        fc.string({ minLength: 1, maxLength: 50 }),
        (user, permissionToCheck) => {
          // Setup
          setActivePinia(createPinia())
          const store = useAuthStore()
          store.setUser(user as User)

          // Act & Assert
          const userPermissions = user.permissions || []
          const isAdmin = user.role === 'admin'

          if (isAdmin) {
            // Admin应该有所有权限
            expect(store.hasPermission(permissionToCheck)).toBe(true)
          } else {
            // 非Admin根据权限列表判断
            expect(store.hasPermission(permissionToCheck)).toBe(
              userPermissions.includes(permissionToCheck)
            )
          }
        }
      ),
      { numRuns: 100 }
    )
  })

  it('should correctly check hasAnyPermission for any permission list', () => {
    fc.assert(
      fc.property(
        userArbitrary,
        fc.array(fc.string({ minLength: 1, maxLength: 50 }), { minLength: 1, maxLength: 10 }),
        (user, permissionsToCheck) => {
          // Setup
          setActivePinia(createPinia())
          const store = useAuthStore()
          store.setUser(user as User)

          // Act & Assert
          const userPermissions = user.permissions || []
          const isAdmin = user.role === 'admin'

          if (isAdmin) {
            expect(store.hasAnyPermission(permissionsToCheck)).toBe(true)
          } else {
            const hasAny = permissionsToCheck.some(p => userPermissions.includes(p))
            expect(store.hasAnyPermission(permissionsToCheck)).toBe(hasAny)
          }
        }
      ),
      { numRuns: 100 }
    )
  })

  it('should correctly check hasAllPermissions for any permission list', () => {
    fc.assert(
      fc.property(
        userArbitrary,
        fc.array(fc.string({ minLength: 1, maxLength: 50 }), { minLength: 1, maxLength: 10 }),
        (user, permissionsToCheck) => {
          // Setup
          setActivePinia(createPinia())
          const store = useAuthStore()
          store.setUser(user as User)

          // Act & Assert
          const userPermissions = user.permissions || []
          const isAdmin = user.role === 'admin'

          if (isAdmin) {
            expect(store.hasAllPermissions(permissionsToCheck)).toBe(true)
          } else {
            const hasAll = permissionsToCheck.every(p => userPermissions.includes(p))
            expect(store.hasAllPermissions(permissionsToCheck)).toBe(hasAll)
          }
        }
      ),
      { numRuns: 100 }
    )
  })

  it('should correctly check role for any user', () => {
    fc.assert(
      fc.property(
        userArbitrary,
        fc.constantFrom('admin', 'user', 'guest', 'operator', 'viewer', 'unknown'),
        (user, roleToCheck) => {
          // Setup
          setActivePinia(createPinia())
          const store = useAuthStore()
          store.setUser(user as User)

          // Act & Assert
          expect(store.hasRole(roleToCheck)).toBe(user.role === roleToCheck)
        }
      ),
      { numRuns: 100 }
    )
  })

  it('should correctly check hasAnyRole for any role list', () => {
    fc.assert(
      fc.property(
        userArbitrary,
        fc.array(fc.constantFrom('admin', 'user', 'guest', 'operator', 'viewer'), { minLength: 1, maxLength: 5 }),
        (user, rolesToCheck) => {
          // Setup
          setActivePinia(createPinia())
          const store = useAuthStore()
          store.setUser(user as User)

          // Act & Assert
          expect(store.hasAnyRole(rolesToCheck)).toBe(rolesToCheck.includes(user.role))
        }
      ),
      { numRuns: 100 }
    )
  })
})
