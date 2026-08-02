/**
 * ProgressAlbum.vue 测试
 * 覆盖：空态、多状态标签（getStatusType 全分支）、进度/图片渲染、props 透传
 */
import { describe, it, expect, afterEach } from 'vitest'
import { mount, enableAutoUnmount } from '@vue/test-utils'
import ProgressAlbum from '@/components/business/ProgressAlbum.vue'

enableAutoUnmount(afterEach)

const ElCardStub = {
  props: ['shadow'],
  template:
    '<div class="stub-card"><div class="stub-card-header"><slot name="header" /></div><slot /></div>',
}

const ElTagStub = {
  props: ['type', 'size'],
  template: '<span class="stub-tag" :type="type"><slot /></span>',
}

const ElProgressStub = {
  props: ['percentage', 'status', 'strokeWidth'],
  template:
    '<div class="stub-progress" :percentage="percentage" :status="status" :stroke-width="strokeWidth" />',
}

const ElImageStub = {
  props: ['src'],
  template: '<img class="stub-img" :src="src" />',
}

const ElEmptyStub = {
  props: ['description'],
  template: '<div class="stub-empty" :description="description" />',
}

function mountAlbum(props: Record<string, unknown> = {}) {
  return mount(ProgressAlbum, {
    props,
    global: {
      stubs: {
        'el-card': ElCardStub,
        'el-tag': ElTagStub,
        'el-progress': ElProgressStub,
        'el-image': ElImageStub,
        'el-empty': ElEmptyStub,
        'el-row': { template: '<div class="stub-row"><slot /></div>' },
        'el-col': { template: '<div class="stub-col"><slot /></div>' },
      },
    },
  })
}

describe('ProgressAlbum.vue', () => {
  it('空数据时渲染空态', () => {
    const wrapper = mountAlbum({ items: [], emptyText: '没有数据' })
    expect(wrapper.find('.stub-empty').exists()).toBe(true)
    expect(wrapper.find('.stub-empty').attributes('description')).toBe('没有数据')

    const wrapper2 = mountAlbum({})
    expect(wrapper2.find('.stub-empty').exists()).toBe(true)
  })

  it('渲染各类状态标签（覆盖 getStatusType 全分支）', () => {
    const items = [
      { name: 'A', status: 'completed' },
      { name: 'B', status: 'in_progress' },
      { name: 'C', status: '进行中' },
      { name: 'D', status: '已完成' },
      { name: 'E', status: 'delayed' },
      { name: 'F', status: '延期' },
      { name: 'G', status: 'cancelled' },
      { name: 'H', status: '已取消' },
      { name: 'I', status: '未知状态' },
    ]
    const wrapper = mountAlbum({ items })
    const tags = wrapper.findAll('span.stub-tag')
    expect(tags).toHaveLength(9)
    expect(tags[0].attributes('type')).toBe('success')
    expect(tags[1].attributes('type')).toBe('warning')
    expect(tags[2].attributes('type')).toBe('warning')
    expect(tags[3].attributes('type')).toBe('success')
    expect(tags[4].attributes('type')).toBe('danger')
    expect(tags[5].attributes('type')).toBe('danger')
    expect(tags[6].attributes('type')).toBe('info')
    expect(tags[7].attributes('type')).toBe('info')
    expect(tags[8].attributes('type')).toBeUndefined()
  })

  it('标题回退（title || name）与进度分支', () => {
    const items = [
      { title: '带标题', status: 'completed', progress: 50 },
      { name: '带名称', status: 'x', progress: 150 },
      { title: '完成项', status: 'completed', progress: 100 },
      { status: 'y' },
    ]
    const wrapper = mountAlbum({ items })
    expect(wrapper.text()).toContain('带标题')
    expect(wrapper.text()).toContain('带名称')
    // 最后一项无 progress → 不渲染进度条
    expect(wrapper.findAll('.stub-progress')).toHaveLength(3)
    const progressProps = wrapper.findAll('.stub-progress').map((p) => p.attributes())
    expect(progressProps[0].percentage).toBe('50')
    expect(progressProps[1].percentage).toBe('100')
    expect(progressProps[2].status).toBe('success')
    expect(progressProps[2].percentage).toBe('100')
  })

  it('描述与图片渲染（最多 3 张）', () => {
    const items = [
      {
        name: 'A',
        status: 'x',
        description: '描述文本',
        images: ['1.png', '2.png', '3.png', '4.png'],
      },
      {
        name: 'B',
        status: 'y',
        progress: 10,
        images: [],
      },
    ]
    const wrapper = mountAlbum({ items })
    expect(wrapper.text()).toContain('描述文本')
    expect(wrapper.findAll('img.stub-img')).toHaveLength(3)
  })

  it('colSpan / strokeWidth props 透传', () => {
    const wrapper = mountAlbum({
      items: [{ name: 'A', status: 'x', progress: 30 }],
      colSpan: 6,
      strokeWidth: 24,
    })
    const col = wrapper.find('.stub-col')
    expect(col.attributes('sm')).toBe('6')
    expect(wrapper.find('.stub-progress').attributes('stroke-width')).toBe('24')
  })
})
