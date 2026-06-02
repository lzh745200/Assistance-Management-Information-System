/**
 * 权限定义
 */

export type Role = string;
export type Permission = string;

export const rolePermissions: Record<string, string[]> = {
  super_admin: ["*"],
  admin: ["read", "write", "delete"],
  manager: ["read", "write"],
  operator: ["read", "write"],
  viewer: ["read"],
  approval_leader: ["read", "approve"],
};

export const routePermissions: Record<string, string[]> = {
  "/dashboard": ["read"],
  "/villages": ["read"],
  "/schools": ["read"],
  "/projects": ["read"],
  "/funds": ["read"],
  "/policies": ["read"],
  "/rural-works": ["read"],
  "/approval": ["read", "approve"],
};