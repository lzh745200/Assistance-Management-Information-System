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
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
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
            <el-button type="success" @click="handleBatchGenerate">
              <el-icon><Key /></el-icon>
              批量生成账号
            </el-button>
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
                @click="handleAssignPermissions(row)"
                >权限管理</el-button
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

    <!-- 权限管理对话框 -->
    <el-dialog v-model="permDialogVisible" title="权限管理" width="680px">
      <el-form :model="permForm" label-width="110px">
        <el-form-item label="用户">
          <el-input
            :value="currentUser?.full_name || currentUser?.username"
            disabled
          />
        </el-form-item>

        <!-- 机器码绑定状态 -->
        <el-divider content-position="left">机器码绑定</el-divider>
        <el-form-item label="绑定状态">
          <el-tag v-if="currentUser?.machine_code" type="success">
            <el-icon><Key /></el-icon>
            已绑定
          </el-tag>
          <el-tag v-else type="info">未绑定</el-tag>
          <span v-if="currentUser?.machine_code" class="machine-code-preview">
            {{ currentUser.machine_code.substring(0, 16) }}...
          </span>
        </el-form-item>
        <el-form-item label="强制机器码绑定">
          <el-switch
            v-model="permForm.machine_binding_required"
            active-text="启用"
            inactive-text="禁用"
          />
          <div class="form-item-tip">开启后该用户必须从绑定的机器登录</div>
        </el-form-item>
        <el-form-item label="允许的权限">
          <el-input
            v-model="permForm.allowed_permissions"
            type="textarea"
            :rows="2"
            placeholder="JSON数组格式的权限白名单，如: ['user:read','village:read']'
为空则使用角色默认权限"
          />
          <div class="form-item-tip">设置后用户只能使用白名单中的权限</div>
        </el-form-item>

        <el-divider content-position="left">功能权限</el-divider>
        <el-form-item label="角色">
          <el-select
            v-model="permForm.role"
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
        <el-form-item label="数据范围">
          <el-select
            v-model="permForm.data_scope"
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
            v-model="permForm.organization_id"
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
        <el-form-item label="具体权限">
          <el-select
            v-model="permForm.permissionList"
            multiple
            placeholder="请选择权限"
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
        </el-form-item>
        <el-form-item label="账户状态">
          <el-switch
            v-model="permForm.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="permDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="confirmPermissions"
          >保存权限</el-button
        >
      </template>
    </el-dialog>

    <!-- 待审核用户对话框 -->
    <el-dialog v-model="pendingDialogVisible" title="待审核用户" width="800px">
      <el-table :data="pendingUsers" border>
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="full_name" label="姓名" min-width="100" />
        <el-table-column prop="email" label="邮箱" min-width="160" />
        <el-table-column prop="created_at" label="注册时间" width="160" />
        <el-table-column label="操作" width="200" align="center">
          <template #default="{ row }">
            <el-button
              type="success"
              size="small"
              @click="handleActivateUser(row)"
              >审核通过</el-button
            >
            <el-button type="danger" size="small" @click="handleDelete(row)"
              >拒绝删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 批量生成账号对话框 -->
    <el-dialog v-model="batchDialogVisible" title="批量生成账号" width="700px">
      <el-form :model="batchForm" label-width="120px">
        <el-form-item label="生成数量">
          <el-input-number v-model="batchForm.count" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="用户名前缀">
          <el-input v-model="batchForm.prefix" placeholder="如: user" />
        </el-form-item>
        <el-form-item label="起始编号">
          <el-input-number v-model="batchForm.startNum" :min="1" />
        </el-form-item>
        <el-form-item label="默认角色">
          <el-select
            v-model="batchForm.role"
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
        <el-form-item label="默认部门">
          <el-input v-model="batchForm.department" placeholder="请输入部门" />
        </el-form-item>
      </el-form>

      <div v-if="generatedAccounts.length > 0" class="generated-accounts">
        <el-divider>生成的账号信息</el-divider>
        <el-table :data="generatedAccounts" border size="small">
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="password" label="初始密码" />
          <el-table-column prop="role" label="角色" />
        </el-table>
        <el-button
          type="success"
          style="margin-top: 10px"
          @click="exportAccounts"
        >
          导出账号列表
        </el-button>
      </div>

      <template #footer>
        <el-button @click="batchDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="generateBatchAccounts"
          >生成账号</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { logger } from "@/utils/logger";
import { generateRandomPassword } from "@/utils/clipboard";

import { ref, reactive, onMounted, computed } from "vue";
import { ElMessage, ElMessageBox, type FormInstance } from "element-plus";
import { Plus, Key } from "@element-plus/icons-vue";
import request from "@/api/request";
import { useAuthStore } from "@/stores/auth";

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
const permDialogVisible = ref(false);
const pendingDialogVisible = ref(false);
const batchDialogVisible = ref(false);
const formRef = ref<FormInstance>();
const currentUser = ref<User | null>(null);

const pendingCount = ref(0);
const pendingUsers = ref<User[]>([]);

const searchForm = reactive({
  username: "",
  name: "",
  role: "",
  is_active: undefined as number | undefined,
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

const permForm = reactive({
  role: "operator",
  data_scope: "org",
  organization_id: null as number | null,
  permissionList: [] as string[],
  is_active: true,
  machine_binding_required: false,
  allowed_permissions: "",
});

const batchForm = reactive({
  count: 5,
  prefix: "user",
  startNum: 1,
  role: "operator",
  department: "",
});

const generatedAccounts = ref<any[]>([]);

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
        is_active:
          searchForm.is_active === 1
            ? true
            : searchForm.is_active === 0
              ? false
              : undefined,
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

const handleActivateUser = (row: any) => {
  currentUser.value = row;
  Object.assign(permForm, {
    role: row.role || "operator",
    data_scope: row.data_scope || "org",
    organization_id: row.organization_id ?? null,
    permissionList: [],
    is_active: true,
  });
  pendingDialogVisible.value = false;
  permDialogVisible.value = true;
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
      loadData();
      loadPendingCount();
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

const handleAssignPermissions = (row: any) => {
  currentUser.value = row;
  const perms = (row.permissions || "").split(",").filter(Boolean);
  Object.assign(permForm, {
    role: row.role || "operator",
    data_scope: row.data_scope || "org",
    organization_id: row.organization_id ?? null,
    permissionList: perms,
    is_active: row.is_active,
    machine_binding_required: row.machine_binding_required || false,
    allowed_permissions: row.allowed_permissions || "",
  });
  permDialogVisible.value = true;
};

const confirmPermissions = async () => {
  submitting.value = true;
  try {
    await request.put(`/users/${currentUser.value?.id}/permissions`, {
      role: permForm.role,
      data_scope: permForm.data_scope,
      organization_id: permForm.organization_id,
      permissions: permForm.permissionList.join(","),
      is_active: permForm.is_active,
      machine_binding_required: permForm.machine_binding_required,
      allowed_permissions: permForm.allowed_permissions,
    });
    ElMessage.success("权限设置成功");
    permDialogVisible.value = false;
    loadData();
    loadPendingCount();
  } catch (error: any) {
    const msg = error?.response?.data?.detail || "权限设置失败";
    ElMessage.error(msg);
  } finally {
    submitting.value = false;
  }
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
    loadData();
    loadPendingCount();
    pendingDialogVisible.value = false;
  } catch (error: any) {
    if (error !== "cancel" && error?.toString() !== "cancel") {
      const msg = error?.response?.data?.detail || "删除失败";
      ElMessage.error(msg);
    }
  }
};

const handleBatchGenerate = () => {
  generatedAccounts.value = [];
  batchDialogVisible.value = true;
};

const generateBatchAccounts = async () => {
  if (!batchForm.prefix) {
    ElMessage.warning("请输入用户名前缀");
    return;
  }

  try {
    const res = await request.post("/users/batch-create", {
      count: batchForm.count,
      prefix: batchForm.prefix,
      start_num: batchForm.startNum,
      role: batchForm.role,
      department: batchForm.department,
    });
    const data = res.data?.data || res.data;
    generatedAccounts.value = data.accounts || [];
    ElMessage.success(res.data?.message || `成功生成账号`);
    loadData();
  } catch (error) {
    ElMessage.error("生成账号失败");
  }
};

const exportAccounts = () => {
  if (generatedAccounts.value.length === 0) return;

  let csv = "\uFEFF用户名,初始密码,角色,部门\n";
  generatedAccounts.value.forEach((acc) => {
    csv += `${acc.username},${acc.password},${acc.role},${acc.department}\n`;
  });

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `账号列表_${new Date().toISOString().split("T")[0]}.csv`;
  link.click();
  URL.revokeObjectURL(url);

  ElMessage.success("账号列表已导出");
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

.generated-accounts {
  margin-top: 20px;
  padding: 15px;
  background: rgba(64, 145, 108, 0.1);
  border-radius: 4px;
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
