<template>
  <div class="guizhou-region-selector">
    <el-form-item label="所在市州">
      <el-select
        :model-value="modelValue?.city"
        placeholder="选择市州"
        clearable
        @update:model-value="onCityChange"
      >
        <el-option v-for="city in GUIZHOU_ALL_CITIES" :key="city" :label="city" :value="city" />
      </el-select>
    </el-form-item>
    <el-form-item label="所在县市">
      <el-select
        :model-value="modelValue?.county"
        placeholder="先选市州"
        clearable
        :disabled="!availableCounties.length"
        @update:model-value="onCountyChange"
      >
        <el-option v-for="c in availableCounties" :key="c" :label="c" :value="c" />
      </el-select>
    </el-form-item>
    <el-form-item v-if="showTownship" label="乡镇">
      <el-select
        :model-value="modelValue?.township"
        placeholder="请选择乡镇"
        :disabled="!availableTownships.length"
        filterable
        clearable
        @update:model-value="onTownshipChange"
      >
        <el-option
          v-for="t in availableTownships"
          :key="t"
          :label="t"
          :value="t"
        />
      </el-select>
    </el-form-item>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { GUIZHOU_ALL_CITIES, getCountiesByCity, getTownshipsByCityCounty } from '@/data/guizhouRegion'

export interface RegionValue {
  city?: string
  county?: string
  township?: string
}

const props = withDefaults(
  defineProps<{
    modelValue?: RegionValue
    showTownship?: boolean
  }>(),
  { showTownship: true }
)

const emit = defineEmits<{
  'update:modelValue': [value: RegionValue]
}>()

const availableCounties = computed(() => {
  if (!props.modelValue?.city) return []
  return getCountiesByCity(props.modelValue.city)
})

const availableTownships = computed(() => {
  if (!props.modelValue?.city || !props.modelValue?.county) return []
  return getTownshipsByCityCounty(props.modelValue.city, props.modelValue.county)
})

function onCityChange(city: string) {
  emit('update:modelValue', {
    ...props.modelValue,
    city: city || undefined,
    county: undefined, // 切换市州时清除县选择
    township: props.modelValue?.township,
  })
}

function onCountyChange(county: string) {
  emit('update:modelValue', {
    ...props.modelValue,
    county: county || undefined,
  })
}

function onTownshipChange(township: string) {
  emit('update:modelValue', {
    ...props.modelValue,
    township: township || undefined,
  })
}
</script>
