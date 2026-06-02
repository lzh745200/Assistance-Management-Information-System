/**
 * 保存状态反馈 Composable
 *
 * 提供 saving / saved / error 三态，
 * 在页面底部或表单旁显示保存状态指示器。
 */

import { ref, computed } from "vue";

export type SaveState = "idle" | "saving" | "saved" | "error";

export function useSaveStatus(autoResetMs = 3000) {
  const state = ref<SaveState>("idle");
  const errorMessage = ref("");
  let resetTimer: ReturnType<typeof setTimeout> | null = null;

  const isSaving = computed(() => state.value === "saving");
  const isSaved = computed(() => state.value === "saved");
  const isError = computed(() => state.value === "error");

  const statusText = computed(() => {
    switch (state.value) {
      case "saving":
        return "正在保存...";
      case "saved":
        return "已保存";
      case "error":
        return errorMessage.value || "保存失败";
      default:
        return "";
    }
  });

  function startSaving() {
    if (resetTimer) clearTimeout(resetTimer);
    state.value = "saving";
    errorMessage.value = "";
  }

  function markSaved() {
    state.value = "saved";
    if (resetTimer) clearTimeout(resetTimer);
    resetTimer = setTimeout(() => {
      state.value = "idle";
    }, autoResetMs);
  }

  function markError(msg = "保存失败") {
    state.value = "error";
    errorMessage.value = msg;
    if (resetTimer) clearTimeout(resetTimer);
    resetTimer = setTimeout(() => {
      state.value = "idle";
      errorMessage.value = "";
    }, autoResetMs * 2);
  }

  /**
   * 包装一个异步保存操作，自动管理状态
   */
  async function wrapSave<T>(fn: () => Promise<T>): Promise<T | undefined> {
    startSaving();
    try {
      const result = await fn();
      markSaved();
      return result;
    } catch (err: any) {
      markError(
        err?.response?.data?.error?.message || err?.message || "保存失败",
      );
      throw err;
    }
  }

  return {
    state,
    isSaving,
    isSaved,
    isError,
    statusText,
    errorMessage,
    startSaving,
    markSaved,
    markError,
    wrapSave,
  };
}
