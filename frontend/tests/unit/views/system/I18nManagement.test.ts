/**
 * views/system/I18nManagement.vue 覆盖率攻坚
 * 覆盖：语言/翻译加载、缺失键检查、详情、搜索过滤、语言切换
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises, enableAutoUnmount } from '@vue/test-utils'
import { nextTick } from 'vue'

enableAutoUnmount(afterEach)

const { ElMessage, i18nApi } = vi.hoisted(() => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
  i18nApi: {
    getLanguages: vi.fn(),
    getCurrentLanguage: vi.fn(),
    getTranslations: vi.fn(),
    getMissingKeys: vi.fn(),
    translate: vi.fn(),
  },
}))

vi.mock('@/api/i18n', () => ({
  i18nApi,
}))

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox: { confirm: vi.fn(() => Promise.resolve('confirm')), alert: vi.fn() },
  ElNotification: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
}))

import I18nManagement from '@/views/system/I18nManagement.vue'

const languagesData = {
  success: true,
  data: [
    { code: 'zh-CN', name: '简体中文', flag: '🇨🇳', default: true },
    { code: 'en', name: 'English', flag: '🇺🇸', default: false },
  ],
}

const translationsData = {
  success: true,
  data: {
    translations: {
      'menu.home': '首页',
      'menu.funds': '资金管理',
      'menu.empty': '',
    },
  },
}

async function mountComp() {
  const w = mount(I18nManagement, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-card': {
          name: 'ElCard',
          template: '<div class="el-card-stub"><slot /><slot name="header" /></div>',
        },
        'el-tag': {
          name: 'ElTag',
          template: '<span class="el-tag-stub"><slot /></span>',
          emits: ['close'],
        },
        'el-select': {
          name: 'ElSelect',
          props: ['modelValue'],
          emits: ['update:modelValue', 'change'],
          template:
            '<select class="el-select-stub" @change="$emit(\'update:modelValue\', $event.target.value); $emit(\'change\', $event.target.value)"><slot /></select>',
        },
        'el-option': { name: 'ElOption', template: '<option :value="value"><slot /></option>' },
        'el-button': {
          name: 'ElButton',
          template: '<button class="el-button-stub"><slot /></button>',
        },
        'el-descriptions': { name: 'ElDescriptions', template: '<dl><slot /></dl>' },
        'el-descriptions-item': {
          name: 'ElDescriptionsItem',
          template: '<div class="el-desc-item-stub"><slot /></div>',
        },
        'el-input': {
          name: 'ElInput',
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template:
            '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        'el-table': { name: 'ElTable', template: '<table class="el-table-stub"><slot /></table>' },
        'el-table-column': {
          name: 'ElTableColumn',
          template: '<div class="el-table-column-stub"><slot :row="rowA" /><slot :row="rowB" /></div>',
          data() {
            return {
              rowA: { key: 'menu.home', value: '首页' },
              rowB: { key: 'menu.empty', value: '' },
            }
          },
        },
        'el-dialog': {
          name: 'ElDialog',
          template: '<div class="el-dialog-stub"><slot /><slot name="footer" /></div>',
          emits: ['update:modelValue'],
        },
        'el-form': { name: 'ElForm', template: '<form><slot /></form>' },
        'el-form-item': { name: 'ElFormItem', template: '<div><slot /></div>' },
        'el-alert': {
          name: 'ElAlert',
          template: '<div class="el-alert-stub"><slot /><slot name="title" /></div>',
        },
      },
    },
  })
  await flushPromises()
  await nextTick()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  i18nApi.getLanguages.mockResolvedValue(languagesData)
  i18nApi.getCurrentLanguage.mockResolvedValue({ success: true, data: { language: 'zh-CN', name: '简体中文' } })
  i18nApi.getTranslations.mockResolvedValue(translationsData)
  i18nApi.getMissingKeys.mockResolvedValue({
    success: true,
    data: {
      source_language: 'zh-CN',
      target_language: 'en',
      source_count: 10,
      target_count: 8,
      missing_keys: ['menu.missing'],
      missing_count: 1,
      extra_keys: ['old.key'],
      completion_rate: 0.8,
    },
  })
  i18nApi.translate.mockResolvedValue({ success: true, data: { value: '首页', fallback: false } })
})

describe('I18nManagement.vue', () => {
  it('渲染并加载语言列表/当前语言', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    expect(i18nApi.getLanguages).toHaveBeenCalled()
    expect(i18nApi.getCurrentLanguage).toHaveBeenCalled()
    expect(vm.languages.length).toBe(2)
    expect(vm.currentLang?.name).toBe('简体中文')
    expect(w.text()).toContain('简体中文')
  })

  it('加载语言失败 → 错误提示', async () => {
    i18nApi.getLanguages.mockRejectedValue(new Error('langs failed'))
    const w = await mountComp()
    expect(ElMessage.error).toHaveBeenCalledWith('加载语言列表失败')
  })

  it('加载语言：无 data → 空数组', async () => {
    i18nApi.getLanguages.mockResolvedValue({ success: true })
    const w = await mountComp()
    expect((w.vm as any).languages).toEqual([])
  })

  it('语言列表：无 flag 的语言', async () => {
    i18nApi.getLanguages.mockResolvedValue({
      success: true,
      data: [{ code: 'fr', name: 'Français' }],
    })
    const w = await mountComp()
    expect((w.vm as any).languages[0].flag).toBeUndefined()
  })

  it('checkMissingKeys：无 data → 报告为 null', async () => {
    i18nApi.getMissingKeys.mockResolvedValue({ success: true })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.checkMissingKeys()
    expect(vm.missingReport).toBeNull()
    expect(ElMessage.success).toHaveBeenCalledWith('翻译覆盖完整！')
  })

  it('加载当前语言失败 → 静默忽略', async () => {
    i18nApi.getCurrentLanguage.mockRejectedValue(new Error('boom'))
    const w = await mountComp()
    expect((w.vm as any).currentLang).toBeNull()
  })

  it('加载当前语言：无 data → null', async () => {
    i18nApi.getCurrentLanguage.mockResolvedValue({ success: true })
    const w = await mountComp()
    expect((w.vm as any).currentLang).toBeNull()
  })

  it('loadTranslations：未选语言 → 返回', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.selectedLanguage = ''
    await vm.loadTranslations()
    expect(i18nApi.getTranslations).not.toHaveBeenCalled()
  })

  it('loadTranslations：成功加载', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    await vm.loadTranslations()
    expect(i18nApi.getTranslations).toHaveBeenCalledWith('en')
    expect(vm.translations['menu.home']).toBe('首页')
    expect(ElMessage.success).toHaveBeenCalledWith('已加载 3 条翻译')
  })

  it('loadTranslations：无数据 → 空对象', async () => {
    i18nApi.getTranslations.mockResolvedValue({ success: true, data: null })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.loadTranslations()
    expect(vm.translations).toEqual({})
  })

  it('loadTranslations：无 translations 字段 → 空对象', async () => {
    i18nApi.getTranslations.mockResolvedValue({ success: true, data: { language: 'en' } })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.loadTranslations()
    expect(vm.translations).toEqual({})
  })

  it('loadTranslations：失败 → 错误提示', async () => {
    i18nApi.getTranslations.mockRejectedValue(new Error('load failed'))
    const w = await mountComp()
    const vm = w.vm as any
    await vm.loadTranslations()
    expect(ElMessage.error).toHaveBeenCalledWith('加载翻译资源失败')
    expect(vm.loading).toBe(false)
  })

  it('checkMissingKeys：有缺失 → 警告', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    await vm.checkMissingKeys()
    expect(i18nApi.getMissingKeys).toHaveBeenCalledWith('zh-CN', 'en')
    expect(vm.missingReport?.missing_count).toBe(1)
    expect(ElMessage.warning).toHaveBeenCalledWith('发现 1 个缺失翻译键')
  })

  it('checkMissingKeys：无缺失 → 成功提示', async () => {
    i18nApi.getMissingKeys.mockResolvedValue({
      success: true,
      data: {
        source_language: 'zh-CN',
        target_language: 'en',
        source_count: 10,
        target_count: 10,
        missing_keys: [],
        missing_count: 0,
        extra_keys: [],
        completion_rate: 1,
      },
    })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.checkMissingKeys()
    expect(ElMessage.success).toHaveBeenCalledWith('翻译覆盖完整！')
  })

  it('checkMissingKeys：失败 → 错误提示', async () => {
    i18nApi.getMissingKeys.mockRejectedValue(new Error('check failed'))
    const w = await mountComp()
    const vm = w.vm as any
    await vm.checkMissingKeys()
    expect(ElMessage.error).toHaveBeenCalledWith('检查缺失键失败')
    expect(vm.checkingMissing).toBe(false)
  })

  it('viewTranslationDetail：成功', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    await vm.viewTranslationDetail('menu.home')
    expect(i18nApi.translate).toHaveBeenCalledWith('menu.home', 'en')
    expect(vm.detailKey).toBe('menu.home')
    expect(vm.detailValue).toBe('首页')
    expect(vm.detailDialogVisible).toBe(true)
  })

  it('viewTranslationDetail：无 value/fallback 字段 → 空值', async () => {
    i18nApi.translate.mockResolvedValue({ success: true, data: {} })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.viewTranslationDetail('menu.home')
    expect(vm.detailValue).toBe('')
    expect(vm.detailFallback).toBe(false)
  })

  it('viewTranslationDetail：回退值', async () => {
    i18nApi.translate.mockResolvedValue({ success: true, data: { value: 'Home', fallback: true } })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.viewTranslationDetail('menu.home')
    expect(vm.detailFallback).toBe(true)
  })

  it('viewTranslationDetail：失败 → 本地兜底', async () => {
    i18nApi.translate.mockRejectedValue(new Error('translate failed'))
    const w = await mountComp()
    const vm = w.vm as any
    vm.translations['menu.home'] = '本地值'
    await vm.viewTranslationDetail('menu.home')
    expect(vm.detailValue).toBe('本地值')
    expect(vm.detailFallback).toBe(false)
  })

  it('viewTranslationDetail：失败且无本地值 → 占位', async () => {
    i18nApi.translate.mockRejectedValue(new Error('translate failed'))
    const w = await mountComp()
    const vm = w.vm as any
    await vm.viewTranslationDetail('unknown.key')
    expect(vm.detailValue).toBe('(未找到)')
  })

  it('addTranslationDialog → info 提示', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.addTranslationDialog('menu.missing')
    expect(ElMessage.info).toHaveBeenCalled()
  })

  it('onLanguageChange：重置搜索并加载翻译', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.searchKeyword = 'home'
    vm.missingReport = { missing_count: 1 }
    vm.onLanguageChange()
    expect(vm.searchKeyword).toBe('')
    expect(vm.missingReport).toBeNull()
    expect(i18nApi.getTranslations).toHaveBeenCalledWith('en')
  })

  it('filteredTranslations：搜索过滤', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    await vm.loadTranslations()
    vm.searchKeyword = 'funds'
    await nextTick()
    expect(vm.filteredTranslations.length).toBe(1)
    expect(vm.filteredTranslations[0].key).toBe('menu.funds')
    vm.searchKeyword = ''
    expect(vm.filteredTranslations.length).toBe(3)
    vm.searchKeyword = '资金'
    expect(vm.filteredTranslations.length).toBe(1)
  })

  it('搜索输入框 v-model', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    const input = w.find('input')
    await input.setValue('home')
    expect(vm.searchKeyword).toBe('home')
  })

  it('语言选择器 change → onLanguageChange', async () => {
    const w = await mountComp()
    const select = w.find('.el-select-stub')
    await select.setValue('zh-CN')
    await nextTick()
    expect((w.vm as any).selectedLanguage).toBe('zh-CN')
    expect(i18nApi.getTranslations).toHaveBeenCalledWith('zh-CN')
  })

  it('缺失键标签点击（@close）→ addTranslationDialog', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    await vm.checkMissingKeys()
    await nextTick()
    expect(vm.missingReport?.missing_keys.length).toBe(1)
  })

  it('缺失报告：无 extra_keys → 0 兜底', async () => {
    i18nApi.getMissingKeys.mockResolvedValue({
      success: true,
      data: {
        source_language: 'zh-CN',
        target_language: 'en',
        source_count: 10,
        target_count: 8,
        missing_keys: ['menu.missing'],
        missing_count: 1,
        completion_rate: 0.8,
      },
    })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.checkMissingKeys()
    expect(vm.missingReport?.extra_keys).toBeUndefined()
  })

  it('表格行详情按钮 + 缺失标签关闭 + 详情对话框关闭', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    await vm.checkMissingKeys()
    await vm.viewTranslationDetail('menu.home')
    await nextTick()
    // 详情对话框 update:modelValue
    const dialog = w.findComponent({ name: 'ElDialog' })
    dialog.vm.$emit('update:modelValue', false)
    await nextTick()
    expect(vm.detailDialogVisible).toBe(false)
    // 详情按钮点击
    const detailBtn = w
      .findAll('button')
      .find((b) => b.text().includes('详情'))
    await detailBtn!.trigger('click')
    expect(i18nApi.translate).toHaveBeenCalled()
    // 缺失标签关闭（对全部 el-tag 触发，含 closable 缺失键标签）
    const tags = w.findAllComponents({ name: 'ElTag' })
    for (const t of tags) {
      t.vm.$emit('close')
    }
    await nextTick()
    expect(ElMessage.info).toHaveBeenCalled()
  })
})
