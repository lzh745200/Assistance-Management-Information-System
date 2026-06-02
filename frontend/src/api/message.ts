/**
 * 消息通知API服务
 * Feature: production-deployment-readiness
 * Requirements: 5.1, 5.2, 5.3, 5.7, 6.2
 */

import { get, post, put, del, apiRequest } from "./request";

// ==================== 类型定义 ====================

/** 消息类型 */
export type MessageType = "system" | "approval" | "task";

/** 站内消息 */
export interface Message {
  id: number;
  user_id: number;
  message_type: MessageType;
  title: string;
  content: string;
  link?: string;
  is_read: boolean;
  created_at: string;
  read_at?: string;
}

/** 消息列表响应 */
export interface MessageListResponse {
  items: Message[];
  total: number;
  page: number;
  page_size: number;
  unread_count: number;
}

/** 通知偏好 */
export interface NotificationPreference {
  id?: number;
  user_id?: number;
  email_approval: boolean;
  email_task: boolean;
  email_system: boolean;
  site_approval: boolean;
  site_task: boolean;
  site_system: boolean;
}

/** 消息模板 */
export interface MessageTemplate {
  id: number;
  code: string;
  name: string;
  message_type: MessageType;
  title_template: string;
  content_template: string;
  email_subject_template?: string;
  email_body_template?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

// ==================== 消息 API ====================

/**
 * 获取消息列表
 */
export async function getMessages(params?: {
  page?: number;
  page_size?: number;
  message_type?: MessageType;
  is_read?: boolean;
}): Promise<MessageListResponse> {
  const response = await get<MessageListResponse>("/messages", { params });
  return response;
}

/**
 * 获取未读消息数量
 */
export async function getUnreadCount(): Promise<number> {
  const response = await get<{ count: number }>("/messages/unread-count");
  return response.count;
}

/**
 * 标记消息为已读
 */
export async function markAsRead(messageIds: number[]): Promise<number> {
  const response = await post<{ count: number }>("/messages/mark-read", {
    message_ids: messageIds,
  });
  return response.count;
}

/**
 * 标记所有消息为已读
 */
export async function markAllAsRead(): Promise<number> {
  const response = await post<{ count: number }>("/messages/mark-all-read", {});
  return response.count;
}

/**
 * 删除消息
 */
export async function deleteMessages(messageIds: number[]): Promise<number> {
  const response = await apiRequest<{ count: number }>({
    method: "DELETE",
    url: "/messages",
    data: { message_ids: messageIds },
  });
  return response.count;
}

// ==================== 通知偏好 API ====================

/**
 * 获取通知偏好
 */
export async function getNotificationPreferences(): Promise<NotificationPreference> {
  const response = await get<NotificationPreference>(
    "/notifications/preferences",
  );
  return response;
}

/**
 * 更新通知偏好
 */
export async function updateNotificationPreferences(
  preferences: Partial<NotificationPreference>,
): Promise<NotificationPreference> {
  const response = await put<NotificationPreference>(
    "/notifications/preferences",
    preferences,
  );
  return response;
}

// ==================== 消息模板 API (管理员) ====================

/**
 * 获取消息模板列表
 */
export async function getMessageTemplates(params?: {
  page?: number;
  page_size?: number;
  message_type?: MessageType;
  is_active?: boolean;
}): Promise<{ items: MessageTemplate[]; total: number }> {
  const response = await get<{ items: MessageTemplate[]; total: number }>(
    "/admin/templates",
    { params },
  );
  return response;
}

/**
 * 获取消息模板详情
 */
export async function getMessageTemplate(
  templateId: number,
): Promise<MessageTemplate> {
  const response = await get<MessageTemplate>(`/admin/templates/${templateId}`);
  return response;
}

/**
 * 创建消息模板
 */
export async function createMessageTemplate(
  data: Omit<MessageTemplate, "id" | "created_at" | "updated_at">,
): Promise<MessageTemplate> {
  const response = await post<MessageTemplate>("/admin/templates", data);
  return response;
}

/**
 * 更新消息模板
 */
export async function updateMessageTemplate(
  templateId: number,
  data: Partial<MessageTemplate>,
): Promise<MessageTemplate> {
  const response = await put<MessageTemplate>(
    `/admin/templates/${templateId}`,
    data,
  );
  return response;
}

/**
 * 删除消息模板
 */
export async function deleteMessageTemplate(templateId: number): Promise<void> {
  await del(`/admin/templates/${templateId}`);
}

// ==================== 工具函数 ====================

/**
 * 格式化消息类型
 */
export function formatMessageType(type: MessageType): {
  text: string;
  type: string;
} {
  const typeMap: Record<MessageType, { text: string; type: string }> = {
    system: { text: "系统通知", type: "info" },
    approval: { text: "审批通知", type: "warning" },
    task: { text: "任务提醒", type: "primary" },
  };
  return typeMap[type] || { text: type, type: "info" };
}

/**
 * 格式化时间为相对时间
 */
export function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 7) return `${days}天前`;

  return date.toLocaleDateString("zh-CN");
}
