<template>
  <div class="forgot-password-page">
    <div class="background-overlay"></div>

    <div class="forgot-container">
      <div class="forgot-card">
        <div class="card-header">
          <div class="icon-wrapper">
            <span class="icon">🔑</span>
          </div>
          <h2>忘记密码</h2>
          <p>使用机器码重置您的密码</p>
        </div>

        <el-steps :active="currentStep" align-center finish-status="success">
          <el-step title="输入信息" />
          <el-step title="验证机器码" />
          <el-step title="重置成功" />
        </el-steps>

        <!-- 步骤1: 输入用户信息 -->
        <div v-if="currentStep === 0" class="step-content">
          <el-form :model="resetForm" label-width="100px">
            <el-form-item label="用户名">
              <el-input
                v-model="resetForm.username"
                placeholder="请输入您的用户名"
                clearable
              />
            </el-form-item>

            <el-form-item label="机器码">
              <el-input
                v-model="resetForm.machine_code"
                placeholder="请输入机器码"
                type="textarea"
                :rows="3"
                clearable
              />
              <div class="form-hint">
                <el-button
                  link
                  type="primary"
                  :loading="loadingMachineCode"
                  @click="useCurrentMachineCode"
                >
                  使用当前机器码
                </el-button>
              </div>
            </el-form-item>

            <el-form-item label="校验码">
              <el-input
                v-model="resetForm.verification_code"
                placeholder="请输入4位数字校验码"
                maxlength="4"
                clearable
              />
              <div class="form-hint">校验码可在"获取机器码"页面查看</div>
            </el-form-item>
          </el-form>

          <div class="action-buttons">
            <el-button @click="goBack">返回登录</el-button>
            <el-button
              type="primary"
              :loading="resetting"
              :disabled="!canSubmit"
              @click="handleResetPassword"
            >
              重置密码
            </el-button>
          </div>
        </div>

        <!-- 步骤2: 重置成功 -->
        <div v-if="currentStep === 1" class="step-content success-content">
          <el-result icon="success" title="密码重置成功">
            <template #sub-title>
              <div class="new-password-display">
                <p>您的新密码是：</p>
                <div class="password-box">
                  <span class="password-text">{{ newPassword }}</span>
                  <el-button
                    link
                    type="primary"
                    style="margin-left: 10px"
                    @click="copyPassword"
                  >
                    复制
                  </el-button>
                </div>
                <el-alert
                  type="warning"
                  :closable="false"
                  style="margin-top: 20px"
                >
                  <template #title>
                    <strong>重要提示：</strong>
                  </template>
                  <div>
                    1. 请妥善保管此密码<br />
                    2. 登录后请立即修改密码<br />
                    3. 此密码仅显示一次，关闭后无法再次查看
                  </div>
                </el-alert>
              </div>
            </template>
            <template #extra>
              <el-button type="primary" @click="goToLogin">
                前往登录
              </el-button>
            </template>
          </el-result>
        </div>
      </div>

      <div class="extra-links">
        <router-link to="/get-machine-code" class="link">
          获取机器码
        </router-link>
        <span class="separator">|</span>
        <router-link to="/login" class="link">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import request from "@/api/request";

const router = useRouter();

const currentStep = ref(0);
const resetting = ref(false);
const loadingMachineCode = ref(false);
const newPassword = ref("");

const resetForm = ref({
  username: "",
  machine_code: "",
  verification_code: "",
});

const canSubmit = computed(() => {
  return (
    !!resetForm.value.username &&
    !!resetForm.value.machine_code &&
    !!resetForm.value.verification_code &&
    resetForm.value.verification_code.length === 4
  );
});

const useCurrentMachineCode = async () => {
  loadingMachineCode.value = true;
  try {
    const response = await request.get("/machine-code/get-machine-code");
    const resData = response.data;
    const payload =
      resData?.code === 200 ? resData.data : (resData?.data ?? resData);
    if (payload?.machine_code) {
      resetForm.value.machine_code = payload.machine_code;
      resetForm.value.verification_code = payload.verification_code ?? "";
      ElMessage.success("已自动填入当前机器码和校验码");
    } else {
      ElMessage.error(resData?.message || "获取机器码失败，请重试");
    }
  } catch (error: any) {
    console.error("[ForgotPassword] 获取机器码失败:", error);
    const msg =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      "获取机器码失败，请检查系统服务是否正常";
    ElMessage.error(msg);
  } finally {
    loadingMachineCode.value = false;
  }
};

const handleResetPassword = async () => {
  if (!canSubmit.value) {
    ElMessage.warning("请填写完整信息");
    return;
  }

  resetting.value = true;

  try {
    const response = await request.post(
      "/machine-code/reset-password-with-machine-code",
      undefined,
      { params: resetForm.value },
    );

    const resData = response.data;
    const payload =
      resData?.code === 200 ? resData.data : (resData?.data ?? resData);
    if (payload?.new_password) {
      newPassword.value = payload.new_password;
      currentStep.value = 1;
      ElMessage.success("密码重置成功");
    } else {
      const errMsg = resData?.message || resData?.detail || "重置密码失败，请检查填写信息";
      ElMessage.error(errMsg);
    }
  } catch (error: any) {
    console.error("[ForgotPassword] 重置密码失败:", error);
    const msg =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      "重置密码失败，请检查网络连接";
    ElMessage.error(msg);
  } finally {
    resetting.value = false;
  }
};

const copyPassword = () => {
  navigator.clipboard.writeText(newPassword.value).then(
    () => {
      ElMessage.success("密码已复制到剪贴板");
    },
    () => {
      ElMessage.error("复制失败，请手动复制");
    },
  );
};

const goBack = () => {
  router.push("/login");
};

const goToLogin = () => {
  router.push("/login");
};
</script>

<style scoped lang="scss">
.forgot-password-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #081c15 0%, #1b4332 100%);
  position: relative;
  padding: 20px;
}

.background-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: url("/images/login-bg/bg1.jpg");
  background-size: cover;
  background-position: center;
  opacity: 0.15;
  z-index: 0;
}

.forgot-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 600px;
}

.forgot-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.card-header {
  text-align: center;
  margin-bottom: 30px;
}

.icon-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #d4af37, #c9a227);
  border-radius: 50%;
  margin-bottom: 20px;
  box-shadow: 0 4px 15px rgba(212, 175, 55, 0.4);
}

.icon {
  font-size: 40px;
}

.card-header h2 {
  font-size: 28px;
  color: #1b4332;
  margin: 0 0 10px 0;
  font-weight: 600;
}

.card-header p {
  color: #666;
  font-size: 15px;
  margin: 0;
}

.step-content {
  margin-top: 30px;
}

.form-hint {
  font-size: 13px;
  color: #909399;
  margin-top: 5px;
}

.action-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 30px;
}

.success-content {
  padding: 20px 0;
}

.new-password-display {
  text-align: center;

  p {
    font-size: 16px;
    color: #606266;
    margin-bottom: 15px;
  }
}

.password-box {
  display: inline-flex;
  align-items: center;
  padding: 15px 25px;
  background: #f5f7fa;
  border: 2px solid #d4af37;
  border-radius: 8px;
  margin-bottom: 10px;
}

.password-text {
  font-size: 24px;
  font-weight: bold;
  color: #1b4332;
  letter-spacing: 2px;
  font-family: "Courier New", monospace;
}

.extra-links {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
}

.link {
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  transition: color 0.3s;

  &:hover {
    color: #d4af37;
  }
}

.separator {
  color: rgba(255, 255, 255, 0.5);
  margin: 0 15px;
}

@media (max-width: 768px) {
  .forgot-card {
    padding: 30px 20px;
  }

  .card-header h2 {
    font-size: 24px;
  }

  .icon-wrapper {
    width: 60px;
    height: 60px;
  }

  .icon {
    font-size: 30px;
  }
}
</style>
