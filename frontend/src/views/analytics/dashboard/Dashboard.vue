<template>
  <div class="analytics-dashboard">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">数据分析仪表板</h2>
        <p class="page-desc">帮扶村综合数据分析与可视化</p>
      </div>
      <div class="header-actions">
        <el-select
          v-model="selectedYear"
          style="width: 120px"
          @change="loadData"
        >
          <el-option
            v-for="year in availableYears"
            :key="year"
            :label="`${year}年`"
            :value="year"
          />
        </el-select>
        <el-button @click="handleExport">
          <el-icon><Download /></el-icon>导出报表
        </el-button>
      </div>
    </div>

    <!-- 筛选器 -->
    <div class="filter-card">
      <el-form :model="filters" inline>
        <el-form-item label="部门">
          <el-select
            v-model="filters.department"
            placeholder="全部"
            clearable
            style="width: 140px"
            @change="loadData"
          >
            <el-option
              v-for="dept in filterOptions.departments"
              :key="dept"
              :label="dept"
              :value="dept"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="地域属性">
          <el-select
            v-model="filters.regionType"
            placeholder="全部"
            clearable
            style="width: 140px"
            @change="loadData"
          >
            <el-option label="三区三州" value="isThreeRegions" />
            <el-option label="边疆地区" value="isBorderArea" />
            <el-option label="民族地区" value="isEthnicArea" />
            <el-option label="革命地区" value="isRevolutionaryArea" />
            <el-option label="重点帮扶县" value="isKeyCounty" />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <!-- 统计卡片 -->
    <el-row v-loading="loading" :gutter="20" class="stat-row">
      <el-col :span="6">
        <div class="stat-card primary">
          <div class="stat-icon">
            <el-icon><OfficeBuilding /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">
              {{ statistics.villages?.totalVillages || 0 }}
            </div>
            <div class="stat-label">帮扶村总数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card success">
          <div class="stat-icon">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">
              {{ formatNumber(statistics.population?.totalPopulation || 0) }}
            </div>
            <div class="stat-label">覆盖人口</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card warning">
          <div class="stat-icon">
            <el-icon><Money /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">
              {{ (statistics.income?.avgPerCapitaIncome || 0).toFixed(2) }}
            </div>
            <div class="stat-label">平均人均收入(万)</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card danger">
          <div class="stat-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatNumber(totalInvestment) }}</div>
            <div class="stat-label">帮扶投入(万)</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <div class="chart-card">
          <h3 class="chart-title">地域分布</h3>
          <div ref="regionChartRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="chart-card">
          <h3 class="chart-title">帮扶投入构成</h3>
          <div ref="investmentChartRef" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <div class="chart-card">
          <h3 class="chart-title">年度趋势对比</h3>
          <div
            ref="trendChartRef"
            class="chart-container"
            style="height: 350px"
          ></div>
        </div>
      </el-col>
    </el-row>

    <!-- 钻取面板 -->
    <div v-if="drillDownData" class="drill-down-panel">
      <div class="panel-header">
        <h3>{{ drillDownTitle }}</h3>
        <el-button text @click="closeDrillDown">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
      <el-table :data="drillDownData.items" stripe border max-height="300">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="value" label="数量" width="100" align="right" />
        <el-table-column
          prop="totalPopulation"
          label="人口"
          width="100"
          align="right"
        />
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { logger } from "@/utils/logger";

import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from "vue";
import {
  Download,
  OfficeBuilding,
  User,
  Money,
  TrendCharts,
  Close,
} from "@element-plus/icons-vue";
import echarts from "@/utils/echarts";
import {
  getSummaryStatistics,
  getFilterOptions,
  drillDown,
} from "@/api/analytics";
import type {
  SummaryStatistics,
  FilterOptions,
  DrillDownResult,
} from "@/types/analytics";

const currentYear = new Date().getFullYear();
// 动态生成年份列表：从2015年到当前年份（取消硬编码6年限制）
const availableYears = Array.from(
  { length: currentYear - 2014 },
  (_, i) => currentYear - i,
);
const selectedYear = ref(currentYear);

const filters = reactive({
  department: "",
  regionType: "",
});

const filterOptions = ref<FilterOptions>({
  departments: [],
  supportUnits: [],
  regionScopes: [],
  revitalizationTiers: [],
  years: [],
});

const statistics = ref<SummaryStatistics>({
  year: currentYear,
  villages: {
    totalVillages: 0,
    threeRegionsCount: 0,
    keyCountyCount: 0,
    provincialDemoCount: 0,
    crossProvinceCount: 0,
  },
  population: { totalPopulation: 0, totalHouseholds: 0, povertyHouseholds: 0 },
  income: { avgPerCapitaIncome: 0, totalCollectiveIncome: 0 },
  investment: {
    industry: 0,
    infrastructure: 0,
    infrastructureRoadKm: 0,
    education: 0,
    educationAidedStudents: 0,
  },
});

const loading = ref(false);
const drillDownData = ref<DrillDownResult | null>(null);
const drillDownTitle = ref("");

const totalInvestment = computed(() => {
  const inv = statistics.value.investment;
  return (inv.industry || 0) + (inv.infrastructure || 0) + (inv.education || 0);
});

// 图表引用
const regionChartRef = ref<HTMLElement>();
const investmentChartRef = ref<HTMLElement>();
const trendChartRef = ref<HTMLElement>();

let regionChart: echarts.ECharts | null = null;
let investmentChart: echarts.ECharts | null = null;
let trendChart: echarts.ECharts | null = null;

const formatNumber = (num: number) => {
  if (num >= 10000) return (num / 10000).toFixed(1) + "万";
  return num.toLocaleString();
};

const loadData = async () => {
  loading.value = true;
  try {
    const params: Record<string, unknown> = { year: selectedYear.value };
    if (filters.department) params.department = filters.department;
    if (filters.regionType === "isThreeRegions") params.isThreeRegions = true;
    if (filters.regionType === "isKeyCounty") params.isKeyCounty = true;

    const result = await getSummaryStatistics(
      params as Parameters<typeof getSummaryStatistics>[0],
    );

    // 确保数据结构完整，设置默认值
    statistics.value = {
      year: result?.year || selectedYear.value,
      villages: {
        totalVillages: result?.villages?.totalVillages || 0,
        threeRegionsCount: result?.villages?.threeRegionsCount || 0,
        keyCountyCount: result?.villages?.keyCountyCount || 0,
        provincialDemoCount: result?.villages?.provincialDemoCount || 0,
        crossProvinceCount: result?.villages?.crossProvinceCount || 0,
      },
      population: {
        totalPopulation: result?.population?.totalPopulation || 0,
        totalHouseholds: result?.population?.totalHouseholds || 0,
        povertyHouseholds: result?.population?.povertyHouseholds || 0,
      },
      income: {
        avgPerCapitaIncome: result?.income?.avgPerCapitaIncome || 0,
        totalCollectiveIncome: result?.income?.totalCollectiveIncome || 0,
      },
      investment: {
        industry: result?.investment?.industry || 0,
        infrastructure: result?.investment?.infrastructure || 0,
        infrastructureRoadKm: result?.investment?.infrastructureRoadKm || 0,
        education: result?.investment?.education || 0,
        educationAidedStudents: result?.investment?.educationAidedStudents || 0,
      },
    };

    updateCharts();
  } catch (error) {
    logger.error("加载统计数据失败:", error);
    // 设置默认空数据，避免 undefined 错误
    statistics.value = {
      year: selectedYear.value,
      villages: {
        totalVillages: 0,
        threeRegionsCount: 0,
        keyCountyCount: 0,
        provincialDemoCount: 0,
        crossProvinceCount: 0,
      },
      population: {
        totalPopulation: 0,
        totalHouseholds: 0,
        povertyHouseholds: 0,
      },
      income: { avgPerCapitaIncome: 0, totalCollectiveIncome: 0 },
      investment: {
        industry: 0,
        infrastructure: 0,
        infrastructureRoadKm: 0,
        education: 0,
        educationAidedStudents: 0,
      },
    };
  } finally {
    loading.value = false;
  }
};

const loadFilterOptions = async () => {
  try {
    filterOptions.value = await getFilterOptions();
  } catch (error) {
    logger.error("加载筛选选项失败:", error);
  }
};

const initCharts = () => {
  // 先销毁旧实例（防止热更新重复初始化）
  regionChart?.dispose();
  investmentChart?.dispose();
  trendChart?.dispose();
  regionChart = null;
  investmentChart = null;
  trendChart = null;

  if (regionChartRef.value) {
    regionChart = echarts.init(regionChartRef.value);
    regionChart.on("click", handleRegionClick as any);
  }
  if (investmentChartRef.value) {
    investmentChart = echarts.init(investmentChartRef.value);
  }
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value);
  }
};

const updateCharts = () => {
  // 地域分布饼图
  if (regionChart) {
    const v = statistics.value.villages;
    regionChart.setOption({
      tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
      legend: { bottom: 10 },
      series: [
        {
          type: "pie",
          radius: ["40%", "70%"],
          data: [
            { value: v.threeRegionsCount, name: "三区三州" },
            { value: v.keyCountyCount, name: "重点帮扶县" },
            { value: v.provincialDemoCount, name: "省级示范" },
            { value: v.crossProvinceCount, name: "跨省帮扶" },
            {
              value: Math.max(
                0,
                v.totalVillages - v.threeRegionsCount - v.keyCountyCount,
              ),
              name: "其他",
            },
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: "rgba(0, 0, 0, 0.5)",
            },
          },
        },
      ],
    });
  }

  // 投入构成饼图
  if (investmentChart) {
    const inv = statistics.value.investment;
    investmentChart.setOption({
      tooltip: { trigger: "item", formatter: "{b}: {c}万 ({d}%)" },
      legend: { bottom: 10 },
      series: [
        {
          type: "pie",
          radius: "60%",
          data: [
            { value: inv.industry, name: "产业帮扶" },
            { value: inv.infrastructure, name: "基础设施" },
            { value: inv.education, name: "教育帮扶" },
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: "rgba(0, 0, 0, 0.5)",
            },
          },
        },
      ],
    });
  }

  // 趋势图
  if (trendChart) {
    const years = availableYears.slice().reverse();
    trendChart.setOption({
      tooltip: { trigger: "axis" },
      legend: { data: ["帮扶村数", "覆盖人口(百人)", "人均收入(万)"] },
      xAxis: { type: "category", data: years.map((y) => `${y}年`) },
      yAxis: [
        { type: "value", name: "数量" },
        { type: "value", name: "收入(万)", position: "right" },
      ],
      series: [
        {
          name: "帮扶村数",
          type: "bar",
          data: years.map(() => statistics.value.villages.totalVillages),
        },
        {
          name: "覆盖人口(百人)",
          type: "bar",
          data: years.map(() =>
            Math.round(statistics.value.population.totalPopulation / 100),
          ),
        },
        {
          name: "人均收入(万)",
          type: "line",
          yAxisIndex: 1,
          data: years.map(() => statistics.value.income.avgPerCapitaIncome),
        },
      ],
    });
  }
};

const handleRegionClick = async (params: { name: string }) => {
  try {
    drillDownTitle.value = `${params.name} - 详细数据`;
    drillDownData.value = await drillDown({
      dimension: "region",
      value: params.name,
      targetDimension: "department",
    });
  } catch (error) {
    logger.error("钻取查询失败:", error);
  }
};

const closeDrillDown = () => {
  drillDownData.value = null;
};

const handleExport = () => {
  // 导出仪表板数据为JSON下载
  const exportData = {
    year: selectedYear.value,
    statistics: statistics.value,
    filters: { ...filters },
    exportTime: new Date().toISOString(),
  };
  const blob = new Blob([JSON.stringify(exportData, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `仪表板数据_${selectedYear.value}.json`;
  a.click();
  URL.revokeObjectURL(url);
};

const handleResize = () => {
  regionChart?.resize();
  investmentChart?.resize();
  trendChart?.resize();
};

onMounted(async () => {
  await loadFilterOptions();
  await nextTick();
  initCharts();
  await loadData();
  window.addEventListener("resize", handleResize);
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  regionChart?.dispose();
  investmentChart?.dispose();
  trendChart?.dispose();
  regionChart = null;
  investmentChart = null;
  trendChart = null;
});
</script>

<style scoped>
.analytics-dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1b4332;
  margin: 0 0 4px 0;
}

.page-desc {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-card {
  background: white;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stat-row {
  margin-bottom: 0;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stat-card.primary .stat-icon {
  background: #e8f5e9;
  color: #40916c;
}
.stat-card.success .stat-icon {
  background: #e3f2fd;
  color: #1976d2;
}
.stat-card.warning .stat-icon {
  background: #fff3e0;
  color: #f57c00;
}
.stat-card.danger .stat-icon {
  background: #fce4ec;
  color: #c2185b;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1b4332;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.chart-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #1b4332;
  margin: 0 0 16px 0;
}

.chart-container {
  height: 300px;
}

.drill-down-panel {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  margin-top: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  color: #1b4332;
}
</style>
