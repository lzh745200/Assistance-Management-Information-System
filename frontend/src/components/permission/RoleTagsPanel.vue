<template>
  <div class="role-tags-panel">
    <el-alert
      type="info"
      :closable="false"
      style="margin-bottom: 16px"
    >
      为用户分配 RBAC 角色。角色包含一组预定义的权限。
      用户会继承所分配角色的所有权限。
    </el-alert>

    <!-- 当前已分配的角色 -->
    <div class="section">
      <h4>已分配角色</h4>
      <div v-if="assignedRoles.length === 0" class="empty-hint">
        暂未分配任何 RBAC 角色
      </div>
      <el-tag
        v-for="role in assignedRoles"
        :key="role.id"
        closable
        :type="role.is_system ? 'primary' : 'success'"
        size="large"
        style="margin: 4px"
        @close="removeRole(role)"
      >
        {{ role.name }}
        <el-tooltip
          v-if="role.description"
          :content="role.description"
          placement="top"
        >
          <el-icon style="margin-left: 4px"><InfoFilled /></el-icon>
        </el-tooltip>
        <span v-if="role.is_system" style="margin-left: 4px; opacity: 0.7">
          (系统)
        </span>
      </el-tag>
    </div>

    <el-divider />

    <!-- 可分配的角色 -->
    <div class="section">
      <h4>可选角色</h4>
      <div v-if="availableRoles.length === 0" class="empty-hint">
        暂无可分配的角色
      </div>
      <el-select
        v-model="selectedRoleId"
        placeholder="选择要分配的角色"
        filterable
        style="width: 320px"
        @change="assignRole"
      >
        <el-option
          v-for="role in availableRoles"
          :key="role.id"
          :label="`${role.name}${role.description ? ' - ' + role.description : ''}`"
          :value="role.id"
        />
      </el-select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { InfoFilled } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import request from "@/api/request";

interface RbacRole {
  id: string;
  name: string;
  description?: string;
  is_system?: boolean;
  is_active?: boolean;
  priority?: number;
  permissions?: string[];
}

const props = defineProps<{
  userId: number;
  allRoles?: RbacRole[];
}>();

const emit = defineEmits<{
  assigned: [];
  removed: [];
}>();

const assignedRoles = ref<RbacRole[]>([]);
const selectedRoleId = ref("");

const availableRoles = computed(() => {
  if (!props.allRoles) return [];
  const assignedIds = new Set(assignedRoles.value.map((r) => r.id));
  return props.allRoles.filter(
    (r) => r.is_active !== false && !assignedIds.has(r.id),
  );
});

async function loadAssignedRoles() {
  try {
    const res = await request.get(`/rbac/user/${props.userId}/roles`);
    assignedRoles.value = (res.data?.data || res.data || []) as RbacRole[];
  } catch {
    assignedRoles.value = [];
  }
}

async function assignRole(roleId: string) {
  if (!roleId) return;
  try {
    await request.post("/rbac/assign/role", {
      user_id: props.userId,
      role_id: roleId,
    });
    selectedRoleId.value = "";
    await loadAssignedRoles();
    emit("assigned");
    ElMessage.success("角色分配成功");
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || "角色分配失败");
  }
}

async function removeRole(role: RbacRole) {
  try {
    await request.delete("/rbac/revoke/role", {
      data: { user_id: props.userId, role_id: role.id },
    });
    await loadAssignedRoles();
    emit("removed");
    ElMessage.success(`角色「${role.name}」已移除`);
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || "角色移除失败");
  }
}

// 暴露加载方法供父组件调用
defineExpose({ loadAssignedRoles, assignedRoles });
</script>

<style scoped lang="scss">
.role-tags-panel {
  .section h4 {
    margin: 0 0 8px 0;
  }
  .empty-hint {
    color: var(--el-text-color-placeholder);
    font-size: 13px;
  }
}
</style>
