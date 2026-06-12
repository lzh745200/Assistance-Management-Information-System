<template>
  <div class="user-management">
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="用户名">
          <el-input
            v-model="searchForm.username"
            placeholder="请输入用户名"
            clearable
          />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input
            v-model="searchForm.name"
            placeholder="请输入姓名"
            clearable
          />
        </el-form-item>
        <el-form-item label="角色">
          <el-select
            v-model="searchForm.role"
            placeholder="请选择角色"
            clearable
            teleported
            fit-input-width
          >
            <el-option
              v-for="role in roleOptions"
              :key="role.value"
              :label="role.label"
              :value="role.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="searchForm.is_active"
            placeholder="请选择状态"
            clearable
            teleported
            fit-input-width
          >
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <div class="title-area">
            <span class="title">用户列表</span>
            <el-badge
              v-if="isAdmin && pendingCount > 0"
              :value="pendingCount"
              class="pending-badge"
            >
              <el-button type="warning" size="small" @click="showPendingUsers"
                >待审核用户</el-button
              >
            </el-badge>
          </div>
          <div v-if="isAdmin" class="header-actions">
            <el-button type="primary" @click="handleAdd">
              <el-icon><Plus /></el-icon>
              新增用户
            </el-button>
            <el-dropdown @command="handlePermPackageCommand">
              <el-button type="info">
                权限包
                <el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="export"
                    >导出权限包</el-dropdown-item
                  >
                  <el-dropdown-item command="import"
                    >导入权限包</el-dropdown-item
                  >
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </template>

      <el-table v-loading="loading" :data="tableData" stripe border>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="full_name" label="姓名" min-width="100" />
        <el-table-column prop="role" label="角色" width="130">
          <template #default="{ row }">
            <el-tag :type="getRoleTagType(row.role)">{{
              getRoleName(row.role)
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="data_scope" label="数据范围" width="120">
          <template #default="{ row }">
            {{ getDataScopeName(row.data_scope) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="organization_name"
          label="所属组织"
          min-width="140"
        >
          <template #default="{ row }">
            {{ row.organization_name || "-" }}
          </template>
        </el-table-column>
        <el-table-column prop="department" label="部门" min-width="120" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="machine_code" label="机器码" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.machine_code" type="success" size="small">
              <el-icon><Key /></el-icon>
              已绑定
            </el-tag>
            <el-tag v-else type="info" size="small">未绑定</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="160" />
        <el-table-column
          prop="is_active"
          label="状态"
          width="80"
          align="center"
        >
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? "启用" : "禁用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          v-if="isAdmin"
          label="操作"
          width="280"
          align="center"
          fixed="right"
        >
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" size="small" @click="handleEdit(row)"
                >编辑</el-button
              >
              <el-button
                type="warning"
                size="small"
                @click="handleResetPassword(row)"
                >重置密码</el-button
              >
              <el-button
                type="success"
                size="small"
                @click="handleRolePermission(row)"
                >角色/权限</el-button
              >
              <el-button type="danger" size="small" @click="handleDelete(row)"
                >删除</el-button
              >
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pagination"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 用户编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formData.username"
            placeholder="请输入用户名"
            :disabled="isEdit"
          />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="formData.full_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="初始密码" prop="password">
          <div style="display: flex; gap: 8px; width: 100%">
            <el-input
              v-model="formData.password"
              type="password"
              placeholder="请输入密码"
              show-password
              style="flex: 1"
            />
            <el-button @click="generatePassword">自动生成</el-button>
          </div>
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select
            v-model="formData.role"
            placeholder="请选择角色"
            style="width: 100%"
            teleported
            fit-input-width
          >
            <el-option
              v-for="role in roleOptions"
              :key="role.value"
              :label="role.label"
              :value="role.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!isEdit" label="数据范围">
          <el-select
            v-model="formData.data_scope"
            placeholder="请选择数据范围"
            style="width: 100%"
            teleported
            fit-input-width
          >
            <el-option
              v-for="scope in dataScopeOptions"
              :key="scope.value"
              :label="scope.label"
              :value="scope.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所属组织">
          <el-tree-select
            v-model="formData.organization_id"
            :data="orgTreeOptions"
            :props="{ label: 'name', value: 'id', children: 'children' } as any"
            placeholder="请选择所属组织"
            check-strictly
            clearable
            filterable
            style="width: 100%"
            teleported
            fit-input-width
          />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="功能权限">
          <el-select
            v-model="formData.permissions"
            multiple
            placeholder="请选择该用户的功能权限（不选则使用角色默认权限）"
            style="width: 100%"
            collapse-tags
            collapse-tags-tooltip
            teleported
            fit-input-width
          >
            <el-option-group
              v-for="group in permissionGroups"
              :key="group.category"
              :label="group.category"
            >
              <el-option
                v-for="perm in group.items"
                :key="perm.code"
                :label="perm.name"
                :value="perm.code"
              />
            </el-option-group>
          </el-select>
          <div class="form-item-tip">
            选择该用户可以使用的具体功能权限，未选择则使用角色默认权限
          </div>
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="formData.department" placeholder="请输入部门" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="formData.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="formData.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch
            v-model="formData.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit"
          >确定</el-button
        >
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="resetPwdDialogVisible" title="重置密码" width="500px">
      <el-form :model="resetPwdForm" label-width="100px">
        <el-form-item label="用户名">
          <el-input :value="currentUser?.username" disabled />
        </el-form-item>
        <el-form-item label="新密码">
          <div style="display: flex; gap: 8px; width: 100%">
            <el-input
              v-model="resetPwdForm.newPassword"
              type="password"
              placeholder="请输入新密码"
              show-password
              style="flex: 1"
            />
            <el-button @click="generateResetPassword">自动生成</el-button>
          </div>
        </el-form-item>
        <el-form-item v-if="resetPwdForm.newPassword" label="生成的密码">
          <el-input :value="resetPwdForm.newPassword" readonly>
            <template #append>
              <el-button @click="copyPassword">复制</el-button>
            </template>
          </el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPwdDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmResetPassword"
          >确认重置</el-button
        >
      </template>
    </el-dialog>

    <!-- 角色/权限分配抽屉 -->
    <PermissionAssignmentDrawer
      v-model="permDrawerVisible"
      :user="permDrawerUser"
      @saved="handlePermSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { logger } from "@/utils/logger";
import { generateRandomPassword } from "@/utils/clipboard";

import { ref, reactive, onMounted, computed } from "vue";
import { ElMessage, ElMessageBox, type FormInstance } from "element-plus";
import { Plus, Key, ArrowDown } from "@element-plus/icons-vue";
import request from "@/api/request";
import { useAuthStore } from "@/stores/auth";
import PermissionAssignmentDrawer from "@/components/permission/PermissionAssignmentDrawer.vue";

const authStore = useAuthStore();
const isAdmin = computed(() => authStore.isAdmin);

interface User {
  id: number;
  username: string;
  full_name: string;
  role: string;
  data_scope?: string;
  department: string;
  phone: string;
  email: string;
  is_active: boolean;
  last_login?: string;
  organization_id?: number | null;
  organization_name?: string;
  permissions?: string;
  created_at?: string;
  machine_code?: string;
  machine_binding_required?: boolean;
  allowed_permissions?: string;
}

const loading = ref(false);
const submitting = ref(false);
const dialogVisible = ref(false);
const dialogTitle = ref("新增用户");
const isEdit = ref(false);
const resetPwdDialogVisible = ref(false);
const permDrawerVisible = ref(false);
const permDrawerUser = ref<User | null>(null);
const pendingDialogVisible = ref(false);
const formRef = ref<FormInstance>();
const currentUser = ref<User | null>(null);

const pendingCount = ref(0);
const pendingUsers = ref<User[]>([]);

const searchForm = reactive({
  username: "",
  name: "",
  role: "",
  is_active: undefined as boolean | undefined,
});

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0,
});

const tableData = ref<User[]>([]);

const formData = reactive({
  id: 0,
  username: "",
  full_name: "",
  password: "",
  role: "operator",
  data_scope: "org",
  department: "",
  phone: "",
  email: "",
  is_active: true,
  organization_id: null as number | null,
  permissions: [] as string[],
});

const orgTreeOptions = ref<any[]>([]);

async function loadOrgTree() {
  try {
    const res = await request.get("/organizations/tree", {
      showError: false,
    } as any);
    orgTreeOptions.value = res.data?.data || res.data || [];
  } catch {
    orgTreeOptions.value = [];
  }
}

const resetPwdForm = reactive({
  newPassword: "",
});

// Permission groups for UI grouping - 与后端 /users/permissions/options 保持一致
const permissionGroups = [
  {
    category: "系统",
    items: [
      { code: "system:manage", name: "系统管理" },
      { code: "user:manage", name: "用户管理" },
      { code: "org:manage", name: "组织管理" },
      { code: "role:manage", name: "角色管理" },
    ],
  },
  {
    category: "数据",
    items: [
      { code: "village:manage", name: "村庄管理" },
      { code: "project:manage", name: "项目管理" },
      { code: "fund:manage", name: "资金管理" },
      { code: "report:manage", name: "报表管理" },
    ],
  },
  {
    category: "操作",
    items: [
      { code: "data:view", name: "数据查看" },
      { code: "data:create", name: "数据创建" },
      { code: "data:edit", name: "数据编辑" },
      { code: "data:delete", name: "数据删除" },
      { code: "data:export", name: "数据导出" },
      { code: "data:import", name: "数据导入" },
    ],
  },
  {
    category: "审批",
    items: [
      { code: "approve:view", name: "查看审批" },
      { code: "approve:submit", name: "提交审批" },
      { code: "approve:process", name: "处理审批" },
    ],
  },
];

const roleOptions = [
  { value: "super_admin", label: "超级管理员" },
  { value: "admin", label: "系统管理员" },
  { value: "approval_leader", label: "审批领导" },
  { value: "manager", label: "管理人员" },
  { value: "operator", label: "操作员" },
  { value: "viewer", label: "查看者" },
];

const dataScopeOptions = [
  { value: "all", label: "全部数据" },
  { value: "org_children", label: "本组织及下级" },
  { value: "org", label: "仅本组织" },
  { value: "self", label: "仅自己" },
];

const rules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 3, max: 20, message: "长度在 3 到 20 个字符", trigger: "blur" },
  ],
  name: [{ required: true, message: "请输入姓名", trigger: "blur" }],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, max: 50, message: "长度在 6 到 50 个字符", trigger: "blur" },
  ],
  role: [{ required: true, message: "请选择角色", trigger: "change" }],
};

const getRoleTagType = (
  role: string,
): "info" | "primary" | "success" | "warning" | "danger" => {
  const types: Record<
    string,
    "info" | "primary" | "success" | "warning" | "danger"
  > = {
    super_admin: "danger",
    admin: "danger",
    approval_leader: "warning",
    manager: "warning",
    operator: "success",
    viewer: "info",
  };
  return types[role] || "info";
};

const getRoleName = (role: string) => {
  const names: Record<string, string> = {
    super_admin: "超级管理员",
    admin: "系统管理员",
    approval_leader: "审批领导",
    manager: "管理人员",
    operator: "操作员",
    viewer: "查看者",
  };
  return names[role] || role;
};

const getDataScopeName = (scope: string) => {
  const names: Record<string, string> = {
    all: "全部",
    org_children: "本组织及下级",
    org: "仅本组织",
    self: "仅自己",
  };
  return names[scope] || scope || "-";
};

const generatePassword = () => {
  formData.password = generateRandomPassword();
};

const generateResetPassword = () => {
  resetPwdForm.newPassword = generateRandomPassword();
};

const copyPassword = async () => {
  try {
    await navigator.clipboard.writeText(resetPwdForm.newPassword);
    ElMessage.success("密码已复制到剪贴板");
  } catch {
    ElMessage.error("复制失败，请手动复制");
  }
};

const loadData = async () => {
  loading.value = true;
  try {
    const response = await request.get("/users", {
      params: {
        page: pagination.page,
        page_size: pagination.size,
        username: searchForm.username || undefined,
        keyword: searchForm.name || undefined,
        role: searchForm.role || undefined,
        is_active: searchForm.is_active,
      },
    });
    const data = response?.data || response;
    tableData.value = data.items || [];
    pagination.total = data.total || tableData.value.length;
  } catch (error) {
    logger.error("加载用户数据失败:", error);
    ElMessage.error("加载用户数据失败");
  } finally {
    loading.value = false;
  }
};

const loadPendingCount = async () => {
  if (!isAdmin.value) return;
  try {
    const res = await request.get("/users/pending/list");
    const data = res.data?.data || res.data || [];
    pendingCount.value = Array.isArray(data) ? data.length : data.total || 0;
  } catch {
    pendingCount.value = 0;
  }
};

const showPendingUsers = async () => {
  try {
    const res = await request.get("/users/pending/list");
    const data = res.data?.data || res.data || [];
    const items = Array.isArray(data) ? data : data.items || [];
    pendingUsers.value = items;
    pendingCount.value = items.length;
    pendingDialogVisible.value = true;
  } catch {
    ElMessage.error("加载待审核用户失败");
  }
};

const handleSearch = () => {
  pagination.page = 1;
  loadData();
};

const handleReset = () => {
  Object.assign(searchForm, {
    username: "",
    name: "",
    role: "",
    is_active: undefined,
  });
  handleSearch();
};

const handleSizeChange = () => {
  pagination.page = 1;
  loadData();
};

const handlePageChange = () => {
  loadData();
};

const handleAdd = () => {
  isEdit.value = false;
  dialogTitle.value = "新增用户";
  Object.assign(formData, {
    id: 0,
    username: "",
    full_name: "",
    password: "",
    role: "operator",
    data_scope: "org",
    department: "",
    phone: "",
    email: "",
    is_active: true,
    organization_id: null,
    permissions: [],
  });
  dialogVisible.value = true;
};

const handleEdit = (row: any) => {
  isEdit.value = true;
  dialogTitle.value = "编辑用户";
  Object.assign(formData, {
    ...row,
    organization_id: row.organization_id ?? null,
  });
  dialogVisible.value = true;
};

const handleSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    submitting.value = true;
    try {
      if (isEdit.value) {
        await request.put(`/users/${formData.id}`, {
          full_name: formData.full_name,
          email: formData.email,
          phone: formData.phone,
          department: formData.department,
        });
        ElMessage.success("用户更新成功");
      } else {
        const res = await request.post("/users", {
          username: formData.username,
          full_name: formData.full_name,
          password: formData.password || undefined,
          email: formData.email,
          phone: formData.phone,
          department: formData.department,
          role: formData.role,
          data_scope: formData.data_scope,
          organization_id: formData.organization_id,
          is_active: formData.is_active,
          permissions: formData.permissions?.join(",") || "",
        });
        const created = res.data?.data;
        if (created?.password) {
          ElMessage.success(
            `用户创建成功！\n用户名: ${formData.username}\n初始密码: ${created.password}`,
          );
        } else {
          ElMessage.success("用户创建成功");
        }
      }
      dialogVisible.value = false;
      await Promise.all([loadData(), loadPendingCount()]);
    } catch (error: any) {
      const msg = error?.response?.data?.detail || "操作失败";
      ElMessage.error(msg);
    } finally {
      submitting.value = false;
    }
  });
};

const handleResetPassword = (row: any) => {
  currentUser.value = row;
  resetPwdForm.newPassword = "";
  resetPwdDialogVisible.value = true;
};

const confirmResetPassword = async () => {
  if (!resetPwdForm.newPassword) {
    ElMessage.warning("请输入或生成新密码");
    return;
  }

  try {
    const newPwd = resetPwdForm.newPassword;
    await request.post(`/users/${currentUser.value?.id}/admin-reset-password`, {
      new_password: newPwd,
    });
    try {
      await navigator.clipboard.writeText(newPwd);
    } catch {
      /* ignore */
    }
    ElMessageBox.alert(
      `新密码：${newPwd}`,
      `用户「${currentUser.value?.username}」密码已重置`,
      { confirmButtonText: "已复制到剪贴板，知道了", type: "success" },
    );
    resetPwdDialogVisible.value = false;
    resetPwdForm.newPassword = "";
  } catch (error: any) {
    const msg = error?.response?.data?.detail || "重置密码失败";
    ElMessage.error(msg);
  }
};

// ── 角色/权限分配抽屉 ──
const handleRolePermission = (row: any) => {
  permDrawerUser.value = row;
  permDrawerVisible.value = true;
};

const handlePermSaved = async () => {
  await Promise.all([loadData(), loadPendingCount()]);
};

// ── 权限包导入/导出 ──
const exportingPermPackage = ref(false);
const importingPermPackage = ref(false);

const handlePermPackageCommand = (command: string) => {
  if (command === "export") handleExportPermissionPackage();
  else if (command === "import") handleImportPermissionPackage();
};

const handleExportPermissionPackage = async () => {
  exportingPermPackage.value = true;
  try {
    const res = await request.post("/permission-packages/export", {});
    const data = res.data?.data || res.data;
    if (data.file_name) {
      const downloadUrl = `/api/v1/permission-packages/download/${data.file_name}`;
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = data.file_name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      ElMessage.success(
        `权限包导出成功 (${data.role_count} 个角色, ${data.user_count} 个用户)`,
      );
    }
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || "导出失败");
  } finally {
    exportingPermPackage.value = false;
  }
};

const handleImportPermissionPackage = () => {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".zip";

  // 清理函数：移除 input 元素 + 重置状态
  const cleanup = () => {
    importingPermPackage.value = false;
    input.remove();
    window.removeEventListener("focus", cleanup);
  };

  // 用户取消文件对话框时 change 事件不触发，用 window focus 代理清理
  window.addEventListener("focus", cleanup, { once: true });

  input.addEventListener("change", async (e: Event) => {
    // 用户已选择文件 → 取消 focus 清理（change 事件先于 focus）
    window.removeEventListener("focus", cleanup);

    importingPermPackage.value = true;
    try {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) { cleanup(); return; }
      const fd = new FormData();
      fd.append("file", file);
      const res = await request.post("/permission-packages/import", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const result = res.data?.data || res.data;
      if (result.success) {
        const p = result.preview || {};
        let msg = `将导入 ${p.role_count || 0} 个角色, ${p.user_legacy_count || 0} 个用户权限`;
        if (p.warnings?.length) msg += `\n警告: ${p.warnings.join("; ")}`;
        await ElMessageBox.confirm(msg, "确认导入权限包", {
          type: "info",
          confirmButtonText: "确认导入",
          cancelButtonText: "取消",
        });
        const cRes = await request.post(
          `/permission-packages/confirm/${encodeURIComponent(file.name)}`,
          { overwrite_existing: true },
        );
        ElMessage.success(
          cRes.data?.data?.message || cRes.data?.message || "导入完成",
        );
        loadData();
      } else {
        ElMessage.error(result.message || "导入失败");
      }
    } catch (err: any) {
      if (err === "cancel") return;
      ElMessage.error(
        err?.response?.data?.detail || err?.message || "导入失败",
      );
    } finally {
      cleanup();
    }
  });

  input.click();
};

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定删除用户 "${row.full_name || row.username}" 吗？`,
      "提示",
      {
        type: "warning",
      },
    );
    await request.delete(`/users/${row.id}`);
    ElMessage.success("删除成功");
    await Promise.all([loadData(), loadPendingCount()]);
    pendingDialogVisible.value = false;
  } catch (error: any) {
    if (error !== "cancel" && error?.toString() !== "cancel") {
      const msg = error?.response?.data?.detail || "删除失败";
      ElMessage.error(msg);
    }
  }
};

onMounted(() => {
  loadData();
  loadOrgTree();
  loadPendingCount();
});
</script>

<style scoped>
.user-management {
  padding: 20px;
}

.search-card,
.table-card {
  margin-bottom: 20px;
  background: #ffffff;
  border: 1px solid #ebeef5;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-area {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.pending-badge :deep(.el-badge__content) {
  top: 4px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-card__header) {
  border-bottom: 1px solid #ebeef5;
  padding: 15px 20px;
}

:deep(.el-form-item__label) {
  color: #303133;
}

.action-buttons {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.action-buttons .el-button + .el-button {
  margin-left: 0;
}

.machine-code-preview {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}

.form-item-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
  margin-top: 4px;
}
</style>
