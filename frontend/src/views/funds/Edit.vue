<template>
  <div class="fund-edit">
    <el-card class="edit-card">
      <template #header>
        <div class="card-header">
          <span class="title">{{
            isEdit ? "编辑经费记录" : "新增经费记录"
          }}</span>
          <el-button @click="handleBack">返回列表</el-button>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="120px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="项目名称" prop="projectName">
              <el-input
                v-model="formData.projectName"
                placeholder="请输入项目名称"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="资金类型" prop="type">
              <el-select
                v-model="formData.type"
                placeholder="请选择"
                style="width: 100%"
              >
                <el-option label="专项资金" value="special" />
                <el-option label="配套资金" value="matching" />
                <el-option label="捐赠资金" value="donation" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="总金额" prop="amount">
              <el-input-number
                v-model="formData.amount"
                :min="0"
                :precision="2"
                controls-position="right"
                style="width: 100%"
              >
                <template #append>万元</template>
              </el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="已使用金额" prop="usedAmount">
              <el-input-number
                v-model="formData.usedAmount"
                :min="0"
                :max="formData.amount"
                :precision="2"
                controls-position="right"
                style="width: 100%"
              >
                <template #append>万元</template>
              </el-input-number>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="拨付日期" prop="allocateDate">
              <el-date-picker
                v-model="formData.allocateDate"
                type="date"
                placeholder="选择日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="使用状态" prop="status">
              <el-select
                v-model="formData.status"
                placeholder="请选择"
                style="width: 100%"
              >
                <el-option label="已拨付" value="allocated" />
                <el-option label="使用中" value="using" />
                <el-option label="已核销" value="settled" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="使用单位" prop="unit">
              <el-input v-model="formData.unit" placeholder="请输入使用单位" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="负责人" prop="manager">
              <el-input
                v-model="formData.manager"
                placeholder="请输入负责人姓名"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="用途说明" prop="purpose">
          <el-input
            v-model="formData.purpose"
            type="textarea"
            :rows="3"
            placeholder="请输入资金用途说明"
          />
        </el-form-item>

        <el-form-item label="备注" prop="remarks">
          <el-input
            v-model="formData.remarks"
            type="textarea"
            :rows="2"
            placeholder="请输入备注信息"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="submitLoading"
            @click="handleSubmit"
          >
            {{ isEdit ? "保存修改" : "立即创建" }}
          </el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button @click="handleBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { logger } from "@/utils/logger";

import { ref, reactive, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useRouterSafe } from "@/composables/useRouterSafe";
import { ElMessage, type FormInstance } from "element-plus";
import request from "@/api/request";

type FormRules = Record<string, any>;

const router = useRouter();
const { pushSafe } = useRouterSafe();
const route = useRoute();
const formRef = ref<FormInstance>();
const submitLoading = ref(false);
const isEdit = ref(false);

const formData = reactive({
  id: "" as string | number,
  projectName: "",
  type: "",
  amount: 0,
  usedAmount: 0,
  allocateDate: "" as string | Date,
  status: "pending",
  unit: "",
  manager: "",
  purpose: "",
  remarks: "",
});

const rules: FormRules = {
  projectName: [
    { required: true, message: "请输入项目名称", trigger: ["blur", "change"] },
    {
      max: 200,
      message: "项目名称不能超过200个字符",
      trigger: ["blur", "change"],
    },
  ],
  type: [{ required: true, message: "请选择资金类型", trigger: "change" }],
  amount: [
    { required: true, message: "请输入总金额", trigger: ["blur", "change"] },
    {
      type: "number",
      min: 0,
      message: "金额不得为负数",
      trigger: ["blur", "change"],
    },
  ],
  usedAmount: [
    {
      type: "number",
      min: 0,
      message: "已使用金额不得为负数",
      trigger: ["blur", "change"],
    },
  ],
  allocateDate: [
    { required: true, message: "请选择拨付日期", trigger: "change" },
  ],
  unit: [
    { required: true, message: "请输入使用单位", trigger: ["blur", "change"] },
    {
      max: 200,
      message: "使用单位不能超过200个字符",
      trigger: ["blur", "change"],
    },
  ],
  manager: [
    {
      max: 50,
      message: "负责人姓名不能超过50个字符",
      trigger: ["blur", "change"],
    },
  ],
  status: [{ required: true, message: "请选择使用状态", trigger: "change" }],
};

/** 后端字段 → 前端表单字段映射 */
const loadData = async (id: string | number) => {
  try {
    const response = await request.get(`/funds/${id}`);
    const d = response.data;
    if (d) {
      formData.id = d.id;
      formData.projectName = d.project_name || d.name || "";
      formData.type = d.type || "";
      formData.amount = Number(d.amount) || 0;
      formData.usedAmount = Number(d.used_amount) || 0;
      formData.allocateDate = d.date || d.allocation_date || "";
      formData.status = d.status || "pending";
      formData.unit = d.source || "";
      formData.manager = d.operator || "";
      formData.purpose = d.purpose || "";
      formData.remarks = d.remarks || "";
    }
  } catch (error) {
    logger.error("[FundEdit] 加载数据失败:", error);
    ElMessage.error("加载数据失败");
  }
};

/** 前端表单字段 → 后端 API 字段映射 */
function buildPayload() {
  // 处理日期格式
  let dateValue = null;
  if (formData.allocateDate) {
    if (typeof formData.allocateDate === "string") {
      dateValue = formData.allocateDate;
    } else if (formData.allocateDate instanceof Date) {
      dateValue = formData.allocateDate.toISOString().split("T")[0];
    }
  }

  // 确保数字字段有有效的默认值
  const amount = formData.amount ?? 0;
  const usedAmount = formData.usedAmount ?? 0;

  return {
    name: formData.projectName || null,
    type: formData.type || null,
    amount: amount,
    planned_amount: amount,
    used_amount: usedAmount,
    date: dateValue,
    status: formData.status || "pending",
    source: formData.unit || null,
    operator: formData.manager || null,
    purpose: formData.purpose || null,
    remarks: formData.remarks || null,
  };
}

const handleSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true;
      try {
        const payload = buildPayload();

        if (isEdit.value && formData.id && formData.id !== "null") {
          await request.put(`/funds/${formData.id}`, payload);
          ElMessage.success("修改成功");
        } else {
          await request.post("/funds", payload);
          ElMessage.success("创建成功");
        }

        setTimeout(() => {
          pushSafe("/funds/list");
        }, 300);
      } catch (error: any) {
        const detail = error?.response?.data?.detail;
        const errorMsg = detail || error?.message || "保存失败，请重试";
        logger.error("[FundEdit] 保存失败:", error);
        ElMessage.error(errorMsg);
      } finally {
        submitLoading.value = false;
      }
    }
  });
};

const handleReset = () => {
  formRef.value?.resetFields();
};

const handleBack = () => {
  router.back();
};

onMounted(() => {
  const id = route.params.id as string;
  // id 必须是有效数字才进入编辑模式，"null"/"undefined" 等无效值视为创建模式
  if (id && id !== "null" && id !== "undefined" && !isNaN(Number(id))) {
    isEdit.value = true;
    loadData(id);
  }
});
</script>

<style scoped>
.fund-edit {
  padding: 20px;
}

.edit-card {
  background: rgba(10, 30, 20, 0.5);
  border: 1px solid rgba(64, 145, 108, 0.3);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 16px;
  font-weight: bold;
  color: #fff;
}

:deep(.el-card__header) {
  background: linear-gradient(135deg, #2d6a4f 0%, #1b4332 100%);
  border-bottom: 1px solid rgba(64, 145, 108, 0.3);
  color: #fff;
}

:deep(.el-form-item__label) {
  color: rgba(255, 255, 255, 0.9);
}

:deep(.el-input__wrapper) {
  background: rgba(10, 30, 20, 0.5);
  border: 1px solid rgba(64, 145, 108, 0.3);
}

:deep(.el-input__inner) {
  color: rgba(255, 255, 255, 0.9);
}

:deep(.el-textarea__inner) {
  background: rgba(10, 30, 20, 0.5);
  border-color: rgba(64, 145, 108, 0.3);
  color: rgba(255, 255, 255, 0.9);
}
</style>
