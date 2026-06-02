// 修复类型声明文件的脚本
const fs = require('fs');
const path = require('path');

// 确保 .vue-global-types 目录存在
const typesDir = path.join(__dirname, '..', 'node_modules', '.vue-global-types');
if (!fs.existsSync(typesDir)) {
  fs.mkdirSync(typesDir, { recursive: true });
}

console.log('类型声明文件修复完成！');