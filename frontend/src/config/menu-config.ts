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
  { key: "dashboard", label: "工作台", path: "/dashboard", icon: "HomeFilled", order: 1 },
  { key: "villages", label: "帮扶村管理", path: "/villages", icon: "Location", order: 2 },
  { key: "schools", label: "帮扶学校管理", path: "/schools", icon: "School", order: 3 },
  { key: "projects", label: "帮扶项目管理", path: "/projects", icon: "Folder", order: 4 },
  { key: "funds-admin", label: "经费管理", path: "/funds", icon: "Money", order: 5, roles: ["admin", "super_admin", "manager"] },
  { key: "funds-user", label: "经费申请", path: "/funds", icon: "Money", order: 6, roles: ["operator", "viewer", "approval_leader"] },
  { key: "policies", label: "政策法规", path: "/policies", icon: "Document", order: 7 },
  { key: "rural-works", label: "乡村工作", path: "/rural-works", icon: "Sunny", order: 8 },
  { key: "approval", label: "审批管理", path: "/approval/pending", icon: "Stamp", order: 9, roles: ["admin", "super_admin", "approval_leader", "manager"] },
  {
    key: "helpData", label: "帮扶数据管理", icon: "TrendCharts", order: 10,
    roles: ["admin", "super_admin", "manager", "operator"],
    children: [
      { key: "comprehensive-entry", label: "综合数据录入", path: "/data-entry" },
      { key: "batch-import", label: "数据批量导入", path: "/data-import/batch", roles: ["admin", "super_admin", "manager"] },
      { key: "data-verify", label: "数据校验审核", path: "/funds", roles: ["admin", "super_admin", "manager"] },
      { key: "data-analysis", label: "数据统计分析", path: "/data-analysis" },
      { key: "report-templates", label: "报表模板管理", path: "/report/templates", roles: ["admin", "super_admin", "manager"] },
      { key: "report-export", label: "报表导出", path: "/report-export", roles: ["admin", "super_admin", "manager"] },
    ],
  },
  {
    key: "analytics", label: "数据分析", icon: "DataAnalysis", order: 11,
    children: [
      { key: "analytics-dashboard", label: "分析仪表盘", path: "/data-analysis/dashboard" },
      { key: "analytics-map", label: "地图可视化", path: "/data-analysis/map" },
      { key: "work-analysis", label: "工作分析", path: "/data-analysis/reports" },
    ],
  },
  {
    key: "reportExport", label: "数据上报", icon: "Upload", order: 12,
    children: [
      { key: "data-package-report", label: "数据上报", path: "/data-package" },
      { key: "data-package-receive", label: "接收数据包", path: "/data-package/receive", roles: ["admin", "super_admin", "manager"] },
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