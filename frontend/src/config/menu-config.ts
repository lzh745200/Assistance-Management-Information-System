/**
 * 菜单配置 - 系统菜单定义源
 * 每个菜单项的 key 必须唯一
 */
export interface MenuChildItem {
  key: string;
  label: string;
  path?: string;
  icon?: string;
  roles?: string[];
  permissions?: string[];
  children?: MenuChildItem[];
  order?: number;
}

export interface MenuItem extends MenuChildItem {
  order: number;
  children?: MenuChildItem[];
}

export const MENU_CONFIG: MenuItem[] = [
  {
    key: "dashboard",
    label: "工作台",
    path: "/dashboard",
    icon: "HomeFilled",
    order: 1,
  },
  {
    key: "villages",
    label: "帮扶村管理",
    path: "/supported-villages",
    icon: "Location",
    order: 2,
  },
  {
    key: "schools",
    label: "帮扶学校管理",
    path: "/schools",
    icon: "School",
    order: 3,
  },
  {
    key: "projects",
    label: "帮扶项目管理",
    path: "/projects",
    icon: "Folder",
    order: 4,
  },
  {
    key: "funds-admin",
    label: "经费管理",
    path: "/funds",
    icon: "Money",
    order: 5,
    roles: ["admin", "super_admin", "manager"],
  },
  {
    key: "funds-user",
    label: "经费申请",
    path: "/funds",
    icon: "Money",
    order: 6,
    roles: ["operator", "viewer", "approval_leader"],
  },
  {
    key: "policies",
    label: "政策法规",
    path: "/policies",
    icon: "Document",
    order: 7,
  },
  {
    key: "todos",
    label: "待办事项",
    path: "/todos",
    icon: "List",
    order: 8,
  },
  {
    key: "rural-works",
    label: "乡村工作",
    path: "/rural-works",
    icon: "Sunny",
    order: 9,
  },
  {
    key: "system-security",
    label: "系统安全",
    icon: "Lock",
    order: 9,
    roles: ["admin", "super_admin"],
    children: [
      {
        key: "zero-trust",
        label: "零信任安全",
        path: "/system/zero-trust",
        icon: "Lock",
      },
      {
        key: "user-permissions",
        label: "用户权限管理",
        path: "/system/user-permissions",
        icon: "User",
      },
      {
        key: "secrets",
        label: "密钥管理",
        path: "/system/secrets",
        icon: "Key",
      },
      {
        key: "data-tier",
        label: "数据分级",
        path: "/system/data-tier",
        icon: "DataBoard",
      },
      {
        key: "error-reports",
        label: "错误报告",
        path: "/system/error-reports",
        icon: "Warning",
      },
      {
        key: "tasks",
        label: "后台任务",
        path: "/system/tasks",
        icon: "Clock",
      },
      {
        key: "update-logs",
        label: "更新日志",
        path: "/system/update-logs",
        icon: "Document",
      },
      {
        key: "i18n",
        label: "国际化",
        path: "/system/i18n",
        icon: "ChatLineSquare",
      },
      {
        key: "environment",
        label: "运行环境",
        path: "/system/environment",
        icon: "Monitor",
      },
    ],
  },
  {
    key: "approval",
    label: "审批管理",
    path: "/approval/pending",
    icon: "Stamp",
    order: 10,
    roles: ["admin", "super_admin", "approval_leader", "manager"],
  },
  {
    key: "help",
    label: "帮助中心",
    path: "/help",
    icon: "QuestionFilled",
    order: 11,
  },
  {
    key: "helpData",
    label: "帮扶数据管理",
    icon: "TrendCharts",
    order: 12,
    roles: ["admin", "super_admin", "manager", "operator"],
    children: [
      {
        key: "comprehensive-entry",
        label: "综合数据录入",
        path: "/data-entry",
      },
      {
        key: "batch-import",
        label: "数据批量导入",
        path: "/data-import/batch",
        roles: ["admin", "super_admin", "manager"],
      },
      {
        key: "data-verify",
        label: "数据校验审核",
        path: "/funds",
        roles: ["admin", "super_admin", "manager"],
      },
      {
        key: "validation-rules",
        label: "校验规则",
        path: "/data-verify/rules",
        icon: "Checked",
        roles: ["admin", "super_admin", "manager"],
      },
      { key: "data-analysis", label: "数据统计分析", path: "/data-analysis" },
      {
        key: "report-templates",
        label: "报表模板管理",
        path: "/report/templates",
        roles: ["admin", "super_admin", "manager"],
      },
      {
        key: "report-export",
        label: "报表导出",
        path: "/report-export",
        roles: ["admin", "super_admin", "manager"],
      },
      {
        key: "batch-operations",
        label: "批量操作",
        path: "/batch",
        roles: ["admin", "super_admin", "manager"],
      },
    ],
  },
  {
    key: "analytics",
    label: "数据分析",
    icon: "DataAnalysis",
    order: 13,
    children: [
      {
        key: "analytics-dashboard",
        label: "分析仪表盘",
        path: "/data-analysis/dashboard",
      },
      { key: "analytics-map", label: "地图可视化", path: "/data-analysis/map" },
      {
        key: "work-analysis",
        label: "工作分析",
        path: "/data-analysis/reports",
      },
      {
        key: "effectiveness-rankings",
        label: "成效排名",
        path: "/effectiveness/rankings",
      },
      {
        key: "effectiveness-evaluate",
        label: "成效评估",
        path: "/effectiveness/evaluate",
      },
      {
        key: "sentiment",
        label: "舆情监测",
        path: "/sentiment",
      },
    ],
  },
  {
    key: "reportExport",
    label: "数据上报",
    icon: "Upload",
    order: 14,
    children: [
      { key: "data-package-report", label: "数据上报", path: "/data-package" },
      {
        key: "data-package-receive",
        label: "接收数据包",
        path: "/data-package/receive",
        roles: ["admin", "super_admin", "manager"],
      },
      { key: "data-package-list", label: "数据包列表", path: "/data-package" },
    ],
  },
];

export function getAllMenuKeys(): string[] {
  const keys: string[] = [];
  function collect(items: MenuItem[]) {
    for (const item of items) {
      keys.push(item.key);
      if (item.children) collect(item.children as MenuItem[]);
    }
  }
  collect(MENU_CONFIG);
  return keys;
}
