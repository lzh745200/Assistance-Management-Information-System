import { defineStore } from "pinia";
import { ref } from "vue";

export interface MenuItem {
  key: string;
  label: string;
  path?: string;
  icon?: string;
  roles?: string[];
  children?: MenuItem[];
  order?: number;
}

/** 递归查找菜单项（辅助函数） */
function _findMenuItem(items: MenuItem[], key: string): MenuItem | undefined {
  for (const item of items) {
    if (item.key === key) return item;
    if (item.children?.length) {
      const found = _findMenuItem(item.children, key);
      if (found) return found;
    }
  }
  return undefined;
}

export const useMenuStore = defineStore("menu", () => {
  const menus = ref<MenuItem[]>([]);
  const activeMenu = ref("");

  function setMenus(items: MenuItem[]) {
    menus.value = items;
  }

  function setActive(key: string) {
    activeMenu.value = key;
  }

  /** 检查用户是否可以访问指定菜单 key（菜单树中存在即视为可访问） */
  function canAccessMenu(menuKey: string): boolean {
    return _findMenuItem(menus.value, menuKey) !== undefined;
  }

  return { menus, activeMenu, setMenus, setActive, canAccessMenu };
});
