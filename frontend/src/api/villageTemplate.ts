/**
 * 帮扶村模板API
 * Feature: supported-village-enhancement
 * Requirements: 13.1, 13.4 - 表格模板下载功能
 */

import request, { get } from "./request";

const BASE_URL = "/templates";

// ==================== 类型定义 ====================

/**
 * 模板信息
 */
export interface TemplateInfo {
  /** 模块标识 */
  module: string;
  /** 模板名称 */
  name: string;
  /** 模板描述 */
  description: string;
  /** 文件名 */
  filename: string;
}

/**
 * 模板列表响应
 */
export interface TemplateListResponse {
  /** 模板总数 */
  total: number;
  /** 模板列表 */
  templates: TemplateInfo[];
}

/**
 * 模板下载参数
 */
export interface DownloadTemplateParams {
  /** 数据年份（可选） */
  year?: number;
  /** 是否包含示例数据 */
  includeExample?: boolean;
}

// ==================== API 函数 ====================

/**
 * 获取可用模板列表
 * Requirements: 13.4
 */
export async function getTemplateList(): Promise<TemplateListResponse> {
  // get<T> 已返回 res.data（解包后的数据），无需再 .data
  return get<TemplateListResponse>(BASE_URL);
}

/**
 * 下载指定模块的Excel模板
 * Requirements: 13.1, 13.4
 *
 * @param module 模块名称
 * @param params 下载参数
 */
export async function downloadTemplate(
  module: string,
  params: DownloadTemplateParams = {},
): Promise<void> {
  const { year, includeExample = true } = params;

  // 构建查询参数
  const queryParams = new URLSearchParams();
  queryParams.append("include_example", String(includeExample));
  if (year) {
    queryParams.append("year", String(year));
  }

  const url = `${BASE_URL}/${module}?${queryParams.toString()}`;

  // 使用 blob 方式下载文件
  const response = await request.get(url, {
    responseType: "blob",
  });

  // 从响应头获取文件名
  const contentDisposition = response.headers["content-disposition"];
  let filename = `${module}_template.xlsx`;

  if (contentDisposition) {
    // 尝试解析 filename*=UTF-8'' 格式
    const utf8Match = contentDisposition.match(/filename\*=UTF-8''(.+)/i);
    if (utf8Match) {
      filename = decodeURIComponent(utf8Match[1]);
    } else {
      // 尝试解析普通 filename= 格式
      const normalMatch = contentDisposition.match(
        /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/,
      );
      if (normalMatch) {
        filename = normalMatch[1].replace(/['"]/g, "");
      }
    }
  }

  // 创建下载链接
  const blob = new Blob([response.data], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(downloadUrl);
}

/**
 * 获取模板模块列表（静态数据，用于离线场景）
 */
export function getStaticTemplateModules(): TemplateInfo[] {
  return [
    {
      module: "village",
      name: "帮扶村基础数据",
      description: "帮扶村基础信息导入模板，包含部门、帮扶单位、村庄名称等字段",
      filename: "帮扶村数据导入模板",
    },
    {
      module: "population",
      name: "人口数据",
      description: "帮扶村人口数据导入模板，包含户数、人口、常住人口等字段",
      filename: "人口数据导入模板",
    },
    {
      module: "income",
      name: "收入数据",
      description: "帮扶村收入数据导入模板，包含人均纯收入、村集体收入等字段",
      filename: "收入数据导入模板",
    },
    {
      module: "funding",
      name: "经费投入",
      description: "帮扶经费投入数据导入模板",
      filename: "经费投入导入模板",
    },
    {
      module: "force",
      name: "力量投入",
      description: "力量投入情况数据导入模板，包含领导干部到村人次等字段",
      filename: "力量投入导入模板",
    },
    {
      module: "industry",
      name: "产业帮扶",
      description: "产业帮扶情况数据导入模板",
      filename: "产业帮扶导入模板",
    },
    {
      module: "infrastructure",
      name: "基础设施",
      description: "基础设施改善情况数据导入模板",
      filename: "基础设施导入模板",
    },
    {
      module: "party",
      name: "党建帮扶",
      description: "党建帮扶情况数据导入模板",
      filename: "党建帮扶导入模板",
    },
    {
      module: "medical",
      name: "医疗帮扶",
      description: "医疗帮扶情况数据导入模板",
      filename: "医疗帮扶导入模板",
    },
    {
      module: "consumption",
      name: "消费帮扶",
      description: "消费帮扶情况数据导入模板",
      filename: "消费帮扶导入模板",
    },
    {
      module: "employment",
      name: "就业帮扶",
      description: "就业帮扶情况数据导入模板",
      filename: "就业帮扶导入模板",
    },
    {
      module: "education",
      name: "教育帮扶",
      description: "教育帮扶情况数据导入模板",
      filename: "教育帮扶导入模板",
    },
  ];
}

/**
 * 根据模块获取模板信息
 * @param module 模块标识
 */
export function getTemplateInfoByModule(
  module: string,
): TemplateInfo | undefined {
  return getStaticTemplateModules().find((t) => t.module === module);
}
