/**
 * RBAC权限路由守卫
 */

import { logger } from "@/utils/logger";
import { useRbacStore } from "@/stores/rbac";
import { useAuthStore } from "@/stores/auth";
import type { RouteLocationNormalized, NavigationGuardNext } from "vue-router";

export interface RoutePermissionGuard {
  /**
   * 检查用户是否有访问路由的权限
   * @param to 目标路由
   * @param from 来源路由
   * @param next 下一步函数
   */
  (
    to: RouteLocationNormalized,
    from: RouteLocationNormalized,
    next: NavigationGuardNext,
  ): void;
}

/** 获取当前用户角色（辅助函数，DRY） */
function _getCurrentRole(): string {
  const authStore = useAuthStore();
  return authStore.user?.role || "";
}

/**
 * 创建权限守卫
 * @param routePermissions 路由权限配置
 */
export function createPermissionGuard(
  routePermissions: Record<string, string[]>,
): RoutePermissionGuard {
  return (to, _from, next) => {
    const rbacStore = useRbacStore();
    const userRole = _getCurrentRole();

    // 获取路由权限要求
    const requiredPermissions = routePermissions[to.path];

    // 如果路由没有权限要求，直接放行
    if (!requiredPermissions || requiredPermissions.length === 0) {
      next();
      return;
    }

    // 检查是否有任意一个所需权限
    const hasPermission = requiredPermissions.some((permission) =>
      rbacStore.hasPermission(userRole, permission),
    );

    if (hasPermission) {
      next();
    } else {
      // 权限不足，跳转到无权限页面
      next({ path: "/403", query: { redirect: to.fullPath } });
    }
  };
}

/**
 * 创建异步权限守卫（等待权限加载完成）
 * @param routePermissions 路由权限配置
 */
export function createAsyncPermissionGuard(
  routePermissions: Record<string, string[]>,
): RoutePermissionGuard {
  return async (to, _from, next) => {
    const rbacStore = useRbacStore();
    const userRole = _getCurrentRole();

    // 等待权限加载完成
    await rbacStore.loadUserPermissions();

    // 获取路由权限要求
    const requiredPermissions = routePermissions[to.path];

    // 如果路由没有权限要求，直接放行
    if (!requiredPermissions || requiredPermissions.length === 0) {
      next();
      return;
    }

    // 检查是否有任意一个所需权限
    const hasPermission = requiredPermissions.some((permission) =>
      rbacStore.hasPermission(userRole, permission),
    );

    if (hasPermission) {
      next();
    } else {
      // 权限不足，跳转到无权限页面
      next({ path: "/403", query: { redirect: to.fullPath } });
    }
  };
}

/**
 * 权限指令 - 用于元素级权限控制
 */
export const permissionDirective = {
  mounted(el: HTMLElement, binding: any) {
    const { value } = binding;
    const rbacStore = useRbacStore();
    const userRole = _getCurrentRole();

    if (!value) {
      logger.warn("v-permission directive requires a permission value");
      return;
    }

    // 检查权限
    const hasPermission = rbacStore.hasPermission(userRole, value);

    if (!hasPermission) {
      // 权限不足，隐藏或禁用元素
      if (binding.arg === "disabled") {
        el.setAttribute("disabled", "true");
        el.classList.add("permission-disabled");
      } else {
        el.style.display = "none";
        el.classList.add("permission-hidden");
      }
    }
  },

  updated(el: HTMLElement, binding: any) {
    const { value } = binding;
    const rbacStore = useRbacStore();
    const userRole = _getCurrentRole();

    if (!value) {
      return;
    }

    // 检查权限
    const hasPermission = rbacStore.hasPermission(userRole, value);

    if (!hasPermission) {
      if (binding.arg === "disabled") {
        el.setAttribute("disabled", "true");
        el.classList.add("permission-disabled");
      } else {
        el.style.display = "none";
        el.classList.add("permission-hidden");
      }
    } else {
      // 权限足够，移除相关样式
      el.removeAttribute("disabled");
      el.style.display = "";
      el.classList.remove("permission-disabled", "permission-hidden");
    }
  },
};

/**
 * 角色指令 - 用于基于角色的显示控制
 */
export const roleDirective = {
  mounted(el: HTMLElement, binding: any) {
    const { value } = binding;
    const rbacStore = useRbacStore();

    if (!value) {
      logger.warn("v-role directive requires a role value");
      return;
    }

    // 检查角色
    const hasRole = rbacStore.hasRole(value);

    if (!hasRole) {
      el.style.display = "none";
      el.classList.add("role-hidden");
    }
  },

  updated(el: HTMLElement, binding: any) {
    const { value } = binding;
    const rbacStore = useRbacStore();

    if (!value) {
      return;
    }

    const hasRole = rbacStore.hasRole(value);

    if (!hasRole) {
      el.style.display = "none";
      el.classList.add("role-hidden");
    } else {
      el.style.display = "";
      el.classList.remove("role-hidden");
    }
  },
};

/**
 * 权限过滤器 - 用于在模板中判断权限
 */
export const permissionFilter = (permission: string): boolean => {
  const rbacStore = useRbacStore();
  const userRole = _getCurrentRole();
  return rbacStore.hasPermission(userRole, permission);
};

/**
 * 角色过滤器 - 用于在模板中判断角色
 */
export const roleFilter = (role: string): boolean => {
  const rbacStore = useRbacStore();
  return rbacStore.hasRole(role);
};
