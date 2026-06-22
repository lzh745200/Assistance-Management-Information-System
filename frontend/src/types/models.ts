/** 核心业务实体 TypeScript 接口定义 */

/** 帮扶村 */
export interface Village {
  id: number
  village_name: string
  county: string
  township?: string
  province?: string
  city?: string
  support_unit?: string
  department?: string
  latitude?: number
  longitude?: number
  is_ethnic_area?: boolean
  created_at?: string
  updated_at?: string
}

/** 帮扶项目 */
export interface Project {
  id: number
  name: string
  code?: string
  type: string
  status: string
  description?: string
  objectives?: string
  village_id?: number
  organization_id?: number
  budget: number
  actual_cost: number
  invested_amount: number
  start_date?: string
  end_date?: string
  actual_start_date?: string
  actual_end_date?: string
  progress: number
  leader?: string
  contact?: string
  responsible_unit?: string
  responsible_person?: string
  created_by?: number
  created_at?: string
  updated_at?: string
}

/** 帮扶学校 */
export interface School {
  id: number
  name: string
  code?: string
  type: string
  province?: string
  city?: string
  district?: string
  address?: string
  latitude?: number
  longitude?: number
  student_count: number
  teacher_count: number
  class_count: number
  established_year?: number
  support_status: string
  support_unit?: string
  support_start_date?: string
  support_end_date?: string
  principal?: string
  contact_phone?: string
  email?: string
  description?: string
  is_active: boolean
  created_at?: string
  updated_at?: string
}

/** 经费记录 */
export interface Fund {
  id: number
  name?: string
  code?: string
  date?: string
  type?: string
  fund_type?: string
  fund_source?: string
  amount: number
  planned_amount: number
  approved_amount?: number
  allocated_amount: number
  used_amount: number
  remaining_amount: number
  project_id?: number
  project_name?: string
  village_id?: number
  school_id?: number
  purpose?: string
  source?: string
  operator?: string
  status: string
  remarks?: string
  created_at?: string
  updated_at?: string
}

/** 用户 */
export interface User {
  id: number
  username: string
  email?: string
  full_name?: string
  role: string
  is_active: boolean
  is_superuser: boolean
  phone?: string
  department?: string
  position?: string
  avatar?: string
  organization_id?: number
  permissions?: string
  must_change_password: boolean
  last_login?: string
  created_at?: string
  updated_at?: string
}
