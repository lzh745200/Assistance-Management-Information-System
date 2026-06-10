<template>
  <div class="security-monitor">
    <el-card>
      <template #header>
        <div class="monitor-header">
          <h3>安全监控面板</h3>
          <el-tag :type="securityStatus.type">{{ securityStatus.text }}</el-tag>
        </div>
      </template>

      <el-table :data="securityEvents" height="400px">
        <el-table-column prop="time" label="时间" width="180" />
        <el-table-column prop="type" label="事件类型" width="120" />
        <el-table-column prop="level" label="安全等级" width="100">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level)">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="详细信息" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="handleDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script lang="ts" setup>
// @ts-nocheck
import { ref, onMounted, onUnmounted } from "vue";
import { ElMessageBox } from "element-plus";
import { SecurityLevel } from "@/utils/security";

type TagType = "success" | "info" | "warning" | "danger" | "primary";

interface SecurityEvent {
  time: string;
  type: string;
  level: SecurityLevel;
  message: string;
  details?: string;
}

const securityEvents = ref<SecurityEvent[]>([]);
const securityStatus = ref<{ type: TagType; text: string }>({
  type: "success",
  text: "安全状态正常",
});

const getLevelType = (level: SecurityLevel) => {
  switch (level) {
    case SecurityLevel.TOP_SECRET:
      return "danger";
    case SecurityLevel.SECRET:
      return "warning";
    case SecurityLevel.CONFIDENTIAL:
      return "primary";
    default:
      return "info";
  }
};

const fetchSecurityEvents = async () => {
  // 模拟获取安全事件数据
  securityEvents.value = [
    {
      time: new Date().toLocaleString(),
      type: "登录成功",
      level: SecurityLevel.INTERNAL,
      message: "管理员从IP 192.168.1.100登录系统",
    },
    {
      time: new Date(Date.now() - 1000 * 60 * 5).toLocaleString(),
      type: "数据访问",
      level: SecurityLevel.CONFIDENTIAL,
      message: "访问了机密级数据: 作战计划",
    },
    {
      time: new Date(Date.now() - 1000 * 60 * 30).toLocaleString(),
      type: "权限变更",
      level: SecurityLevel.SECRET,
      message: "用户权限提升为机密级",
    },
  ];
};

const handleDetail = (event: SecurityEvent) => {
  ElMessageBox.alert(event.details || event.message, "安全事件详情");
};

onMounted(() => {
  fetchSecurityEvents();
  // 模拟实时监控
  const _monitorTimer = setInterval(() => {
    // 实际项目中调用API获取最新安全事件（Demo模式不生成假数据）
    // Demo mode: no fake data generation
  }, 5000);

  onUnmounted(() => {
    clearInterval(_monitorTimer);
  });
});
</script>

<style scoped>
.security-monitor {
  margin: 20px;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
