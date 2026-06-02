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

export const useMenuStore = defineStore("menu", () => {
  const menus = ref<MenuItem[]>([]);
  const activeMenu = ref("");

  function setMenus(items: MenuItem[]) {
    menus.value = items;
  }

  function setActive(key: string) {
    activeMenu.value = key;
  }

  return { menus, activeMenu, setMenus, setActive };
});