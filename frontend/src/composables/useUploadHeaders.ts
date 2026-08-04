/**
 * el-upload 原生上传请求头（统一 CSRF 修复）
 *
 * el-upload 的 :action 模式使用原生 XHR/FormData 直发,
 * 不经过 axios 拦截器 → 必须手动携带 Authorization + X-CSRF-Token。
 */
import { computed, onMounted, ref } from 'vue'
import { getCsrfToken } from '@/api/request'
import { AuthStorage } from '@/utils/authStorage'

export function useUploadHeaders() {
  const csrfToken = ref('')

  const ensureCsrf = () => {
    getCsrfToken().then((t) => {
      if (t) csrfToken.value = t
    })
  }

  onMounted(ensureCsrf)

  const uploadHeaders = computed(() => {
    const token = AuthStorage.getToken() || ''
    const headers: Record<string, string> = {}
    if (token) headers.Authorization = `Bearer ${token}`
    if (csrfToken.value) headers['X-CSRF-Token'] = csrfToken.value
    return headers
  })

  return { uploadHeaders, ensureCsrf }
}
