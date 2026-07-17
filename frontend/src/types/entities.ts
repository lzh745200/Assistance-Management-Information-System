/**
 * 实体类型定义
 * 与后端 SQLAlchemy 模型 to_dict() 输出对齐
 */

// ==================== 用户相关 ====================

// 用户角色
export type UserRole = 'admin' | 'manager' | 'user' | 'guest' | 'super_admin'

// 用户实体
export interface User {
  id: number | string
  username: string
  realName?: string
  nickname?: string
  role: UserRole
  email?: string
  phone?: string
  permissions: string[]
  avatar?: string
  is_active?: boolean
  is_superuser?: boolean
  must_change_password?: boolean
  organization_id?: number
  created_at?: string
  updated_at?: string
}

// ==================== 帮扶村 ====================

// 村庄状态
export type VillageStatus = 'active' | 'inactive' | 'pending'

// 帮扶村实体（与 SupportedVillage.to_dict() 对齐）
export interface Village {
  id: number | string
  name: string
  village_name: string
  code?: string
  region?: string
  county?: string
  township?: string
  department?: string
  population: number
  area: number
  status: VillageStatus
  is_active: boolean
  is_deleted?: boolean
  isDeleted?: boolean
  organization_id?: number
  region_code?: string
  description?: string
  created_at?: string
  updated_at?: string
  createdAt?: string
  updatedAt?: string
}

// ==================== 学校 ====================

// 学校类型
export type SchoolType = 'primary' | 'middle' | 'high' | 'vocational'

// 学校状态
export type SchoolStatus = 'active' | 'inactive' | 'under_construction'

// 学校实体
export interface School {
  id: number | string
  name: string
  code?: string
  type: SchoolType
  address?: string
  student_count?: number
  teacher_count?: number
  studentCount?: number
  teacherCount?: number
  status: SchoolStatus
  is_active: boolean
  is_deleted?: boolean
  isDeleted?: boolean
  village_id?: number | string
  villageId?: number | string
  organization_id?: number
  created_at?: string
  updated_at?: string
  createdAt?: string
  updatedAt?: string
}

// ==================== 经费 ====================

// 资金类别
export type FundCategory = 'infrastructure' | 'education' | 'healthcare' | 'agriculture' | 'other'

// 资金状态
export type FundStatus =
  | 'pending'
  | 'planned'
  | 'approved'
  | 'allocated'
  | 'in_use'
  | 'completed'
  | 'audited'

// 经费实体（与 Fund.to_dict() 对齐）
export interface Fund {
  id: number | string
  name?: string
  code?: string
  amount: number
  planned_amount?: number
  approved_amount?: number
  allocated_amount?: number
  used_amount?: number
  remaining_amount?: number
  fund_type?: string
  fund_source?: string
  category?: FundCategory
  status: FundStatus
  purpose?: string
  source?: string
  project_id?: number | string
  village_id?: number | string
  school_id?: number | string
  organization_id?: number
  is_active: boolean
  is_deleted?: boolean
  isDeleted?: boolean
  created_at?: string
  updated_at?: string
  createdAt?: string
  updatedAt?: string
}

// ==================== 项目 ====================

// 项目状态
export type ProjectStatus =
  | 'draft'
  | 'pending'
  | 'approved'
  | 'in_progress'
  | 'completed'
  | 'cancelled'

// 项目实体（与 Project.to_dict() 对齐）
export interface Project {
  id: number | string
  name: string
  code?: string
  type?: string
  description?: string
  objectives?: string
  status: ProjectStatus
  budget: number
  actual_cost?: number
  invested_amount?: number
  start_date?: string
  end_date?: string
  actual_start_date?: string
  actual_end_date?: string
  progress?: number
  priority?: string
  leader?: string
  village_id?: number | string
  villageId?: number | string
  organization_id?: number
  is_active: boolean
  is_deleted?: boolean
  isDeleted?: boolean
  created_by?: number
  created_at?: string
  updated_at?: string
  createdAt?: string
  updatedAt?: string
}

// 军队人员实体
export interface ArmyPersonnel {
  id: string
  name: string
  rank?: string
  unit?: string
  role?: string
  phone?: string
  email?: string
  status?: string
  assignedVillageId?: string
  createdAt?: string
  updatedAt?: string
}
