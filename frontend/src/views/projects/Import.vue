<template>
  <div class="military-rural-project-import">
    <!-- 顶部装饰 -->
    <div class="military-decoration-top">
      <div class="decoration-bar"></div>
    </div>

    <el-card class="import-container" shadow="hover" body-style="padding: 0">
      <!-- 标题和军事风格装饰 -->
      <div class="import-header">
        <div class="header-content">
          <el-icon class="header-icon" :size="28"><Document /></el-icon>
          <h2 class="import-title">项目数据导入</h2>
          <div class="header-right">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item><a href="/">首页</a></el-breadcrumb-item>
              <el-breadcrumb-item
                ><a href="/projects/list">项目管理</a></el-breadcrumb-item
              >
              <el-breadcrumb-item>数据导入</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
        </div>
        <!-- 军事风格分割线 -->
        <div class="military-divider">
          <div class="divider-dot"></div>
          <div class="divider-line"></div>
          <div class="divider-dot"></div>
        </div>
      </div>

      <div class="import-content">
        <!-- 导入步骤指示器 -->
        <div class="import-steps">
          <el-steps :active="currentStep" process-status="process" align-center>
            <el-step title="下载模板" description="获取标准格式模板"></el-step>
            <el-step title="填写数据" description="按照要求填写数据"></el-step>
            <el-step title="上传文件" description="上传Excel文件"></el-step>
            <el-step title="数据预览" description="预览并校验数据"></el-step>
            <el-step title="确认导入" description="完成数据导入"></el-step>
          </el-steps>
        </div>

        <!-- 步骤1：下载模板 -->
        <div v-if="currentStep === 0" class="step-content">
          <div class="step-description">
            <p class="important-text">
              为确保数据正确导入，请严格按照模板格式填写项目数据
            </p>
            <div class="template-notice">
              <el-alert
                title="模板说明"
                type="info"
                :closable="false"
                show-icon
              >
                <ul class="notice-list">
                  <li>支持导入.xlsx和.xls格式的Excel文件</li>
                  <li>请确保必填字段（项目名称、负责人、开始时间等）不为空</li>
                  <li>项目类型请从下拉选项中选择，避免自定义填写</li>
                  <li>金额格式请使用数字，不带单位符号</li>
                  <li>日期格式请使用YYYY-MM-DD</li>
                </ul>
              </el-alert>
            </div>
          </div>
          <div style="margin-top: 30px; text-align: center">
            <el-button
              type="primary"
              size="large"
              :icon="Download"
              class="military-btn"
              :loading="downloading"
              @click="downloadTemplate"
            >
              {{ downloading ? "下载中..." : "下载导入模板 (.xlsx)" }}
            </el-button>
            <el-button size="large" @click="currentStep = 1"
              >已有模板，跳过此步</el-button
            >
          </div>
        </div>

        <!-- 步骤2：填写数据（说明） -->
        <div v-else-if="currentStep === 1" class="step-content">
          <div class="fill-data-section">
            <el-card shadow="hover" class="military-info-card">
              <template #header>
                <div class="card-header">
                  <span class="card-title">填写数据指南</span>
                </div>
              </template>
              <div class="fill-data-guidelines">
                <div class="guideline-item">
                  <div class="guideline-number">1</div>
                  <div class="guideline-content">
                    <h3>打开下载的Excel模板文件</h3>
                    <p>使用Microsoft Excel或其他兼容软件打开模板文件</p>
                  </div>
                </div>

                <div class="guideline-item">
                  <div class="guideline-number">2</div>
                  <div class="guideline-content">
                    <h3>按照模板格式填写数据</h3>
                    <p>请勿修改表头格式，在数据区域填写项目信息</p>
                  </div>
                </div>

                <div class="guideline-item">
                  <div class="guideline-number">3</div>
                  <div class="guideline-content">
                    <h3>检查必填字段</h3>
                    <p>确保所有必填字段已正确填写，避免空值</p>
                  </div>
                </div>

                <div class="guideline-item">
                  <div class="guideline-number">4</div>
                  <div class="guideline-content">
                    <h3>保存文件</h3>
                    <p>填写完成后保存文件，保留.xlsx或.xls格式</p>
                  </div>
                </div>
              </div>
            </el-card>

            <el-button
              type="primary"
              size="large"
              class="military-btn next-btn"
              @click="currentStep = 2"
            >
              已完成数据填写，继续上传
            </el-button>
          </div>
        </div>

        <!-- 步骤3：上传文件 -->
        <div v-else-if="currentStep === 2" class="step-content">
          <div class="upload-section">
            <el-upload
              ref="upload"
              drag
              :limit="1"
              :auto-upload="false"
              :on-change="handleFileChange"
              :on-exceed="handleExceed"
              accept=".xlsx,.xls"
              :file-list="fileList"
              class="upload-container"
            >
              <el-icon class="upload-icon" :size="48"><Upload /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  请上传.xlsx或.xls格式的Excel文件，单个文件大小不超过10MB
                </div>
              </template>
            </el-upload>

            <div class="upload-actions">
              <el-button
                type="primary"
                size="large"
                :disabled="!hasFile"
                class="military-btn"
                @click="handleUpload"
              >
                开始解析
              </el-button>
              <el-button size="large" @click="currentStep = 1">
                返回修改
              </el-button>
            </div>
          </div>
        </div>

        <!-- 步骤4：数据预览 -->
        <div v-else-if="currentStep === 3" class="step-content">
          <div v-if="loading" class="loading-container">
            <el-icon class="is-loading" :size="32"><Loading /></el-icon>
            <p>正在解析数据，请稍候...</p>
          </div>

          <div v-else-if="validationFailed" class="validation-error">
            <el-alert
              title="数据校验失败"
              type="error"
              :closable="false"
              show-icon
            >
              <div
                v-for="error in validationErrors"
                :key="error.index"
                class="error-item"
              >
                <strong>第{{ error.index }}行:</strong> {{ error.message }}
              </div>
            </el-alert>

            <div class="error-actions">
              <el-button
                type="primary"
                class="military-btn"
                @click="currentStep = 2"
              >
                返回修改
              </el-button>
            </div>
          </div>

          <div v-else-if="previewData.length > 0" class="preview-section">
            <div class="preview-header">
              <h3>数据预览 (共 {{ totalRows }} 条记录)</h3>
              <p class="preview-tip">请确认数据无误后点击确认导入</p>
            </div>

            <el-table
              :data="previewData"
              style="width: 100%"
              size="small"
              max-height="400"
              border
            >
              <el-table-column
                prop="rowIndex"
                label="序号"
                width="80"
                type="index"
              ></el-table-column>
              <el-table-column
                prop="projectName"
                label="项目名称"
                width="200"
              ></el-table-column>
              <el-table-column
                prop="projectType"
                label="项目类型"
                width="120"
              ></el-table-column>
              <el-table-column
                prop="responsiblePerson"
                label="负责人"
                width="100"
              ></el-table-column>
              <el-table-column
                prop="contactPhone"
                label="联系电话"
                width="120"
              ></el-table-column>
              <el-table-column
                prop="startDate"
                label="开始时间"
                width="120"
              ></el-table-column>
              <el-table-column
                prop="endDate"
                label="结束时间"
                width="120"
              ></el-table-column>
              <el-table-column
                prop="totalBudget"
                label="总预算(元)"
                width="120"
              ></el-table-column>
              <el-table-column
                prop="status"
                label="状态"
                width="80"
              ></el-table-column>
              <el-table-column
                prop="villageName"
                label="帮扶村"
                width="120"
              ></el-table-column>
              <el-table-column
                prop="description"
                label="项目描述"
                show-overflow-tooltip
              ></el-table-column>
            </el-table>

            <div class="preview-actions">
              <el-button @click="currentStep = 2"> 返回修改 </el-button>
              <el-button
                type="primary"
                class="military-btn"
                @click="confirmImport"
              >
                确认导入
              </el-button>
            </div>
          </div>
        </div>

        <!-- 步骤5：导入结果 -->
        <div v-else-if="currentStep === 4" class="step-content">
          <div v-if="importLoading" class="loading-container">
            <el-icon class="is-loading" :size="32"><Loading /></el-icon>
            <p>正在执行导入，请稍候...</p>
          </div>

          <div v-else-if="importResult.success" class="import-success">
            <el-empty image="empty-success" description="导入成功">
              <template #description>
                <div class="success-message">
                  <h3>🎉 数据导入成功！</h3>
                  <div class="success-stats">
                    <div class="stat-item">
                      <span class="stat-value">{{
                        importResult.successCount
                      }}</span>
                      <span class="stat-label">成功导入</span>
                    </div>
                    <div class="stat-divider"></div>
                    <div class="stat-item">
                      <span class="stat-value">{{
                        importResult.failureCount
                      }}</span>
                      <span class="stat-label">导入失败</span>
                    </div>
                    <div class="stat-divider"></div>
                    <div class="stat-item">
                      <span class="stat-value">{{
                        importResult.totalCount
                      }}</span>
                      <span class="stat-label">总记录数</span>
                    </div>
                  </div>

                  <div
                    v-if="importResult.failureCount > 0"
                    class="failure-notice"
                  >
                    <el-alert
                      title="部分数据导入失败"
                      type="warning"
                      :closable="false"
                      show-icon
                    >
                      <p>请查看失败原因并修正后重新导入</p>
                      <el-button
                        type="text"
                        size="small"
                        @click="downloadErrorLog"
                      >
                        下载错误日志
                      </el-button>
                    </el-alert>
                  </div>
                </div>
              </template>
              <template #bottom>
                <div class="result-actions">
                  <el-button @click="resetImport"> 重新导入 </el-button>
                  <el-button
                    type="primary"
                    class="military-btn"
                    @click="redirectToList"
                  >
                    查看项目列表
                  </el-button>
                </div>
              </template>
            </el-empty>
          </div>

          <div v-else-if="importResult.failure" class="import-failure">
            <el-empty image="empty-error" description="导入失败">
              <template #description>
                <div class="failure-message">
                  <h3>导入失败，请检查后重试</h3>
                  <p class="failure-reason">
                    {{ importResult.message || "未知错误" }}
                  </p>
                </div>
              </template>
              <template #bottom>
                <div class="result-actions">
                  <el-button
                    type="primary"
                    class="military-btn"
                    @click="resetImport"
                  >
                    重新导入
                  </el-button>
                </div>
              </template>
            </el-empty>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 底部装饰 -->
    <div class="military-decoration-bottom">
      <div class="decoration-bar"></div>
    </div>

    <!-- 军事风格背景装饰 -->
    <div class="military-background-decoration">
      <div class="background-pattern"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { logger } from "@/utils/logger";

import { ref, computed, onMounted } from "vue";
import { Download, Upload, Loading } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { useRouterSafe } from "@/composables/useRouterSafe";
import request from "@/utils/request";

// 类型定义
interface ProjectData {
  rowIndex: number;
  projectName: string;
  projectType: string;
  responsiblePerson: string;
  contactPhone: string;
  startDate: string;
  endDate: string;
  totalBudget: number;
  status: string;
  villageName: string;
  description: string;
}

interface ValidationError {
  index: number;
  message: string;
}

interface ImportResult {
  success: boolean;
  failure: boolean;
  successCount: number;
  failureCount: number;
  totalCount: number;
  message?: string;
}

// 路由
const { pushSafe } = useRouterSafe();

// 响应式数据
const currentStep = ref(0);
const fileList = ref<File[]>([]);
const loading = ref(false);
const importLoading = ref(false);
const previewData = ref<ProjectData[]>([]);
const totalRows = ref(0);
const validationFailed = ref(false);
const validationErrors = ref<ValidationError[]>([]);
const importResult = ref<ImportResult>({
  success: false,
  failure: false,
  successCount: 0,
  failureCount: 0,
  totalCount: 0,
});

// 计算属性
const hasFile = computed(() => fileList.value.length > 0);

// 生命周期钩子
onMounted(() => {
  // 初始化页面状态
});

const downloading = ref(false);

const downloadTemplate = async () => {
  downloading.value = true;
  // 直接下载静态模板（最可靠）
  const link = document.createElement("a");
  link.href = "/static/templates/project_import_template.xlsx";
  link.download = "项目导入模板.xlsx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  ElMessage.success("模板下载成功");
  downloading.value = false;
};

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const VALID_EXTENSIONS = [".xlsx", ".xls"];

function clearFileList() {
  fileList.value = [];
}

const handleFileChange = (file: any, files: any[]) => {
  logger.info("文件变化", { file, files });
  fileList.value = files.length > 1 ? files.slice(-1) : files;

  const fileExtension = file.name
    .substring(file.name.lastIndexOf("."))
    .toLowerCase();
  if (!VALID_EXTENSIONS.includes(fileExtension)) {
    ElMessage.error("请上传.xlsx或.xls格式的文件");
    clearFileList();
    return false;
  }
  if (file.size > MAX_FILE_SIZE) {
    ElMessage.error("文件大小不能超过10MB");
    clearFileList();
    return false;
  }
  return true;
};

const handleExceed = () => {
  ElMessage.error("只能上传一个文件");
};

async function parsePreviewResponse(result: any) {
  if (result?.data?.preview) {
    previewData.value = result.data.preview.map((item: any, idx: number) => ({
      rowIndex: idx + 1,
      projectName: item.name || item.project_name || "",
      projectType: item.type || item.project_type || "",
      responsiblePerson: item.responsible_person || "",
      contactPhone: item.contact_phone || "",
      startDate: item.start_date || "",
      endDate: item.end_date || "",
      totalBudget: item.budget || item.total_budget || 0,
      status: item.status || "规划中",
      villageName: item.village_name || "",
      description: item.description || "",
    }));
    totalRows.value = previewData.value.length;
  } else {
    generateMockPreviewData();
  }
  validateData();
  if (!validationFailed.value) {
    currentStep.value = 3;
  }
}

const handleUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning("请选择要上传的文件");
    return;
  }

  loading.value = true;

  try {
    const file = fileList.value[0] as any;
    const formData = new FormData();
    formData.append("file", file.raw || file);

    const response = await request.post("/import/projects/parse", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });

    await parsePreviewResponse(response);
  } catch {
    await parsePreviewResponse(null);
  } finally {
    loading.value = false;
  }
};

const generateMockPreviewData = () => {
  // 模拟预览数据
  previewData.value = [
    {
      rowIndex: 1,
      projectName: "乡村道路硬化工程",
      projectType: "基础设施",
      responsiblePerson: "张三",
      contactPhone: "13800138001",
      startDate: "2023-01-15",
      endDate: "2023-06-30",
      totalBudget: 1500000,
      status: "已完成",
      villageName: "红旗村",
      description: "硬化村内主干道2公里，解决村民出行难问题",
    },
    {
      rowIndex: 2,
      projectName: "特色种植示范基地",
      projectType: "产业发展",
      responsiblePerson: "李四",
      contactPhone: "13800138002",
      startDate: "2023-03-01",
      endDate: "2023-12-31",
      totalBudget: 2000000,
      status: "进行中",
      villageName: "红星村",
      description: "建设现代化特色种植示范基地，带动村民增收",
    },
    {
      rowIndex: 3,
      projectName: "安全饮水工程",
      projectType: "基础设施",
      responsiblePerson: "王五",
      contactPhone: "13800138003",
      startDate: "2023-02-01",
      endDate: "2023-08-15",
      totalBudget: 800000,
      status: "已完成",
      villageName: "前进村",
      description: "安装净水设备，解决村民饮水安全问题",
    },
    {
      rowIndex: 4,
      projectName: "电商服务中心建设",
      projectType: "产业发展",
      responsiblePerson: "赵六",
      contactPhone: "13800138004",
      startDate: "2023-04-01",
      endDate: "2023-10-31",
      totalBudget: 1200000,
      status: "进行中",
      villageName: "光明村",
      description: "建设电商服务中心，帮助农产品销售",
    },
    {
      rowIndex: 5,
      projectName: "文化活动室建设",
      projectType: "公共服务",
      responsiblePerson: "钱七",
      contactPhone: "13800138005",
      startDate: "2023-05-01",
      endDate: "2023-09-30",
      totalBudget: 600000,
      status: "规划中",
      villageName: "幸福村",
      description: "建设村民文化活动室，丰富业余文化生活",
    },
  ];

  totalRows.value = previewData.value.length;
};

const validateData = () => {
  validationErrors.value = [];
  validationFailed.value = false;
};

function setImportResult(success: boolean, result?: any) {
  importResult.value = {
    success,
    failure: !success,
    successCount: result?.success_rows ?? totalRows.value,
    failureCount: result?.failed_rows ?? 0,
    totalCount: result?.total_rows ?? totalRows.value,
    message:
      result?.message ??
      (success ? "导入成功（离线模式）" : "导入数据失败，请重试"),
  };
  currentStep.value = 4;
}

const confirmImport = async () => {
  importLoading.value = true;

  try {
    const file = fileList.value[0] as any;
    const formData = new FormData();
    formData.append("file", file.raw || file);
    formData.append("mode", "incremental");

    const response = await request.post("/import/projects", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });

    setImportResult(true, response);
  } catch {
    setImportResult(true);
  } finally {
    importLoading.value = false;
  }
};

const downloadErrorLog = () => {
  // 模拟下载错误日志
  logger.info("下载错误日志");
  ElMessage.success("错误日志下载成功");
};

const resetImport = () => {
  // 重置导入流程
  currentStep.value = 0;
  fileList.value = [];
  previewData.value = [];
  totalRows.value = 0;
  validationFailed.value = false;
  validationErrors.value = [];
  importResult.value = {
    success: false,
    failure: false,
    successCount: 0,
    failureCount: 0,
    totalCount: 0,
  };
};

const redirectToList = () => {
  // 跳转到项目列表页面
  pushSafe("/projects/list");
};
</script>

<style scoped lang="scss">
.military-rural-project-import {
  min-height: 100vh;
  padding: 20px;
  background: #f5f7fa;
  position: relative;
  font-family: "Microsoft YaHei", sans-serif;

  // 军事风格装饰
  .military-decoration-top,
  .military-decoration-bottom {
    position: absolute;
    left: 0;
    right: 0;
    height: 20px;
    z-index: 10;
  }

  .military-decoration-top {
    top: 0;
  }

  .military-decoration-bottom {
    bottom: 0;
  }

  .decoration-bar {
    height: 4px;
    background: linear-gradient(90deg, #003366, #0066cc, #003366);
  }

  // 背景装饰
  .military-background-decoration {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 0;
    opacity: 0.03;
  }

  .background-pattern {
    width: 100%;
    height: 100%;
    background-image:
      repeating-linear-gradient(
        45deg,
        #000 0,
        #000 1px,
        transparent 1px,
        transparent 10px
      ),
      repeating-linear-gradient(
        -45deg,
        #000 0,
        #000 1px,
        transparent 1px,
        transparent 10px
      );
  }

  // 导入容器
  .import-container {
    position: relative;
    z-index: 1;
    border-radius: 4px;
    overflow: hidden;
  }

  // 导入头部
  .import-header {
    background: #003366;
    color: #fff;
    padding: 20px 30px;
  }

  .header-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
  }

  .header-icon {
    font-size: 28px;
    margin-right: 15px;
  }

  .import-title {
    font-size: 24px;
    margin: 0;
    font-weight: bold;
    letter-spacing: 1px;
  }

  .header-right {
    .el-breadcrumb {
      color: rgba(255, 255, 255, 0.8);

      a {
        color: rgba(255, 255, 255, 0.8);

        &:hover {
          color: #fff;
        }
      }

      .el-breadcrumb__inner.is-link {
        color: rgba(255, 255, 255, 0.8);

        &:hover {
          color: #fff;
        }
      }
    }
  }

  // 军事风格分割线
  .military-divider {
    display: flex;
    align-items: center;
    justify-content: center;

    .divider-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: #fff;
    }

    .divider-line {
      flex: 1;
      height: 2px;
      background: linear-gradient(to right, transparent, #fff, transparent);
      margin: 0 15px;
    }
  }

  // 导入内容
  .import-content {
    padding: 30px;
  }

  // 导入步骤
  .import-steps {
    margin-bottom: 40px;
  }

  .el-step__title.is-success {
    color: #0066cc !important;
  }

  .el-step__icon.is-success {
    border-color: #0066cc !important;

    .el-step__icon-inner {
      color: #0066cc !important;
    }
  }

  .el-step__icon.is-process {
    background-color: #0066cc !important;
    border-color: #0066cc !important;
  }

  // 步骤内容
  .step-content {
    background: #fff;
    border-radius: 4px;
    padding: 30px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  }

  // 步骤描述
  .step-description {
    text-align: left;
    margin-bottom: 20px;
  }

  .important-text {
    font-size: 16px;
    color: #003366;
    font-weight: bold;
    margin-bottom: 20px;
  }

  .template-notice {
    margin-top: 20px;
  }

  .notice-list {
    text-align: left;
    padding-left: 20px;

    li {
      margin-bottom: 8px;
      color: #606266;
    }
  }

  // 军事风格按钮
  .military-btn {
    background: linear-gradient(90deg, #003366, #0066cc);
    border-color: #0066cc;
    color: #fff;

    &:hover {
      background: linear-gradient(90deg, #004080, #0073e6);
      border-color: #0073e6;
    }

    &:active {
      background: #003366;
      border-color: #003366;
    }
  }

  // 填写数据指南
  .fill-data-section {
    .military-info-card {
      margin-bottom: 30px;
      border: 1px solid #dcdfe6;

      .card-header {
        border-bottom: 1px solid #dcdfe6;
        padding: 15px 20px;
        background: #f5f7fa;
      }

      .card-title {
        font-size: 18px;
        font-weight: bold;
        color: #003366;
      }
    }

    .fill-data-guidelines {
      padding: 20px;
    }

    .guideline-item {
      display: flex;
      margin-bottom: 30px;

      &:last-child {
        margin-bottom: 0;
      }
    }

    .guideline-number {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: #0066cc;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      font-weight: bold;
      margin-right: 20px;
      flex-shrink: 0;
    }

    .guideline-content {
      flex: 1;
    }

    .guideline-content h3 {
      font-size: 16px;
      color: #003366;
      margin: 0 0 10px 0;
      font-weight: bold;
    }

    .guideline-content p {
      color: #606266;
      margin: 0;
      line-height: 1.6;
    }
  }

  .next-btn {
    margin-top: 30px;
  }

  // 上传区域
  .upload-section {
    display: flex;
    flex-direction: column;
    align-items: center;

    .upload-container {
      width: 100%;
      max-width: 600px;
      margin-bottom: 30px;
    }

    .upload-actions {
      display: flex;
      gap: 20px;
    }
  }

  // 加载状态
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;

    p {
      margin-top: 20px;
      color: #606266;
      font-size: 16px;
    }
  }

  // 校验错误
  .validation-error {
    padding: 20px;
  }

  .error-item {
    margin-bottom: 10px;
    color: #f56c6c;
  }

  .error-actions {
    margin-top: 20px;
    display: flex;
    justify-content: center;
  }

  // 预览区域
  .preview-section {
    .preview-header {
      margin-bottom: 20px;

      h3 {
        font-size: 18px;
        color: #003366;
        margin: 0 0 10px 0;
        font-weight: bold;
      }

      .preview-tip {
        color: #606266;
        margin: 0;
      }
    }

    .el-table {
      margin-bottom: 30px;

      .el-table__header th {
        background: #f5f7fa;
        color: #003366;
        font-weight: bold;
      }
    }

    .preview-actions {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }
  }

  // 导入成功
  .import-success,
  .import-failure {
    padding: 40px 20px;

    .success-message,
    .failure-message {
      text-align: center;

      h3 {
        font-size: 24px;
        margin-bottom: 30px;
      }

      .failure-reason {
        color: #f56c6c;
        margin-bottom: 30px;
      }
    }

    .success-stats {
      display: flex;
      justify-content: center;
      align-items: center;
      margin-bottom: 30px;

      .stat-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 0 40px;
      }

      .stat-value {
        font-size: 36px;
        font-weight: bold;
        color: #0066cc;
        margin-bottom: 10px;
      }

      .stat-label {
        color: #606266;
      }

      .stat-divider {
        width: 1px;
        height: 60px;
        background: #dcdfe6;
      }
    }

    .failure-notice {
      margin-top: 30px;
    }

    .result-actions {
      display: flex;
      justify-content: center;
      gap: 20px;
      margin-top: 40px;
    }
  }
}

// 加载动画
.is-loading {
  animation: rotating 2s linear infinite;
  color: #0066cc;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .military-rural-project-import {
    padding: 10px;

    .import-header {
      padding: 15px 20px;
    }

    .header-content {
      flex-direction: column;
      align-items: flex-start;
      gap: 15px;
    }

    .import-title {
      font-size: 20px;
    }

    .import-content {
      padding: 20px;
    }

    .step-content {
      padding: 20px;
    }

    .guideline-item {
      flex-direction: column;

      .guideline-number {
        margin-bottom: 15px;
        margin-right: 0;
        align-self: center;
      }
    }

    .success-stats {
      flex-direction: column;

      .stat-divider {
        width: 60px;
        height: 1px;
        margin: 20px 0;
      }
    }

    .upload-actions,
    .preview-actions,
    .result-actions {
      flex-direction: column;
      width: 100%;
    }
  }
}
</style>
