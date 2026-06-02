<template>
  <div class="form-wizard" role="form" :aria-label="title">
    <!-- 步骤指示器 -->
    <el-steps
      :active="currentStep"
      finish-status="success"
      align-center
      class="mb-6"
      aria-label="表单步骤"
    >
      <el-step
        v-for="(step, index) in steps"
        :key="index"
        :title="step.title"
        :description="step.description"
        :status="stepStatus(index)"
      />
    </el-steps>

    <!-- 步骤内容 -->
    <div class="step-content" role="region" :aria-label="`步骤 ${currentStep + 1}: ${steps[currentStep]?.title}`">
      <slot :name="`step-${currentStep}`" :step="currentStep" :data="formData" />
    </div>

    <!-- 操作按钮 -->
    <div class="step-actions">
      <el-button v-if="currentStep > 0" @click="prevStep" :disabled="isPending">
        上一步
      </el-button>
      <el-button
        v-if="currentStep < steps.length - 1"
        type="primary"
        @click="nextStep"
        :loading="isPending"
      >
        下一步
      </el-button>
      <el-button
        v-else
        type="primary"
        @click="finish"
        :loading="isPending"
      >
        {{ finishText }}
      </el-button>
      <el-button @click="reset">重置</el-button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"

export interface WizardStep {
  title: string
  description?: string
  /** 步骤验证函数，返回 true 方可进入下一步 */
  validate?: (data: Record<string, any>) => boolean | Promise<boolean>
}

const props = defineProps<{
  steps: WizardStep[]
  title?: string
  finishText?: string
}>()

const emit = defineEmits<{
  (e: "finish", data: Record<string, any>): void
  (e: "step-change", step: number): void
}>()

const currentStep = ref(0)
const isPending = ref(false)
const formData = ref<Record<string, any>>({})

const stepErrors = ref<Record<number, boolean>>({})

type StepStatus = "success" | "error" | "process" | "wait" | "finish"

function stepStatus(index: number): StepStatus {
  if (index < currentStep.value) return "success"
  if (index === currentStep.value && stepErrors.value[index]) return "error"
  if (index === currentStep.value) return "process"
  return "wait"
}

/** Shared validation — returns true if the current step passes (or has no validator). */
async function validateCurrentStep(): Promise<boolean> {
  const step = props.steps[currentStep.value]
  if (!step?.validate) return true
  isPending.value = true
  try {
    const valid = await step.validate(formData.value)
    if (!valid) stepErrors.value[currentStep.value] = true
    return valid
  } finally {
    isPending.value = false
  }
}

async function nextStep() {
  if (!(await validateCurrentStep())) return
  stepErrors.value[currentStep.value] = false
  currentStep.value++
  emit("step-change", currentStep.value)
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
    emit("step-change", currentStep.value)
  }
}

async function finish() {
  if (!(await validateCurrentStep())) return
  emit("finish", formData.value)
}

function reset() {
  currentStep.value = 0
  formData.value = {}
  stepErrors.value = {}
}
</script>

<style scoped>
.form-wizard {
  padding: 16px;
}

.mb-6 {
  margin-bottom: 24px;
}

.step-content {
  min-height: 200px;
  padding: 16px 0;
}

.step-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-light);
}

.auto-save-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
</style>
