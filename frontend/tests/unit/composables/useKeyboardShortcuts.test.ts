import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useKeyboardShortcuts, formatShortcut } from '@/composables/useKeyboardShortcuts'
import type { Shortcut } from '@/composables/useKeyboardShortcuts'

describe('formatShortcut', () => {
  it('formats Ctrl+S', () => {
    expect(formatShortcut({ key: 's', ctrl: true, handler: () => {} })).toBe('Ctrl+S')
  })

  it('formats Shift+Alt+Escape', () => {
    expect(formatShortcut({ key: 'Escape', shift: true, alt: true, handler: () => {} })).toBe('Shift+Alt+Escape')
  })

  it('formats plain Enter', () => {
    expect(formatShortcut({ key: 'Enter', handler: () => {} })).toBe('Enter')
  })

  it('formats F5', () => {
    expect(formatShortcut({ key: 'F5', handler: () => {} })).toBe('F5')
  })

  it('uppercases single-char keys', () => {
    expect(formatShortcut({ key: 'a', ctrl: true, handler: () => {} })).toBe('Ctrl+A')
  })
})

describe('useKeyboardShortcuts', () => {
  let handler: ReturnType<typeof vi.fn>

  beforeEach(() => {
    handler = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  function createTestShortcut(overrides: Partial<Shortcut> = {}): Shortcut {
    return {
      key: 's',
      ctrl: true,
      handler,
      description: 'Save',
      group: 'File',
      ...overrides,
    }
  }

  it('returns registered shortcuts', () => {
    const shortcut = createTestShortcut()
    const { registered } = useKeyboardShortcuts([shortcut])
    expect(registered.value).toHaveLength(1)
    expect(registered.value[0].key).toBe('s')
    expect(registered.value[0].ctrl).toBe(true)
  })

  it('register adds a new shortcut', () => {
    const shortcut = createTestShortcut()
    const { registered, register } = useKeyboardShortcuts([])
    register(shortcut)
    expect(registered.value).toHaveLength(1)
  })

  it('unregister removes a shortcut', () => {
    const shortcut = createTestShortcut()
    const { registered, unregister } = useKeyboardShortcuts([shortcut])
    expect(registered.value).toHaveLength(1)
    unregister(shortcut)
    expect(registered.value).toHaveLength(0)
  })

  it('conflicts detects duplicate combos', () => {
    const h1 = vi.fn()
    const h2 = vi.fn()
    const s1 = createTestShortcut({ handler: h1 })
    const s2 = createTestShortcut({ handler: h2 })
    const { conflicts } = useKeyboardShortcuts([s1, s2])
    expect(conflicts.value).toHaveLength(1)
    expect(conflicts.value[0].combo).toBe('Ctrl+S')
  })

  it('groupedShortcuts groups by group', () => {
    const h1 = vi.fn()
    const h2 = vi.fn()
    const h3 = vi.fn()
    const s1 = createTestShortcut({ group: 'File', handler: h1 })
    const s2 = createTestShortcut({ key: 'o', ctrl: true, group: 'File', handler: h2 })
    const s3 = createTestShortcut({ key: 'h', group: 'Help', handler: h3 })
    const { groupedShortcuts } = useKeyboardShortcuts([s1, s2, s3])
    expect(groupedShortcuts.value.has('File')).toBe(true)
    expect(groupedShortcuts.value.has('Help')).toBe(true)
    expect(groupedShortcuts.value.get('File')!.length).toBe(2)
  })

  it('showHelp defaults to false', () => {
    const { showHelp } = useKeyboardShortcuts([])
    expect(showHelp.value).toBe(false)
  })
})
