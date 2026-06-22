/**
 * 帮扶项目相关类型定义
 * 覆盖16个数据板块
 */

/** 板块1-4: 基础信息 */
export interface HelpProjectBasicInfo {
  /** 自动序号 */
  serialNo?: number
  /** 部门单位 */
  department: string
  /** 具体帮扶单位 */
  supportUnit: string
  /** 定点帮扶村名称 */
  villageName: string
  /** 所属省份 */
  province: string
  /** 所属市/州 */
  city: string
  /** 所属县/区 */
  county: string
  /** 所属乡镇 */
  township: string
  /** 是否三区三州 */
  isThreeRegionsThreeStates: boolean
  /** 是否边疆地区 */
  isBorderArea: boolean
  /** 是否民族地区 */
  isEthnicArea: boolean
  /** 是否革命地区 */
  isRevolutionaryArea: boolean
  /** 是否160个重点帮扶县 */
  isKeyCounty: boolean
  /** 是否振兴梯队 */
  isRevitalizationTier: boolean
  /** 帮扶开始年份 */
  helpStartYear: number
  /** 帮扶结束年份 */
  helpEndYear?: number
  /** 帮扶类型 */
  helpType: string
  /** 纳入总盘子标识 */
  includedInOverallPlan: boolean
}

/** 人口与经济数据（时间序列 2020-2025） */
export interface PopulationEconomicData {
  year: number
  /** 总人口 */
  totalPopulation: number
  /** 户数 */
  households: number
  /** 脱贫人口 */
  povertyAlleviatedPopulation: number
  /** 人均收入（元） */
  perCapitaIncome: number
  /** 村集体经济收入（万元） */
  collectiveEconomyIncome: number
}

/** 板块5: 投入情况 */
export interface InvestmentData {
  /** 经费投入年份 */
  year: number
  /** 部队投入（万元） */
  militaryInvestment: number
  /** 协调地方投入（万元） */
  localInvestment: number
  /** 领导干部到村人次 */
  leaderVisits: number
  /** 官兵到村人次 */
  soldierVisits: number
}

/** 板块6: 产业帮扶 */
export interface IndustryHelp {
  /** 投入金额（万元） */
  investment: number
  /** 项目类型 */
  projectType: string
  /** 项目数量 */
  projectCount: number
  /** 带动就业人数 */
  employmentDriven: number
  /** 年度 */
  year: number
}

/** 板块7: 基础设施 */
export interface InfrastructureHelp {
  investment: number
  projectType: string
  projectCount: number
  /** 受益人数 */
  beneficiaries: number
  year: number
}

/** 板块8: 党建帮扶 */
export interface PartyBuildingHelp {
  investment: number
  activityType: string
  activityCount: number
  year: number
}

/** 板块9: 医疗帮扶 */
export interface MedicalHelp {
  investment: number
  activityType: string
  activityCount: number
  /** 受益人数 */
  beneficiaries: number
  year: number
}

/** 板块10: 消费帮扶（2025年数据） */
export interface ConsumptionHelp {
  /** 采购金额（万元） */
  purchaseAmount: number
  /** 采购产品类型 */
  productType: string
  /** 帮销金额（万元） */
  salesAmount: number
  year: number
}

/** 板块11: 就业帮扶（2025年数据） */
export interface EmploymentHelp {
  /** 帮助就业人数 */
  employedCount: number
  /** 技能培训人次 */
  trainedCount: number
  /** 劳务输出人数 */
  laborExportCount: number
  year: number
}

/** 板块12: 教育帮扶 */
export interface EducationHelp {
  investment: number
  activityType: string
  activityCount: number
  /** 受助学生数 */
  aidedStudents: number
  /** 关联学校ID */
  relatedSchoolIds?: string[]
  year: number
}

/** 板块13: 表彰情况 */
export interface HonorRecord {
  /** 表彰级别 */
  level: '国家级' | '省级' | '市级' | '其他'
  /** 表彰名称 */
  honorName: string
  /** 获得年份 */
  year: number
  /** 表彰单位/个人 */
  recipient: string
}

/** 板块14: 跨单位协作 */
export interface CrossUnitCollaboration {
  /** 是否跨大单位 */
  isCrossUnit: boolean
  /** 是否跨省 */
  isCrossProvince: boolean
  /** 是否跨市 */
  isCrossCity: boolean
  /** 协作单位列表 */
  collaboratingUnits: string[]
  /** 协作内容描述 */
  description: string
}

/** 板块15: 关联与附件 */
export interface AttachmentInfo {
  /** 文件名 */
  fileName: string
  /** 文件路径 */
  filePath: string
  /** 文件类型 */
  fileType: 'image' | 'document' | 'other'
  /** 上传时间 */
  uploadedAt: string
  /** 文件大小（字节） */
  fileSize: number
}

/** 村委会成员信息 */
export interface VillageCommitteeMember {
  /** 姓名 */
  name: string
  /** 职务 */
  position: string
  /** 联系方式 */
  phone: string
  /** 是否退役军人 */
  isVeteran: boolean
  /** 备注 */
  remark?: string
}

/** 村委会介绍 */
export interface VillageCommitteeInfo {
  /** 村委会基本情况描述 */
  overview: string
  /** 村委会成员列表 */
  members: VillageCommitteeMember[]
  /** 村特色产业情况 */
  specialIndustry: string
  /** 村集体收入情况 */
  collectiveIncomeDesc: string
  /** 村集体收入金额（万元） */
  collectiveIncomeAmount: number
}

/** 帮扶项目完整数据结构 */
export interface HelpProject {
  id: string
  /** 基础信息 */
  basicInfo: HelpProjectBasicInfo
  /** 人口与经济数据（多年） */
  populationData: PopulationEconomicData[]
  /** 投入情况（多年） */
  investmentData: InvestmentData[]
  /** 产业帮扶（多年） */
  industryHelp: IndustryHelp[]
  /** 基础设施（多年） */
  infrastructureHelp: InfrastructureHelp[]
  /** 党建帮扶（多年） */
  partyBuildingHelp: PartyBuildingHelp[]
  /** 医疗帮扶（多年） */
  medicalHelp: MedicalHelp[]
  /** 消费帮扶 */
  consumptionHelp: ConsumptionHelp[]
  /** 就业帮扶 */
  employmentHelp: EmploymentHelp[]
  /** 教育帮扶（多年） */
  educationHelp: EducationHelp[]
  /** 表彰记录 */
  honors: HonorRecord[]
  /** 跨单位协作 */
  collaboration: CrossUnitCollaboration
  /** 附件列表 */
  attachments: AttachmentInfo[]
  /** 关联经费记录ID */
  relatedFundIds: string[]
  /** 关联学校ID */
  relatedSchoolIds: string[]
  /** 创建时间 */
  createdAt: string
  /** 更新时间 */
  updatedAt: string
  /** 创建人 */
  createdBy: string
  /** 状态 */
  status: 'draft' | 'pending' | 'approved' | 'rejected'
}

/** 帮扶项目筛选参数 */
export interface HelpProjectFilter {
  keyword?: string
  department?: string
  supportUnit?: string
  province?: string
  city?: string
  county?: string
  helpType?: string
  isRevitalizationTier?: boolean
  yearStart?: number
  yearEnd?: number
  status?: string
  isKeyCounty?: boolean
  isThreeRegionsThreeStates?: boolean
  page?: number
  pageSize?: number
}

/** 帮扶项目统计摘要 */
export interface HelpProjectSummary {
  totalProjects: number
  totalVillages: number
  totalInvestment: number
  militaryInvestment: number
  localInvestment: number
  industryProjects: number
  infrastructureProjects: number
  educationProjects: number
  medicalProjects: number
  partyBuildingProjects: number
  totalBeneficiaries: number
  honorsCount: number
}

/** 导入模板类型 */
export type ImportTemplateType = 'standard' | 'simplified' | 'yearly_update'

/** 导入模板描述 */
export interface ImportTemplate {
  type: ImportTemplateType
  name: string
  description: string
  fields: string[]
}
