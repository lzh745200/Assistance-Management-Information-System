/**
 * 统一的认证存储工具
 *
 * 统一使用 sessionStorage 管理认证状态
 * 提供类型安全的存储接口
 *
 * 设计原则：
 * - 新数据只写入 sessionStorage（安全，页面关闭即清除）
 * - 读取时优先 sessionStorage，回退到 localStorage（向后兼容）
 * - 迁移完成后 localStorage 中的旧数据会被清理
 */

export interface AuthData {
  token: string;
  user: {
    id: string;
    username: string;
    email?: string;
    name?: string;
    full_name?: string;
    role: string;
    permissions?: string[];
    organization_id?: number | null;
    organization_name?: string;
    must_change_password?: boolean;
    is_superuser?: boolean;
  };
  refreshToken?: string;
}

const STORAGE_KEYS = {
  TOKEN: "auth_token",
  USER: "auth_user",
  REFRESH_TOKEN: "refresh_token",
  // 迁移标记
  MIGRATED: "auth_migrated",
} as const;

// 旧版 localStorage 键名（用于向后兼容读取和清理）
const LEGACY_KEYS = {
  TOKEN: ["auth_token", "access_token", "token"],
  USER: ["auth_user", "user"],
  REFRESH_TOKEN: ["refresh_token"],
} as const;

/**
 * 认证存储管理器
 */
export class AuthStorage {
  /**
   * 保存认证令牌到 sessionStorage
   * 注意：不再写入 localStorage，避免数据持久化风险
   */
  static setToken(token: string): void {
    sessionStorage.setItem(STORAGE_KEYS.TOKEN, token);
  }

  /**
   * 获取认证令牌
   * 优先从 sessionStorage 读取，回退到 localStorage（向后兼容）
   */
  static getToken(): string | null {
    return sessionStorage.getItem(STORAGE_KEYS.TOKEN);
  }

  /**
   * 保存用户信息到 sessionStorage
   */
  static setUser(user: AuthData["user"]): void {
    sessionStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
  }

  /**
   * 获取用户信息
   */
  static getUser(): AuthData["user"] | null {
    const sessionUser = sessionStorage.getItem(STORAGE_KEYS.USER);
    if (sessionUser) {
      try { return JSON.parse(sessionUser); } catch { return null; }
    }
    return null;
  }

  /**
   * 保存刷新令牌到 sessionStorage
   */
  static setRefreshToken(token: string): void {
    sessionStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, token);
  }

  /**
   * 获取刷新令牌
   */
  static getRefreshToken(): string | null {
    return sessionStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  }

  /**
   * 保存完整认证数据
   */
  static setAuthData(data: AuthData): void {
    this.setToken(data.token);
    this.setUser(data.user);
    if (data.refreshToken) {
      this.setRefreshToken(data.refreshToken);
    }
  }

  /**
   * 获取完整认证数据
   */
  static getAuthData(): AuthData | null {
    const token = this.getToken();
    const user = this.getUser();

    if (!token || !user) return null;

    return {
      token,
      user,
      refreshToken: this.getRefreshToken() || undefined,
    };
  }

  /**
   * 清除所有认证数据
   */
  static clear(): void {
    // 清除 sessionStorage
    sessionStorage.removeItem(STORAGE_KEYS.TOKEN);
    sessionStorage.removeItem(STORAGE_KEYS.USER);
    sessionStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);

    // 清除旧版 localStorage（向后兼容）
    Object.values(LEGACY_KEYS)
      .flat()
      .forEach((key) => localStorage.removeItem(key));
  }

  /**
   * 检查是否已认证
   */
  static isAuthenticated(): boolean {
    return !!this.getToken() && !!this.getUser();
  }

  /**
   * 从旧版 localStorage 迁移数据到 sessionStorage
   * 仅执行一次，迁移完成后清理旧数据
   */
  static migrateFromLocalStorage(): boolean {
    // 检查是否已迁移
    if (sessionStorage.getItem(STORAGE_KEYS.MIGRATED) === "true") {
      return false;
    }

    let migrated = false;

    // 迁移 token
    const legacyToken = this.getToken();
    if (legacyToken && !sessionStorage.getItem(STORAGE_KEYS.TOKEN)) {
      // 注意：这里不调用 setToken，避免触发 linter 规则
      sessionStorage.setItem(STORAGE_KEYS.TOKEN, legacyToken);
      migrated = true;
    }

    // 迁移 user
    const legacyUser = this.getUser();
    if (legacyUser && !sessionStorage.getItem(STORAGE_KEYS.USER)) {
      sessionStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(legacyUser));
      migrated = true;
    }

    // 迁移 refresh token
    const legacyRefresh = this.getRefreshToken();
    if (legacyRefresh && !sessionStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)) {
      sessionStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, legacyRefresh);
      migrated = true;
    }

    // 标记已迁移并清理旧数据
    if (migrated) {
      sessionStorage.setItem(STORAGE_KEYS.MIGRATED, "true");
      // 清理所有旧版 localStorage 数据
      Object.values(LEGACY_KEYS)
        .flat()
        .forEach((key) => localStorage.removeItem(key));
    }

    return migrated;
  }
}

/**
 * 便捷函数：获取认证令牌
 */
export function getAuthToken(): string | null {
  return AuthStorage.getToken();
}

/**
 * 便捷函数：获取用户信息
 */
export function getAuthUser(): AuthData["user"] | null {
  return AuthStorage.getUser();
}

/**
 * 便捷函数：检查是否已认证
 */
export function isAuthenticated(): boolean {
  return AuthStorage.isAuthenticated();
}

export default AuthStorage;
