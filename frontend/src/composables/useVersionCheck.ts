/**
 * useVersionCheck — 版本指纹校验
 *
 * 应用启动时从服务器获取 /version.json，与 localStorage 中
 * 缓存的版本号比对。版本不一致 → 提示用户系统已更新 → 自动强制刷新。
 * fetch 失败时静默跳过，不阻塞应用启动。
 *
 * Usage (在 App.vue onMounted 中):
 *   import { checkVersion } from '@/composables/useVersionCheck';
 *   onMounted(() => { checkVersion(); });
 */
import { ElMessage } from "element-plus";

/** localStorage 键名 */
const VERSION_KEY = "app_version";

/** 版本比对后自动刷新的延迟（毫秒） */
const RELOAD_DELAY = 1500;

/**
 * 检查应用版本是否需要更新。
 * 从服务器获取 /version.json，与本地缓存比对。
 * 不一致时：显示提示 → 更新缓存 → 延迟后强制刷新。
 * 网络错误时静默跳过。
 */
export async function checkVersion(): Promise<void> {
  try {
    const response = await fetch(`/version.json?t=${Date.now()}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      // 404 或其他 HTTP 错误 → 静默跳过（可能 version.json 未部署）
      return;
    }

    const data = (await response.json()) as { version?: string };
    const serverVersion = data?.version;

    if (!serverVersion) {
      return; // version.json 格式不正确
    }

    const cachedVersion = localStorage.getItem(VERSION_KEY);

    if (!cachedVersion) {
      // 首次访问 → 保存版本号，不刷新
      localStorage.setItem(VERSION_KEY, serverVersion);
      return;
    }

    if (cachedVersion !== serverVersion) {
      // 版本不一致 → 提示用户 + 延迟刷新
      localStorage.setItem(VERSION_KEY, serverVersion);
      ElMessage.warning({
        message: `系统已更新至 v${serverVersion}，即将自动刷新...`,
        duration: RELOAD_DELAY,
      });
      setTimeout(() => {
        // 强制刷新，绕过浏览器缓存
        window.location.reload();
      }, RELOAD_DELAY);
    }
    // 版本一致 → 无需操作
  } catch {
    // 网络错误 → 静默跳过，不阻塞应用
    console.debug("[VersionCheck] /version.json 获取失败，跳过版本检查");
  }
}

export default checkVersion;
