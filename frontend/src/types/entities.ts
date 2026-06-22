/**
 * 实体类型定义
 */

// 用户角色
export type UserRole = 'admin' | 'manager' | 'user' | 'guest'

// 用户实体
export interface User {
  id: string
  username: string
  realName?: string
  role: UserRole
  email?: string
  phone?: string
  permissions: string[]
  avatar?: string
  createdAt: string
  updatedAt: string
}

// 村庄状态
export type VillageStatus = 'active' | 'inactive' | 'pending'

// 村庄实体
export interface Village {
  id: string
  name: string
  code: string
  region: string
  population: number
  area: number
  status: VillageStatus
  description?: string
  createdAt: string
  updatedAt: string
}

// 学校类型
export type SchoolType = 'primary' | 'middle' | 'high' | 'vocational'

// 学校状态
export type SchoolStatus = 'active' | 'inactive' | 'under_construction'

// 学校实体
export interface School {
  id: string
  name: string
  code: string
  type: SchoolType
  address: string
  studentCount: number
  teacherCount: number
  status: SchoolStatus
  villageId?: string
  createdAt: string
  updatedAt: string
}

// 资金类别
export type FundCategory = 'infrastructure' | 'education' | 'healthcare' | 'agriculture'

// 资金状态
export type FundStatus = 'pending' | 'approved' | 'disbursed' | 'completed'

// 资金实体
export interface Fund {
  id: string
  name: string
  amount: number
  category: FundCategory
  status: FundStatus
  allocatedAt: string
  description?: string
  villageId?: string
  createdAt: string
  updatedAt: string
}

// 项目状态
export type ProjectStatus = 'planning' | 'in_progress' | 'completed' | 'cancelled'

// 项目实体
export interface Project {
  id: number | string
  name: string
  description?: string
  status: ProjectStatus
  budget: number
  startDate: string
  endDate?: string
  villageId?: string
  createdAt: string
  updatedAt: string
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
