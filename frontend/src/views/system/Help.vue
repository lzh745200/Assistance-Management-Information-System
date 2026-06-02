<template>
  <div class="help-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">帮助文档</h2>
        <p class="page-desc">系统使用指南和常见问题解答</p>
      </div>
      <el-input
        v-model="searchKeyword"
        placeholder="搜索帮助内容..."
        clearable
        style="width: 300px"
        @input="onSearch"
      >
        <template #prefix
          ><el-icon><Search /></el-icon
        ></template>
      </el-input>
    </div>

    <div class="help-layout">
      <!-- 左侧目录 -->
      <el-card class="toc-panel">
        <template #header
          ><span style="font-weight: 600; color: #1b4332">目录</span></template
        >
        <el-menu :default-active="activeSection" @select="scrollToSection">
          <el-menu-item
            v-for="section in filteredSections"
            :key="section.id"
            :index="section.id"
          >
            <el-icon v-if="section.icon"
              ><component :is="section.icon"
            /></el-icon>
            <span>{{ section.title }}</span>
          </el-menu-item>
        </el-menu>
      </el-card>

      <!-- 右侧内容 -->
      <div class="content-panel">
        <el-card
          v-for="section in filteredSections"
          :id="section.id"
          :key="section.id"
          class="help-section"
        >
          <template #header>
            <div class="section-header">
              <el-icon v-if="section.icon" :size="20" color="#1b4332"
                ><component :is="section.icon"
              /></el-icon>
              <span class="section-title">{{ section.title }}</span>
            </div>
          </template>
          <!-- eslint-disable vue/no-v-html -->
          <div
            class="section-content"
            v-html="safeSectionContent(section.content)"
          />
          <!-- eslint-enable vue/no-v-html -->
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import {
  Search,
  HomeFilled,
  Location,
  School,
  Money,
  Folder,
  Document,
  Sunny,
  Stamp,
  DataAnalysis,
  Setting,
  Download,
  MapLocation,
  QuestionFilled,
} from "@element-plus/icons-vue";
import { sanitizeHtml } from "@/utils/sanitize";

/** XSS 防护：即使当前内容是静态硬编码，也统一过 sanitize 以防止后续改为动态加载时遗漏 */
function safeSectionContent(html: string): string {
  return sanitizeHtml(html);
}

// Ensure dynamic icons are available
defineExpose({
  Search,
  HomeFilled,
  Location,
  School,
  Money,
  Folder,
  Document,
  Sunny,
  Stamp,
  DataAnalysis,
  Setting,
  Download,
  MapLocation,
  QuestionFilled,
});

const searchKeyword = ref("");
const activeSection = ref("overview");

interface HelpSection {
  id: string;
  title: string;
  icon: string;
  content: string;
}

const sections: HelpSection[] = [
  {
    id: "overview",
    title: "系统概述",
    icon: "HomeFilled",
    content: `
      <p>帮扶管理信息系统是一套面向军队帮扶工作的综合管理平台，支持离线单机运行。</p>
      <p><strong>主要功能模块：</strong></p>
      <ul>
        <li>帮扶村管理 — 管理帮扶村基本信息、年度数据</li>
        <li>帮扶学校管理 — 管理援建学校、助学兴教项目</li>
        <li>经费管理 — 预算编制、经费收支、分析报表</li>
        <li>帮扶项目管理 — 项目全生命周期管理</li>
        <li>政策法规 — 政策文件管理、在线预览</li>
        <li>乡村工作 — 年度任务分配、填报、审批</li>
        <li>审批管理 — 流程审批、我的申请、审批总览</li>
        <li>数据分析 — 统计仪表板、地图可视化、工作分析</li>
        <li>报表导出 — 多格式导出（Excel/PDF/Word）</li>
      </ul>
    `,
  },
  {
    id: "login",
    title: "登录与账号",
    icon: "Setting",
    content: `
      <p><strong>首次登录：</strong>使用管理员分配的账号密码登录系统。</p>
      <p><strong>修改密码：</strong>点击右上角头像 → 修改密码。</p>
      <p><strong>角色说明：</strong></p>
      <ul>
        <li><strong>超级管理员</strong> — 系统配置、用户管理、备份恢复</li>
        <li><strong>管理员</strong> — 数据管理、审批总览</li>
        <li><strong>操作员</strong> — 数据录入、任务填报</li>
        <li><strong>审批领导</strong> — 审批操作</li>
        <li><strong>查看者</strong> — 只读查看</li>
      </ul>
    `,
  },
  {
    id: "village",
    title: "帮扶村管理",
    icon: "Location",
    content: `
      <p>进入「帮扶村管理」菜单，可查看所有帮扶村列表。</p>
      <p><strong>新增帮扶村：</strong>点击「新增帮扶村」按钮，填写村名、所属县市、帮扶单位等信息。</p>
      <p><strong>年度数据管理：</strong>在帮扶村详情页，点击「年度数据管理」Tab，可录入当年人口、收入、产业等数据。</p>
      <p><strong>批量导入：</strong>通过「数据批量导入」页面，下载标准模板，填写后上传导入。</p>
    `,
  },
  {
    id: "school",
    title: "帮扶学校管理",
    icon: "School",
    content: `
      <p>管理援建学校信息，包括基本信息、助学兴教项目和资助学生。</p>
      <p><strong>助学兴教项目：</strong>在学校详情页，点击「助学兴教项目」Tab 管理项目。</p>
      <p><strong>资助学生管理：</strong>在学校详情页，点击「资助学生管理」Tab 录入和管理资助学生信息。</p>
    `,
  },
  {
    id: "funds",
    title: "经费管理",
    icon: "Money",
    content: `
      <p>经费管理支持预算编制、经费收支记录和分析报表。</p>
      <p><strong>新增经费记录：</strong>点击「新增经费记录」，填写名称、金额、类型等。</p>
      <p><strong>预算管理：</strong>进入「预算管理」页面编制年度预算。</p>
      <p><strong>经费分析：</strong>查看各类经费的投入趋势和分类分析图表。</p>
    `,
  },
  {
    id: "policy",
    title: "政策法规",
    icon: "Document",
    content: `
      <p>管理政策法规文件，支持分类浏览、搜索和在线预览。</p>
      <p><strong>上传政策文件：</strong>点击「新增政策」，填写标题、文号、发布日期，并上传附件（支持 PDF/Word/图片）。</p>
      <p><strong>在线预览：</strong>在政策详情页可直接预览 PDF 和 Word 文件。</p>
      <p><strong>筛选：</strong>支持按年度、文号快速筛选。</p>
    `,
  },
  {
    id: "ruralwork",
    title: "乡村工作",
    icon: "Sunny",
    content: `
      <p>乡村工作模块支持年度任务分配、下级填报、审批和报告生成的完整闭环。</p>
      <p><strong>任务分配（上级）：</strong>创建年度工作任务，选择下级单位进行分配。</p>
      <p><strong>任务填报（下级）：</strong>查看待办任务，填写完成情况并上传佐证材料。</p>
      <p><strong>年度报告：</strong>自动汇总任务完成情况，生成 PDF 报告。</p>
    `,
  },
  {
    id: "approval",
    title: "审批管理",
    icon: "Stamp",
    content: `
      <p>审批管理分为三个视图：</p>
      <ul>
        <li><strong>我的申请</strong> — 查看自己提交的审批单及其状态</li>
        <li><strong>待办审批</strong> — 审批领导查看和处理待审批任务</li>
        <li><strong>审批总览</strong>（管理员） — 查看所有审批数据，设置超时提醒规则</li>
      </ul>
      <p><strong>批量审批：</strong>在待办审批列表中勾选多条记录，点击批量审批。</p>
    `,
  },
  {
    id: "analytics",
    title: "数据分析",
    icon: "DataAnalysis",
    content: `
      <p>数据分析模块提供多维度的数据统计和可视化功能。</p>
      <ul>
        <li><strong>分析仪表板</strong> — ECharts 图表展示关键指标</li>
        <li><strong>工作分析</strong> — 工作完成情况分析（Chart.js 图表 + 明细表）</li>
        <li><strong>地图可视化</strong> — Leaflet 离线地图展示帮扶点分布，支持距离和车程计算</li>
        <li><strong>数据统计分析</strong> — 投入分析、分类统计、地区分布等多维报表</li>
      </ul>
    `,
  },
  {
    id: "export",
    title: "报表导出",
    icon: "Download",
    content: `
      <p>报表导出中心支持将各类数据导出为 Excel、PDF 或 Word 格式。</p>
      <p><strong>操作步骤：</strong></p>
      <ol>
        <li>选择报表类型（帮扶村汇总、资金分析、项目进度等）</li>
        <li>配置时间范围、数据范围和导出格式</li>
        <li>点击「开始导出」</li>
        <li>在导出历史中下载文件</li>
      </ol>
      <p><strong>打印预览：</strong>点击「打印预览」可在浏览器中预览A4排版效果。</p>
    `,
  },
  {
    id: "backup",
    title: "备份与恢复",
    icon: "Setting",
    content: `
      <p>系统支持手动备份和定时自动备份。</p>
      <p><strong>手动备份：</strong>进入「备份管理」页面，点击「立即备份」。</p>
      <p><strong>定时备份：</strong>配置备份周期（每日/每周/每月），系统会自动执行。</p>
      <p><strong>恢复：</strong>选择历史备份文件进行恢复。</p>
      <p><strong>注意：</strong>系统启动时会自动检查数据库完整性，如检测到异常会尝试从最近备份恢复。</p>
    `,
  },
  {
    id: "faq",
    title: "常见问题",
    icon: "QuestionFilled",
    content: `
      <p><strong>Q: 系统打不开怎么办？</strong></p>
      <p>A: 确保后端服务已启动。查看任务栏托盘区是否有系统图标。如服务未启动，双击桌面快捷方式重新打开。</p>
      <p><strong>Q: 数据如何备份？</strong></p>
      <p>A: 进入系统管理 → 备份管理，可进行手动备份。建议配置每日自动备份。</p>
      <p><strong>Q: 导入数据失败怎么办？</strong></p>
      <p>A: 请确保使用系统提供的标准模板，所有必填字段已填写。查看上传结果中的错误详情。</p>
      <p><strong>Q: 地图不显示怎么办？</strong></p>
      <p>A: 系统支持离线地图。如无离线瓦片，会自动使用 ECharts 矢量地图作为回退。</p>
    `,
  },
];

const filteredSections = computed(() => {
  if (!searchKeyword.value.trim()) return sections;
  const keyword = searchKeyword.value.toLowerCase();
  return sections.filter(
    (s) =>
      s.title.toLowerCase().includes(keyword) ||
      s.content.toLowerCase().includes(keyword),
  );
});

function onSearch() {
  // 搜索时自动跳转到第一个匹配的section
  if (filteredSections.value.length > 0) {
    activeSection.value = filteredSections.value[0].id;
  }
}

function scrollToSection(id: string) {
  activeSection.value = id;
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}
</script>

<style scoped>
.help-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
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
  margin: 0 0 4px;
}
.page-desc {
  font-size: 14px;
  color: #666;
  margin: 0;
}
.help-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 16px;
  align-items: start;
}
.toc-panel {
  position: sticky;
  top: 16px;
}
.content-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.help-section {
  scroll-margin-top: 16px;
}
.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1b4332;
}
.section-content {
  line-height: 1.8;
  color: #333;
}
.section-content :deep(ul),
.section-content :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}
.section-content :deep(li) {
  margin-bottom: 4px;
}
.section-content :deep(strong) {
  color: #1b4332;
}
.section-content :deep(p) {
  margin: 8px 0;
}
</style>
