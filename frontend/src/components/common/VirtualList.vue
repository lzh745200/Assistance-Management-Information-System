<template>
  <div
    ref="containerRef"
    class="virtual-list"
    :style="{ height: containerHeight + 'px', overflow: 'auto' }"
    @scroll="onScroll"
  >
    <div :style="{ height: totalHeight + 'px', position: 'relative' }">
      <div
        :style="{
          position: 'absolute',
          top: offsetY + 'px',
          left: 0,
          right: 0,
        }"
      >
        <div
          v-for="item in visibleItems"
          :key="item._index"
          :style="{ height: itemHeight + 'px' }"
          class="virtual-list-item"
        >
          <slot :item="item.data" :index="item._index" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" generic="T">
import { ref, computed, onMounted } from "vue";

const props = withDefaults(
  defineProps<{
    items: T[];
    itemHeight: number;
    containerHeight?: number;
    buffer?: number;
  }>(),
  {
    containerHeight: 400,
    buffer: 5,
  },
);

const containerRef = ref<HTMLElement | null>(null);
const scrollTop = ref(0);

const totalHeight = computed(() => props.items.length * props.itemHeight);

const startIndex = computed(() => {
  const idx = Math.floor(scrollTop.value / props.itemHeight) - props.buffer;
  return Math.max(0, idx);
});

const endIndex = computed(() => {
  const visibleCount = Math.ceil(props.containerHeight / props.itemHeight);
  const idx = startIndex.value + visibleCount + 2 * props.buffer;
  return Math.min(props.items.length, idx);
});

const offsetY = computed(() => startIndex.value * props.itemHeight);

const visibleItems = computed(() => {
  return props.items.slice(startIndex.value, endIndex.value).map((data, i) => ({
    data,
    _index: startIndex.value + i,
  }));
});

function onScroll(e: Event) {
  const target = e.target as HTMLElement;
  scrollTop.value = target.scrollTop;
}

onMounted(() => {
  if (containerRef.value) {
    scrollTop.value = containerRef.value.scrollTop;
  }
});
</script>

<style scoped>
.virtual-list {
  will-change: transform;
}
.virtual-list-item {
  box-sizing: border-box;
}
</style>
