<template>
  <div class="pass-code-management">
    <el-card class="generate-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>生成组织通行证码</span>
        </div>
      </template>

      <el-form
        ref="generateFormRef"
        :model="generateForm"
        :rules="generateRules"
        label-width="140px"
      >
        <el-form-item label="选择组织单位" prop="organization_id">
          <el-select
            v-model="generateForm.organization_id"
            placeholder="请选择组织单位"
            filterable
            style="width: 100%"
            @change="handleOrganizationChange"
          >
            <el-option
              v-for="org in organizationList"
              :key="org.id"
              :label="org.name"
              :value="org.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="校验码" prop="verification_code">
          <el-input
            v-model="generateForm.verification_code"
            placeholder="选择组织后自动生成"
            readonly
            style="width: 200px"
          />
        </el-form-item>

        <el-form-item label="允许下级生成">
          <el-switch v-model="generateForm.allow_subordinate_generation" />
          <span class="form-tip">开启后，下级组织可以生成自己的通行证码</span>
        </el-form-item>

        <el-form-item label="备注说明">
          <el-input
            v-model="generateForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入备注说明（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="generating"
            @click="handleGenerate"
          >
            生成通行证码
          </el-button>
          <el-button @click="handleResetForm">重置</el-button>
        </el-form-item>

        <el-form-item v-if="generatedPassCode" label="生成结果">
          <div class="generated-result">
            <div class="pass-code-display">
              <span class="pass-code-text">{{ generatedPassCode }}</span>
              <el-button
                type="primary"
                size="small"
                :icon="CopyDocument"
                @click="handleCopyPassCode"
              >
                复制
              </el-button>
            </div>
            <div class="result-tip">
              请妥善保管通行证码，并及时分发给相关组织
            </div>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="list-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>通行证码生成记录</span>
        </div>
      </template>

      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="组织单位">
          <el-select
            v-model="queryForm.organization_id"
            placeholder="全部"
            clearable
            filterable
            style="width: 200px"
          >
            <el-option
              v-for="org in organizationList"
              :key="org.id"
              :label="org.name"
              :value="org.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select
            v-model="queryForm.status"
            placeholder="全部"
            clearable
            style="width: 120px"
          >
            <el-option label="待使用" value="pending" />
            <el-option label="已激活" value="active" />
            <el-option label="已撤销" value="revoked" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleQuery">
            查询
          </el-button>
          <el-button :icon="Refresh" @click="handleResetQuery">
            重置
          </el-button>
          <el-button
            type="success"
            :icon="Download"
            :loading="exporting"
            @click="handleExport"
          >
            导出
          </el-button>
        </el-form-item>
      </el-form>

      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
        style="width: 100%"
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column
          prop="organization_name"
          label="组织单位"
          min-width="180"
        />
        <el-table-column
          prop="verification_code"
          label="校验码"
          width="100"
          align="center"
        />
        <el-table-column prop="pass_code" label="通行证码" width="180">
          <template #default="{ row }">
            <div class="pass-code-cell">
              <span>{{ row.pass_code }}</span>
              <el-button
                type="primary"
                size="small"
                text
                :icon="CopyDocument"
                @click="handleCopy(row.pass_code)"
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column
          prop="allow_subordinate_generation"
          label="允许下级生成"
          width="120"
          align="center"
        >
          <template #default="{ row }">
            <el-tag
              :type="row.allow_subordinate_generation ? 'success' : 'info'"
            >
              {{ row.allow_subordinate_generation ? "是" : "否" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              :type="
                row.status === 'active'
                  ? 'success'
                  : row.status === 'pending'
                    ? 'warning'
                    : 'info'
              "
            >
              {{
                row.status === "active"
                  ? "已激活"
                  : row.status === "pending"
                    ? "待使用"
                    : "已撤销"
              }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="created_at"
          label="生成时间"
          width="180"
          align="center"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleQuery"
        @current-change="handleQuery"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, reactive, onMounted } from "vue";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import {
  Search,
  Refresh,
  Download,
  CopyDocument,
} from "@element-plus/icons-vue";
import {
  getOrganizationVerificationCode,
  createOrganizationPassCode,
  getOrganizationPassCodeList,
  exportOrganizationPassCodes,
  type CreateOrganizationPassCodeRequest,
  type OrganizationPassCodeResponse,
} from "@/api/organizationPassCode";
import { getOrganizationTree } from "@/api/organization";
import type { OrganizationTreeNode } from "@/types/organization";

// 表单引用
const generateFormRef = ref<FormInstance>();

// 组织列表
const organizationList = ref<OrganizationTreeNode[]>([]);

// 生成表单
const generateForm = reactive<CreateOrganizationPassCodeRequest>({
  organization_id: 0,
  verification_code: "",
  allow_subordinate_generation: false,
  description: "",
});

// 表单验证规则
const generateRules: FormRules = {
  organization_id: [
    { required: true, message: "请选择组织单位", trigger: "change" },
  ],
  verification_code: [
    { required: true, message: "校验码不能为空", trigger: "blur" },
  ],
};

// 生成状态
const generating = ref(false);
const generatedPassCode = ref("");

// 查询表单
const queryForm = reactive({
  organization_id: undefined as number | undefined,
  status: undefined as string | undefined,
});

// 表格数据
const tableData = ref<OrganizationPassCodeResponse[]>([]);
const loading = ref(false);
const exporting = ref(false);

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
});

// 加载组织列表
const loadOrganizations = async () => {
  try {
    const response = await getOrganizationTree();
    // 扁平化组织树
    const flattenTree = (
      nodes: OrganizationTreeNode[],
    ): OrganizationTreeNode[] => {
      const result: OrganizationTreeNode[] = [];
      const traverse = (node: OrganizationTreeNode) => {
        result.push(node);
        if (node.children && node.children.length > 0) {
          node.children.forEach(traverse);
        }
      };
      nodes.forEach(traverse);
      return result;
    };
    // 处理响应数据：可能是数组或包含 data 属性的对象
    let treeData: OrganizationTreeNode[] = [];
    if (Array.isArray(response)) {
      treeData = response;
    } else if (response && typeof response === "object" && "data" in response) {
      const dataField = (response as any).data;
      treeData = Array.isArray(dataField) ? dataField : [];
    }
    organizationList.value = flattenTree(treeData);
  } catch (error) {
    console.error("加载组织列表失败:", error);
    ElMessage.error("加载组织列表失败");
  }
};

// 组织变更处理
const handleOrganizationChange = async (orgId: number) => {
  if (!orgId) {
    generateForm.verification_code = "";
    return;
  }

  try {
    const response = await getOrganizationVerificationCode(orgId);
    generateForm.verification_code = response.verification_code;
  } catch (error) {
    console.error("获取校验码失败:", error);
    ElMessage.error("获取校验码失败");
  }
};

// 生成通行证码
const handleGenerate = async () => {
  if (!generateFormRef.value) return;

  await generateFormRef.value.validate(async (valid) => {
    if (!valid) return;

    try {
      generating.value = true;
      const response = await createOrganizationPassCode(generateForm);
      generatedPassCode.value = response.pass_code;
      ElMessage.success("通行证码生成成功");

      // 刷新列表
      await handleQuery();
    } catch (error: any) {
      console.error("生成通行证码失败:", error);
      ElMessage.error(error.response?.data?.detail || "生成通行证码失败");
    } finally {
      generating.value = false;
    }
  });
};

// 重置表单
const handleResetForm = () => {
  generateFormRef.value?.resetFields();
  generatedPassCode.value = "";
};

// 复制通行证码
const handleCopyPassCode = () => {
  handleCopy(generatedPassCode.value);
};

// 复制到剪贴板
const handleCopy = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text);
    ElMessage.success("复制成功");
  } catch (error) {
    console.error("复制失败:", error);
    ElMessage.error("复制失败");
  }
};

// 查询列表
const handleQuery = async () => {
  try {
    loading.value = true;
    const response = await getOrganizationPassCodeList({
      organization_id: queryForm.organization_id,
      status: queryForm.status,
      page: pagination.page,
      page_size: pagination.page_size,
    });
    tableData.value = response.items || [];
    pagination.total = response.total || 0;
  } catch (error) {
    console.error("查询列表失败:", error);
    ElMessage.error("查询列表失败");
  } finally {
    loading.value = false;
  }
};

// 重置查询
const handleResetQuery = () => {
  queryForm.organization_id = undefined;
  queryForm.status = undefined;
  pagination.page = 1;
  handleQuery();
};

// 导出
const handleExport = async () => {
  try {
    exporting.value = true;
    const response = await exportOrganizationPassCodes({
      organization_id: queryForm.organization_id,
      status: queryForm.status,
    });

    // 创建下载链接
    const blob = new Blob([response], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `组织通行证码列表_${new Date().getTime()}.xlsx`;
    link.click();
    window.URL.revokeObjectURL(url);

    ElMessage.success("导出成功");
  } catch (error) {
    console.error("导出失败:", error);
    ElMessage.error("导出失败");
  } finally {
    exporting.value = false;
  }
};

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return "-";
  const date = new Date(dateStr);
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
};

// 初始化
onMounted(() => {
  loadOrganizations();
  handleQuery();
});
</script>

<style scoped lang="scss">
.pass-code-management {
  padding: 20px;

  .generate-card,
  .list-card {
    margin-bottom: 20px;

    .card-header {
      font-size: 16px;
      font-weight: bold;
    }
  }

  .form-tip {
    margin-left: 10px;
    font-size: 12px;
    color: #909399;
  }

  .generated-result {
    .pass-code-display {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px;
      background-color: #f5f7fa;
      border-radius: 4px;

      .pass-code-text {
        font-size: 18px;
        font-weight: bold;
        color: #409eff;
        font-family: "Courier New", monospace;
      }
    }

    .result-tip {
      margin-top: 10px;
      font-size: 12px;
      color: #e6a23c;
    }
  }

  .query-form {
    margin-bottom: 20px;
  }

  .pass-code-cell {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;

    span {
      font-family: "Courier New", monospace;
    }
  }

  .el-pagination {
    margin-top: 20px;
    justify-content: flex-end;
  }
}
</style>
