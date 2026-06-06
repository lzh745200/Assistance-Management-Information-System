/**
 * 确认对话框 Composable（ElMessageBox 封装）
 */
import { ElMessageBox } from "element-plus";

export interface ConfirmOptions {
  title?: string;
  message: string;
  confirmButtonText?: string;
  cancelButtonText?: string;
  type?: "success" | "warning" | "info" | "error";
}

export function useConfirm() {
  async function confirm(options: ConfirmOptions): Promise<boolean> {
    try {
      await ElMessageBox.confirm(options.message, options.title || "确认", {
        confirmButtonText: options.confirmButtonText || "确定",
        cancelButtonText: options.cancelButtonText || "取消",
        type: options.type || "warning",
      });
      return true;
    } catch {
      return false;
    }
  }

  return { confirm };
}
