<template>
  <div class="progress-gallery">
    <el-page-header title="返回" @back="goBack">
      <template #content>
        <span class="page-title">项目进度画廊</span>
      </template>
    </el-page-header>

    <el-card class="main-card" shadow="never">
      <!-- 项目基本信息 -->
      <div class="project-info">
        <h2>{{ projectData.name }}</h2>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="项目编号">{{
            projectData.code
          }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{
            projectData.startDate
          }}</el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag :type="getStatusType(projectData.status)">{{
              projectData.status
            }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="负责单位" :span="2">{{
            projectData.unit
          }}</el-descriptions-item>
          <el-descriptions-item label="投资金额"
            >{{ projectData.budget }} 万元</el-descriptions-item
          >
        </el-descriptions>
      </div>

      <!-- 进度相册 -->
      <el-divider content-position="left">
        <h3>项目进度记录</h3>
      </el-divider>

      <ProgressAlbum
        title="项目进度相册"
        :data="progressData"
        :reference-id="projectId"
        type="project"
        @upload="handleUpload"
        @view="handleView"
      />
    </el-card>

    <!-- 大图查看对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      :title="currentViewData?.title"
      width="80%"
      :fullscreen="isFullscreen"
    >
      <div v-if="currentViewType === 'comparison'">
        <ImageComparison
          :before-image="currentViewData?.beforeImage"
          :after-image="currentViewData?.afterImage"
          :before-label="currentViewData?.beforeLabel"
          :after-label="currentViewData?.afterLabel"
          :before-date="currentViewData?.beforeDate"
          :after-date="currentViewData?.afterDate"
          :location="currentViewData?.location"
          :description="currentViewData?.description"
        />
      </div>
      <div v-else-if="currentViewType === 'image'">
        <img
          :src="currentViewData?.url"
          :alt="currentViewData?.title"
          class="full-image"
        />
      </div>
      <template #footer>
        <el-button @click="isFullscreen = !isFullscreen">
          {{ isFullscreen ? "退出全屏" : "全屏" }}
        </el-button>
        <el-button type="primary" @click="viewDialogVisible = false"
          >关闭</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { logger } from "@/utils/logger";
import { safeRouteParam } from "@/composables/useRouterSafe";

import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import ProgressAlbum from "@/components/business/ProgressAlbum.vue";
import ImageComparison from "@/components/business/ImageComparison.vue";
import request from "@/api/request";

const route = useRoute();
const router = useRouter();

const projectId = ref(safeRouteParam(route.params.id));
const viewDialogVisible = ref(false);
const isFullscreen = ref(false);
const currentViewType = ref<"comparison" | "image">("image");
const currentViewData = ref<any>(null);

const projectData = ref({
  name: "示范村基础设施建设项目",
  code: "PRJ-2024-001",
  startDate: "2024-01-15",
  status: "进行中",
  unit: "某军区政治工作部",
  budget: 500,
});

interface ProgressItem {
  date: string;
  title: string;
  description?: string;
  comparisons?: any[];
  images?: any[];
  stats?: Array<{ label: string; value: string | number }>;
}

const progressData = ref<ProgressItem[]>([
  {
    date: "2024-03-15",
    title: "项目启动阶段",
    description: "完成项目规划和前期准备工作",
    comparisons: [
      {
        id: 1,
        title: "村道改造前后对比",
        beforeImage: "/images/progress/before1.jpg",
        afterImage: "/images/progress/after1.jpg",
        beforeLabel: "改造前",
        afterLabel: "改造后",
        beforeDate: "2024-01-15",
        afterDate: "2024-03-15",
        location: "李家村主干道",
        description: "村道从土路改造为水泥路，宽度从3米增加到6米",
        category: "基础设施",
      },
    ],
    stats: [
      { label: "完成进度", value: "20%" },
      { label: "投入资金", value: "100万" },
      { label: "受益人口", value: "300人" },
    ],
  },
  {
    date: "2024-05-20",
    title: "中期建设阶段",
    description: "主要基础设施建设完成",
    comparisons: [
      {
        id: 2,
        title: "文化广场建设",
        beforeImage: "/images/progress/before2.jpg",
        afterImage: "/images/progress/after2.jpg",
        beforeLabel: "建设前",
        afterLabel: "建设后",
        beforeDate: "2024-03-15",
        afterDate: "2024-05-20",
        location: "李家村文化广场",
        description: "新建600平米文化广场，配备健身器材和休闲设施",
        category: "公共设施",
      },
    ],
    images: [
      {
        id: 101,
        url: "/images/progress/detail1.jpg",
        thumbnail: "/images/progress/detail1_thumb.jpg",
        title: "路灯安装",
        category: "基础设施",
      },
      {
        id: 102,
        url: "/images/progress/detail2.jpg",
        thumbnail: "/images/progress/detail2_thumb.jpg",
        title: "绿化工程",
        category: "环境美化",
      },
    ],
    stats: [
      { label: "完成进度", value: "60%" },
      { label: "投入资金", value: "300万" },
      { label: "受益人口", value: "500人" },
    ],
  },
  {
    date: "2024-07-10",
    title: "项目验收阶段",
    description: "项目基本完工，进入验收阶段",
    comparisons: [
      {
        id: 3,
        title: "村容村貌整体提升",
        beforeImage: "/images/progress/before3.jpg",
        afterImage: "/images/progress/after3.jpg",
        beforeLabel: "整治前",
        afterLabel: "整治后",
        beforeDate: "2024-01-15",
        afterDate: "2024-07-10",
        location: "李家村全景",
        description: "通过半年建设，村容村貌焕然一新",
        category: "整体效果",
      },
    ],
    stats: [
      { label: "完成进度", value: "95%" },
      { label: "投入资金", value: "480万" },
      { label: "受益人口", value: "1200人" },
    ],
  },
]);

const goBack = () => {
  router.back();
};

const getStatusType = (status: string) => {
  const typeMap: Record<string, any> = {
    进行中: "primary",
    已完成: "success",
    暂停: "warning",
    计划中: "info",
  };
  return typeMap[status] || "info";
};

const handleUpload = async (uploadData: any) => {
  try {
    // 调用上传API
    const formData = new FormData();
    formData.append("file", uploadData.file);
    formData.append("title", uploadData.title || "");
    formData.append("description", uploadData.description || "");
    formData.append("category", uploadData.category || "progress");
    formData.append("reference_id", projectId.value.toString());
    formData.append("type", "project");

    const response = await request.post("/files/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    if (response?.code === 200) {
      ElMessage.success("上传成功");
      // 刷新数据
      await loadProgressData();
    } else {
      throw new Error(response?.message || "上传失败");
    }
  } catch (error: any) {
    logger.error("Upload failed:", error);
    ElMessage.error(
      error.response?.data?.message || error.message || "上传失败",
    );
  }
};

const handleView = (viewData: any) => {
  currentViewType.value = viewData.type;
  currentViewData.value = viewData.data;
  viewDialogVisible.value = true;
};

const loadProjectData = async () => {
  try {
    const response = await request.get(`/projects/${projectId.value}`);
    if (response) {
      Object.assign(projectData.value, response);
    }
  } catch (error: any) {
    logger.error("Load project data failed:", error);
    ElMessage.warning("加载项目数据失败，使用默认数据");
  }
};

const loadProgressData = async () => {
  try {
    const response = await request.get(
      `/projects/${projectId.value}/progress`,
      {
        params: {
          skip: 0,
          limit: 100,
        },
      },
    );
    if (response) {
      progressData.value = response.items || response || [];
    }
  } catch (error: any) {
    logger.error("Load progress data failed:", error);
    ElMessage.warning("加载进度数据失败，使用默认数据");
  }
};

onMounted(() => {
  // 加载项目数据和进度数据
  loadProjectData();
  loadProgressData();
});
</script>

<style scoped lang="scss">
.progress-gallery {
  padding: 20px;

  .page-title {
    font-size: 18px;
    font-weight: 600;
  }

  .main-card {
    margin-top: 20px;

    .project-info {
      margin-bottom: 30px;

      h2 {
        margin: 0 0 20px 0;
        font-size: 24px;
        color: #303133;
      }
    }
  }

  .full-image {
    width: 100%;
    height: auto;
    display: block;
    border-radius: 4px;
  }
}
</style>
