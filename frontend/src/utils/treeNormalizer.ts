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

/** 生成稳定的、基于内容的回退键 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function makeStableId(node: any): string {
  const raw = String(
    node.id ??
      node.key ??
      `_node_${(node.name || node.label || "").substring(0, 20)}`,
  );
  // 确保以字母开头 — 纯数字 id（如 0）会导致 DOM setAttribute('0', …) 异常
  return /^[0-9]/.test(raw) ? `_${raw}` : raw;
}

/** 将单节点 id 转为字符串，白名单属性，递归标准化子节点 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function normalizeTreeNode(node: any): any {
  const hasChildrenArray = Array.isArray(node.children);
  const children = hasChildrenArray
    ? node.children.length
      ? normalizeTreeNodes(node.children)
      : []
    : undefined;

  return {
    id: makeStableId(node),
    name: node.name,
    label: node.label ?? node.name,
    children,
    leaf: hasChildrenArray
      ? node.children.length === 0
      : (node.leaf ?? !node.children?.length),
  };
}

/** 递归规范化整棵树 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function normalizeTreeNodes(nodes: any[]): any[] {
  return nodes.map((node) => normalizeTreeNode(node));
}
