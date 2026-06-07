/**
 * Electron Worker Thread Pool
 *
 * 将 CPU/IO 密集型任务从主进程转移到 Worker 线程，防止 UI 假死。
 *
 * 支持任务类型：
 *   - encrypt-file:   AES-256-GCM 文件加密
 *   - decrypt-file:   文件解密
 *   - hash-file:      SHA-256 文件哈希（用于完整性校验）
 *   - compress:       gzip 压缩大 JSON
 *   - decompress:     gzip 解压
 *
 * Usage:
 *   const { workerPool } = require('./worker-pool');
 *   const result = await workerPool.exec('encrypt-file', { inputPath, outputPath, key });
 */

const { Worker } = require('worker_threads');
const path = require('path');
const os = require('os');

const MAX_WORKERS = Math.max(2, os.cpus().length - 1);
const WORKER_SCRIPT = path.join(__dirname, 'worker-tasks.js');

class WorkerPool {
  constructor(maxWorkers = MAX_WORKERS) {
    this.maxWorkers = maxWorkers;
    this._workers = [];
    this._queue = [];
    this._active = 0;
    this._idCounter = 0;
  }

  /**
   * 执行任务
   * @param {string} task - 任务类型
   * @param {object} payload - 任务参数
   * @param {number} [timeout=120000] - 超时 (ms)
   * @returns {Promise<any>}
   */
  exec(task, payload, timeout = 120000) {
    return new Promise((resolve, reject) => {
      const id = ++this._idCounter;
      const timer = setTimeout(() => {
        reject(new Error(`Worker task "${task}" timed out after ${timeout}ms`));
        this._cleanup(id);
      }, timeout);

      this._queue.push({ id, task, payload, resolve, reject, timer });
      this._processNext();
    });
  }

  _processNext() {
    if (this._queue.length === 0) return;
    if (this._active >= this.maxWorkers) return;

    const job = this._queue.shift();
    this._active++;

    const worker = new Worker(WORKER_SCRIPT, {
      workerData: { task: job.task, payload: job.payload },
    });

    worker.on('message', (result) => {
      clearTimeout(job.timer);
      if (result.error) {
        job.reject(new Error(result.error));
      } else {
        job.resolve(result.data);
      }
      this._active--;
      worker.terminate();
      this._processNext();
    });

    worker.on('error', (err) => {
      clearTimeout(job.timer);
      job.reject(err);
      this._active--;
      this._processNext();
    });

    worker.on('exit', (code) => {
      if (code !== 0) {
        clearTimeout(job.timer);
        job.reject(new Error(`Worker exited with code ${code}`));
        this._active--;
        this._processNext();
      }
    });
  }

  _cleanup(id) {
    this._queue = this._queue.filter((j) => j.id !== id);
  }

  get stats() {
    return { active: this._active, queued: this._queue.length, max: this.maxWorkers };
  }
}

// 单例
const workerPool = new WorkerPool();
module.exports = { WorkerPool, workerPool };
