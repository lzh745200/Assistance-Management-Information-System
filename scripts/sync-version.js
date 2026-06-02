#!/usr/bin/env node
/**
 * 版本号同步脚本
 * 从根目录 package.json 读取 version 字段，自动同步到所有相关文件。
 *
 * 用法:
 *   node scripts/sync-version.js          # 同步当前版本
 *   node scripts/sync-version.js 1.0.4    # 设置并同步到指定版本
 */
'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

// ─── 读取/设置版本号 ──────────────────────────
const rootPkgPath = path.join(ROOT, 'package.json');
const rootPkg = JSON.parse(fs.readFileSync(rootPkgPath, 'utf-8'));

const newVersion = process.argv[2] || rootPkg.version;
if (!newVersion || !/^\d+\.\d+\.\d+/.test(newVersion)) {
  console.error('无效的版本号:', newVersion);
  process.exit(1);
}

// 如果指定了新版本号，先更新根 package.json
if (process.argv[2] && rootPkg.version !== newVersion) {
  rootPkg.version = newVersion;
  fs.writeFileSync(rootPkgPath, JSON.stringify(rootPkg, null, 2) + '\n', 'utf-8');
  console.log(`  [ROOT] package.json → ${newVersion}`);
}

console.log(`\n同步版本号: ${newVersion}\n`);

let updatedCount = 0;

// ─── 辅助函数 ──────────────────────────────────
function replaceInFile(relPath, pattern, replacement) {
  const absPath = path.join(ROOT, relPath);
  if (!fs.existsSync(absPath)) {
    console.log(`  [SKIP] ${relPath} (文件不存在)`);
    return;
  }
  let content = fs.readFileSync(absPath, 'utf-8');
  const newContent = content.replace(pattern, replacement);
  if (content !== newContent) {
    fs.writeFileSync(absPath, newContent, 'utf-8');
    console.log(`  [OK]   ${relPath}`);
    updatedCount++;
  } else {
    console.log(`  [--]   ${relPath} (已是最新)`);
  }
}

function updateJsonFile(relPath, jsonPath) {
  const absPath = path.join(ROOT, relPath);
  if (!fs.existsSync(absPath)) {
    console.log(`  [SKIP] ${relPath} (文件不存在)`);
    return;
  }
  const obj = JSON.parse(fs.readFileSync(absPath, 'utf-8'));
  const keys = jsonPath.split('.');
  let target = obj;
  for (let i = 0; i < keys.length - 1; i++) {
    target = target[keys[i]];
  }
  const lastKey = keys[keys.length - 1];
  if (target[lastKey] !== newVersion) {
    target[lastKey] = newVersion;
    fs.writeFileSync(absPath, JSON.stringify(obj, null, 2) + '\n', 'utf-8');
    console.log(`  [OK]   ${relPath} → ${jsonPath}`);
    updatedCount++;
  } else {
    console.log(`  [--]   ${relPath} (已是最新)`);
  }
}

// ─── 执行同步 ──────────────────────────────────

// 1. frontend/package.json
updateJsonFile('frontend/package.json', 'version');

// 2. resources/config/default.json
updateJsonFile('resources/config/default.json', 'app.version');

// 3. frontend/src/config/constants.ts
replaceInFile(
  'frontend/src/config/constants.ts',
  /export const SYSTEM_VERSION = "[^"]+"/,
  `export const SYSTEM_VERSION = "${newVersion}"`
);

// 4. frontend/src/config/appConfig.ts
replaceInFile(
  'frontend/src/config/appConfig.ts',
  /version: "[^"]+"/,
  `version: "${newVersion}"`
);

// 5. frontend/src/stores/app.ts
replaceInFile(
  'frontend/src/stores/app.ts',
  /version: '[^']+'/,
  `version: '${newVersion}'`
);

// 6. frontend/src/utils/local-storage.ts
replaceInFile(
  'frontend/src/utils/local-storage.ts',
  /version: '[^']+'/,
  `version: '${newVersion}'`
);

// 7. backend/app/core/config.py
replaceInFile(
  'backend/app/core/config.py',
  /PROJECT_VERSION: str = "[^"]+"/,
  `PROJECT_VERSION: str = "${newVersion}"`
);

// 8. .env.example
replaceInFile(
  '.env.example',
  /PROJECT_VERSION=.*/,
  `PROJECT_VERSION=${newVersion}`
);

// 9. Dockerfile
replaceInFile(
  'Dockerfile',
  /version="[^"]+"/,
  `version="${newVersion}"`
);

// 10. LoginSafe.vue 版权行（硬编码版本号）
replaceInFile(
  'frontend/src/views/auth/LoginSafe.vue',
  /V\d+\.\d+\.\d+/,
  `V${newVersion}`
);

// 11. SystemConfig.vue DEFAULTS
replaceInFile(
  'frontend/src/views/system/SystemConfig.vue',
  /version: 'V[^']+'/,
  `version: 'V${newVersion}'`
);

// 12. generate_ppt.py
replaceInFile(
  'scripts/build/generate_ppt.py',
  /版本 \d+\.\d+\.\d+/g,
  `版本 ${newVersion}`
);
replaceInFile(
  'scripts/build/generate_ppt.py',
  /v\d+\.\d+\.\d+/g,
  `v${newVersion}`
);

console.log(`\n完成: 更新了 ${updatedCount} 个文件\n`);
