import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFundsStore } from '@/stores/funds'

describe('useFundsStore', () => {
  let store: ReturnType<typeof useFundsStore>
  beforeEach(() => { setActivePinia(createPinia()); store = useFundsStore() })
  it('initializes', () => { expect(store).toBeDefined() })
})
