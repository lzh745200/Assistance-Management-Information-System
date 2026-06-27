import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  desensitizeByRole,
  maskPhone,
  maskIdCard,
  maskName,
  maskBankCard,
  maskEmail,
  maskAddress,
  maskAmount,
  autoDesensitize,
  type UserRole,
} from '@/utils/desensitize'

export function useDesensitize() {
  const authStore = useAuthStore()

  const role = computed<UserRole | string>(() => authStore.user?.role ?? 'viewer')

  function ds(
    value: string | number | null | undefined,
    type: 'phone' | 'idCard' | 'name' | 'bankCard' | 'email' | 'address' | 'amount' | 'militaryID'
  ): string {
    return desensitizeByRole(value, type, role.value)
  }

  return {
    role,
    ds,
    maskPhone,
    maskIdCard,
    maskName,
    maskBankCard,
    maskEmail,
    maskAddress,
    maskAmount,
    autoDesensitize,
  }
}
