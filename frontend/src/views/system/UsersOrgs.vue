<template>
  <div class="users-orgs-page">
    <el-card class="header-card">
      <h2>用户与组织管理</h2>
      <p class="description">管理用户账户、组织架构和权限分配</p>
    </el-card>

    <el-row :gutter="20">
      <!-- 左侧：组织树 -->
      <el-col :span="8">
        <el-card class="org-tree-card">
          <template #header>
            <div class="card-header-flex">
              <span>组织架构</span>
              <el-button size="small" type="primary" @click="showAddOrgDialog">
                <el-icon><Plus /></el-icon>
                新增
              </el-button>
            </div>
          </template>

          <el-tree
            :data="organizationTree"
            :props="treeProps"
            node-key="id"
            default-expand-all
            highlight-current
            @node-click="handleOrgClick"
          >
            <template #default="{ node, data }">
              <span class="custom-tree-node">
                <span>{{ node.label }}</span>
                <span class="tree-node-actions">
                  <el-button
                    type="primary"
                    link
                    size="small"
                    @click.stop="handleEditOrg(data)"
                  >
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button
                    type="danger"
                    link
                    size="small"
                    @click.stop="handleDeleteOrg(data)"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </span>
              </span>
            </template>
          </el-tree>
        </el-card>
      </el-col>

      <!-- 右侧：用户列表 -->
      <el-col :span="16">
        <el-card class="users-card">
          <template #header>
            <div class="card-header-flex">
              <span>
                {{
                  selectedOrg ? `${selectedOrg.name} - 用户列表` : "所有用户"
                }}
              </span>
              <el-button size="small" @click="loadUsers">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>

          <!-- 搜索栏 -->
          <div class="search-bar">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索用户名、姓名"
              clearable
              style="width: 300px"
            />
            <el-button
              type="primary"
              style="margin-left: 10px"
              @click="showAddUserDialog"
            >
              <el-icon><Plus /></el-icon>
              新增用户
            </el-button>
          </div>

          <!-- 用户表格 -->
          <el-table
            v-loading="loading"
            :data="filteredUsers"
            stripe
            style="width: 100%; margin-top: 20px"
          >
            <el-table-column prop="username" label="用户名" width="120" />
            <el-table-column prop="full_name" label="姓名" width="100" />
            <el-table-column prop="role" label="角色" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="
                    row.role === 'admin'
                      ? 'danger'
                      : row.role === 'viewer'
                        ? 'info'
                        : 'primary'
                  "
                  size="small"
                >
                  {{
                    row.role === "admin"
                      ? "管理员"
                      : row.role === "viewer"
                        ? "查看员"
                        : row.role || "普通用户"
                  }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="所属组织" min-width="150">
              <template #default="{ row }">
                {{ row.organization_name || row.department || "未分配" }}
              </template>
            </el-table-column>
            <el-table-column prop="data_scope" label="数据范围" width="100" />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag
                  :type="row.is_active ? 'success' : 'danger'"
                  size="small"
                >
                  {{ row.is_active ? "正常" : "禁用" }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="机器码" min-width="120">
              <template #default="{ row }">
                {{
                  row.machine_code
                    ? row.machine_code.substring(0, 16) + "..."
                    : "未绑定"
                }}
              </template>
            </el-table-column>
            <el-table-column label="注册时间" width="160">
              <template #default="{ row }">
                {{
                  row.created_at
                    ? row.created_at.substring(0, 19).replace("T", " ")
                    : ""
                }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="handleEditUser(row)"
                >
                  编辑
                </el-button>
                <el-button
                  type="danger"
                  link
                  size="small"
                  @click="handleDeleteUser(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新增用户对话框 -->
    <el-dialog v-model="addUserDialogVisible" title="新增用户" width="600px">
      <el-form
        ref="addUserFormRef"
        :model="addUserForm"
        :rules="addUserRules"
        label-width="90px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="addUserForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="addUserForm.full_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="所属组织">
          <el-select
            v-model="addUserForm.organization_id"
            placeholder="请选择组织"
            style="width: 100%"
            clearable
          >
            <!-- clearable 替代不指定组织选项 -->
            <el-option
              v-for="org in flatOrganizationList"
              :key="org.id"
              :label="org.name"
              :value="org.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select
            v-model="addUserForm.role"
            placeholder="请选择角色"
            style="width: 100%"
          >
            <el-option label="系统管理员" value="admin" />
            <el-option label="审批领导" value="approval_leader" />
            <el-option label="管理人员" value="manager" />
            <el-option label="操作员" value="operator" />
            <el-option label="查看者" value="viewer" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据范围" prop="data_scope">
          <el-select
            v-model="addUserForm.data_scope"
            placeholder="请选择数据范围"
            style="width: 100%"
          >
            <el-option label="全部数据" value="all" />
            <el-option label="本组织及下级" value="org_children" />
            <el-option label="仅本组织" value="org" />
            <el-option label="仅自己" value="self" />
          </el-select>
        </el-form-item>
        <el-form-item label="功能权限">
          <el-select
            v-model="addUserForm.permissions"
            multiple
            placeholder="请选择功能权限（不选则使用角色默认权限）"
            style="width: 100%"
            collapse-tags
            collapse-tags-tooltip
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
          <div style="font-size: 12px; color: #909399; margin-top: 4px">
            选择该用户可以使用的具体功能权限
          </div>
        </el-form-item>
        <el-form-item label="初始密码" prop="password">
          <el-input
            v-model="addUserForm.password"
            type="password"
            placeholder="请输入初始密码"
            show-password
          />
          <el-button
            size="small"
            style="margin-top: 5px"
            @click="handleGeneratePassword"
          >
            生成随机密码
          </el-button>
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="addUserForm.email"
            placeholder="请输入邮箱（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addUserDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleAddUser"
          >确定</el-button
        >
      </template>
    </el-dialog>

    <!-- 编辑用户对话框 -->
    <el-dialog v-model="editUserDialogVisible" title="编辑用户" width="500px">
      <el-form
        ref="editUserFormRef"
        :model="editUserForm"
        :rules="editUserRules"
        label-width="90px"
      >
        <el-form-item label="用户名">
          <el-input v-model="editUserForm.username" disabled />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="editUserForm.full_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="所属组织">
          <el-select
            v-model="editUserForm.organization_id"
            placeholder="请选择组织"
            style="width: 100%"
            clearable
          >
            <!-- clearable 替代不指定组织选项 -->
            <el-option
              v-for="org in flatOrganizationList"
              :key="org.id"
              :label="org.name"
              :value="org.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select
            v-model="editUserForm.role"
            placeholder="请选择角色"
            style="width: 100%"
          >
            <el-option label="系统管理员" value="admin" />
            <el-option label="审批领导" value="approval_leader" />
            <el-option label="管理人员" value="manager" />
            <el-option label="操作员" value="operator" />
            <el-option label="查看者" value="viewer" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据范围" prop="data_scope">
          <el-select
            v-model="editUserForm.data_scope"
            placeholder="请选择数据范围"
            style="width: 100%"
          >
            <el-option label="全部数据" value="all" />
            <el-option label="本组织及下级" value="org_children" />
            <el-option label="仅本组织" value="org" />
            <el-option label="仅自己" value="self" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="editUserForm.is_active" />
          <span style="margin-left: 10px">{{
            editUserForm.is_active ? "正常" : "禁用"
          }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editUserDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleUpdateUser"
          >确定</el-button
        >
      </template>
    </el-dialog>

    <!-- 新增组织对话框 -->
    <el-dialog v-model="addOrgDialogVisible" title="新增组织" width="500px">
      <el-form
        ref="addOrgFormRef"
        :model="addOrgForm"
        :rules="addOrgRules"
        label-width="90px"
      >
        <el-form-item label="组织名称" prop="name">
          <el-input v-model="addOrgForm.name" placeholder="请输入组织名称" />
        </el-form-item>
        <el-form-item label="上级组织">
          <el-select
            v-model="addOrgForm.parent_id"
            placeholder="请选择上级组织（可选）"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="org in flatOrganizationList"
              :key="org.id"
              :label="org.name"
              :value="org.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="组织编码" prop="code">
          <el-input
            v-model="addOrgForm.code"
            placeholder="请输入组织编码（可选）"
          />
        </el-form-item>
        <el-form-item label="排序号">
          <el-input-number
            v-model="addOrgForm.sort_order"
            :min="0"
            :max="9999"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="addOrgForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入组织描述（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addOrgDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="orgSubmitting" @click="handleAddOrg"
          >确定</el-button
        >
      </template>
    </el-dialog>

    <!-- 编辑组织对话框 -->
    <el-dialog v-model="editOrgDialogVisible" title="编辑组织" width="500px">
      <el-form
        ref="editOrgFormRef"
        :model="editOrgForm"
        :rules="editOrgRules"
        label-width="90px"
      >
        <el-form-item label="组织名称" prop="name">
          <el-input v-model="editOrgForm.name" placeholder="请输入组织名称" />
        </el-form-item>
        <el-form-item label="上级组织">
          <el-select
            v-model="editOrgForm.parent_id"
            placeholder="请选择上级组织"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="org in selectableParentOrgs"
              :key="org.id"
              :label="org.name"
              :value="org.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="组织编码" prop="code">
          <el-input
            v-model="editOrgForm.code"
            placeholder="请输入组织编码（可选）"
          />
        </el-form-item>
        <el-form-item label="排序号">
          <el-input-number
            v-model="editOrgForm.sort_order"
            :min="0"
            :max="9999"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="editOrgForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入组织描述（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editOrgDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="orgSubmitting"
          @click="handleUpdateOrg"
          >确定</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import {
  ElMessage,
  ElMessageBox,
  type FormInstance,
  type FormRules,
} from "element-plus";
import { Plus, Refresh, Edit, Delete } from "@element-plus/icons-vue";
import request from "@/api/request";
import { generateRandomPassword, flattenTree } from "@/utils/clipboard";

const loading = ref(false);
const submitting = ref(false);
const organizationTree = ref<any[]>([]);
const users = ref<any[]>([]);
const selectedOrg = ref<any>(null);
const searchKeyword = ref("");

// 新增用户对话框
const addUserDialogVisible = ref(false);
const addUserFormRef = ref<FormInstance>();
const addUserForm = ref({
  username: "",
  full_name: "",
  email: "",
  role: "operator",
  data_scope: "org",
  password: "",
  organization_id: null as number | null,
  permissions: [] as string[],
});
const addUserRules: FormRules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 3, max: 50, message: "用户名长度为3-50个字符", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请输入初始密码", trigger: "blur" },
    { min: 8, message: "密码长度不能少于8个字符", trigger: "blur" },
  ],
  role: [{ required: true, message: "请选择角色", trigger: "change" }],
  data_scope: [
    { required: true, message: "请选择数据范围", trigger: "change" },
  ],
};

// 编辑用户对话框
const editUserDialogVisible = ref(false);
const editUserFormRef = ref<FormInstance>();
const editUserForm = ref({
  id: 0,
  username: "",
  full_name: "",
  email: "",
  role: "operator",
  data_scope: "org",
  is_active: true,
  organization_id: null as number | null,
});
const editUserRules: FormRules = {
  full_name: [
    { max: 100, message: "姓名长度不能超过100个字符", trigger: "blur" },
  ],
  role: [{ required: true, message: "请选择角色", trigger: "change" }],
  data_scope: [
    { required: true, message: "请选择数据范围", trigger: "change" },
  ],
};

// 权限选项组 - 与后端保持一致
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

// ---------- 组织管理 ----------
const addOrgDialogVisible = ref(false);
const editOrgDialogVisible = ref(false);
const orgSubmitting = ref(false);
const addOrgFormRef = ref<FormInstance>();
const editOrgFormRef = ref<FormInstance>();

const addOrgForm = ref({
  name: "",
  parent_id: null as number | null,
  code: "",
  sort_order: 0,
  description: "",
});

const editOrgForm = ref({
  id: 0,
  name: "",
  parent_id: null as number | null,
  code: "",
  sort_order: 0,
  description: "",
});

const addOrgRules: FormRules = {
  name: [
    { required: true, message: "请输入组织名称", trigger: "blur" },
    { min: 1, max: 100, message: "组织名称长度为1-100个字符", trigger: "blur" },
  ],
};

const editOrgRules: FormRules = {
  name: [
    { required: true, message: "请输入组织名称", trigger: "blur" },
    { min: 1, max: 100, message: "组织名称长度为1-100个字符", trigger: "blur" },
  ],
};

// 可选择的上级组织（排除自身和子组织）
const selectableParentOrgs = computed(() => {
  const currentId = editOrgForm.value.id;
  if (!currentId) return flatOrganizationList.value;

  const excludeIds = new Set<number>();
  const collectChildren = (orgs: any[]) => {
    for (const org of orgs) {
      if (org.id === currentId) continue;
      excludeIds.add(org.id);
      if (org.children?.length) collectChildren(org.children);
    }
  };
  collectChildren(organizationTree.value);

  return flatOrganizationList.value.filter((org) => !excludeIds.has(org.id));
});

// 显示新增组织对话框
const showAddOrgDialog = () => {
  addOrgForm.value = {
    name: "",
    parent_id: selectedOrg.value?.id || null,
    code: "",
    sort_order: 0,
    description: "",
  };
  addOrgDialogVisible.value = true;
};

// 新增组织
const handleAddOrg = async () => {
  if (!addOrgFormRef.value) return;

  try {
    await addOrgFormRef.value.validate();
    orgSubmitting.value = true;

    const response = await request.post("/organizations", {
      name: addOrgForm.value.name,
      parent_id: addOrgForm.value.parent_id,
      code: addOrgForm.value.code || undefined,
      sort_order: addOrgForm.value.sort_order,
      description: addOrgForm.value.description || undefined,
    });

    if (response.data?.code === 200 || response.data?.id) {
      ElMessage.success("组织创建成功");
      addOrgDialogVisible.value = false;
      loadOrganizationTree();
    } else {
      ElMessage.error(response.data?.detail || "创建组织失败");
    }
  } catch (error: any) {
    console.error("创建组织失败:", error);
    ElMessage.error(error.response?.data?.detail || "创建组织失败");
  } finally {
    orgSubmitting.value = false;
  }
};

// 编辑组织
const handleEditOrg = (data: any) => {
  editOrgForm.value = {
    id: data.id,
    name: data.name,
    parent_id: data.parent_id || null,
    code: data.code || "",
    sort_order: data.sort_order || 0,
    description: data.description || "",
  };
  editOrgDialogVisible.value = true;
};

// 更新组织
const handleUpdateOrg = async () => {
  if (!editOrgFormRef.value) return;

  try {
    await editOrgFormRef.value.validate();
    orgSubmitting.value = true;

    const response = await request.put(
      `/organizations/${editOrgForm.value.id}`,
      {
        name: editOrgForm.value.name,
        parent_id: editOrgForm.value.parent_id,
        code: editOrgForm.value.code || undefined,
        sort_order: editOrgForm.value.sort_order,
        description: editOrgForm.value.description || undefined,
      },
    );

    if (response.data?.code === 200 || response.data?.id) {
      ElMessage.success("组织更新成功");
      editOrgDialogVisible.value = false;
      loadOrganizationTree();
    } else {
      ElMessage.error(response.data?.detail || "更新组织失败");
    }
  } catch (error: any) {
    console.error("更新组织失败:", error);
    ElMessage.error(error.response?.data?.detail || "更新组织失败");
  } finally {
    orgSubmitting.value = false;
  }
};

// 删除组织
const handleDeleteOrg = async (data: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除组织 "${data.name}" 吗？${data.children?.length ? "该组织包含下级组织，将一并删除。" : ""}此操作不可恢复。`,
      "删除确认",
      {
        confirmButtonText: "确定删除",
        cancelButtonText: "取消",
        type: "warning",
      },
    );

    const response = await request.delete(`/organizations/${data.id}`);

    if (response.data?.code === 200 || response.status === 200) {
      ElMessage.success("组织删除成功");
      if (selectedOrg.value?.id === data.id) {
        selectedOrg.value = null;
      }
      loadOrganizationTree();
    } else {
      ElMessage.error(response.data?.detail || "删除组织失败");
    }
  } catch (error: any) {
    if (error !== "cancel") {
      console.error("删除组织失败:", error);
      ElMessage.error(error.response?.data?.detail || "删除组织失败");
    }
  }
};

const treeProps = {
  children: "children",
  label: "name",
};

// 扁平化组织树
const flatOrganizationList = computed(() => {
  const tree = organizationTree.value;
  if (!tree || tree.length === 0) return [];
  return flattenTree(tree);
});

const filteredUsers = computed(() => {
  let result = users.value;
  if (selectedOrg.value) {
    result = result.filter(
      (u: any) => u.organization_id === selectedOrg.value.id,
    );
  }
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase();
    result = result.filter(
      (u: any) =>
        (u.username || "").toLowerCase().includes(kw) ||
        (u.full_name || "").toLowerCase().includes(kw),
    );
  }
  return result;
});

const loadUsers = async () => {
  loading.value = true;
  try {
    const response = await request.get("/users", {
      params: { page_size: 200 },
    });
    users.value = response.data.items || [];
  } catch (error: any) {
    ElMessage.error(error.message || "加载用户列表失败");
  } finally {
    loading.value = false;
  }
};

const loadOrganizationTree = async () => {
  try {
    const response = await request.get("/organizations/tree");
    if (response.data?.code === 200) {
      organizationTree.value = response.data.data || [];
    } else if (Array.isArray(response.data)) {
      organizationTree.value = response.data;
    }
  } catch (error: any) {
    ElMessage.error(error.message || "加载组织树失败");
  }
};

const handleOrgClick = (data: any) => {
  selectedOrg.value = data;
};

// 显示新增用户对话框
const showAddUserDialog = () => {
  addUserForm.value = {
    username: "",
    full_name: "",
    email: "",
    role: "operator",
    data_scope: "org",
    password: "",
    organization_id: selectedOrg.value?.id || null,
    permissions: [],
  };
  addUserDialogVisible.value = true;
};

// 生成随机密码（使用共享工具）
const handleGeneratePassword = () => {
  addUserForm.value.password = generateRandomPassword();
};

// 新增用户
const handleAddUser = async () => {
  if (!addUserFormRef.value) return;

  try {
    await addUserFormRef.value.validate();
    submitting.value = true;

    const response = await request.post("/users", {
      username: addUserForm.value.username,
      full_name: addUserForm.value.full_name || undefined,
      email: addUserForm.value.email || undefined,
      password: addUserForm.value.password,
      role: addUserForm.value.role,
      data_scope: addUserForm.value.data_scope,
      organization_id: addUserForm.value.organization_id,
      permissions: addUserForm.value.permissions?.join(",") || "",
    });

    if (response.data?.code === 200 || response.data?.id) {
      ElMessage.success("用户创建成功");
      addUserDialogVisible.value = false;
      loadUsers();
    } else {
      ElMessage.error(response.data?.detail || "创建用户失败");
    }
  } catch (error: any) {
    console.error("创建用户失败:", error);
    ElMessage.error(error.response?.data?.detail || "创建用户失败");
  } finally {
    submitting.value = false;
  }
};

// 编辑用户
const handleEditUser = (row: any) => {
  editUserForm.value = {
    id: row.id,
    username: row.username,
    full_name: row.full_name || "",
    email: row.email || "",
    role: row.role || "operator",
    data_scope: row.data_scope || "org",
    is_active: row.is_active !== false,
    organization_id: row.organization_id || null,
  };
  editUserDialogVisible.value = true;
};

// 更新用户
const handleUpdateUser = async () => {
  if (!editUserFormRef.value) return;

  try {
    await editUserFormRef.value.validate();
    submitting.value = true;

    const response = await request.put(`/users/${editUserForm.value.id}`, {
      full_name: editUserForm.value.full_name || undefined,
      email: editUserForm.value.email || undefined,
      role: editUserForm.value.role,
      data_scope: editUserForm.value.data_scope,
      is_active: editUserForm.value.is_active,
      organization_id: editUserForm.value.organization_id,
    });

    if (response.data?.code === 200 || response.data?.id) {
      ElMessage.success("用户更新成功");
      editUserDialogVisible.value = false;
      loadUsers();
    } else {
      ElMessage.error(response.data?.detail || "更新用户失败");
    }
  } catch (error: any) {
    console.error("更新用户失败:", error);
    ElMessage.error(error.response?.data?.detail || "更新用户失败");
  } finally {
    submitting.value = false;
  }
};

// 删除用户
const handleDeleteUser = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${row.username}" 吗？此操作不可恢复。`,
      "删除确认",
      {
        confirmButtonText: "确定删除",
        cancelButtonText: "取消",
        type: "warning",
      },
    );

    const response = await request.delete(`/users/${row.id}`);

    if (response.data?.code === 200 || response.status === 200) {
      ElMessage.success("用户删除成功");
      loadUsers();
    } else {
      ElMessage.error(response.data?.detail || "删除用户失败");
    }
  } catch (error: any) {
    if (error !== "cancel") {
      console.error("删除用户失败:", error);
      ElMessage.error(error.response?.data?.detail || "删除用户失败");
    }
  }
};

onMounted(() => {
  loadOrganizationTree();
  loadUsers();
});
</script>

<style scoped lang="scss">
.users-orgs-page {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;

  h2 {
    margin: 0 0 8px 0;
    font-size: 24px;
    color: #303133;
  }

  .description {
    margin: 0;
    color: #909399;
    font-size: 14px;
  }
}

.card-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.org-tree-card {
  height: calc(100vh - 200px);
  overflow-y: auto;
}

.users-card {
  height: calc(100vh - 200px);
  overflow-y: auto;
}

.search-bar {
  margin-bottom: 15px;
}

.custom-tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 8px;
}

.tree-node-actions {
  display: none;
  gap: 4px;
}

.custom-tree-node:hover .tree-node-actions {
  display: flex;
}
</style>
