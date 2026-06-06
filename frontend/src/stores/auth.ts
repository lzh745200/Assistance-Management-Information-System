import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { apiRequest, _setCachedToken } from "@/api/request";
import { getCurrentUser } from "@/api/queries/user";
import { AuthStorage } from "@/utils/authStorage";
import { ADMIN_ROLES } from "@/utils/roleAccess";
import type { AuthData } from "@/utils/authStorage";
import type { ApiResponse } from "@/types/api";

export type UserInfo = AuthData["user"];

/** Wire-format login response (snake_case, matches backend JSON) */
interface LoginPayload {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  user: UserInfo;
  must_change_password?: boolean;
}

export const useAuthStore = defineStore("auth", () => {
  const token = ref(AuthStorage.getToken() || "");
  const user = ref<UserInfo | null>(AuthStorage.getUser());
  const error = ref("");

  const isAuthenticated = computed(() => !!token.value);
  const isAdmin = computed(
    () =>
      user.value?.is_superuser === true ||
      ADMIN_ROLES.includes(user.value?.role ?? ""),
  );
  const mustChangePassword = computed(
    () => user.value?.must_change_password ?? false,
  );

  function persistAuth(t: string, u: UserInfo, refreshToken?: string) {
    token.value = t;
    user.value = u;
    _setCachedToken(t);
    AuthStorage.setAuthData({ token: t, user: u, refreshToken });
  }

  function logout() {
    token.value = "";
    user.value = null;
    error.value = "";
    _setCachedToken(null);
    AuthStorage.clear();
  }

  /**
   * 登录；返回 true 表示登录成功，false 表示失败。
   */
  async function login(username: string, password: string): Promise<boolean> {
    error.value = "";

    try {
      const res = await apiRequest<ApiResponse<LoginPayload>>({
        method: "POST",
        url: "/auth/login",
        data: { username, password },
        timeout: 60000, // 登录超时 60s，bcrypt 纯 Python 回退时仍需安全兜底
      });

      if (res.code === 200 && res.data) {
        persistAuth(
          res.data.access_token,
          res.data.user,
          res.data.refresh_token,
        );
        return true;
      }

      error.value = res.message || "登录失败";
      return false;
    } catch (err: any) {
      const msg = err?.response?.data?.message || err?.message || "登录失败";
      error.value = msg;
      return false;
    }
  }

  /**
   * 页面刷新时恢复用户信息（token 已存在但 user 对象可能丢失）。
   * 仅在有 token 但无 user 时调用。
   */
  async function fetchUser() {
    if (!token.value || user.value) return;
    try {
      const res = await getCurrentUser();
      if (res.code === 200 && res.data) {
        user.value = res.data as UserInfo;
        AuthStorage.setUser(res.data as UserInfo);
      }
    } catch {
      // 401 已由 api/request.ts 拦截器 + 路由守卫处理跳转
    }
  }

  return {
    token,
    user,
    error,
    mustChangePassword,
    isAuthenticated,
    isAdmin,
    logout,
    login,
    fetchUser,
  };
});
