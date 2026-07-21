import { onBeforeRouteLeave } from 'vue-router'
import { onBeforeUnmount } from 'vue'
import { ElMessageBox } from 'element-plus'
import type { Ref } from 'vue'

export function useDirtyGuard(isDirty: Ref<boolean>) {
  const confirmLeave = () => {
    if (!isDirty.value) return true
    return ElMessageBox.confirm('有未保存的更改，确定离开吗？', '提示', {
      confirmButtonText: '离开',
      cancelButtonText: '留下',
      type: 'warning',
    })
      .then(() => true)
      .catch(() => false)
  }

  onBeforeRouteLeave(async () => {
    return await confirmLeave()
  })

  // Also handle browser close/refresh
  const handler = (e: BeforeUnloadEvent) => {
    if (isDirty.value) {
      e.preventDefault()
      e.returnValue = ''
    }
  }
  window.addEventListener('beforeunload', handler)
  onBeforeUnmount(() => window.removeEventListener('beforeunload', handler))
}
