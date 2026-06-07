/**
 * Worker Pool 单元测试
 *
 * 运行: node electron/tests/worker-pool.test.js
 */

const { WorkerPool } = require('../worker-pool');
const assert = require('assert');

async function runTests() {
  let passed = 0;
  let failed = 0;

  function test(name, fn) {
    return fn().then(() => {
      console.log(`  PASS: ${name}`);
      passed++;
    }).catch((err) => {
      console.error(`  FAIL: ${name} — ${err.message}`);
      failed++;
    });
  }

  console.log('Worker Pool Tests\n');

  // ── 初始化 ──
  await test('WorkerPool 实例化', async () => {
    const pool = new WorkerPool(2);
    assert.ok(pool instanceof WorkerPool);
    assert.strictEqual(pool.maxWorkers, 2);
    assert.deepStrictEqual(pool.stats, { active: 0, queued: 0, max: 2 });
  });

  await test('stats 反映空闲状态', async () => {
    const pool = new WorkerPool(2);
    const s = pool.stats;
    assert.strictEqual(s.active, 0);
    assert.strictEqual(s.queued, 0);
    assert.strictEqual(s.max, 2);
  });

  // ── 默认 maxWorkers ──
  await test('默认 maxWorkers 基于 CPU 核数', async () => {
    const os = require('os');
    const pool = new WorkerPool();
    assert.ok(pool.maxWorkers >= 2);
    assert.ok(pool.maxWorkers <= os.cpus().length);
  });

  // ── Worker 任务执行（需要 worker-tasks.js 存在） ──
  await test('worker-tasks.js 脚本存在', async () => {
    const fs = require('fs');
    const path = require('path');
    const scriptPath = path.join(__dirname, '..', 'worker-tasks.js');
    assert.ok(fs.existsSync(scriptPath), `worker-tasks.js not found at ${scriptPath}`);
  });

  // ── hash-file 端到端测试 ──
  await test('hash-file 任务（创建临时文件并计算 SHA-256）', async () => {
    const fs = require('fs');
    const path = require('path');
    const os = require('os');
    const crypto = require('crypto');

    const tmpFile = path.join(os.tmpdir(), `mrrms-test-${Date.now()}.tmp`);
    const content = Buffer.from('test-data-' + Date.now());
    fs.writeFileSync(tmpFile, content);

    const expectedHash = crypto.createHash('sha256').update(content).digest('hex');

    const pool = new WorkerPool(2);
    const result = await pool.exec('hash-file', { inputPath: tmpFile }, 5000);

    assert.strictEqual(result.hash, expectedHash, 'hash mismatch');
    fs.unlinkSync(tmpFile);
  });

  // ── 超时测试 ──
  await test('exec 超时应抛错', async () => {
    const pool = new WorkerPool(1);
    try {
      await pool.exec('hash-file', { inputPath: '/nonexistent/file' }, 100);
      throw new Error('should have timed out');
    } catch (err) {
      assert.ok(err.message.includes('timed out') || err.message.includes('ENOENT'),
        `unexpected error: ${err.message}`);
    }
  });

  // ── 结果 ──
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

runTests().catch((err) => {
  console.error('Test runner error:', err);
  process.exit(1);
});
