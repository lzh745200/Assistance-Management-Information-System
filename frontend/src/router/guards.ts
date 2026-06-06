/**
 * 路由守卫
 */
import router from "./index";
import { AuthStorage } from "@/utils/authStorage";
import { ADMIN_ROLES } from "@/utils/roleAccess";

const whiteList = ["/login", "/register", "/forgot-password"];

router.beforeEach((to, _from, next) => {
  document.title = (to.meta?.title as string) || "帮扶管理信息系统";

  // 优先检查 meta.noAuth（public 路由），避免白名单遗漏导致无限重定向
  if (to.meta?.noAuth === true || whiteList.includes(to.path)) {
    next();
    return;
  }

  // 直接从 AuthStorage 读取 — 401 拦截器清理存储后此处能立即感知
  const token = AuthStorage.getToken();
  if (!token) {
    next(`/login?redirect=${to.path}`);
    return;
  }

  // 角色权限检查：meta.roles 非空时校验用户是否有对应角色
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

  next();
});

export default router;
