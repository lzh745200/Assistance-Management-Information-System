#!/usr/bin/env node
/**
 * 前端代码质量检测脚本
 * 用法: npm run quality:check
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');
const reportDir = path.join(rootDir, 'quality-reports');

// 创建报告目录
if (!fs.existsSync(reportDir)) {
  fs.mkdirSync(reportDir, { recursive: true });
}

const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);

console.log('=========================================');
console.log('前端代码质量检测开始');
console.log('=========================================');
console.log('');

// 辅助函数：执行命令并捕获输出
function runCommand(command, description, outputFile = null) {
  console.log('=========================================');
  console.log(description);
  console.log('=========================================');

  try {
    const output = execSync(command, {
      cwd: rootDir,
      encoding: 'utf-8',
      stdio: outputFile ? 'pipe' : 'inherit'
    });

    if (outputFile && output) {
      const filePath = path.join(reportDir, outputFile);
      fs.writeFileSync(filePath, output);
      console.log(`📄 报告已保存: ${outputFile}`);
    }

    console.log('✅ 检查通过');
    return { success: true, output };
  } catch (error) {
    if (outputFile && error.stdout) {
      const filePath = path.join(reportDir, outputFile);
      fs.writeFileSync(filePath, error.stdout);
      console.log(`📄 报告已保存: ${outputFile}`);
    }
    console.log('⚠️  发现问题');
    return { success: false, output: error.stdout || error.message };
  } finally {
    console.log('');
  }
}

// 1. ESLint 检查
const eslintResult = runCommand(
  'npx eslint src --ext .vue,.js,.ts --format json',
  '1. ESLint 代码规范检查',
  `eslint_${timestamp}.json`
);

// 生成 ESLint 文本报告
if (!eslintResult.success) {
  runCommand(
    'npx eslint src --ext .vue,.js,.ts',
    '   生成可读报告',
    `eslint_${timestamp}.txt`
  );
}

// 2. TypeScript 类型检查
runCommand(
  'npx vue-tsc --noEmit',
  '2. TypeScript 类型检查',
  `typecheck_${timestamp}.txt`
);

// 3. 安全漏洞扫描
console.log('=========================================');
console.log('3. npm audit 安全漏洞扫描');
console.log('=========================================');
try {
  const auditOutput = execSync('npm audit --json', {
    cwd: rootDir,
    encoding: 'utf-8'
  });

  const auditData = JSON.parse(auditOutput);
  const auditFile = path.join(reportDir, `npm-audit_${timestamp}.json`);
  fs.writeFileSync(auditFile, JSON.stringify(auditData, null, 2));

  console.log(`📊 漏洞统计:`);
  console.log(`  🔴 严重: ${auditData.metadata?.vulnerabilities?.critical || 0}`);
  console.log(`  🟠 高危: ${auditData.metadata?.vulnerabilities?.high || 0}`);
  console.log(`  🟡 中危: ${auditData.metadata?.vulnerabilities?.moderate || 0}`);
  console.log(`  🟢 低危: ${auditData.metadata?.vulnerabilities?.low || 0}`);
  console.log(`📄 报告已保存: npm-audit_${timestamp}.json`);
} catch (error) {
  console.log('⚠️  发现安全漏洞');
  if (error.stdout) {
    const auditFile = path.join(reportDir, `npm-audit_${timestamp}.json`);
    fs.writeFileSync(auditFile, error.stdout);
    console.log(`📄 报告已保存: npm-audit_${timestamp}.json`);
  }
}
console.log('');

// 4. 依赖过期检查
console.log('=========================================');
console.log('4. 依赖包版本检查');
console.log('=========================================');
try {
  const ncuOutput = execSync('npx npm-check-updates --format json', {
    cwd: rootDir,
    encoding: 'utf-8'
  });

  const ncuFile = path.join(reportDir, `ncu_${timestamp}.json`);
  fs.writeFileSync(ncuFile, ncuOutput);

  const ncuData = JSON.parse(ncuOutput);
  const outdatedCount = Object.keys(ncuData).length;

  if (outdatedCount > 0) {
    console.log(`⚠️  发现 ${outdatedCount} 个可更新的依赖包`);
    console.log('运行 "npx npm-check-updates -u" 更新 package.json');
  } else {
    console.log('✅ 所有依赖包都是最新版本');
  }

  console.log(`📄 报告已保存: ncu_${timestamp}.json`);
} catch (error) {
  console.log('⚠️  检查失败');
}
console.log('');

// 5. 测试覆盖率
runCommand(
  'npm run test:coverage',
  '5. 测试覆盖率检查',
  `coverage_${timestamp}.txt`
);

// 6. 构建大小分析
console.log('=========================================');
console.log('6. 构建产物大小分析');
console.log('=========================================');
try {
  execSync('npm run build', {
    cwd: rootDir,
    stdio: 'inherit'
  });

  // 分析 dist 目录大小
  const distDir = path.join(rootDir, 'dist');
  if (fs.existsSync(distDir)) {
    const getDirectorySize = (dir) => {
      let size = 0;
      const files = fs.readdirSync(dir);

      for (const file of files) {
        const filePath = path.join(dir, file);
        const stats = fs.statSync(filePath);

        if (stats.isDirectory()) {
          size += getDirectorySize(filePath);
        } else {
          size += stats.size;
        }
      }

      return size;
    };

    const totalSize = getDirectorySize(distDir);
    const sizeMB = (totalSize / 1024 / 1024).toFixed(2);

    console.log(`📦 构建产物总大小: ${sizeMB} MB`);

    // 保存构建分析
    const buildInfo = {
      timestamp: new Date().toISOString(),
      totalSize: totalSize,
      totalSizeMB: sizeMB
    };

    const buildFile = path.join(reportDir, `build-size_${timestamp}.json`);
    fs.writeFileSync(buildFile, JSON.stringify(buildInfo, null, 2));
    console.log(`📄 报告已保存: build-size_${timestamp}.json`);
  }
} catch (error) {
  console.log('⚠️  构建失败');
}
console.log('');

// 7. 代码复杂度分析（使用 ESLint complexity 规则）
console.log('=========================================');
console.log('7. 代码复杂度分析');
console.log('=========================================');
try {
  const complexityOutput = execSync(
    'npx eslint src --ext .vue,.js,.ts --rule "complexity: [error, 15]" --format json',
    {
      cwd: rootDir,
      encoding: 'utf-8'
    }
  );

  const complexityFile = path.join(reportDir, `complexity_${timestamp}.json`);
  fs.writeFileSync(complexityFile, complexityOutput);
  console.log('✅ 代码复杂度符合标准（< 15）');
  console.log(`📄 报告已保存: complexity_${timestamp}.json`);
} catch (error) {
  if (error.stdout) {
    const complexityFile = path.join(reportDir, `complexity_${timestamp}.json`);
    fs.writeFileSync(complexityFile, error.stdout);

    const data = JSON.parse(error.stdout);
    const complexFiles = data.filter(f => f.errorCount > 0).length;
    console.log(`⚠️  发现 ${complexFiles} 个文件复杂度过高`);
    console.log(`📄 报告已保存: complexity_${timestamp}.json`);
  }
}
console.log('');

// 8. 统计 any 类型使用情况
console.log('=========================================');
console.log('8. TypeScript any 类型使用统计');
console.log('=========================================');
try {
  const grepOutput = execSync(
    'grep -r ": any" src --include="*.ts" --include="*.vue" || true',
    {
      cwd: rootDir,
      encoding: 'utf-8',
      shell: '/bin/bash'
    }
  );

  const anyCount = grepOutput.split('\n').filter(line => line.trim()).length;
  console.log(`⚠️  发现 ${anyCount} 处使用 any 类型`);
  console.log('建议: 使用具体类型替代 any，提升类型安全');

  const anyFile = path.join(reportDir, `any-usage_${timestamp}.txt`);
  fs.writeFileSync(anyFile, grepOutput);
  console.log(`📄 报告已保存: any-usage_${timestamp}.txt`);
} catch (error) {
  console.log('✅ 未发现 any 类型使用');
}
console.log('');

// 9. 统计 v-html 使用情况（XSS 风险）
console.log('=========================================');
console.log('9. XSS 风险检查 (v-html 使用)');
console.log('=========================================');
try {
  const vhtmlOutput = execSync(
    'grep -r "v-html" src --include="*.vue" || true',
    {
      cwd: rootDir,
      encoding: 'utf-8',
      shell: '/bin/bash'
    }
  );

  const vhtmlCount = vhtmlOutput.split('\n').filter(line => line.trim()).length;

  if (vhtmlCount > 0) {
    console.log(`⚠️  发现 ${vhtmlCount} 处使用 v-html`);
    console.log('建议: 确保所有 v-html 内容都经过 DOMPurify 清理');

    const vhtmlFile = path.join(reportDir, `v-html-usage_${timestamp}.txt`);
    fs.writeFileSync(vhtmlFile, vhtmlOutput);
    console.log(`📄 报告已保存: v-html-usage_${timestamp}.txt`);
  } else {
    console.log('✅ 未发现 v-html 使用');
  }
} catch (error) {
  console.log('✅ 未发现 v-html 使用');
}
console.log('');

// 10. 统计 console.log 使用情况
console.log('=========================================');
console.log('10. 生产代码清理检查 (console.log)');
console.log('=========================================');
try {
  const consoleOutput = execSync(
    'grep -r "console\\." src --include="*.ts" --include="*.vue" --include="*.js" || true',
    {
      cwd: rootDir,
      encoding: 'utf-8',
      shell: '/bin/bash'
    }
  );

  const consoleCount = consoleOutput.split('\n').filter(line => line.trim() && !line.includes('logger')).length;

  if (consoleCount > 0) {
    console.log(`⚠️  发现 ${consoleCount} 处使用 console`);
    console.log('建议: 生产环境应使用统一的 logger 工具');

    const consoleFile = path.join(reportDir, `console-usage_${timestamp}.txt`);
    fs.writeFileSync(consoleFile, consoleOutput);
    console.log(`📄 报告已保存: console-usage_${timestamp}.txt`);
  } else {
    console.log('✅ 未发现直接使用 console');
  }
} catch (error) {
  console.log('✅ 未发现直接使用 console');
}
console.log('');

// 汇总报告
console.log('=========================================');
console.log('检测完成！');
console.log('=========================================');
console.log('');
console.log(`📁 所有报告保存在: ${reportDir}/`);
console.log('');
console.log('💡 建议:');
console.log('  1. 优先修复安全漏洞（npm audit）');
console.log('  2. 减少 any 类型使用，提升类型安全');
console.log('  3. 确保 v-html 内容经过清理');
console.log('  4. 保持测试覆盖率在 80% 以上');
console.log('  5. 定期更新依赖包');
console.log('');
