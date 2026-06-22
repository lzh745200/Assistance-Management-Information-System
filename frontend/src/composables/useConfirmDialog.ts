/**
 * 确认对话框 Composable（响应式状态管理）
 */
import { ref, reactive } from 'vue'

export interface ConfirmDialogOptions {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  showCancel?: boolean
  type?: 'info' | 'warning' | 'error' | 'success'
}

export function useConfirmDialog() {
  const isVisible = ref(false)
  const options = reactive<ConfirmDialogOptions>({
    title: '确认',
    message: '',
    confirmText: '确定',
    cancelText: '取消',
    showCancel: true,
    type: 'info',
  })

  let resolveCallback: ((value: boolean) => void) | null = null

  function confirm(opts: ConfirmDialogOptions): Promise<boolean> {
    Object.assign(options, opts)
    isVisible.value = true
    return new Promise((resolve) => {
      resolveCallback = resolve
    })
  }

  function handleConfirm() {
    isVisible.value = false
    resolveCallback?.(true)
  }

  function handleCancel() {
    isVisible.value = false
    resolveCallback?.(false)
  }

  return { isVisible, options, confirm, handleConfirm, handleCancel }
}
