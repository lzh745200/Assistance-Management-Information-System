import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import type { DirectiveBinding } from 'vue'

vi.mock('@/utils/authStorage', () => ({
  AuthStorage: { getUser: vi.fn() },
}))

import { AuthStorage } from '@/utils/authStorage'
import { vWatermark } from '@/directives/watermark'
import watermarkDefault from '@/directives/watermark'

const mockedGetUser = AuthStorage.getUser as ReturnType<typeof vi.fn>

function makeEl() {
  const el = document.createElement('div')
  return el
}

describe('directives/watermark', () => {
  beforeEach(() => {
    mockedGetUser.mockReset()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('默认导出即 vWatermark', () => {
    expect(watermarkDefault).toBe(vWatermark)
    expect(typeof vWatermark.mounted).toBe('function')
    expect(typeof vWatermark.updated).toBe('function')
  })

  it('mounted 带 binding.value 时使用指定文本', () => {
    const el = makeEl()
    vWatermark.mounted!(el, { value: '张三 2024-01-01' } as DirectiveBinding)
    const layer = el.querySelector('.watermark-layer') as HTMLElement
    expect(layer).not.toBeNull()
    expect(layer!.style.backgroundImage).toContain('data:image/png')
    expect(el.style.position).toBe('relative')
  })

  it('updated 更新水印文本', () => {
    const el = makeEl()
    vWatermark.mounted!(el, { value: 'old' } as DirectiveBinding)
    vWatermark.updated!(el, { value: 'new' } as DirectiveBinding)
    expect(el.querySelectorAll('.watermark-layer').length).toBe(1)
  })

  it('重复挂载时移除旧水印', () => {
    const el = makeEl()
    vWatermark.mounted!(el, { value: 'a' } as DirectiveBinding)
    vWatermark.mounted!(el, { value: 'b' } as DirectiveBinding)
    expect(el.querySelectorAll('.watermark-layer').length).toBe(1)
  })

  it('无 value 时使用用户名+日期', () => {
    mockedGetUser.mockReturnValue({ username: 'admin' })
    const el = makeEl()
    vWatermark.mounted!(el, { value: '' } as DirectiveBinding)
    expect(el.querySelector('.watermark-layer')).not.toBeNull()
  })

  it('用户有 name 时优先使用 name', () => {
    mockedGetUser.mockReturnValue({ name: '王五', username: 'wangwu' })
    const el = makeEl()
    vWatermark.mounted!(el, { value: null } as DirectiveBinding)
    expect(el.querySelector('.watermark-layer')).not.toBeNull()
  })

  it('用户无 name/username 时使用 用户 默认名', () => {
    mockedGetUser.mockReturnValue({ name: '', username: '' } as any)
    const el = makeEl()
    vWatermark.mounted!(el, { value: null } as DirectiveBinding)
    expect(el.querySelector('.watermark-layer')).not.toBeNull()
  })

  it('updated 无 value 时使用默认文本', () => {
    mockedGetUser.mockReturnValue({ username: 'admin' })
    const el = makeEl()
    vWatermark.mounted!(el, { value: 'x' } as DirectiveBinding)
    vWatermark.updated!(el, { value: '' } as DirectiveBinding)
    expect(el.querySelectorAll('.watermark-layer').length).toBe(1)
  })

  it('无用户时使用内部系统默认文本', () => {
    mockedGetUser.mockReturnValue(null)
    const el = makeEl()
    vWatermark.mounted!(el, { value: '' } as DirectiveBinding)
    expect(el.querySelector('.watermark-layer')).not.toBeNull()
  })

  it('getUser 抛错时回退默认文本', () => {
    mockedGetUser.mockImplementation(() => {
      throw new Error('storage broken')
    })
    const el = makeEl()
    vWatermark.mounted!(el, { value: '' } as DirectiveBinding)
    expect(el.querySelector('.watermark-layer')).not.toBeNull()
  })

  it('getContext 返回 null 时不创建水印', () => {
    const spy = vi
      .spyOn(HTMLCanvasElement.prototype, 'getContext')
      .mockReturnValue(null as any)
    const el = makeEl()
    vWatermark.mounted!(el, { value: 'x' } as DirectiveBinding)
    expect(el.querySelector('.watermark-layer')).toBeNull()
    spy.mockRestore()
  })

  it('容器已有 position 时不覆盖', () => {
    const el = makeEl()
    el.style.position = 'absolute'
    vWatermark.mounted!(el, { value: 'x' } as DirectiveBinding)
    expect(el.style.position).toBe('absolute')
  })
})
