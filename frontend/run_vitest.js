const { execSync } = require('child_process');
const fs = require('fs');
const path = 'c:\\military-Rural Revitalization-system\\frontend';

console.log('Starting vitest...');
try {
  const r = execSync('npx vitest run --coverage', {
    cwd: path,
    timeout: 600000,
    encoding: 'utf8',
    stdio: 'pipe'
  });
  fs.writeFileSync(path + '\\vitest_out.txt', r);
  console.log('DONE - passed');
} catch(e) {
  const out = (e.stdout || '') + (e.stderr || '') + (e.message || '');
  fs.writeFileSync(path + '\\vitest_out.txt', out);
  console.log('DONE - failed');
}
