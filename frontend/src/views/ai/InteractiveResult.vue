<template>
  <div class="ai-analysis-page">
    <el-card class="status-card">
      <template #header>
        <div class="card-header">
          <span class="title">AI 智能分析</span>
          <el-tag
            :type="serviceStatus === 'available' ? 'success' : 'info'"
            size="small"
          >
            {{ serviceStatus === "available" ? "服务可用" : "加载中..." }}
          </el-tag>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-card shadow="hover" class="action-card">
            <h3>数据分析</h3>
            <p class="desc">对系统数据进行摘要或趋势分析</p>
            <el-form :model="analyzeForm" label-position="top">
              <el-form-item label="分析类型">
                <el-radio-group v-model="analyzeForm.type">
                  <el-radio value="summary">数据摘要</el-radio>
                  <el-radio value="trend">趋势分析</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="分析说明（可选）">
                <el-input
                  v-model="analyzeForm.description"
                  type="textarea"
                  :rows="2"
                  placeholder="描述您想分析的内容..."
                />
              </el-form-item>
              <el-button
                type="primary"
                :loading="analyzing"
                @click="runAnalysis"
                >开始分析</el-button
              >
            </el-form>
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card shadow="hover" class="action-card">
            <h3>智能推荐</h3>
            <p class="desc">获取系统运营的智能化建议</p>
            <el-button
              type="success"
              :loading="recommending"
              @click="getRecommendations"
              >获取推荐</el-button
            >
            <div v-if="recommendations.length > 0" class="recommendations">
              <el-divider content-position="left">推荐建议</el-divider>
              <div
                v-for="(rec, idx) in recommendations"
                :key="idx"
                class="rec-item"
              >
                <el-tag
                  :type="
                    rec.priority === 'high'
                      ? 'danger'
                      : rec.priority === 'medium'
                        ? 'warning'
                        : 'info'
                  "
                  size="small"
                  >{{ rec.priority }}</el-tag
                >
                <span class="rec-content">{{ rec.content }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <el-card v-if="analysisResult" class="result-card">
      <template #header>
        <div class="card-header">
          <span class="title">分析结果</span>
          <el-tag size="small">{{ analysisResult.analysis_type }}</el-tag>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item
          v-for="(value, key) in analysisResult.result"
          :key="key"
          :label="String(key)"
          >{{ value }}</el-descriptions-item
        >
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { ElMessage } from "element-plus";
import request from "@/api/request";

const serviceStatus = ref("loading");
const analyzing = ref(false);
const recommending = ref(false);
const analysisResult = ref<any>(null);
const recommendations = ref<any[]>([]);
const analyzeForm = reactive({ type: "summary", description: "" });

async function loadStatus() {
  try {
    const { data } = await request.get("/ai/status");
    if (data?.data?.services?.local_analysis)
      serviceStatus.value = data.data.services.local_analysis.status;
  } catch {
    serviceStatus.value = "unavailable";
  }
}

async function runAnalysis() {
  analyzing.value = true;
  try {
    const { data } = await request.post("/ai/analyze", {
      analysis_type: analyzeForm.type,
      data: {},
      description: analyzeForm.description || undefined,
    });
    if (data?.data) {
      analysisResult.value = data.data;
      ElMessage.success("分析完成");
    }
  } catch {
    ElMessage.error("分析失败");
  } finally {
    analyzing.value = false;
  }
}

async function getRecommendations() {
  recommending.value = true;
  try {
    const { data } = await request.post("/ai/recommendations", { context: {} });
    if (data?.data?.recommendations) {
      recommendations.value = data.data.recommendations;
      ElMessage.success("获取推荐成功");
    }
  } catch {
    ElMessage.error("获取推荐失败");
  } finally {
    recommending.value = false;
  }
}

onMounted(() => loadStatus());
</script>

<style scoped>
.ai-analysis-page {
  padding: 20px;
}
.status-card {
  margin-bottom: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.title {
  font-size: 16px;
  font-weight: 600;
}
.action-card {
  min-height: 300px;
}
.action-card h3 {
  margin: 0 0 8px 0;
  color: #1b4332;
}
.desc {
  color: #909399;
  font-size: 13px;
  margin-bottom: 16px;
}
.result-card {
  margin-top: 20px;
}
.recommendations {
  margin-top: 12px;
}
.rec-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}
.rec-content {
  font-size: 14px;
}
</style>
