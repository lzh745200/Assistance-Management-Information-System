<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="rules"
    :disabled="mode === 'view'"
    label-width="120px"
  >
    <!-- 基本信息 -->
    <el-divider content-position="left">基本信息</el-divider>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="序号" prop="sequenceNo">
          <el-input-number
            v-model="formData.sequenceNo"
            :min="1"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="部门单位" prop="department">
          <el-input
            v-model="formData.department"
            placeholder="请输入部门单位"
          />
        </el-form-item>
      </el-col>
    </el-row>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="帮扶单位" prop="supportUnit">
          <el-input
            v-model="formData.supportUnit"
            placeholder="请输入帮扶单位"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="帮扶村名称" prop="villageName">
          <el-input
            v-model="formData.villageName"
            placeholder="请输入帮扶村名称"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <!-- 地域属性 - 贵州省地区选择 -->
    <el-divider content-position="left">地域属性</el-divider>
    <el-row :gutter="20">
      <el-col :span="24">
        <el-form-item label="所在地区">
          <GuizhouRegionSelector
            v-model="regionValue"
            :disabled="mode === 'view'"
            :show-township="true"
          />
        </el-form-item>
      </el-col>
    </el-row>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="地区范围" prop="regionScope">
          <el-input
            v-model="formData.regionScope"
            placeholder="请输入地区范围"
          />
        </el-form-item>
      </el-col>
    </el-row>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-form-item label="三区三州">
          <el-switch v-model="formData.isThreeRegions" />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="边疆地区">
          <el-switch v-model="formData.isBorderArea" />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="民族地区">
          <el-switch v-model="formData.isEthnicArea" />
        </el-form-item>
      </el-col>
    </el-row>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-form-item label="革命地区">
          <el-switch v-model="formData.isRevolutionaryArea" />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="重点帮扶县">
          <el-switch v-model="formData.isKeyCounty" />
        </el-form-item>
      </el-col>
    </el-row>

    <!-- 振兴发展属性 -->
    <el-divider content-position="left">振兴发展属性</el-divider>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="振兴梯队" prop="revitalizationTier">
          <el-select
            v-model="formData.revitalizationTier"
            placeholder="选择振兴梯队"
            clearable
            style="width: 100%"
          >
            <el-option label="第一梯队" value="第一梯队" />
            <el-option label="第二梯队" value="第二梯队" />
            <el-option label="第三梯队" value="第三梯队" />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="梯次振兴等级" prop="tieredDevelopmentLevel">
          <el-select
            v-model="formData.tieredDevelopmentLevel"
            placeholder="选择梯次振兴发展等级"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="level in TIERED_DEVELOPMENT_LEVELS.filter(
                (l) => l !== null,
              ) as string[]"
              :key="level"
              :label="level"
              :value="level"
            />
          </el-select>
        </el-form-item>
      </el-col>
    </el-row>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-form-item label="省级示范">
          <el-switch v-model="formData.isProvincialDemo" />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="百村示范">
          <el-switch v-model="formData.isHundredVillageDemo" />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="梯次振兴">
          <el-switch v-model="formData.isTieredDevelopment" />
        </el-form-item>
      </el-col>
    </el-row>

    <!-- 跨域帮扶 -->
    <el-divider content-position="left">跨域帮扶</el-divider>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-form-item label="跨省帮扶">
          <el-switch v-model="formData.isCrossProvince" />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="跨市帮扶">
          <el-switch v-model="formData.isCrossCity" />
        </el-form-item>
      </el-col>
    </el-row>

    <!-- 协作与表彰 -->
    <el-divider content-position="left">协作与表彰</el-divider>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-form-item label="跨单位协作">
          <el-switch v-model="formData.isCrossUnitCooperation" />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="纳入总盘子">
          <el-switch v-model="formData.isInOverallPlan" />
        </el-form-item>
      </el-col>
    </el-row>
    <el-row>
      <el-col :span="24">
        <el-form-item label="获得表彰" prop="honors">
          <el-input
            v-model="formData.honors"
            type="textarea"
            :rows="3"
            placeholder="请输入获得的国家或省级表彰"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <!-- 过渡期帮扶经费（2021-2026年度） -->
    <el-divider content-position="left">过渡期帮扶经费（按年度）</el-divider>
    <el-table
      :data="transitionFundingRows"
      border
      size="small"
      style="margin-bottom: 16px"
    >
      <el-table-column label="年份" width="80" align="center">
        <template #default="{ row }">{{ row.year }}</template>
      </el-table-column>
      <el-table-column label="部队投入(万元)" min-width="160">
        <template #default="{ row }">
          <el-input-number
            v-model="row.militaryInvestment"
            :min="0"
            :precision="2"
            size="small"
            style="width: 100%"
          />
        </template>
      </el-table-column>
      <el-table-column label="地方投入(万元)" min-width="160">
        <template #default="{ row }">
          <el-input-number
            v-model="row.localInvestment"
            :min="0"
            :precision="2"
            size="small"
            style="width: 100%"
          />
        </template>
      </el-table-column>
    </el-table>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="部队合计(万元)">
          <el-input
            :model-value="transitionMilitaryTotal.toFixed(2)"
            disabled
          />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="地方合计(万元)">
          <el-input :model-value="transitionLocalTotal.toFixed(2)" disabled />
        </el-form-item>
      </el-col>
    </el-row>

    <!-- 地理位置 -->
    <el-divider content-position="left">地理位置</el-divider>
    <el-row>
      <el-col :span="24">
        <el-form-item label="坐标设置">
          <MapPicker
            v-model:latitude="formData.latitude"
            v-model:longitude="formData.longitude"
            :disabled="mode === 'view'"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <!-- 操作按钮 -->
    <el-form-item v-if="mode !== 'view'" class="form-actions">
      <el-button type="primary" @click="handleSubmit">保存</el-button>
      <el-button @click="handleCancel">取消</el-button>
    </el-form-item>
    <el-form-item v-else class="form-actions">
      <el-button @click="handleCancel">关闭</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { logger } from "@/utils/logger";

/**
 * 帮扶村表单组件
 *
 * Feature: supported-village-enhancement
 * Requirements: 1.3, 23.1, 16.1, 16.2, 16.3
 */
import { ref, reactive, watch, computed, onMounted } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import type {
  SupportedVillage,
  SupportedVillageCreate,
  TieredDevelopmentLevel,
} from "@/types/analytics";
import GuizhouRegionSelector from "@/components/common/GuizhouRegionSelector.vue";
import type { RegionValue } from "@/components/common/GuizhouRegionSelector.vue";
import MapPicker from "@/components/MapPicker.vue";
import { DEFAULT_CITY, DEFAULT_PROVINCE } from "@/components/common/qiannanRegion";
import {
  getTransitionFunding,
  saveTransitionFunding,
} from "@/api/supportedVillage";

/**
 * 梯次振兴发展等级选项
 * Requirements: 23.1
 */
const TIERED_DEVELOPMENT_LEVELS: TieredDevelopmentLevel[] = [
  "示范级",
  "达标级",
  "基础级",
];

const props = defineProps<{
  village?: SupportedVillage | null;
  mode: "create" | "edit" | "view";
}>();

const emit = defineEmits<{
  submit: [data: SupportedVillageCreate];
  cancel: [];
}>();

const formRef = ref<FormInstance>();

const formData = reactive<SupportedVillageCreate>({
  sequenceNo: undefined,
  department: "",
  supportUnit: "",
  villageName: "",
  // 地域属性 - 贵州省地区选择
  province: DEFAULT_PROVINCE,
  city: "",
  county: "",
  regionScope: "",
  isThreeRegions: 0,
  isBorderArea: 0,
  isEthnicArea: 0,
  isRevolutionaryArea: 0,
  isKeyCounty: 0,
  revitalizationTier: "",
  isProvincialDemo: 0,
  isHundredVillageDemo: 0,
  isTieredDevelopment: false,
  tieredDevelopmentLevel: null, // 梯次振兴发展等级 (Requirements: 23.1)
  isCrossProvince: false,
  isCrossCity: false,
  isCrossUnitCooperation: false,
  isInOverallPlan: false,
  honors: "",
  transitionFundMilitaryTotal: 0,
  transitionFundLocalTotal: 0,
  latitude: null,
  longitude: null,
});

const rules: FormRules = {
  department: [{ required: true, message: "请输入部门单位", trigger: "blur" }],
  supportUnit: [{ required: true, message: "请输入帮扶单位", trigger: "blur" }],
  villageName: [
    { required: true, message: "请输入帮扶村名称", trigger: "blur" },
  ],
};

// 过渡期帮扶经费按年度数据
const TRANSITION_YEARS = [2021, 2022, 2023, 2024, 2025, 2026];
const transitionFundingRows = ref(
  TRANSITION_YEARS.map((y) => ({
    year: y,
    militaryInvestment: 0,
    localInvestment: 0,
  })),
);
const transitionMilitaryTotal = computed(() =>
  transitionFundingRows.value.reduce(
    (s, r) => s + (r.militaryInvestment || 0),
    0,
  ),
);
const transitionLocalTotal = computed(() =>
  transitionFundingRows.value.reduce((s, r) => s + (r.localInvestment || 0), 0),
);

async function loadTransitionFunding() {
  if (!props.village?.id) return;
  try {
    const resp = await getTransitionFunding(props.village.id);
    const items = (resp as any)?.data || resp || [];
    for (const item of items) {
      const row = transitionFundingRows.value.find((r) => r.year === item.year);
      if (row) {
        row.militaryInvestment = Number(item.militaryInvestment || 0);
        row.localInvestment = Number(item.localInvestment || 0);
      }
    }
  } catch {
    /* 无数据时保持默认值 */
  }
}

/** 区域值双向绑定：flat formData ↔ RegionValue 对象 */
const regionValue = computed<RegionValue>({
  get: () => ({
    city: formData.city || undefined,
    county: formData.county || undefined,
    township: (formData as any).township || undefined,
  }),
  set: (val: RegionValue) => {
    formData.city = val.city || "";
    formData.county = val.county || "";
    (formData as any).township = val.township || "";
  },
});

// 监听 village 变化，填充表单
watch(
  () => props.village,
  (village) => {
    if (village) {
      Object.assign(formData, {
        sequenceNo: village.sequenceNo,
        department: village.department,
        supportUnit: village.supportUnit,
        villageName: village.villageName,
        // 地域属性
        province: village.province || DEFAULT_PROVINCE,
        prefecture: village.city || DEFAULT_CITY,
        county: village.county || "",
        regionScope: village.regionScope || "",
        // 布尔字段强制转换，确保正确显示
        isThreeRegions: Boolean(village.isThreeRegions),
        isBorderArea: Boolean(village.isBorderArea),
        isEthnicArea: Boolean(village.isEthnicArea),
        isRevolutionaryArea: Boolean(village.isRevolutionaryArea),
        isKeyCounty: Boolean(village.isKeyCounty),
        revitalizationTier: village.revitalizationTier || "",
        isProvincialDemo: Boolean(village.isProvincialDemo),
        isHundredVillageDemo: Boolean(village.isHundredVillageDemo),
        isTieredDevelopment: Boolean(village.isTieredDevelopment),
        tieredDevelopmentLevel: village.tieredDevelopmentLevel || null,
        isCrossProvince: Boolean(village.isCrossProvince),
        isCrossCity: Boolean(village.isCrossCity),
        isCrossUnitCooperation: Boolean(village.isCrossUnitCooperation),
        isInOverallPlan: Boolean(village.isInOverallPlan),
        honors: village.honors || "",
        transitionFundMilitaryTotal:
          (village as any).transitionFundMilitaryTotal || 0,
        transitionFundLocalTotal:
          (village as any).transitionFundLocalTotal || 0,
        latitude: village.latitude ?? null,
        longitude: village.longitude ?? null,
      });

      // 加载过渡期经费按年度数据
      if (village.id) {
        loadTransitionFunding();
      }
    }
  },
  { immediate: true },
);

async function handleSubmit() {
  if (!formRef.value) return;
  try {
    await formRef.value.validate();
    // 同步更新总额字段
    formData.transitionFundMilitaryTotal = transitionMilitaryTotal.value;
    formData.transitionFundLocalTotal = transitionLocalTotal.value;
    emit("submit", { ...formData });
    // 保存过渡期经费按年度数据
    if (props.village?.id) {
      const items = transitionFundingRows.value.map((r) => ({
        year: r.year,
        militaryInvestment: r.militaryInvestment || 0,
        localInvestment: r.localInvestment || 0,
        totalInvestment: (r.militaryInvestment || 0) + (r.localInvestment || 0),
      }));
      await saveTransitionFunding(props.village.id, { items }).catch((err) => {
        console.error("[SupportedVillageForm] 保存过渡资金失败:", err);
        ElMessage.error("过渡资金保存失败，请重试");
      });
    }
  } catch (error) {
    logger.error("表单验证失败:", error);
  }
}

onMounted(() => {
  // 过渡期经费数据加载已移至 watch 中，确保 village 变化时自动加载
});

function handleCancel() {
  emit("cancel");
}
</script>

<style scoped lang="scss">
.form-actions {
  margin-top: 24px;
  text-align: right;
}
</style>
