/**
 * 数据库健康检查工具
 */

import { localDatabase } from "./LocalDatabase";
import { logger } from "./logger";

export interface HealthReport {
  overall: "healthy" | "warning" | "error";
  checks: Record<string, { status: string; message: string }>;
  timestamp: string;
}

export interface RepairResult {
  success: boolean;
  repaired: string[];
  failed: string[];
}

/**
 * 检查数据库健康状态
 */
export async function checkDatabaseHealth(): Promise<HealthReport> {
  const report: HealthReport = {
    overall: "healthy",
    checks: {},
    timestamp: new Date().toISOString(),
  };

  try {
    // 检查存储可用性
    const storageCheck = await checkStorageAvailability();
    report.checks.storage = storageCheck;

    // 检查数据完整性
    const integrityCheck = await checkDataIntegrity();
    report.checks.integrity = integrityCheck;

    // 检查必要表
    const tablesCheck = await checkRequiredTables();
    report.checks.tables = tablesCheck;

    // 计算总体状态
    const statuses = Object.values(report.checks).map((c) => c.status);
    if (statuses.includes("error")) {
      report.overall = "error";
    } else if (statuses.includes("warning")) {
      report.overall = "warning";
    }

    logger.info("数据库健康检查完成", report);
  } catch (error) {
    report.overall = "error";
    report.checks.general = {
      status: "error",
      message: error instanceof Error ? error.message : "未知错误",
    };
    logger.error(
      "数据库健康检查失败",
      error instanceof Error ? error : new Error(String(error)),
    );
  }

  return report;
}

/**
 * 修复数据库问题
 */
export async function repairDatabase(): Promise<RepairResult> {
  const result: RepairResult = {
    success: true,
    repaired: [],
    failed: [],
  };

  try {
    // 尝试初始化缺失的表
    const tables = ["users", "projects", "armyPersonnel", "ruralWorks"];

    for (const table of tables) {
      try {
        const data = await localDatabase.getAll(table);
        if (!data) {
          // 表不存在，尝试创建
          await localDatabase.add(table, { _init: true });
          await localDatabase.delete(table, 1);
          result.repaired.push(`表 ${table} 已创建`);
        }
      } catch (error) {
        result.failed.push(`表 ${table} 修复失败`);
      }
    }

    result.success = result.failed.length === 0;
    logger.info("数据库修复完成", result);
  } catch (error) {
    result.success = false;
    result.failed.push("修复过程发生错误");
    logger.error(
      "数据库修复失败",
      error instanceof Error ? error : new Error(String(error)),
    );
  }

  return result;
}

/**
 * 检查存储可用性
 */
async function checkStorageAvailability(): Promise<{
  status: string;
  message: string;
}> {
  try {
    const storage = await localDatabase.checkStorage();
    const usagePercent =
      storage.total > 0 ? (storage.used / storage.total) * 100 : 0;

    if (!storage.available) {
      return { status: "error", message: "存储不可用" };
    }

    if (usagePercent > 90) {
      return {
        status: "warning",
        message: `存储使用率: ${usagePercent.toFixed(1)}%`,
      };
    }

    return {
      status: "healthy",
      message: `存储使用率: ${usagePercent.toFixed(1)}%`,
    };
  } catch {
    return { status: "error", message: "无法检查存储状态" };
  }
}

/**
 * 检查数据完整性
 */
async function checkDataIntegrity(): Promise<{
  status: string;
  message: string;
}> {
  try {
    const isValid = await localDatabase.validateDataIntegrity();
    return isValid
      ? { status: "healthy", message: "数据完整性正常" }
      : { status: "warning", message: "数据可能不完整" };
  } catch {
    return { status: "error", message: "数据完整性检查失败" };
  }
}

/**
 * 检查必要表
 */
async function checkRequiredTables(): Promise<{
  status: string;
  message: string;
}> {
  try {
    const requiredTables = ["users", "projects"];
    const missingTables: string[] = [];

    for (const table of requiredTables) {
      try {
        await localDatabase.getAll(table);
      } catch {
        missingTables.push(table);
      }
    }

    if (missingTables.length > 0) {
      return {
        status: "warning",
        message: `缺失表: ${missingTables.join(", ")}`,
      };
    }

    return { status: "healthy", message: "所有必要表存在" };
  } catch {
    return { status: "error", message: "表检查失败" };
  }
}

export default {
  checkDatabaseHealth,
  repairDatabase,
};
