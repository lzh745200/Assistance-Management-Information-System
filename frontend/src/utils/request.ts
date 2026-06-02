/**
 * HTTP 请求工具模块
 *
 * 从 api/request 重新导出，保持向后兼容
 *
 * _需求: 5.3_
 */

import request, {
  get,
  post,
  put,
  del,
  patch,
  cancelRequest,
  cancelAllRequests,
  isRequestCancelled,
  getPendingRequestCount,
  createCancelableRequest,
  requestWithTimeout,
  isSuccess,
  type RequestConfig,
} from "@/api/request";

export default request;

export {
  get,
  post,
  put,
  del,
  patch,
  cancelRequest,
  cancelAllRequests,
  isRequestCancelled,
  getPendingRequestCount,
  createCancelableRequest,
  requestWithTimeout,
  isSuccess,
  type RequestConfig,
};
