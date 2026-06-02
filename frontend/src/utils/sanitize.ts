/**
 * HTML 内容安全清理工具
 * 用于 v-html 渲染前的 XSS 防护
 *
 * 使用 DOMPurify 库替代手写 DOM 解析，防止 mutation-XSS (mXSS) 攻击。
 */

import DOMPurify from "dompurify";

/** 允许的 HTML 标签白名单 */
const ALLOWED_TAGS = [
  "p",
  "br",
  "b",
  "strong",
  "i",
  "em",
  "u",
  "s",
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "ul",
  "ol",
  "li",
  "blockquote",
  "pre",
  "code",
  "table",
  "thead",
  "tbody",
  "tr",
  "th",
  "td",
  "a",
  "img",
  "div",
  "span",
];

/** 允许的属性白名单 */
const ALLOWED_ATTR = [
  "href",
  "title",
  "target",
  "rel",
  "src",
  "alt",
  "width",
  "height",
  "class",
  "border",
  "colspan",
  "rowspan",
];

/** 危险 URI 协议前缀 */
const DANGEROUS_PROTOCOLS = ["javascript:", "vbscript:", "data:", "file:"];

// 钩子 1：为外部链接添加安全属性 + 拦截危险 URI
DOMPurify.addHook("afterSanitizeAttributes", (node) => {
  // 拦截 href/src 中的危险协议（javascript:, data:, vbscript:, file:）
  for (const attr of ["href", "src"]) {
    const val = node.getAttribute(attr);
    if (val) {
      const normalized = val.toLowerCase().trim();
      if (DANGEROUS_PROTOCOLS.some((p) => normalized.startsWith(p))) {
        node.removeAttribute(attr);
      }
    }
  }

  // 为外部链接添加 rel 和 target
  if (node.tagName === "A") {
    node.setAttribute("rel", "noopener noreferrer");
    const href = node.getAttribute("href") || "";
    if (href && !href.startsWith("#") && !href.startsWith("/")) {
      node.setAttribute("target", "_blank");
    }
  }
});

export function sanitizeHtml(html: string): string {
  if (!html || typeof html !== "string") {
    return "";
  }

  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    ALLOW_DATA_ATTR: false,
  });
}

export function stripHtml(html: string): string {
  if (!html || typeof html !== "string") {
    return "";
  }
  // 使用 DOMPurify 移除所有 HTML 标签，避免 innerHTML XSS 风险
  const purified = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: [],
    ALLOW_DATA_ATTR: false,
  });
  const temp = document.createElement("div");
  temp.innerHTML = purified;
  return temp.textContent || temp.innerText || "";
}

export function escapeHtml(text: string): string {
  if (!text || typeof text !== "string") {
    return "";
  }
  const escapeMap: Record<string, string> = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  };
  return text.replace(/[&<>"']/g, (char) => escapeMap[char] || char);
}

export default {
  sanitizeHtml,
  stripHtml,
  escapeHtml,
};
