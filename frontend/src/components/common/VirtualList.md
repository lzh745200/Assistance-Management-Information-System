# VirtualList 虚拟列表组件

## 功能说明

VirtualList 是一个高性能的虚拟滚动列表组件，用于渲染大量数据时优化性能。

## 特性

- ✅ 虚拟滚动：只渲染可见区域的元素
- ✅ 高性能：支持数万条数据流畅滚动
- ✅ 缓冲区：预渲染上下缓冲区的元素，提升滚动体验
- ✅ 响应式：自动适应容器大小变化
- ✅ TypeScript：完整的类型支持
- ✅ 灵活插槽：自定义列表项渲染

## 使用示例

### 基础用法

```vue
<template>
  <VirtualList
    :data="items"
    :item-height="48"
    :buffer-size="5"
  >
    <template #default="{ item, index }">
      <div class="list-item">
        <span>{{ index + 1 }}. {{ item.name }}</span>
      </div>
    </template>
  </VirtualList>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import VirtualList from '@/components/common/VirtualList.vue';

interface Item {
  id: number;
  name: string;
}

const items = ref<Item[]>([]);

// 生成大量测试数据
for (let i = 0; i < 10000; i++) {
  items.value.push({
    id: i,
    name: `Item ${i}`
  });
}
</script>
```

### 自定义key字段

```vue
<VirtualList
  :data="users"
  :item-height="60"
  key-field="userId"
>
  <template #default="{ item }">
    <div class="user-item">
      <h4>{{ item.username }}</h4>
      <p>{{ item.email }}</p>
    </div>
  </template>
</VirtualList>
```

### 使用暴露的方法

```vue
<template>
  <div>
    <div class="toolbar">
      <el-button @click="scrollToTop">滚动到顶部</el-button>
      <el-button @click="scrollToBottom">滚动到底部</el-button>
      <el-button @click="scrollToIndex(500)">滚动到第500项</el-button>
    </div>

    <VirtualList
      ref="listRef"
      :data="items"
      :item-height="48"
    >
      <template #default="{ item }">
        <div>{{ item.name }}</div>
      </template>
    </VirtualList>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import VirtualList from '@/components/common/VirtualList.vue';

const listRef = ref<InstanceType<typeof VirtualList>>();

const scrollToTop = () => {
  listRef.value?.scrollToTop();
};

const scrollToBottom = () => {
  listRef.value?.scrollToBottom();
};

const scrollToIndex = (index: number) => {
  listRef.value?.scrollToIndex(index);
};
</script>
```

## Props

| 参数 | 说明 | 类型 | 默认值 | 必填 |
|------|------|------|--------|------|
| data | 列表数据 | T[] | - | 是 |
| itemHeight | 每项的高度（px） | number | - | 是 |
| bufferSize | 缓冲区大小（上下各缓冲几项） | number | 5 | 否 |
| keyField | 用作key的字段名 | string | 'id' | 否 |

## Slots

| 名称 | 说明 | 参数 |
|------|------|------|
| default | 列表项内容 | { item: T, index: number } |

## Methods

| 方法名 | 说明 | 参数 |
|--------|------|------|
| scrollToIndex | 滚动到指定索引 | (index: number, behavior?: ScrollBehavior) |
| scrollToTop | 滚动到顶部 | - |
| scrollToBottom | 滚动到底部 | - |

## 性能优化建议

1. **固定高度**：确保每项高度一致，使用固定的 itemHeight
2. **合理的缓冲区**：bufferSize 默认为5，可根据实际情况调整
3. **避免复杂计算**：在列表项中避免复杂的计算和深层嵌套
4. **使用key**：确保每项有唯一的key，提升渲染性能

## 适用场景

- ✅ 大数据列表（1000+条）
- ✅ 无限滚动列表
- ✅ 日志查看器
- ✅ 聊天消息列表
- ✅ 文件列表
- ✅ 搜索结果列表

## 不适用场景

- ❌ 列表项高度不一致
- ❌ 需要展开/折叠的树形列表
- ❌ 数据量很小（<100条）
- ❌ 需要复杂的拖拽排序

## 注意事项

1. 列表项必须有固定高度
2. 容器必须有明确的高度（不能是auto）
3. 数据变化时会自动重置滚动位置
4. 使用泛型支持任意数据类型
