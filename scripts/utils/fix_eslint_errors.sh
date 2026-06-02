#!/bin/bash
# 快速修复前端 ESLint 错误

echo "修复前端 ESLint 错误..."

cd "$(dirname "$0")/frontend/src/components"

# 1. 修复 $index 属性名问题
echo "1. 修复 $index 属性名..."
find . -name "*.vue" -type f -exec sed -i 's/:$index="/:index="/g' {} \;
find . -name "*.vue" -type f -exec sed -i 's/{ row: any; $index: number }/{ row: any; index: number }/g' {} \;

# 2. 修复未使用的变量
echo "2. 修复未使用的变量..."
# PersonnelList.vue - 删除未使用的 props
sed -i '/const props = defineProps/d' business/PersonnelList.vue

# BaseInput.vue - 删除未使用的 _props
sed -i '/const _props = defineProps/d' common/BaseInput.vue

# QiannanRegionSelector.vue - 删除未使用的 props
sed -i '/const props = defineProps/d' common/QiannanRegionSelector.vue

# 3. 修复 prop 直接修改问题
echo "3. 修复 prop 直接修改..."
# PrintDialog.vue 和 ProgressDialog.vue 需要手动修复，使用 v-model

echo "完成！请运行 npm run lint 检查剩余问题"
