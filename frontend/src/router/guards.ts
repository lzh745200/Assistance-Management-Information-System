/**
 * 路由守卫 — 认证 + 菜单权限双重校验
 */
import router from "./index";
import { AuthStorage } from "@/utils/authStorage";
import { ADMIN_ROLES } from "@/utils/roleAccess";
import { useMenuStore } from "@/stores/menu";

const whiteList = ["/login", "/register", "/forgot-password"];

router.beforeEach(async (to, _from, next) => {
  document.title = (to.meta?.title as string) || "帮扶管理信息系统";

  // 公开路由直接放行
  if (to.meta?.noAuth === true || whiteList.includes(to.path)) {
    next();
    return;
  }

  // 未登录 → 登录页
  const token = AuthStorage.getToken();
  if (!token) {
    next(`/login?redirect=${to.path}`);
    return;
  }

  // 角色权限检查：meta.roles 非空时校验用户角色
  const requiredRoles = to.meta?.roles as string[] | undefined;
  if (requiredRoles && requiredRoles.length > 0) {
    const user = AuthStorage.getUser() as Record<string, any> | null;
    const userRole = user?.role || "";
    const hasAccess =
      ADMIN_ROLES.includes(userRole) || requiredRoles.includes(userRole);
    if (!hasAccess) {
      next("/403");
      return;
    }
  }

  // 菜单权限检查：确保菜单已加载，然后根据路由 meta.menuKey 检查可见性
  const menuKey = to.meta?.menuKey as string | undefined;
  if (menuKey) {
    const menuStore = useMenuStore();
    // 首次访问时加载菜单
    if (!menuStore.loaded) {
      await menuStore.fetchMenus();
    }
    if (!menuStore.canAccessMenu(menuKey)) {
      next("/403");
      return;
    }
  }

  next();
});

export default router;
