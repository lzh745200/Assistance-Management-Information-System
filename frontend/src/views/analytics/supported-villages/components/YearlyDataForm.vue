<template>
  <div class="yearly-data-form">
    <el-form ref="formRef" :model="formData" label-width="100px">
      <!-- 年份选择 -->
      <el-form-item label="数据年份">
        <el-select
          v-model="selectedYear"
          style="width: 160px"
          @change="loadYearlyData"
        >
          <el-option
            v-for="year in availableYears"
            :key="year"
            :label="`${year}年`"
            :value="year"
          />
        </el-select>
        <el-button
          style="margin-left: 12px"
          :loading="copying"
          :disabled="selectedYear <= availableYears[availableYears.length - 1]"
          @click="handleCopyFromLastYear"
        >
          复制 {{ selectedYear - 1 }} 年数据
        </el-button>
        <el-tooltip
          content="将上一年度已录入数据复制到当前选中年份，便于在历史数据基础上修改"
          placement="top"
        >
          <el-icon style="margin-left: 6px; color: #909399; cursor: help"
            ><QuestionFilled
          /></el-icon>
        </el-tooltip>
      </el-form-item>

      <!-- 人口数据 -->
      <el-divider content-position="left">人口与户籍数据</el-divider>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="总户数">
            <el-input-number
              v-model="formData.population.totalHouseholds"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="总人数">
            <el-input-number
              v-model="formData.population.totalPopulation"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="常住人口数">
            <el-input-number
              v-model="formData.population.residentPopulation"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <!-- 脱贫不稳定户 -->
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="脱贫不稳定户(户)">
            <el-input-number
              v-model="formData.population.unstablePovertyHouseholds"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="脱贫不稳定户(人)">
            <el-input-number
              v-model="formData.population.unstablePovertyPopulation"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <!-- 边缘易致贫户 -->
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="边缘易致贫户(户)">
            <el-input-number
              v-model="formData.population.marginalPovertyHouseholds"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="边缘易致贫户(人)">
            <el-input-number
              v-model="formData.population.marginalPovertyPopulation"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <!-- 突发严重困难户 -->
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="突发严重困难户(户)">
            <el-input-number
              v-model="formData.population.suddenDifficultyHouseholds"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="突发严重困难户(人)">
            <el-input-number
              v-model="formData.population.suddenDifficultyPopulation"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <!-- 村两委退役军人 -->
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="村支书(退役军人)">
            <el-input-number
              v-model="formData.population.veteranVillageSecretary"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="村委员(退役军人)">
            <el-input-number
              v-model="formData.population.veteranVillageCommittee"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 收入数据 -->
      <el-divider content-position="left">收入数据</el-divider>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="村人均纯收入(万元)">
            <el-input-number
              v-model="formData.income.perCapitaIncome"
              :min="0"
              :precision="4"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="县区人均收入(万元)">
            <el-input-number
              v-model="formData.income.countyPerCapitaIncome"
              :min="0"
              :precision="4"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="村集体收入(万元)">
            <el-input-number
              v-model="formData.income.collectiveIncome"
              :min="0"
              :precision="2"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 力量投入 -->
      <el-divider content-position="left">力量投入情况</el-divider>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="军以上领导到村(人次)">
            <el-input-number
              v-model="formData.forceInvestment.seniorLeaderVisits"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="帮扶单位官兵到村(人次)">
            <el-input-number
              v-model="formData.forceInvestment.unitSoldierVisits"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 产业帮扶 -->
      <el-divider content-position="left">产业帮扶</el-divider>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="当年投入(万元)">
            <el-input-number
              v-model="formData.industry.investment"
              :min="0"
              :precision="2"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="计划投入(万元)">
            <el-input-number
              v-model="formData.industry.plannedInvestment"
              :min="0"
              :precision="2"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="12">
        <el-col :span="6">
          <el-form-item label="种植养殖(个)">
            <el-input-number
              v-model="formData.industry.plantingBreeding"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="帮扶车间(个)">
            <el-input-number
              v-model="formData.industry.workshop"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="乡村旅游(个)">
            <el-input-number
              v-model="formData.industry.ruralTourism"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="其他(个)">
            <el-input-number
              v-model="formData.industry.otherIndustry"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 基础设施 -->
      <el-divider content-position="left">改善基础设施</el-divider>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="当年投入(万元)">
            <el-input-number
              v-model="formData.infrastructure.investment"
              :min="0"
              :precision="2"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="计划投入(万元)">
            <el-input-number
              v-model="formData.infrastructure.plannedInvestment"
              :min="0"
              :precision="2"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="12">
        <el-col :span="6">
          <el-form-item label="乡村道路(公里)">
            <el-input-number
              v-model="formData.infrastructure.roadKm"
              :min="0"
              :precision="2"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="住房改造(户)">
            <el-input-number
              v-model="formData.infrastructure.housingRenovation"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="水利设施(个)">
            <el-input-number
              v-model="formData.infrastructure.waterFacilities"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="文化广场(个)">
            <el-input-number
              v-model="formData.infrastructure.culturalPlaza"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="12">
        <el-col :span="6">
          <el-form-item label="书屋网吧(个)">
            <el-input-number
              v-model="formData.infrastructure.libraryCafe"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 党建帮扶 -->
      <el-divider content-position="left">党建帮扶</el-divider>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="当年投入(万元)">
            <el-input-number
              v-model="formData.partyBuilding.investment"
              :min="0"
              :precision="2"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="计划投入(万元)">
            <el-input-number
              v-model="formData.partyBuilding.plannedInvestment"
              :min="0"
              :precision="2"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="12">
        <el-col :span="6">
          <el-form-item label="结对帮扶党支部(个)">
            <el-input-number
              v-model="formData.partyBuilding.pairedBranches"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="党建指导员(人)">
            <el-input-number
              v-model="formData.partyBuilding.partyInstructors"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="联建共促活动(次)">
            <el-input-number
              v-model="formData.partyBuilding.jointActivities"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="乡风文明活动(次)">
            <el-input-number
              v-model="formData.partyBuilding.civilizationActivities"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 医疗帮扶 -->
      <el-divider content-position="left">医疗帮扶</el-divider>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="当年投入(万元)">
            <el-input-number
              v-model="formData.medical.investment"
              :min="0"
              :precision="2"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="计划投入(万元)">
            <el-input-number
              v-model="formData.medical.plannedInvestment"
              :min="0"
              :precision="2"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="帮建卫生院室(个)">
            <el-input-number
              v-model="formData.medical.clinicsBuilt"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="巡诊群众(人次)">
            <el-input-number
              v-model="formData.medical.patientsServed"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 消费帮扶 -->
      <el-divider content-position="left">消费帮扶</el-divider>
      <el-row :gutter="12">
        <el-col :span="6">
          <el-form-item label="采购村产品(万元)">
            <el-input-number
              v-model="formData.consumption.villageProductsPurchase"
              :min="0"
              :precision="2"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="采购他村产品(万元)">
            <el-input-number
              v-model="formData.consumption.otherProductsPurchase"
              :min="0"
              :precision="2"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="营区销售专柜(个)">
            <el-input-number
              v-model="formData.consumption.salesCounters"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="惠及群众(人)">
            <el-input-number
              v-model="formData.consumption.benefitedPopulation"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 就业帮扶 -->
      <el-divider content-position="left">就业帮扶</el-divider>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="聘用脱贫群众(人)">
            <el-input-number
              v-model="formData.employment.hiredPopulation"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="技能培训(人次)">
            <el-input-number
              v-model="formData.employment.trainedPopulation"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="推荐就业(人次)">
            <el-input-number
              v-model="formData.employment.recommendedEmployment"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 教育帮扶 -->
      <el-divider content-position="left">教育帮扶</el-divider>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="教育投入(万元)">
            <el-input-number
              v-model="formData.education.investment"
              :min="0"
              :precision="2"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="12">
        <el-col :span="6">
          <el-form-item label="捐赠帮扶村学校(所)">
            <el-input-number
              v-model="formData.education.donatedSchools"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="援建外村学校(所)">
            <el-input-number
              v-model="formData.education.aidedExternalSchools"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="助学兴教活动(次)">
            <el-input-number
              v-model="formData.education.educationActivities"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="资助困难学生(人)">
            <el-input-number
              v-model="formData.education.aidedStudents"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="12">
        <el-col :span="6">
          <el-form-item label="官兵辅导员(人)">
            <el-input-number
              v-model="formData.education.volunteerCounselors"
              :min="0"
              style="width: 160px"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item style="margin-top: 30px">
        <el-button type="primary" :loading="saving" @click="handleSave"
          >保存</el-button
        >
        <el-button @click="handleClose">取消</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { logger } from "@/utils/logger";

import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { QuestionFilled } from "@element-plus/icons-vue";
import {
  getYearlyData,
  savePopulationData,
  saveIncomeData,
  saveIndustryData,
  saveInfrastructureData,
  saveEducationData,
  saveForceInvestmentData,
  savePartyBuildingData,
  saveMedicalData,
  saveConsumptionData,
  saveEmploymentData,
  copyYearData,
} from "@/api/supportedVillage";

const props = defineProps<{
  villageId: number;
  villageName: string;
}>();

const emit = defineEmits<{
  close: [];
}>();

const formRef = ref();
defineExpose({ formRef });
const saving = ref(false);
const copying = ref(false);
const currentYear = new Date().getFullYear();
const selectedYear = ref(currentYear);
const availableYears = Array.from(
  { length: currentYear - 2000 + 2 },
  (_, i) => currentYear + 1 - i,
);

const formData = reactive({
  population: {
    year: selectedYear.value,
    totalHouseholds: 0,
    totalPopulation: 0,
    residentPopulation: 0,
    unstablePovertyHouseholds: 0,
    unstablePovertyPopulation: 0,
    marginalPovertyHouseholds: 0,
    marginalPovertyPopulation: 0,
    suddenDifficultyHouseholds: 0,
    suddenDifficultyPopulation: 0,
    veteranVillageSecretary: 0,
    veteranVillageCommittee: 0,
  },
  income: {
    year: selectedYear.value,
    perCapitaIncome: 0,
    countyPerCapitaIncome: 0,
    collectiveIncome: 0,
  },
  forceInvestment: {
    year: selectedYear.value,
    seniorLeaderVisits: 0,
    unitSoldierVisits: 0,
  },
  industry: {
    year: selectedYear.value,
    investment: 0,
    plannedInvestment: 0,
    plantingBreeding: 0,
    workshop: 0,
    ruralTourism: 0,
    otherIndustry: 0,
  },
  infrastructure: {
    year: selectedYear.value,
    investment: 0,
    plannedInvestment: 0,
    roadKm: 0,
    housingRenovation: 0,
    waterFacilities: 0,
    culturalPlaza: 0,
    libraryCafe: 0,
  },
  partyBuilding: {
    year: selectedYear.value,
    investment: 0,
    plannedInvestment: 0,
    pairedBranches: 0,
    partyInstructors: 0,
    jointActivities: 0,
    civilizationActivities: 0,
  },
  medical: {
    year: selectedYear.value,
    investment: 0,
    plannedInvestment: 0,
    clinicsBuilt: 0,
    patientsServed: 0,
  },
  consumption: {
    year: selectedYear.value,
    villageProductsPurchase: 0,
    otherProductsPurchase: 0,
    salesCounters: 0,
    benefitedPopulation: 0,
  },
  employment: {
    year: selectedYear.value,
    hiredPopulation: 0,
    trainedPopulation: 0,
    recommendedEmployment: 0,
  },
  education: {
    year: selectedYear.value,
    investment: 0,
    donatedSchools: 0,
    aidedExternalSchools: 0,
    educationActivities: 0,
    aidedStudents: 0,
    volunteerCounselors: 0,
  },
});

const loadYearlyData = async () => {
  try {
    const resp = await getYearlyData(props.villageId, selectedYear.value);
    const raw: Record<string, any> = (resp as any)?.data || resp || {};
    // 后端 _SECTION_MODEL key → formData 属性名映射
    const sectionMap: Record<string, keyof typeof formData> = {
      population: "population",
      income: "income",
      "force-investment": "forceInvestment",
      industry: "industry",
      infrastructure: "infrastructure",
      "party-building": "partyBuilding",
      medical: "medical",
      consumption: "consumption",
      employment: "employment",
      education: "education",
    };
    for (const [apiKey, formKey] of Object.entries(sectionMap)) {
      if (raw[apiKey]) {
        Object.assign(formData[formKey], { ...raw[apiKey], year: selectedYear.value });
      }
    }
  } catch (error) {
    logger.error("加载年度数据失败:", error);
    ElMessage.warning("加载数据失败，将使用空白表单");
  }
};

const handleCopyFromLastYear = async () => {
  const fromYear = selectedYear.value - 1;
  const toYear = selectedYear.value;
  try {
    await ElMessageBox.confirm(
      `将复制 ${fromYear} 年的数据到 ${toYear} 年，当前 ${toYear} 年已有数据将被覆盖，是否继续？`,
      "确认复制",
      { confirmButtonText: "复制", cancelButtonText: "取消", type: "warning" },
    );
  } catch {
    return;
  }
  copying.value = true;
  try {
    await copyYearData(props.villageId, fromYear, toYear);
    ElMessage.success(`已将 ${fromYear} 年数据复制到 ${toYear} 年`);
    await loadYearlyData();
  } catch (e) {
    logger.error("复制上年数据失败:", e);
    ElMessage.error("复制失败，请确认上年度已有数据后重试");
  } finally {
    copying.value = false;
  }
};

const handleSave = async () => {
  saving.value = true;
  try {
    await Promise.all([
      savePopulationData(
        props.villageId,
        selectedYear.value,
        formData.population,
      ),
      saveIncomeData(props.villageId, selectedYear.value, formData.income),
      saveForceInvestmentData(
        props.villageId,
        selectedYear.value,
        formData.forceInvestment,
      ),
      saveIndustryData(props.villageId, selectedYear.value, formData.industry),
      saveInfrastructureData(
        props.villageId,
        selectedYear.value,
        formData.infrastructure,
      ),
      savePartyBuildingData(
        props.villageId,
        selectedYear.value,
        formData.partyBuilding,
      ),
      saveMedicalData(props.villageId, selectedYear.value, formData.medical),
      saveConsumptionData(
        props.villageId,
        selectedYear.value,
        formData.consumption,
      ),
      saveEmploymentData(
        props.villageId,
        selectedYear.value,
        formData.employment,
      ),
      saveEducationData(
        props.villageId,
        selectedYear.value,
        formData.education,
      ),
    ]);
    ElMessage.success("保存成功");
    emit("close");
  } catch (error) {
    logger.error("保存失败:", error);
    ElMessage.error("保存失败，请重试");
  } finally {
    saving.value = false;
  }
};

const handleClose = () => {
  emit("close");
};

onMounted(() => {
  loadYearlyData();
});
</script>

<style scoped>
.yearly-data-form {
  padding: 20px;
}
</style>
