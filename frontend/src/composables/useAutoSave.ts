/**
 * 自动保存 Composable — 增强版
 *
 * 支持:
 * - 防抖自动保存
 * - localStorage 草稿持久化（防页面关闭丢失）
 * - 草稿恢复提醒
 * - 暂停/恢复
 * - 保存状态指示
 *
 * @example
 * const { isDirty, isSaving, lastSaved, hasDraft, markDirty, triggerSave, restoreDraft, clearDraft } = useAutoSave(
 *   async () => await api.saveProject(projectForm.value),
 *   { delayMs: 3000, storageKey: 'project-draft', persistDraft: true }
 * )
 */

import { ref, onUnmounted, type Ref } from "vue";

export interface AutoSaveOptions {
  /** 防抖延迟 (ms)，默认 3000 */
  delayMs?: number;
  /** 草稿 localStorage 键名，为空则不持久化 */
  storageKey?: string;
  /** 是否持久化草稿 (默认 true) */
  persistDraft?: boolean;
  /** 是否启用 (默认 true) */
  enabled?: boolean;
  /** 草稿数据（用于持久化） */
  draftData?: Ref<Record<string, any>> | (() => Record<string, any>);
}

export interface AutoSaveReturn {
  isDirty: Ref<boolean>;
  isSaving: Ref<boolean>;
  lastSaved: Ref<Date | null>;
  hasDraft: Ref<boolean>;
  /** 标记数据已变更（触发防抖自动保存） */
  markDirty: () => void;
  /** 立即保存（跳过防抖） */
  triggerSave: () => Promise<void>;
  /** 恢复上次草稿 */
  restoreDraft: () => Record<string, any> | null;
  /** 清除草稿 */
  clearDraft: () => void;
  /** 暂停自动保存 */
  pause: () => void;
  /** 恢复自动保存 */
  resume: () => void;
}

export function useAutoSave(
  saveFn: () => Promise<void>,
  options: AutoSaveOptions = {},
): AutoSaveReturn {
  const {
    delayMs = 3000,
    storageKey,
    persistDraft = true,
    enabled = true,
    draftData,
  } = options;

  const isDirty = ref(false);
  const isSaving = ref(false);
  const lastSaved = ref<Date | null>(null);
  const isPaused = ref(false);

  let timer: ReturnType<typeof setTimeout> | null = null;

  // 检查是否有草稿
  const hasDraft = ref(!!(storageKey && localStorage.getItem(storageKey)));

  // 持久化草稿到 localStorage
  function persistDraftData() {
    if (!storageKey || !persistDraft) return;
    try {
      let data: Record<string, any> = {};
      if (typeof draftData === "function") {
        data = draftData();
      } else if (draftData?.value) {
        data = draftData.value;
      }
      if (data && Object.keys(data).length > 0) {
        localStorage.setItem(
          storageKey,
          JSON.stringify({
            data,
            timestamp: new Date().toISOString(),
          }),
        );
        hasDraft.value = true;
      }
    } catch (e) {
      console.error(`[auto-save] 保存草稿 "${storageKey}" 失败:`, e);
    }
  }

  // 恢复草稿
  function restoreDraft(): Record<string, any> | null {
    if (!storageKey) return null;
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) return null;
      return JSON.parse(raw).data;
    } catch {
      return null;
    }
  }

  // 清除草稿
  function clearDraft() {
    if (storageKey) {
      localStorage.removeItem(storageKey);
      hasDraft.value = false;
    }
  }

  function markDirty() {
    isDirty.value = true;
    if (timer) clearTimeout(timer);

    // 先持久化草稿
    persistDraftData();

    timer = setTimeout(() => {
      triggerSave();
    }, delayMs);
  }

  async function triggerSave() {
    if (!isDirty.value || isSaving.value) return;
    if (isPaused.value) return;
    if (enabled === false) return;

    isSaving.value = true;
    try {
      await saveFn();
      isDirty.value = false;
      lastSaved.value = new Date();
      clearDraft();
    } catch (e) {
      console.error("[auto-save] 保存失败:", e);
    } finally {
      isSaving.value = false;
    }
  }

  function pause() {
    isPaused.value = true;
  }

  function resume() {
    isPaused.value = false;
  }

  // 页面关闭前保存草稿（仅在启用持久化时注册监听器）
  function onBeforeUnload(e: BeforeUnloadEvent) {
    if (isDirty.value) {
      persistDraftData();
      e.preventDefault();
      e.returnValue = "您有未保存的更改，确定要离开吗？";
    }
  }

  if (typeof window !== "undefined" && storageKey && persistDraft) {
    window.addEventListener("beforeunload", onBeforeUnload);
  }

  onUnmounted(() => {
    if (timer) clearTimeout(timer);
    if (typeof window !== "undefined") {
      window.removeEventListener("beforeunload", onBeforeUnload);
    }
    // 组件卸载时触发保存
    if (isDirty.value) {
      triggerSave();
    }
  });

  return {
    isDirty,
    isSaving,
    lastSaved,
    hasDraft,
    markDirty,
    triggerSave,
    restoreDraft,
    clearDraft,
    pause,
    resume,
  };
}
