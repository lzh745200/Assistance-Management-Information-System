/**
 * 用户权限路由示例配置
 * 此文件供参考，实际路由配置在 index.ts 中
 */
export const userPermissionRoutes = [
  {
    path: "/profile",
    name: "Profile",
    meta: { title: "个人中心", roles: ["*"] },
  },
  {
    path: "/change-password",
    name: "ChangePassword",
    meta: { title: "修改密码", roles: ["*"] },
  },
];
