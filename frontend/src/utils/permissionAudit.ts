/**
 * 权限审计工具
 *
 * 开发环境下自动扫描路由配置和权限映射，检测以下冲突：
 * 1. 路由配置了 meta.roles 但角色权限映射中不存在对应权限
 * 2. 路由配置了 meta.requiredPermissions 但角色映射中缺少
 * 3. 同一路由同时配置了 requiresAdmin 和普通用户角色
 * 4. 菜单入口指向了用户无权限访问的路由
 */

import { logger } from "@/utils/logger";
import type { RouteRecordRaw } from "vue-router";
import {
  type Role,
  type Permission,
  rolePermissions,
  routePermissions,
} from "@/router/permissions";

interface AuditIssue {
  level: "error" | "warn" | "info";
  route: string;
  message: string;
}

const NORMAL_ROLES: Role[] = ["operator", "viewer", "approval_leader"];

/**
 * 审计路由权限配置
 */
export function auditRoutePermissions(routes: RouteRecordRaw[]): AuditIssue[] {
  const issues: AuditIssue[] = [];

  function walk(routeList: RouteRecordRaw[], parentPath = "") {
    for (const route of routeList) {
      const fullPath = `${parentPath}/${route.path}`.replace(/\/+/g, "/");
      const meta = route.meta as Record<string, unknown> | undefined;

      if (meta) {
        // 检查 1: requiresAdmin 与 roles 冲突
        if (meta.requiresAdmin && Array.isArray(meta.roles)) {
          const roles = meta.roles as string[];
          const hasNormalRole = roles.some((r) =>
            NORMAL_ROLES.includes(r as Role),
          );
          if (hasNormalRole) {
            issues.push({
              level: "error",
              route: fullPath,
              message: `路由同时设置了 requiresAdmin=true 和普通用户角色 [${roles.join(",")}]，存在权限冲突`,
            });
          }
        }

        // 检查 2: roles 中的角色是否在 rolePermissions 中定义
        if (Array.isArray(meta.roles)) {
          for (const role of meta.roles as string[]) {
            if (!(role in rolePermissions)) {
              issues.push({
                level: "error",
                route: fullPath,
                message: `角色 "${role}" 未在 rolePermissions 中定义`,
              });
            }
          }
        }

        // 检查 3: requiredPermissions 是否被至少一个角色拥有
        if (Array.isArray(meta.requiredPermissions)) {
          for (const perm of meta.requiredPermissions as string[]) {
            const rolesWithPerm = (
              Object.keys(rolePermissions) as Role[]
            ).filter((r) => rolePermissions[r].includes(perm as Permission));
            if (rolesWithPerm.length === 0) {
              issues.push({
                level: "warn",
                route: fullPath,
                message: `权限 "${perm}" 未分配给任何角色，该路由将无人可访问`,
              });
            }
          }
        }
      }

      // 检查 4: routePermissions 中的路由名是否存在于路由配置
      if (route.name && typeof route.name === "string") {
        const routeName = route.name;
        if (routePermissions[routeName]) {
          const requiredPerms = routePermissions[routeName];
          // 确保至少有一个非管理员角色能访问（如果路由不是管理员专属）
          if (!meta?.requiresAdmin) {
            const anyNormalCanAccess = NORMAL_ROLES.some((role) => {
              const perms = rolePermissions[role] || [];
              return requiredPerms.some((p) => perms.includes(p));
            });
            if (!anyNormalCanAccess && !meta?.roles) {
              issues.push({
                level: "info",
                route: fullPath,
                message: `路由 "${routeName}" 的权限 [${requiredPerms.join(",")}] 仅管理员角色拥有，但未标记 requiresAdmin 或 roles`,
              });
            }
          }
        }
      }

      // 递归子路由
      if (route.children?.length) {
        walk(route.children, fullPath);
      }
    }
  }

  walk(routes);
  return issues;
}

/**
 * 审计角色权限映射（检查对称性和完整性）
 */
export function auditRolePermissions(): AuditIssue[] {
  const issues: AuditIssue[] = [];

  // 收集 routePermissions 中使用到的所有权限
  const usedPermissions = new Set<string>();
  for (const perms of Object.values(routePermissions)) {
    perms.forEach((p) => usedPermissions.add(p));
  }

  // 检查每个角色是否有"孤立"权限（定义了但没有路由使用）
  for (const [role, perms] of Object.entries(rolePermissions)) {
    for (const perm of perms) {
      if (!usedPermissions.has(perm)) {
        issues.push({
          level: "info",
          route: "-",
          message: `角色 "${role}" 拥有权限 "${perm}"，但没有路由使用该权限`,
        });
      }
    }
  }

  return issues;
}

/**
 * 在开发环境下执行权限审计并打印结果
 */
export function runPermissionAudit(routes: RouteRecordRaw[]): void {
  if (import.meta.env.PROD) return;

  const routeIssues = auditRoutePermissions(routes);
  const roleIssues = auditRolePermissions();
  const allIssues = [...routeIssues, ...roleIssues];

  if (allIssues.length === 0) {
    logger.info(
      "%c✅ 权限审计通过，未发现冲突",
      "color: green; font-weight: bold",
    );
    return;
  }

  console.group("%c🔍 权限审计报告", "color: #409eff; font-weight: bold");

  const errors = allIssues.filter((i) => i.level === "error");
  const warns = allIssues.filter((i) => i.level === "warn");
  const infos = allIssues.filter((i) => i.level === "info");

  if (errors.length) {
    console.group(`❌ 错误 (${errors.length})`);
    errors.forEach((i) => logger.error(`[${i.route}] ${i.message}`));
    console.groupEnd();
  }

  if (warns.length) {
    console.group(`⚠️ 警告 (${warns.length})`);
    warns.forEach((i) => logger.warn(`[${i.route}] ${i.message}`));
    console.groupEnd();
  }

  if (infos.length) {
    console.group(`ℹ️ 提示 (${infos.length})`);
    infos.forEach((i) => logger.info(`[${i.route}] ${i.message}`));
    console.groupEnd();
  }

  console.groupEnd();
}
