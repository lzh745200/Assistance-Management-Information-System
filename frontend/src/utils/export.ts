/**
 * 导出工具兼容层
 *
 * 重新导出 exportUtil 中的方法，保持旧路径兼容
 */

export { exportUtil, exportUtil as default } from "./exportUtil";
export const exportToExcel = exportUtil.exportToExcel;
export const exportToCSV = exportUtil.exportToCSV;
export const exportToPDF = exportUtil.exportToPDF;
