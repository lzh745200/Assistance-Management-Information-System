import { logger } from "@/utils/logger";
import { ObjectDirective } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useMenuStore } from "@/stores/menu";
import { ADMIN_ROLES } from "@/utils/roleAccess";

/**
 * 权限指令：支持四种用法
 *
 * 1. 角色列表： v-permission="['admin', 'manager']"
 * 2. 按钮级权限码： v-permission="'project:create'"
 * 3. 菜单 key 检查： v-permission="{ menu: 'system' }"
 * 4. 模块 view/edit 粒度： v-permission="{ module: 'village', level: 'edit' }"
 *    - level: 'view' → 检查 {module}:read，无权限则移除元素
 *    - level: 'edit' → 检查 {module}:write，无权限则隐藏/禁用元素
 *
 * 管理员自动拥有所有权限
 */
export const permission: ObjectDirective = {
  mounted(el, binding) {
    const { value } = binding;
    const authStore = useAuthStore();
    const menuStore = useMenuStore();
    const currentRole = authStore.user?.role || "";

    // 管理员始终放行
    if (ADMIN_ROLES.includes(currentRole) || authStore.user?.is_superuser) {
      return;
    }

    // 模式 3：菜单 key 检查，如 v-permission="{ menu: 'system' }"
    if (value && typeof value === "object" && "menu" in value) {
      if (!menuStore.canAccessMenu(value.menu as string)) {
        el.parentNode && el.parentNode.removeChild(el);
      }
      return;
    }

    // 模式 2：字符串权限码，如 v-permission="'project:create'"
    if (typeof value === "string") {
      const userPermissions: string[] = authStore.user?.permissions || [];
      if (!userPermissions.includes(value)) {
        el.parentNode && el.parentNode.removeChild(el);
      }
      return;
    }

    // 模式 1：角色数组，如 v-permission="['admin', 'manager']"
    if (Array.isArray(value) && value.length > 0) {
      const roles = Array.isArray(currentRole) ? currentRole : [currentRole];
      const hasPermission = roles.some((role) => value.includes(role));
      if (!hasPermission) {
        el.parentNode && el.parentNode.removeChild(el);
      }
      return;
    }

    // 模式 4：模块 view/edit 粒度，如 v-permission="{ module: 'village', level: 'edit' }"
    if (
      value &&
      typeof value === "object" &&
      "module" in value &&
      "level" in value
    ) {
      _applyModulePermission(
        el,
        value as { module: string; level: "view" | "edit" },
      );
      return;
    }

    // 无效用法提示
    if (import.meta.env.DEV) {
      logger.warn(
        `v-permission: 需要传入角色数组、权限码字符串或菜单配置对象，当前值:`,
        value,
      );
    }
  },

  updated(el, binding) {
    const { value, oldValue } = binding;
    // 如果值没变，不需要重新检查
    if (JSON.stringify(value) === JSON.stringify(oldValue)) {
      return;
    }

    const authStore = useAuthStore();
    const menuStore = useMenuStore();
    const currentRole = authStore.user?.role || "";

    // 管理员始终放行
    if (ADMIN_ROLES.includes(currentRole) || authStore.user?.is_superuser) {
      el.style.display = "";
      el.removeAttribute("disabled");
      return;
    }

    // 模式 3：菜单 key 检查
    if (value && typeof value === "object" && "menu" in value) {
      if (!menuStore.canAccessMenu(value.menu as string)) {
        el.style.display = "none";
      } else {
        el.style.display = "";
      }
      return;
    }

    // 模式 2：字符串权限码
    if (typeof value === "string") {
      const userPermissions: string[] = authStore.user?.permissions || [];
      if (!userPermissions.includes(value)) {
        el.style.display = "none";
      } else {
        el.style.display = "";
      }
      return;
    }

    // 模式 1：角色数组
    if (Array.isArray(value) && value.length > 0) {
      const roles = [currentRole];
      const hasPermission = roles.some((role) => value.includes(role));
      el.style.display = hasPermission ? "" : "none";
      return;
    }

    // 模式 4：模块 view/edit 粒度
    if (
      value &&
      typeof value === "object" &&
      "module" in value &&
      "level" in value
    ) {
      _applyModulePermission(
        el,
        value as { module: string; level: "view" | "edit" },
      );
      return;
    }
  },
};

/**
 * 应用模块级 view/edit 权限到元素（mounted / updated 共用）
 */
function _applyModulePermission(
  el: HTMLElement,
  { module: mod, level }: { module: string; level: "view" | "edit" },
): void {
  const authStore = useAuthStore();
  const permMap = authStore.modulePermissions;
  const modPerm = permMap[mod] || { view: false, edit: false };
  if (level === "view") {
    el.style.display = modPerm.view || modPerm.edit ? "" : "none";
  } else if (level === "edit") {
    el.style.display = modPerm.edit ? "" : "none";
  }
}
