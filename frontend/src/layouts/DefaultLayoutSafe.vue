<template>
  <div class="layout-container">
    <!-- WCAG 2.1: 跳过导航链接 -->
    <a href="#main-content" class="skip-link">跳到主内容</a>

    <el-aside :width="isCollapsed ? '64px' : '220px'" class="layout-aside" role="navigation" aria-label="主导航">
      <div class="aside-header">
        <img src="/images/badges/badge.png" class="app-logo" alt="系统标识" />
        <span v-show="!isCollapsed" class="app-title">帮扶管理信息系统</span>
      </div>
      <el-scrollbar>
        <el-menu
          :default-active="route.path"
          :collapse="isCollapsed"
          router
          class="aside-menu"
          background-color="#1a3c2a"
          text-color="#c8d6c4"
          active-text-color="#d4af37"
        >
          <el-menu-item index="/dashboard">
            <el-icon><HomeFilled /></el-icon>
            <template #title>工作台</template>
          </el-menu-item>

          <el-sub-menu index="village-group">
            <template #title><el-icon><Location /></el-icon><span>帮扶村管理</span></template>
            <el-menu-item index="/supported-villages">帮扶村</el-menu-item>
            <el-menu-item index="/supported-villages/yearly">年度概览</el-menu-item>
            <el-menu-item index="/data-entry">数据录入</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="project-group">
            <template #title><el-icon><Folder /></el-icon><span>帮扶项目</span></template>
            <el-menu-item index="/projects">项目列表</el-menu-item>
            <el-menu-item index="/projects/management">项目管控</el-menu-item>
            <el-menu-item index="/projects/import">项目导入</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="fund-group">
            <template #title><el-icon><Money /></el-icon><span>经费管理</span></template>
            <el-menu-item index="/funds">经费总览</el-menu-item>
            <el-menu-item index="/funds/analysis">经费分析</el-menu-item>
            <el-menu-item index="/funds/budget">预算管理</el-menu-item>
            <el-menu-item index="/funds/contract">合同管理</el-menu-item>
            <el-menu-item index="/funds/anomaly">异常资金</el-menu-item>
            <el-menu-item index="/funds/lifecycle">资金周期</el-menu-item>
            <el-menu-item index="/funds/apply">经费申请</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="school-group">
            <template #title><el-icon><School /></el-icon><span>帮扶学校</span></template>
            <el-menu-item index="/schools">学校列表</el-menu-item>
            <el-menu-item index="/schools/analysis">学校分析</el-menu-item>
          </el-sub-menu>

          <el-menu-item index="/policies">
            <el-icon><Document /></el-icon>
            <template #title>帮扶政策</template>
          </el-menu-item>

          <el-sub-menu index="rural-group">
            <template #title><el-icon><Stamp /></el-icon><span>乡村振兴</span></template>
            <el-menu-item index="/rural-works">工作首页</el-menu-item>
            <el-menu-item index="/rural-works/list">工作列表</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="approval-group">
            <template #title><el-icon><Checked /></el-icon><span>审批管理</span></template>
            <el-menu-item index="/approval">审批概览</el-menu-item>
            <el-menu-item index="/approval/pending">待审批</el-menu-item>
            <el-menu-item index="/approval/my">我的申请</el-menu-item>
            <el-menu-item index="/approval/history">审批历史</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="data-group">
            <template #title><el-icon><DataAnalysis /></el-icon><span>数据分析</span></template>
            <el-menu-item index="/data-analysis">分析首页</el-menu-item>
            <el-menu-item index="/data-analysis/dashboard">分析仪表板</el-menu-item>
            <el-menu-item index="/data-analysis/map">地图可视化</el-menu-item>
            <el-menu-item index="/data-analysis/assessment">成效评估</el-menu-item>
          </el-sub-menu>

          <el-menu-item index="/work-calendar">
            <el-icon><Calendar /></el-icon>
            <template #title>工作日历</template>
          </el-menu-item>

          <el-sub-menu index="datasync-group">
            <template #title><el-icon><Connection /></el-icon><span>数据管理</span></template>
            <el-menu-item index="/data-management">数据概览</el-menu-item>
            <el-menu-item index="/data-management/backup">数据备份</el-menu-item>
            <el-menu-item index="/data-management/logs">操作日志</el-menu-item>
            <el-menu-item index="/data-sync/export">数据导出</el-menu-item>
            <el-menu-item index="/data-sync/import">数据导入</el-menu-item>
            <el-menu-item index="/data-package">数据包管理</el-menu-item>
          </el-sub-menu>

          <el-menu-item index="/organization">
            <el-icon><OfficeBuilding /></el-icon>
            <template #title>组织机构</template>
          </el-menu-item>

          <el-sub-menu index="system-group">
            <template #title><el-icon><Setting /></el-icon><span>系统管理</span></template>
            <el-menu-item index="/system/users">用户管理</el-menu-item>
            <el-menu-item index="/system/roles">角色管理</el-menu-item>
            <el-menu-item index="/system/audit">审计管理</el-menu-item>
            <el-menu-item index="/system/backup">备份管理</el-menu-item>
            <el-menu-item index="/system/config">系统配置</el-menu-item>
            <el-menu-item index="/system/monitoring">系统监控</el-menu-item>
            <el-menu-item index="/system/health">系统健康</el-menu-item>
            <el-menu-item index="/admin/machine-code">机器码管理</el-menu-item>
          </el-sub-menu>

          <el-menu-item index="/message">
            <el-icon><Message /></el-icon>
            <template #title>消息中心</template>
          </el-menu-item>
        </el-menu>
      </el-scrollbar>
    </el-aside>

    <el-container class="layout-main">
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapsed = !isCollapsed">
            <component :is="isCollapsed ? Expand : Fold" />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentRoute">{{ currentRoute }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="28">
                <el-icon><User /></el-icon>
              </el-avatar>
              <span class="username">{{ username }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="change-password">修改密码</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="layout-content" id="main-content" role="main" aria-label="主内容区">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>

      <el-footer class="layout-footer" height="32px">
        <span>帮扶管理信息系统 v1.2.0</span>
      </el-footer>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  HomeFilled, Folder, Money, Location, DataAnalysis, Setting,
  Expand, Fold, User, School, Document, Stamp, Checked, Connection,
  OfficeBuilding, Message, Calendar,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isCollapsed = ref(false)
const username = computed(() => authStore.user?.username || authStore.user?.full_name || '管理员')
const currentRoute = computed(() => (route.meta?.title as string) || '')

function handleCommand(command: string) {
  switch (command) {
    case 'profile': router.push('/profile'); break
    case 'change-password': router.push('/change-password'); break
    case 'logout':
      authStore.logout()
      router.push('/login')
      break
  }
}
</script>

<style scoped>
.layout-container { display: flex; height: 100vh; overflow: hidden; }
.layout-aside { background-color: #1a3c2a; transition: width 0.3s; overflow: hidden; }
.aside-header { height: 56px; display: flex; align-items: center; justify-content: center; padding: 0 12px; border-bottom: 1px solid #2d5a3f; gap: 0; }
.app-title { color: #d4af37; font-size: 20px; font-weight: 800; white-space: nowrap; letter-spacing: 2px; margin-left: 10px; }
.app-logo { width: 32px; height: 32px; flex-shrink: 0; }
.aside-menu { border-right: none; }
.layout-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.layout-header {
  height: 50px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 16px; border-bottom: 2px solid #2d5a3f;
  background: linear-gradient(135deg, #1b4332, #2d6a4f, #40916c);
  color: #ffffff;
}
.header-left { display: flex; align-items: center; gap: 12px; }
.collapse-btn { font-size: 20px; cursor: pointer; color: #c8d6c4; }
.collapse-btn:hover { color: #d4af37; }
/* 面包屑导航 — 金黄/白色 */
.layout-header :deep(.el-breadcrumb__inner) { color: #c8d6c4; font-weight: 500; }
.layout-header :deep(.el-breadcrumb__inner.is-link:hover) { color: #d4af37; }
.layout-header :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) { color: #d4af37; font-weight: 700; }
.layout-header :deep(.el-breadcrumb__separator) { color: #6a9c7a; }
.header-right { display: flex; align-items: center; }
.user-info { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.username { font-size: 14px; color: #c8d6c4; }
.layout-content { flex: 1; overflow: auto; background: #f0f4f0; padding: 16px; }
.layout-footer {
  display: flex; align-items: center; justify-content: center; font-size: 12px;
  color: #8fbc8f; border-top: 2px solid #2d5a3f; background: #1a3c2a;
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.skip-link { position:absolute; top:-100px; left:0; z-index:1000; padding:8px 16px;
  background:#d4af37; color:#1a3c2a; font-weight:700; border-radius:0 0 4px 0;
  transition:top .2s; }
.skip-link:focus { top:0; }
</style>
