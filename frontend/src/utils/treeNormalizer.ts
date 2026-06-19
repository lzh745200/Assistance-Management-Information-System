/**
 * 组织树节点规范化工具
 *
 * 解决 Element Plus el-tree / el-tree-select 无法处理数值型 id 的问题：
 * el-tree 内部通过 setAttribute('id', ...) 设置 DOM id 属性，
 * 当 id 为 0 或纯数字时触发 DOMException: "'0' is not a valid attribute name"
 *
 * 根因修复建议：后端 API 返回 id 为字符串（在路由/服务层统一转换）
 * 当前前端侧统一用此工具兜底。
 */

/** 将单节点 id 转为字符串（保留 children 并设置 leaf 标志） */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function normalizeTreeNode(node: any): any {
  return {
    ...node,
    id: String(node.id ?? ""),
    leaf: !node.children || node.children.length === 0,
  };
}

/** 递归规范化整棵树 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function normalizeTreeNodes(nodes: any[]): any[] {
  return nodes.map((node) => ({
    ...node,
    id: String(node.id ?? node.key ?? ""),
    children: node.children ? normalizeTreeNodes(node.children) : undefined,
  }));
}
