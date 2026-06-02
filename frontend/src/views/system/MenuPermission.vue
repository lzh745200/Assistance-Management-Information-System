<template>
  <div class="menu-permission-page">
    <el-card>
      <template #header>
        <div class="page-header">
          <span class="page-title">菜单权限管理</span>
          <el-space>
            <el-button :loading="exporting" @click="handleExportConfig">
              导出配置
            </el-button>
            <el-upload
              :before-upload="handleImportConfig"
              :show-file-list="false"
              accept=".json"
            >
              <el-button :loading="importing">导入配置</el-button>
            </el-upload>
          </el-space>
        </div>
      </template>

      <el-alert type="info" :closable="false" style="margin-bottom: 16px">
        在此为用户配置可见菜单。留空表示继承角色默认菜单；清空表示无菜单。
        修改后用户刷新页面即可生效。
      </el-alert>

      <el-row :gutter="16">
        <!-- 左侧：用户选择 -->
        <el-col :span="8">
          <div class="user-panel">
            <el-input
              v-model="userSearch"
              placeholder="搜索用户名/姓名"
              prefix-icon="Search"
              clearable
              style="margin-bottom: 12px"
            />
            <el-scrollbar height="calc(100vh - 320px)">
              <div
                v-for="user in filteredUsers"
                :key="user.id"
                class="user-item"
                :class="{ active: selectedUserId === user.id }"
                @click="selectUser(user)"
              >
                <div class="user-info">
                  <span class="username">{{ user.username }}</span>
                  <span class="full-name">{{
                    user.full_name || user.name
                  }}</span>
                </div>
                <div class="user-meta">
                  <el-tag size="small">{{ getRoleLabel(user.role) }}</el-tag>
                </div>
              </div>
              <el-empty
                v-if="filteredUsers.length === 0"
                description="暂无匹配用户"
                :image-size="60"
              />
            </el-scrollbar>
          </div>
        </el-col>

        <!-- 右侧：菜单配置 -->
        <el-col :span="16">
          <div v-if="selectedUser" class="menu-panel">
            <div class="menu-panel-header">
              <span>
                当前配置用户：
                <strong>{{ selectedUser.username }}</strong>
                ({{ getRoleLabel(selectedUser.role) }})
              </span>
              <el-space>
                <el-button
                  size="small"
                  :disabled="!selectedUser.is_customized"
                  @click="resetToRoleDefault"
                >
                  恢复角色默认
                </el-button>
                <el-button
                  type="primary"
                  size="small"
                  :loading="saving"
                  @click="saveConfig"
                >
                  保存配置
                </el-button>
              </el-space>
            </div>

            <!-- 角色默认菜单提示 -->
            <el-alert
              v-if="selectedUser.is_customized"
              type="info"
              :closable="false"
              style="margin: 12px 0"
            >
              当前为自定义配置。角色默认包含
              {{ selectedUser.role_default_keys?.length || 0 }} 个菜单。
            </el-alert>

            <!-- 角色默认菜单展示 -->
            <div class="role-default-info">
              <span class="label">角色默认菜单：</span>
              <el-tag
                v-for="key in selectedUser.role_default_keys"
                :key="key"
                size="small"
                style="margin: 2px"
              >
                {{ getMenuLabel(key) }}
              </el-tag>
            </div>

            <!-- 菜单树选择 -->
            <el-tree
              ref="menuTreeRef"
              :data="menuTreeData"
              :props="treeProps"
              show-checkbox
              node-key="key"
              :default-checked-keys="checkedMenuKeys"
              :default-expanded-keys="expandedKeys"
              @check="handleTreeCheck"
            >
              <template #default="{ data }">
                <span class="tree-node">
                  <span class="menu-label">{{ data.label }}</span>
                  <span v-if="data.path" class="menu-path">{{
                    data.path
                  }}</span>
                </span>
              </template>
            </el-tree>
          </div>

          <el-empty v-else description="请从左侧选择用户" :image-size="80" />
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { MENU_CONFIG, getAllMenuKeys } from "@/config/menu-config";
import api from "@/utils/request";

interface User {
  id: number;
  username: string;
  full_name?: string;
  name?: string;
  role: string;
  is_active: boolean;
}

interface UserMenuConfig {
  user_id: number;
  username: string;
  full_name?: string;
  role: string;
  mode: "custom" | "role_default";
  menu_keys: string[];
  is_customized: boolean;
  role_default_keys: string[];
}

interface MenuNode {
  key: string;
  label: string;
  path?: string;
  children?: MenuNode[];
}

const userSearch = ref("");
const users = ref<User[]>([]);
const selectedUserId = ref<number | null>(null);
const selectedUser = ref<UserMenuConfig | null>(null);
const checkedMenuKeys = ref<string[]>([]);
const saving = ref(false);
const exporting = ref(false);
const importing = ref(false);
const menuTreeRef = ref();

const treeProps = {
  label: "label",
  children: "children",
};

const allMenuKeys = getAllMenuKeys();
const expandedKeys = computed(() => allMenuKeys);

const filteredUsers = computed(() => {
  if (!userSearch.value) return users.value;
  const search = userSearch.value.toLowerCase();
  return users.value.filter(
    (u) =>
      u.username.toLowerCase().includes(search) ||
      (u.full_name || u.name || "").toLowerCase().includes(search),
  );
});

const menuTreeData = computed<MenuNode[]>(() => {
  return MENU_CONFIG as MenuNode[];
});

function getRoleLabel(role: string): string {
  const roleMap: Record<string, string> = {
    super_admin: "超级管理员",
    admin: "管理员",
    approval_leader: "审批领导",
    manager: "管理人员",
    operator: "操作员",
    viewer: "查看者",
  };
  return roleMap[role] || role;
}

function getMenuLabel(key: string): string {
  function findLabel(items: MenuNode[], k: string): string | null {
    for (const item of items) {
      if (item.key === k) return item.label;
      if (item.children) {
        const found = findLabel(item.children, k);
        if (found) return found;
      }
    }
    return null;
  }
  return findLabel(menuTreeData.value, key) || key;
}

async function loadUsers() {
  try {
    const res = await api.get<{ data?: User[] }>("/users");
    if (res.data?.data) {
      users.value = res.data.data.filter((u) => u.is_active !== false);
    }
  } catch (error) {
    ElMessage.error("加载用户列表失败");
  }
}

async function selectUser(user: User) {
  selectedUserId.value = user.id;
  try {
    const res = await api.get<{
      data?: UserMenuConfig;
    }>(`/menus/user-menus/${user.id}`);
    if (res.data?.data) {
      selectedUser.value = res.data.data;
      checkedMenuKeys.value = res.data.data.menu_keys || [];
    }
  } catch (error) {
    ElMessage.error(`加载用户 ${user.username} 的菜单配置失败`);
    selectedUser.value = null;
  }
}

function handleTreeCheck() {
  if (!menuTreeRef.value) return;
  checkedMenuKeys.value = menuTreeRef.value.getCheckedKeys() as string[];
}

async function saveConfig() {
  if (!selectedUser.value) return;

  saving.value = true;
  try {
    const menu_keys = checkedMenuKeys.value;
    await api.put(`/menus/user-menus/${selectedUser.value.user_id}`, {
      menu_keys,
    });
    ElMessage.success("菜单权限设置成功");
    // 重新加载用户配置
    await selectUser({
      id: selectedUser.value.user_id,
      username: selectedUser.value.username,
      role: selectedUser.value.role,
      is_active: true,
    });
  } catch (error) {
    ElMessage.error("保存失败");
  } finally {
    saving.value = false;
  }
}

async function resetToRoleDefault() {
  if (!selectedUser.value) return;

  try {
    await ElMessageBox.confirm(
      "确定要恢复该用户的角色默认菜单吗？",
      "确认恢复",
      { type: "warning" },
    );

    await api.put(`/menus/user-menus/${selectedUser.value.user_id}`, {
      menu_keys: null,
    });
    ElMessage.success("已恢复角色默认菜单");
    // 重新加载用户配置
    await selectUser({
      id: selectedUser.value.user_id,
      username: selectedUser.value.username,
      role: selectedUser.value.role,
      is_active: true,
    });
  } catch (error: any) {
    if (error !== "cancel") {
      ElMessage.error("操作失败");
    }
  }
}

function handleExportConfig() {
  if (!selectedUser.value) {
    ElMessage.warning("请先选择一个用户");
    return;
  }

  exporting.value = true;
  try {
    const config = {
      version: "1.0",
      exported_at: new Date().toISOString(),
      user: {
        user_id: selectedUser.value.user_id,
        username: selectedUser.value.username,
        role: selectedUser.value.role,
        menu_keys: checkedMenuKeys.value,
      },
    };

    const blob = new Blob([JSON.stringify(config, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `menu-config-${selectedUser.value.username}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    ElMessage.success("配置已导出");
  } catch (error) {
    ElMessage.error("导出失败");
  } finally {
    exporting.value = false;
  }
}

async function handleImportConfig(file: File) {
  importing.value = true;
  try {
    const text = await file.text();
    const config = JSON.parse(text);

    if (!config.user?.user_id || !config.user?.menu_keys) {
      ElMessage.error("无效的配置文件格式");
      return;
    }

    const { user_id, menu_keys } = config.user;

    // 如果当前选中了用户，可以选择导入到当前用户或其他用户
    if (!selectedUser.value || selectedUser.value.user_id !== user_id) {
      // 尝试选中配置中的用户
      const user = users.value.find((u) => u.id === user_id);
      if (user) {
        await selectUser(user);
      } else {
        ElMessage.error(`找不到用户 ID: ${user_id}`);
        return;
      }
    }

    // 更新选中的菜单
    checkedMenuKeys.value = menu_keys;
    if (menuTreeRef.value) {
      menuTreeRef.value.setCheckedKeys(menu_keys);
    }

    // 保存
    await api.put(`/menus/user-menus/${user_id}`, { menu_keys });

    // 重新加载
    await selectUser({
      id: user_id,
      username: config.user.username,
      role: config.user.role,
      is_active: true,
    });

    ElMessage.success("配置已导入并保存");
  } catch (error: any) {
    ElMessage.error(`导入失败: ${error.message || "格式错误"}`);
  } finally {
    importing.value = false;
  }
  return false; // 阻止默认上传行为
}

onMounted(async () => {
  await loadUsers();
});
</script>

<style scoped>
.menu-permission-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: #1b4332;
}

.user-panel {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px;
}

.user-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.user-item:hover {
  background: #fff;
  border-color: #1b4332;
}

.user-item.active {
  background: #fff;
  border-color: #1b4332;
  box-shadow: 0 2px 8px rgba(27, 67, 50, 0.15);
}

.user-info {
  display: flex;
  flex-direction: column;
}

.username {
  font-weight: 500;
  color: #303133;
}

.full-name {
  font-size: 12px;
  color: #909399;
}

.user-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.menu-panel {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
}

.menu-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.role-default-info {
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #fff;
  border-radius: 4px;
  font-size: 13px;
}

.role-default-info .label {
  color: #606266;
  margin-right: 8px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
}

.menu-label {
  color: #303133;
}

.menu-path {
  color: #909399;
  font-size: 12px;
}
</style>
