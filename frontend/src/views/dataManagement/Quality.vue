<template>
  <div class="quality-page">
    <div class="page-header">
      <h2 class="page-title">数据质量监控</h2>
      <p class="page-desc">
        实时监控系统数据质量，检查完整性、一致性和准确性，给出修改建议
      </p>
    </div>

    <!-- 质量概览统计 -->
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card class="stat-card"
          ><div class="stat-num">{{ stats.totalVillages }}</div>
          <div class="stat-lbl">帮扶村总数</div></el-card
        >
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card success"
          ><div class="stat-num">
            {{ (stats.popFillRate * 100).toFixed(1) }}%
          </div>
          <div class="stat-lbl">人口数据填报率</div></el-card
        >
      </el-col>
      <el-col :span="6">
        <el-card
          class="stat-card"
          :class="stats.incomeFillRate < 0.6 ? 'warning' : 'success'"
          ><div class="stat-num">
            {{ (stats.incomeFillRate * 100).toFixed(1) }}%
          </div>
          <div class="stat-lbl">收入数据填报率</div></el-card
        >
      </el-col>
      <el-col :span="6">
        <el-card
          class="stat-card"
          :class="stats.anomalyCount > 0 ? 'danger' : 'success'"
          ><div class="stat-num">{{ stats.anomalyCount }}</div>
          <div class="stat-lbl">异常记录数</div></el-card
        >
      </el-col>
    </el-row>

    <!-- 检查操作 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据质量报告</span>
          <div>
            <span
              v-if="stats.generatedAt"
              style="font-size: 12px; color: #999; margin-right: 16px"
              >生成时间: {{ stats.generatedAt }}</span
            >
            <el-button
              type="warning"
              :loading="fullChecking"
              @click="runFullCheck"
              >全面检查</el-button
            >
            <el-button type="primary" :loading="loading" @click="loadReport"
              >刷新报告</el-button
            >
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <!-- 填报缺失概览 -->
        <el-tab-pane label="填报缺失" name="missing">
          <el-table
            v-loading="loading"
            :data="missingVillages"
            stripe
            max-height="500"
          >
            <el-table-column
              prop="village_name"
              label="帮扶村"
              min-width="120"
            />
            <el-table-column prop="county" label="县/市" width="100" />
            <el-table-column label="人口数据填报" width="120" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="
                    row.population_missing_years.length === 0
                      ? 'success'
                      : 'danger'
                  "
                  size="small"
                >
                  {{ row.population_filled }}/{{ stats.expectedYears.length }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="缺失年份(人口)" min-width="180">
              <template #default="{ row }">
                <span
                  v-if="row.population_missing_years.length === 0"
                  style="color: #67c23a"
                  >已完成</span
                >
                <span v-else style="color: #f56c6c">{{
                  row.population_missing_years.join(", ")
                }}</span>
              </template>
            </el-table-column>
            <el-table-column label="收入数据填报" width="120" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="
                    row.income_missing_years.length === 0 ? 'success' : 'danger'
                  "
                  size="small"
                >
                  {{ row.income_filled }}/{{ stats.expectedYears.length }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="缺失年份(收入)" min-width="180">
              <template #default="{ row }">
                <span
                  v-if="row.income_missing_years.length === 0"
                  style="color: #67c23a"
                  >已完成</span
                >
                <span v-else style="color: #f56c6c">{{
                  row.income_missing_years.join(", ")
                }}</span>
              </template>
            </el-table-column>
            <el-table-column label="建议" width="180">
              <template #default="{ row }">
                <span
                  v-if="
                    row.population_missing_years.length +
                      row.income_missing_years.length >
                    0
                  "
                  style="color: #e6a23c; font-size: 12px"
                >
                  请补充缺失年份数据
                </span>
                <span v-else style="color: #67c23a; font-size: 12px"
                  >数据完整</span
                >
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 异常值检测 -->
        <el-tab-pane label="异常值检测" name="anomalies">
          <el-alert
            v-if="anomalies.length === 0"
            title="未发现异常数据"
            type="success"
            :closable="false"
            show-icon
            style="margin-bottom: 16px"
          />
          <el-table v-else :data="anomalies" stripe max-height="500">
            <el-table-column prop="village_name" label="帮扶村" width="120" />
            <el-table-column prop="year" label="年份" width="80" />
            <el-table-column
              prop="previous_value"
              label="上年人均收入"
              width="120"
            />
            <el-table-column
              prop="current_value"
              label="当年人均收入"
              width="120"
            />
            <el-table-column label="变动率" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="row.severity === 'high' ? 'danger' : 'warning'"
                  size="small"
                >
                  {{ (row.change_rate * 100).toFixed(1) }}%
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="严重程度" width="90">
              <template #default="{ row }">
                <el-tag
                  :type="row.severity === 'high' ? 'danger' : 'warning'"
                  size="small"
                  >{{ row.severity === "high" ? "高" : "中" }}</el-tag
                >
              </template>
            </el-table-column>
            <el-table-column label="建议" min-width="200">
              <template #default="{ row }">
                <span style="font-size: 12px; color: #e6a23c">
                  人均收入波动超过50%，请核实{{ row.village_name
                  }}{{ row.year }}年度收入数据是否正确
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 填报进度矩阵 -->
        <el-tab-pane label="填报进度" name="progress">
          <el-table v-loading="loading" :data="progressMatrix" stripe>
            <el-table-column prop="county" label="县/市" width="120" fixed />
            <el-table-column
              prop="total_villages"
              label="村庄数"
              width="80"
              align="center"
            />
            <el-table-column
              v-for="yr in stats.expectedYears"
              :key="yr"
              :label="String(yr)"
              align="center"
              width="100"
            >
              <template #default="{ row }">
                <el-tag
                  v-if="row.years[yr]"
                  :type="
                    row.years[yr].rate >= 1
                      ? 'success'
                      : row.years[yr].rate >= 0.5
                        ? 'warning'
                        : 'danger'
                  "
                  size="small"
                >
                  {{ (row.years[yr].rate * 100).toFixed(0) }}%
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 全面检查结果 -->
        <el-tab-pane label="全面检查" name="full">
          <el-alert
            v-if="!fullCheckResults"
            title="请点击“全面检查”按钮开始对系统数据进行全面检查"
            type="info"
            :closable="false"
            show-icon
          />
          <div v-else>
            <!-- 检查总结 -->
            <el-descriptions :column="4" border style="margin-bottom: 16px">
              <el-descriptions-item label="总检查项">
                {{ fullCheckResults.summary?.total_checks ?? 0 }}
              </el-descriptions-item>
              <el-descriptions-item label="通过">
                <el-tag type="success">{{
                  fullCheckResults.summary?.passed ?? 0
                }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="警告">
                <el-tag type="warning">{{
                  fullCheckResults.summary?.warnings ?? 0
                }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="错误">
                <el-tag type="danger">{{
                  fullCheckResults.summary?.errors ?? 0
                }}</el-tag>
              </el-descriptions-item>
            </el-descriptions>

            <!-- 检查详情 -->
            <el-collapse v-model="activeCheckItems">
              <el-collapse-item
                v-for="(check, index) in fullCheckResults.checks || []"
                :key="index"
                :name="index"
              >
                <template #title>
                  <div style="display: flex; align-items: center; width: 100%">
                    <el-icon
                      v-if="check.status === 'pass'"
                      color="#67c23a"
                      style="margin-right: 8px"
                    >
                      <SuccessFilled />
                    </el-icon>
                    <el-icon
                      v-else-if="check.status === 'warning'"
                      color="#e6a23c"
                      style="margin-right: 8px"
                    >
                      <WarningFilled />
                    </el-icon>
                    <el-icon v-else color="#f56c6c" style="margin-right: 8px">
                      <CircleCloseFilled />
                    </el-icon>
                    <span style="flex: 1">{{ check.check_name }}</span>
                    <el-tag
                      :type="
                        check.status === 'pass'
                          ? 'success'
                          : check.status === 'warning'
                            ? 'warning'
                            : 'danger'
                      "
                      size="small"
                      style="margin-right: 16px"
                    >
                      {{ check.issues_count }} 项问题
                    </el-tag>
                  </div>
                </template>
                <div v-if="check.issues && check.issues.length > 0">
                  <el-table
                    :data="check.issues"
                    stripe
                    size="small"
                    max-height="300"
                  >
                    <el-table-column prop="module" label="模块" width="120" />
                    <el-table-column
                      prop="record_id"
                      label="记录ID"
                      width="100"
                    />
                    <el-table-column prop="field" label="字段" width="120" />
                    <el-table-column
                      prop="issue"
                      label="问题描述"
                      min-width="200"
                    />
                    <el-table-column
                      prop="suggestion"
                      label="修改建议"
                      min-width="200"
                    />
                  </el-table>
                </div>
                <el-empty v-else description="未发现问题" :image-size="60" />
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { ElMessage } from "element-plus";
import {
  SuccessFilled,
  WarningFilled,
  CircleCloseFilled,
} from "@element-plus/icons-vue";
import request from "@/api/request";

const loading = ref(false);
const fullChecking = ref(false);
const activeTab = ref("missing");
const activeCheckItems = ref<number[]>([]);

const stats = reactive({
  totalVillages: 0,
  popFillRate: 0,
  incomeFillRate: 0,
  anomalyCount: 0,
  expectedYears: [] as number[],
  generatedAt: "",
});

const missingVillages = ref<any[]>([]);
const anomalies = ref<any[]>([]);
const progressMatrix = ref<any[]>([]);
const fullCheckResults = ref<any>(null);

async function loadReport() {
  loading.value = true;
  try {
    const res = await request.get("/data-quality/report");
    const d = res.data;

    stats.generatedAt = d.generated_at || "";

    // 空值率报告
    const nr = d.null_rate_report || {};
    stats.totalVillages = nr.total_villages ?? 0;
    stats.popFillRate = nr.population_fill_rate ?? 0;
    stats.incomeFillRate = nr.income_fill_rate ?? 0;
    stats.expectedYears = nr.expected_years ?? [];
    missingVillages.value = (nr.villages ?? []).filter(
      (v: any) =>
        v.population_missing_years?.length > 0 ||
        v.income_missing_years?.length > 0,
    );

    // 异常值
    anomalies.value = d.income_anomalies ?? [];
    stats.anomalyCount = anomalies.value.length;

    // 填报进度
    const fp = d.filing_progress || {};
    progressMatrix.value = (fp.matrix ?? []).map((item: any) => ({
      ...item,
      years: Object.fromEntries(
        Object.entries(item.years || {}).map(([k, v]: [string, any]) => [
          Number(k),
          v,
        ]),
      ),
    }));
  } catch (err: any) {
    ElMessage.error(
      err?.response?.data?.error || err?.message || "加载数据质量报告失败",
    );
  } finally {
    loading.value = false;
  }
}

async function runFullCheck() {
  fullChecking.value = true;
  try {
    const res = await request.post("/data-quality/full-check");
    fullCheckResults.value = res.data;
    activeTab.value = "full";

    // 默认展开有问题的检查项
    activeCheckItems.value = (fullCheckResults.value.checks || [])
      .map((check: any, index: number) => (check.issues_count > 0 ? index : -1))
      .filter((i: number) => i >= 0);

    const summary = fullCheckResults.value.summary || {};
    if (summary.errors > 0) {
      ElMessage.warning(
        `检查完成，发现 ${summary.errors} 个错误和 ${summary.warnings} 个警告`,
      );
    } else if (summary.warnings > 0) {
      ElMessage.warning(`检查完成，发现 ${summary.warnings} 个警告`);
    } else {
      ElMessage.success("检查完成，数据质量良好！");
    }
  } catch (err: any) {
    ElMessage.error(err.message || "全面检查失败");
  } finally {
    fullChecking.value = false;
  }
}

onMounted(() => {
  loadReport();
});
</script>

<style scoped>
.quality-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1b4332;
  margin: 0 0 4px;
}
.page-desc {
  font-size: 14px;
  color: #666;
  margin: 0;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.stat-card {
  text-align: center;
  padding: 20px;
}
.stat-num {
  font-size: 28px;
  font-weight: 700;
  color: #1b4332;
}
.stat-card.success .stat-num {
  color: #67c23a;
}
.stat-card.warning .stat-num {
  color: #e6a23c;
}
.stat-card.danger .stat-num {
  color: #f56c6c;
}
.stat-lbl {
  font-size: 13px;
  color: #666;
  margin-top: 4px;
}
</style>
