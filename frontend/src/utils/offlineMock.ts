/**
 * 离线 Mock 数据模块
 *
 * 当后端服务不可用时，为所有 API 请求提供模拟数据，
 * 确保系统在纯前端模式下完全可用。
 */

import { AuthStorage } from "./authStorage";

// ==================== 工具函数 ====================

/** 检查当前是否使用内置账号（离线模式） */
export function isOfflineMode(): boolean {
  const token = AuthStorage.getToken() || "";
  return token.startsWith("builtin-token-");
}

/** 构造标准列表响应 */
function listResponse(items: any[], total?: number) {
  return {
    data: { items, total: total ?? items.length, page: 1, page_size: 20 },
  };
}

/** 构造标准成功响应 */
function successResponse(data: any = null, message = "操作成功") {
  return { data: { success: true, message, data } };
}

/** 构造单条记录响应 */
function detailResponse(item: any) {
  return { data: item };
}

// ==================== 模拟数据 ====================

const mockVillages = [
  {
    id: 1,
    name: "红星村",
    province: "四川省",
    city: "成都市",
    district: "郫都区",
    population: 3200,
    poverty_count: 45,
    status: "帮扶中",
  },
  {
    id: 2,
    name: "向阳村",
    province: "四川省",
    city: "成都市",
    district: "双流区",
    population: 2800,
    poverty_count: 32,
    status: "帮扶中",
  },
  {
    id: 3,
    name: "青山村",
    province: "云南省",
    city: "昆明市",
    district: "安宁市",
    population: 1500,
    poverty_count: 120,
    status: "重点帮扶",
  },
  {
    id: 4,
    name: "丰收村",
    province: "贵州省",
    city: "遵义市",
    district: "仁怀市",
    population: 4100,
    poverty_count: 18,
    status: "已脱贫",
  },
  {
    id: 5,
    name: "复兴村",
    province: "四川省",
    city: "绵阳市",
    district: "三台县",
    population: 2200,
    poverty_count: 67,
    status: "帮扶中",
  },
];

const mockSchools = [
  {
    id: 1,
    name: "红星希望小学",
    type: "小学",
    students: 580,
    teachers: 24,
    village_id: 1,
    status: "帮扶中",
  },
  {
    id: 2,
    name: "八一中学",
    type: "中学",
    students: 920,
    teachers: 56,
    village_id: 2,
    status: "帮扶中",
  },
  {
    id: 3,
    name: "阳光中心小学",
    type: "小学",
    students: 450,
    teachers: 18,
    village_id: 3,
    status: "重点帮扶",
  },
  {
    id: 4,
    name: "育才初级中学",
    type: "中学",
    students: 680,
    teachers: 42,
    village_id: 5,
    status: "帮扶中",
  },
];

const mockProjects = [
  {
    id: 1,
    name: "村道硬化工程",
    type: "基础设施",
    budget: 85,
    spent: 62,
    progress: 73,
    status: "进行中",
    village_id: 1,
  },
  {
    id: 2,
    name: "校舍翻新项目",
    type: "教育帮扶",
    budget: 120,
    spent: 120,
    progress: 100,
    status: "已完成",
    village_id: 2,
  },
  {
    id: 3,
    name: "饮水安全工程",
    type: "基础设施",
    budget: 45,
    spent: 38,
    progress: 85,
    status: "进行中",
    village_id: 3,
  },
  {
    id: 4,
    name: "产业技能培训",
    type: "技能培训",
    budget: 20,
    spent: 15,
    progress: 75,
    status: "进行中",
    village_id: 5,
  },
  {
    id: 5,
    name: "光伏发电站",
    type: "产业发展",
    budget: 200,
    spent: 180,
    progress: 90,
    status: "进行中",
    village_id: 1,
  },
];

const mockFunds = [
  {
    id: 1,
    project_id: 1,
    amount: 500000,
    category: "基建",
    status: "已拨付",
    created_at: "2026-01-15",
  },
  {
    id: 2,
    project_id: 2,
    amount: 1200000,
    category: "教育",
    status: "已拨付",
    created_at: "2026-02-10",
  },
  {
    id: 3,
    project_id: 3,
    amount: 450000,
    category: "水利",
    status: "审批中",
    created_at: "2026-03-05",
  },
  {
    id: 4,
    project_id: 4,
    amount: 200000,
    category: "培训",
    status: "已拨付",
    created_at: "2026-03-20",
  },
];

const mockPolicies = [
  {
    id: 1,
    title: "乡村振兴促进法",
    category: "法律",
    publish_date: "2021-04-29",
    status: "现行有效",
  },
  {
    id: 2,
    title: "关于实现巩固拓展脱贫攻坚成果同乡村振兴有效衔接的意见",
    category: "政策",
    publish_date: "2020-12-16",
    status: "现行有效",
  },
  {
    id: 3,
    title: "乡村建设行动实施方案",
    category: "方案",
    publish_date: "2022-05-23",
    status: "现行有效",
  },
];

const mockUsers = [
  {
    id: 1,
    username: "admin",
    full_name: "系统管理员",
    role: "admin",
    organization: "总部",
    is_active: true,
  },
  {
    id: 2,
    username: "zhangsan",
    full_name: "张三",
    role: "operator",
    organization: "成都分部",
    is_active: true,
  },
  {
    id: 3,
    username: "lisi",
    full_name: "李四",
    role: "viewer",
    organization: "昆明分部",
    is_active: true,
  },
];

const mockOrganizations = [
  { id: 1, name: "总部", code: "HQ", parent_id: null, level: 0 },
  { id: 2, name: "成都分部", code: "CD", parent_id: 1, level: 1 },
  { id: 3, name: "昆明分部", code: "KM", parent_id: 1, level: 1 },
  { id: 4, name: "绵阳工作组", code: "MY", parent_id: 2, level: 2 },
];

const mockDashboardStats = {
  village_count: 24,
  school_count: 18,
  project_count: 56,
  fund_total: 1865,
  completed_projects: 42,
  pending_approvals: 8,
  poverty_count: 320,
  beneficiary_count: 3580,
};

const mockApprovalTasks = [
  {
    id: 1,
    title: "红星村基础设施改造项目经费申请",
    entity_type: "fund",
    entity_id: 1,
    status: "pending",
    current_level: 1,
    priority: 2,
    submitter_id: 2,
    submitter_name: "张三",
    created_at: "2026-04-18T09:30:00",
  },
  {
    id: 2,
    title: "向阳村学校扩建项目立项",
    entity_type: "project",
    entity_id: 3,
    status: "pending",
    current_level: 1,
    priority: 1,
    submitter_id: 2,
    submitter_name: "张三",
    created_at: "2026-04-19T14:20:00",
  },
  {
    id: 3,
    title: "青山村产业发展资金拨付",
    entity_type: "fund",
    entity_id: 3,
    status: "approved",
    current_level: 2,
    priority: 3,
    submitter_id: 2,
    submitter_name: "张三",
    created_at: "2026-04-15T10:00:00",
    completed_at: "2026-04-16T16:30:00",
  },
];

const mockApprovalWorkflows = [
  {
    id: 1,
    name: "经费审批流程",
    entity_type: "fund",
    description: "帮扶经费申请与拨付审批",
    is_active: true,
    level_count: 2,
    nodes: [
      {
        id: 1,
        level: 1,
        name: "部门负责人审核",
        approver_type: "role",
        timeout_hours: 24,
      },
      {
        id: 2,
        level: 2,
        name: "分管领导审批",
        approver_type: "role",
        timeout_hours: 48,
      },
    ],
  },
  {
    id: 2,
    name: "项目立项审批",
    entity_type: "project",
    description: "帮扶项目立项与变更审批",
    is_active: true,
    level_count: 2,
    nodes: [
      {
        id: 3,
        level: 1,
        name: "项目办审核",
        approver_type: "role",
        timeout_hours: 48,
      },
      {
        id: 4,
        level: 2,
        name: "总指挥审批",
        approver_type: "role",
        timeout_hours: 72,
      },
    ],
  },
];

const mockWorkLogs = [
  {
    id: 1,
    title: "红星村入户走访调研",
    content: "走访12户贫困家庭，了解实际困难，记录帮扶需求。",
    log_type: "visit",
    log_date: "2026-04-18",
    start_time: "09:00",
    end_time: "17:00",
    location: "红星村三组",
    participants: "张三、李四、王五",
    related_village_id: 1,
    category: "走访调研",
    created_at: "2026-04-18T18:00:00",
  },
  {
    id: 2,
    title: "向阳村学校捐赠仪式",
    content: "组织捐赠课桌椅80套、图书500册，参加师生共计120人。",
    log_type: "activity",
    log_date: "2026-04-15",
    start_time: "10:00",
    end_time: "12:00",
    location: "向阳村八一中学",
    participants: "赵六、钱七",
    related_village_id: 2,
    category: "捐赠活动",
    created_at: "2026-04-15T14:30:00",
  },
  {
    id: 3,
    title: "季度工作总结会议",
    content: "总结第一季度帮扶工作成效，部署下一阶段重点任务。",
    log_type: "meeting",
    log_date: "2026-04-10",
    start_time: "14:00",
    end_time: "16:30",
    location: "总部会议室",
    participants: "全体帮扶队员",
    category: "工作会议",
    created_at: "2026-04-10T17:00:00",
  },
];

const mockRuralWorks = [
  {
    id: 1,
    code: "RW-2026-001",
    name: "红星村道路硬化工程",
    type: "infrastructure",
    status: "in_progress",
    village_id: 1,
    village_name: "红星村",
    responsible_person: "张三",
    contact_phone: "13800138001",
    start_date: "2026-03-01",
    end_date: "2026-06-30",
    description: "硬化村内主干道3.5公里，宽度4.5米。",
    target: "改善出行条件，惠及320户村民",
    progress: 65,
    created_at: "2026-03-01T08:00:00",
    updated_at: "2026-04-18T10:00:00",
  },
  {
    id: 2,
    code: "RW-2026-002",
    name: "向阳村产业种植培训",
    type: "education",
    status: "completed",
    village_id: 2,
    village_name: "向阳村",
    responsible_person: "李四",
    contact_phone: "13800138002",
    start_date: "2026-01-10",
    end_date: "2026-03-20",
    description: "组织果树种植技术培训，覆盖50户农户。",
    target: "提升种植技能，增加人均收入2000元",
    progress: 100,
    created_at: "2026-01-10T08:00:00",
    updated_at: "2026-03-20T16:00:00",
  },
  {
    id: 3,
    code: "RW-2026-003",
    name: "青山村饮水安全工程",
    type: "infrastructure",
    status: "in_progress",
    village_id: 3,
    village_name: "青山村",
    responsible_person: "王五",
    contact_phone: "13800138003",
    start_date: "2026-02-15",
    end_date: "2026-05-30",
    description: "建设集中供水站2座，铺设管网5公里。",
    target: "解决1500人安全饮水问题",
    progress: 80,
    created_at: "2026-02-15T08:00:00",
    updated_at: "2026-04-19T09:00:00",
  },
];

const mockMessages = [
  {
    id: 1,
    user_id: 1,
    message_type: "approval",
    title: "新的审批待处理",
    content: "您有2条经费审批申请待处理，请及时审核。",
    is_read: false,
    created_at: "2026-04-19T10:00:00",
  },
  {
    id: 2,
    user_id: 1,
    message_type: "task",
    title: "项目进度提醒",
    content: "青山村饮水安全工程进度已达80%，请安排阶段性验收。",
    is_read: false,
    created_at: "2026-04-18T09:00:00",
  },
  {
    id: 3,
    user_id: 1,
    message_type: "system",
    title: "系统维护通知",
    content: "系统将于本周日凌晨2点进行例行维护，预计持续30分钟。",
    is_read: true,
    created_at: "2026-04-15T08:00:00",
    read_at: "2026-04-15T09:30:00",
  },
];

const mockSyncLogs = [
  {
    id: 1,
    sync_type: "export",
    status: "completed",
    package_name: "export_20260418_001.zip",
    total_records: 1250,
    success_records: 1250,
    failed_records: 0,
    conflicts_count: 0,
    created_at: "2026-04-18T08:00:00",
    completed_at: "2026-04-18T08:02:15",
    user_name: "admin",
  },
  {
    id: 2,
    sync_type: "import",
    status: "completed",
    package_name: "import_20260410_003.zip",
    total_records: 860,
    success_records: 855,
    failed_records: 5,
    conflicts_count: 3,
    created_at: "2026-04-10T14:30:00",
    completed_at: "2026-04-10T14:35:42",
    user_name: "admin",
  },
];

const mockMachineCodes = [
  {
    id: 1,
    machine_code: "MC-2026-A1B2C3D4",
    pass_code: "PASS-12345678",
    status: "active",
    username: "admin",
    description: "总部主服务器",
    created_at: "2026-01-15T10:00:00",
    activated_at: "2026-01-15T10:05:00",
  },
  {
    id: 2,
    machine_code: "MC-2026-E5F6G7H8",
    pass_code: "PASS-87654321",
    status: "pending",
    description: "成都分部终端",
    created_at: "2026-04-10T14:20:00",
  },
];

/** 从路径末尾提取数字 ID（如 /villages/123 → 123），无匹配返回 null */
const _idRegexCache = new Map<string, RegExp>();
function extractIdFromPath(path: string, prefix: string): number | null {
  let re = _idRegexCache.get(prefix);
  if (!re) {
    re = new RegExp(
      `^${prefix.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\/(\\d+)$`,
    );
    _idRegexCache.set(prefix, re);
  }
  const match = path.match(re);
  return match ? parseInt(match[1], 10) : null;
}

// ==================== URL 匹配与路由 ====================

/**
 * 离线模式下的回退响应
 * 为各模块提供有意义的模拟数据，确保 UI 展示真实业务场景
 */
export function getMockResponse(method: string, url: string): any | null {
  let path = url
    .replace(/^(https?:\/\/[^/]+)?/, "")
    .replace(/\/api\/v1/, "")
    .split("?")[0];
  if (!path.startsWith("/")) path = "/" + path;
  path = path.replace(/\/$/, "") || "/";

  const m = method.toUpperCase();

  if (m === "GET") {
    if (path === "/auth/me") {
      const user = AuthStorage.getUser();
      if (user) return detailResponse(user);
      return null;
    }

    // 工作台统计
    if (path === "/dashboard/stats" || path === "/dashboard") {
      return detailResponse(mockDashboardStats);
    }

    // 帮扶村（旧路由）
    if (path === "/villages" || path.startsWith("/villages/")) {
      const id = extractIdFromPath(path, "/villages");
      if (id !== null) {
        return detailResponse(
          mockVillages.find((v) => v.id === id) || mockVillages[0],
        );
      }
      return listResponse(mockVillages);
    }

    // 帮扶村管理（新路由 — 前端主要使用）
    if (
      path === "/supported-villages" ||
      path.startsWith("/supported-villages/")
    ) {
      const id = extractIdFromPath(path, "/supported-villages");
      if (id !== null) {
        return detailResponse(
          mockVillages.find((v) => v.id === id) || mockVillages[0],
        );
      }
      return listResponse(mockVillages);
    }

    // 帮扶学校
    if (path === "/schools" || path.startsWith("/schools")) {
      const id = extractIdFromPath(path, "/schools");
      if (id !== null) {
        return detailResponse(
          mockSchools.find((s) => s.id === id) || mockSchools[0],
        );
      }
      return listResponse(mockSchools);
    }

    // 帮扶项目
    if (path === "/projects" || path.startsWith("/projects")) {
      const id = extractIdFromPath(path, "/projects");
      if (id !== null) {
        return detailResponse(
          mockProjects.find((p) => p.id === id) || mockProjects[0],
        );
      }
      return listResponse(mockProjects);
    }

    // 经费管理
    if (path === "/funds" || path.startsWith("/funds")) {
      return listResponse(mockFunds);
    }

    // 政策法规
    if (path === "/policies" || path.startsWith("/policies")) {
      const id = extractIdFromPath(path, "/policies");
      if (id !== null) {
        return detailResponse(
          mockPolicies.find((p) => p.id === id) || mockPolicies[0],
        );
      }
      return listResponse(mockPolicies);
    }

    // 用户管理
    if (path === "/users" || path.startsWith("/users")) {
      return listResponse(mockUsers);
    }

    // 组织管理
    if (path === "/organizations" || path.startsWith("/organizations")) {
      return listResponse(mockOrganizations);
    }

    // 菜单权限
    if (path === "/menus/accessible") {
      return { data: { success: true, data: [], source: "offline" } };
    }

    // 审批管理
    if (path.startsWith("/approval")) {
      if (path === "/approval/workflows") {
        return { data: mockApprovalWorkflows };
      }
      const workflowId = extractIdFromPath(path, "/approval/workflows");
      if (workflowId !== null) {
        return {
          data:
            mockApprovalWorkflows.find((w) => w.id === workflowId) ||
            mockApprovalWorkflows[0],
        };
      }
      if (path === "/approval/tasks/pending") {
        return {
          data: mockApprovalTasks.filter((t) => t.status === "pending"),
        };
      }
      if (path === "/approval/tasks/all" || path === "/approval/history") {
        return { data: mockApprovalTasks };
      }
      if (path.match(/^\/approval\/tasks\/\d+\/diff$/)) {
        return {
          data: {
            task_id: 1,
            entity_type: "fund",
            entity_id: 1,
            original_data: { amount: 300000, status: "draft" },
            change_data: { amount: 500000, status: "pending" },
            diff_fields: ["amount", "status"],
          },
        };
      }
      return { data: [] };
    }

    // 工作日志
    if (path.startsWith("/work-logs")) {
      if (path === "/work-logs") {
        return listResponse(mockWorkLogs);
      }
      const id = extractIdFromPath(path, "/work-logs");
      if (id !== null) {
        return detailResponse(
          mockWorkLogs.find((w) => w.id === id) || mockWorkLogs[0],
        );
      }
      if (path === "/work-logs/calendar") {
        return { data: { items: mockWorkLogs, year: 2026, month: 4 } };
      }
      return listResponse([]);
    }

    // 乡村工作
    if (path.startsWith("/rural-works")) {
      if (path === "/rural-works") {
        return {
          data: {
            items: mockRuralWorks,
            total: mockRuralWorks.length,
            skip: 0,
            limit: 20,
          },
        };
      }
      const id = extractIdFromPath(path, "/rural-works");
      if (id !== null) {
        return {
          data: {
            data: mockRuralWorks.find((w) => w.id === id) || mockRuralWorks[0],
          },
        };
      }
      if (path === "/rural-works/statistics/summary") {
        return {
          data: {
            data: {
              total: 3,
              planned: 0,
              in_progress: 2,
              completed: 1,
              delayed: 0,
              by_type: { infrastructure: 2, education: 1 },
              completion_rate: 33.3,
            },
          },
        };
      }
      if (path === "/rural-works/villages") {
        return {
          data: {
            data: [
              { id: 1, name: "红星村" },
              { id: 2, name: "向阳村" },
              { id: 3, name: "青山村" },
            ],
          },
        };
      }
      if (path === "/rural-works/years") {
        return { data: { data: [2024, 2025, 2026] } };
      }
      if (path === "/rural-works/report/generate") {
        return {
          data: {
            data: {
              total: 3,
              status_counts: {
                planned: 0,
                in_progress: 2,
                completed: 1,
                delayed: 0,
              },
              type_counts: { infrastructure: 2, education: 1 },
              village_counts: { 红星村: 1, 向阳村: 1, 青山村: 1 },
              avg_progress: 81.7,
              completion_rate: 33.3,
              monthly_trend: {
                "2026-01": { total: 1, completed: 0 },
                "2026-02": { total: 1, completed: 0 },
                "2026-03": { total: 1, completed: 1 },
                "2026-04": { total: 3, completed: 1 },
              },
              generated_at: new Date().toISOString(),
            },
          },
        };
      }
      return { data: { items: [], total: 0, skip: 0, limit: 20 } };
    }

    // 消息通知
    if (path.startsWith("/messages")) {
      if (path === "/messages") {
        return {
          data: {
            items: mockMessages,
            total: mockMessages.length,
            page: 1,
            page_size: 20,
            unread_count: 2,
          },
        };
      }
      if (path === "/messages/unread-count") {
        return { data: { count: 2 } };
      }
      return { data: [] };
    }

    // 通知偏好
    if (path.startsWith("/notifications")) {
      if (path === "/notifications/preferences") {
        return {
          data: {
            email_approval: true,
            email_task: true,
            email_system: false,
            site_approval: true,
            site_task: true,
            site_system: true,
          },
        };
      }
      return { data: {} };
    }

    // 数据同步
    if (path.startsWith("/data-sync")) {
      if (path === "/data-sync/logs") {
        return {
          data: {
            success: true,
            data: mockSyncLogs,
            count: mockSyncLogs.length,
          },
        };
      }
      const conflictId = extractIdFromPath(path, "/data-sync/conflicts");
      if (conflictId !== null) {
        return { data: { success: true, data: [], count: 0 } };
      }
      return { data: { success: true, message: "" } };
    }

    // 机器码管理
    if (path.startsWith("/machine-code")) {
      if (path === "/machine-code/get-machine-code") {
        return {
          data: {
            data: {
              machine_code: "MC-2026-OFFLINE-DEMO",
              verification_code: "VF-12345678",
              machine_info: {
                system: "Windows",
                release: "10",
                version: "10.0.19045",
                machine: "AMD64",
                processor: "Intel64 Family 6",
                node: "offline-pc",
              },
            },
          },
        };
      }
      if (path === "/machine-code/admin/list") {
        return {
          data: {
            data: { total: mockMachineCodes.length, items: mockMachineCodes },
          },
        };
      }
      if (path === "/machine-code/machine-info") {
        return {
          data: {
            system: "Windows",
            release: "10",
            version: "10.0.19045",
            machine: "AMD64",
            processor: "Intel64 Family 6",
            node: "offline-pc",
          },
        };
      }
      return { data: { success: true } };
    }

    // 统计类返回模拟数据
    if (path.match(/\/stats$/) || path.match(/\/statistics$/)) {
      return detailResponse(mockDashboardStats);
    }

    // 列表类返回空列表兜底
    return listResponse([]);
  }

  if (m === "POST") {
    // 导入解析
    if (path === "/import/projects/parse") {
      return {
        data: {
          preview: [
            {
              name: "乡村道路硬化工程",
              type: "基础设施",
              responsible_person: "张三",
              contact_phone: "13800138001",
              start_date: "2026-01-15",
              end_date: "2026-06-30",
              budget: 1500000,
              status: "进行中",
              village_name: "红星村",
              description: "硬化村内主干道2公里",
            },
            {
              name: "特色种植示范基地",
              type: "产业发展",
              responsible_person: "李四",
              contact_phone: "13800138002",
              start_date: "2026-03-01",
              end_date: "2026-12-31",
              budget: 2000000,
              status: "进行中",
              village_name: "向阳村",
              description: "建设现代化特色种植示范基地",
            },
          ],
        },
      };
    }
    // 导入确认
    if (path === "/import/projects" || path === "/import/villages") {
      return successResponse(
        { total_rows: 5, success_rows: 5, failed_rows: 0, skipped_rows: 0 },
        "导入成功（离线模式）",
      );
    }
    return successResponse(
      { id: "offline-" + Date.now() },
      "操作成功（离线模式）",
    );
  }

  if (m === "PUT" || m === "PATCH") {
    return successResponse(null, "更新成功（离线模式）");
  }

  if (m === "DELETE") {
    return successResponse(null, "删除成功（离线模式）");
  }

  return listResponse([]);
}
