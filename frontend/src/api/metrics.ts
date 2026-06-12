/**
 * 监控指标 API
 */

import request from "@/api/request";

/**
 * 获取监控 Dashboard 数据
 */
export function getMetricsDashboard() {
  return request({
    url: "/system/metrics/dashboard",
    method: "get",
  });
}

/**
 * 获取健康指标
 */
export function getHealthMetrics() {
  return request({
    url: "/system/metrics/health",
    method: "get",
  });
}

/**
 * 获取 Prometheus 格式指标
 */
export function getPrometheusMetrics() {
  return request({
    url: "/monitoring/metrics/prometheus",
    method: "get",
    responseType: "text",
  });
}

/**
 * 获取业务指标
 */
export function getBusinessMetrics() {
  return request({
    url: "/monitoring/metrics/business",
    method: "get",
  });
}
