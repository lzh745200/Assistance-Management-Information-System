/**
 * 系统常量配置
 *
 * 定义系统名称、版权信息等常量，确保全系统一致性
 * Requirements: 1.1, 1.2, 1.3
 */

// ==================== 系统名称常量 ====================

/** 系统版本 */
export const SYSTEM_VERSION = "1.2.0";

/** 系统全称 */
export const SYSTEM_NAME = "帮扶管理信息系统";

/** 系统简称 */
export const SYSTEM_SHORT_NAME = "帮扶管理信息系统";

/** 系统英文名称 */
export const SYSTEM_NAME_EN = "Assistance Management Information System";

// ==================== 系统副标题 ====================

/** 系统副标题/口号 - Requirements: 17.1, 17.2 */
export const SYSTEM_SUBTITLE = "精准帮扶、助力振兴";

/** 系统简短副标题 */
export const SYSTEM_SUBTITLE_SHORT = "精准帮扶、助力振兴";

// ==================== 版权信息 ====================

/** 版权所有单位 */
export const COPYRIGHT_OWNER = "梁正辉";

/** 版权年份 */
export const COPYRIGHT_YEAR = "2026";

/** 完整版权声明 */
export const COPYRIGHT_TEXT = `© ${COPYRIGHT_YEAR} ${COPYRIGHT_OWNER} 版权所有`;

// ==================== 安全等级 ====================

/** 安全等级 */
export const SECURITY_LEVEL = "等级保护三级";

/** 系统类型 */
export const SYSTEM_TYPE = "涉密信息系统";

/** 安全声明 */
export const SECURITY_STATEMENT = `${SYSTEM_TYPE} | ${SECURITY_LEVEL}`;

// ==================== 页面标题 ====================

/** 登录页标题 */
export const LOGIN_PAGE_TITLE = SYSTEM_NAME;

/** 浏览器标签页标题 */
export const DOCUMENT_TITLE = SYSTEM_NAME;

// ==================== 默认配置 ====================

/** 默认配置对象 */
export const SYSTEM_CONFIG = {
  version: SYSTEM_VERSION,
  name: SYSTEM_NAME,
  shortName: SYSTEM_SHORT_NAME,
  nameEn: SYSTEM_NAME_EN,
  subtitle: SYSTEM_SUBTITLE,
  subtitleShort: SYSTEM_SUBTITLE_SHORT,
  copyrightOwner: COPYRIGHT_OWNER,
  copyrightYear: COPYRIGHT_YEAR,
  copyrightText: COPYRIGHT_TEXT,
  securityLevel: SECURITY_LEVEL,
  systemType: SYSTEM_TYPE,
  securityStatement: SECURITY_STATEMENT,
} as const;

// ==================== 登录背景图片配置 ====================

/** 登录页背景图片列表 - 将图片放到 public/images/login-bg/ 目录下 */
// 只保留最小的3张图片，减少首次加载时间
export const LOGIN_BACKGROUND_IMAGES: string[] = [
  "/images/login-bg/bg3.jpg", // 74KB - 最小，首先加载
  "/images/login-bg/bg5.jpg", // 81KB
  "/images/login-bg/bg10.jpg", // 182KB
];

/** 徽章图片列表 - 将图片放到 public/images/badges/ 目录下 */
// 使用7张徽章图片进行轮播
export const LOGIN_BADGE_IMAGES: string[] = [
  "/images/badges/badge1.png",
  "/images/badges/badge2.png",
  "/images/badges/badge3.png",
  "/images/badges/badge4.png",
  "/images/badges/badge5.png",
  "/images/badges/badge6.png",
  "/images/badges/badge7.png",
];

/** 背景图片轮播间隔（毫秒） */
export const LOGIN_BG_INTERVAL = 8000;

/** 徽章图片轮播间隔（毫秒） */
export const LOGIN_BADGE_INTERVAL = 5000;

/** 背景图片切换动画时长（毫秒） */
export const LOGIN_BG_TRANSITION = 1000;

export default SYSTEM_CONFIG;
