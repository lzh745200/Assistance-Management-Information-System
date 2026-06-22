/**
 * RBAC权限管理相关类型定义
 */

// 权限枚举
export enum Permission {
  // 用户管理
  USER_READ = 'user:read',
  USER_WRITE = 'user:write',
  USER_DELETE = 'user:delete',
  USER_MANAGE_ROLES = 'user:manage_roles',

  // 组织管理
  ORG_READ = 'org:read',
  ORG_WRITE = 'org:write',
  ORG_DELETE = 'org:delete',

  // 帮扶村管理
  VILLAGE_READ = 'village:read',
  VILLAGE_WRITE = 'village:write',
  VILLAGE_DELETE = 'village:delete',
  VILLAGE_EXPORT = 'village:export',

  // 政策管理
  POLICY_READ = 'policy:read',
  POLICY_WRITE = 'policy:write',
  POLICY_DELETE = 'policy:delete',
  POLICY_PUBLISH = 'policy:publish',

  // 备份管理
  BACKUP_CREATE = 'backup:create',
  BACKUP_RESTORE = 'backup:restore',
  BACKUP_DELETE = 'backup:delete',
  BACKUP_DOWNLOAD = 'backup:download',

  // 系统管理
  SYSTEM_CONFIG = 'system:config',
  SYSTEM_MONITOR = 'system:monitor',
  SYSTEM_LOGS = 'system:logs',

  // 审计管理
  AUDIT_READ = 'audit:read',
  AUDIT_EXPORT = 'audit:export',

  // 数据分析
  ANALYTICS_READ = 'analytics:read',
  ANALYTICS_EXPORT = 'analytics:export',

  // 管理员权限
  ADMIN_ALL = 'admin:all',
}

// 角色相关类型
export interface Role {
  id: string
  name: string
  description: string
  permissions?: string[]
  is_system: boolean
  is_active: boolean
  priority: number
  created_at: string
  updated_at: string
}

export interface RoleCreate {
  name: string
  description: string
  permissions: string[]
  is_system?: boolean
}

export interface RoleUpdate {
  name?: string
  description?: string
  permissions?: string[]
  is_active?: boolean
}

// 用户角色关联
export interface UserRole {
  id: string
  user_id: string
  role_id: string
  role_name: string
  role_description?: string
  granted_by: string
  expires_at?: string
  created_at: string
}

// 用户权限
export interface UserPermission {
  id: string
  user_id: string
  permission: string
  granted_by: string
  expires_at?: string
  created_at: string
}

// 权限检查请求
export interface PermissionCheckRequest {
  permission: string
  resource_type?: string
  resource_id?: string
}

// 权限检查响应
export interface PermissionCheckResponse {
  success: boolean
  has_permission: boolean
  permission: string
  user_id: string
}

// 用户权限响应
export interface UserPermissionsResponse {
  user_id: string
  permissions: string[]
  roles: UserRole[]
}

// 角色分配
export interface RoleAssignment {
  user_id: string
  role_id: string
  expires_at?: string
}

// 权限授予
export interface PermissionGrant {
  user_id: string
  permission: string
  expires_at?: string
}

// 格式化的权限数据（前端专用）
export interface FormattedPermissions {
  user: {
    read: boolean
    write: boolean
    delete: boolean
    manageRoles: boolean
  }
  village: {
    read: boolean
    write: boolean
    delete: boolean
    export: boolean
  }
  policy: {
    read: boolean
    write: boolean
    delete: boolean
    publish: boolean
  }
  backup: {
    create: boolean
    restore: boolean
    delete: boolean
    download: boolean
  }
  system: {
    config: boolean
    monitor: boolean
    logs: boolean
  }
  analytics: {
    read: boolean
    export: boolean
  }
  admin: boolean
}

// 前端权限数据
export interface FrontendPermissionsData {
  permissions: FormattedPermissions
  roles: UserRole[]
  role_names: string[]
  is_admin: boolean
}

// 权限类别
export interface PermissionCategory {
  code: string
  name: string
  description: string
  category: string
}

// 路由权限配置
export interface RoutePermissions {
  [route: string]: string[]
}

// API响应类型
export interface RbacApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

// 角色列表响应
export interface RolesListResponse {
  success: boolean
  data: Role[]
  total: number
}

// 权限列表响应
export interface PermissionsListResponse {
  success: boolean
  data: PermissionCategory[]
  categories: { [category: string]: PermissionCategory[] }
  total: number
}
