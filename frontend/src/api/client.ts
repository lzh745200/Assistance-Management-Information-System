/**
 * API 客户端
 *
 * 复用 request.ts 的 axios 实例，统一拦截逻辑（token 自动刷新、离线 mock 等）。
 * 保留此文件以兼容已有 import，避免引入第二套独立实例导致行为不一致。
 */
import request from "./request";

export default request;
