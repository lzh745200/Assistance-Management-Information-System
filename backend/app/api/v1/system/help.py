"""
帮助信息API
提供系统使用帮助、用户手册、常见问题解答等功能
助力军队乡村振兴管理系统官兵快速上手使用
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/help", tags=["帮助中心"])


# ==================== 静态帮助数据 ====================

_HELP_ARTICLES = [
    {
        "id": 1,
        "category": "quick_start",
        "title": "系统快速入门指南",
        "content": (
            "《军队乡村振兴管理系统》是面向军队单位帮扶乡村工作的综合管理平台。"
            "系统支持帮扶村庄、学校、项目、资金的全流程管理。\n\n"
            "基本操作流程：\n"
            "1. 注册账号或使用分配的通行码登录系统\n"
            "2. 完善组织信息，建立帮扶单位组织树\n"
            "3. 录入帮扶村庄基础信息\n"
            "4. 创建帮扶项目并关联村庄\n"
            "5. 管理项目资金预算和支出\n"
            "6. 使用数据看板查看帮扶成效\n\n"
            "详细操作请参阅各模块帮助文档。"
        ),
        "tags": ["入门", "导航"],
    },
    {
        "id": 2,
        "category": "user_guide",
        "title": "用户管理与权限控制",
        "content": (
            "系统采用基于角色的访问控制模型（RBAC），支持多级权限管理。\n\n"
            "用户角色说明：\n"
            "- 超级管理员：拥有系统全部权限，可管理所有模块和用户\n"
            "- 单位管理员：管理本单位及下属单位的业务数据\n"
            "- 普通用户：查看和编辑本人负责的业务数据\n"
            "- 审计员：查看审计日志和系统操作记录\n\n"
            "权限颗粒度支持：页面访问权限、数据操作权限、数据范围权限。"
        ),
        "tags": ["用户", "权限", "RBAC"],
    },
    {
        "id": 3,
        "category": "business",
        "title": "帮扶村管理操作指南",
        "content": (
            "帮扶村管理是本系统的核心功能模块。\n\n"
            "主要功能：\n"
            "1. 基础信息管理：录入村庄基本信息（人口、面积、基础设施等）\n"
            "2. 年度数据管理：逐年录入帮扶成效数据\n"
            "3. 帮扶项目关联：将项目与村庄关联，追踪帮扶进展\n"
            "4. 数据导入导出：支持Excel批量导入导出\n"
            "5. 分布地图：在离线地图上查看帮扶村庄分布\n\n"
            "数据录入规范请参考【数据填报标准】帮助文档。"
        ),
        "tags": ["村庄", "帮扶", "数据"],
    },
    {
        "id": 4,
        "category": "business",
        "title": "资金管理操作指南",
        "content": (
            "资金管理模块支持帮扶项目资金的全生命周期管理。\n\n"
            "核心流程：\n"
            "1. 预算编制：创建年度资金预算\n"
            "2. 资金拨付：记录资金拨付明细\n"
            "3. 支出管理：逐笔记录项目支出\n"
            "4. 资金审批：支持多级审批工作流\n"
            "5. 台账查询：多维度资金统计和报表\n\n"
            "系统严格遵循军队财务管理制度，确保资金安全。"
        ),
        "tags": ["资金", "预算", "审批"],
    },
    {
        "id": 5,
        "category": "faq",
        "title": "常见问题解答（FAQ）",
        "content": (
            "Q1：忘记密码怎么办？\n"
            "A1：联系单位系统管理员重置密码，或使用注册邮箱找回。\n\n"
            "Q2：数据导入失败怎么处理？\n"
            "A2：请检查Excel模板格式是否正确，确保必填字段完整。可下载标准导入模板。\n\n"
            "Q3：系统运行缓慢如何优化？\n"
            "A3：尝试清理缓存、关闭不必要的浏览器标签页。如仍有问题请联系技术支持。\n\n"
            "Q4：支持哪些操作系统？\n"
            "A4：系统支持Windows 10及以上版本、麒麟V10国产操作系统。\n\n"
            "Q5：数据安全性如何保障？\n"
            "A5：系统采用本地离线部署架构，数据存储在本机SQLite数据库，支持加密备份。"
        ),
        "tags": ["FAQ", "常见问题"],
    },
    {
        "id": 6,
        "category": "technical",
        "title": "系统架构与安全说明",
        "content": (
            "系统采用离线单机架构，确保数据安全可控。\n\n"
            "技术架构：\n"
            "- 后端：Python + FastAPI + SQLAlchemy 2.0\n"
            "- 前端：Vue 3 + TypeScript + Element Plus\n"
            "- 桌面壳：Electron 28\n"
            "- 数据库：SQLite（WAL模式，支持并发）\n\n"
            "安全特性：\n"
            "- JWT双Token认证体系\n"
            "- bcrypt密码哈希（10轮加密）\n"
            "- RBAC + 数据范围权限控制\n"
            "- 操作审计日志完整追踪\n"
            "- 机器码绑定与授权验证\n"
            "- 数据包加密传输"
        ),
        "tags": ["架构", "安全", "技术"],
    },
]


# ==================== Pydantic 模型 ====================

class HelpArticleCreate(BaseModel):
    """创建帮助文档"""
    category: str = Field(..., description="分类: quick_start/user_guide/business/faq/technical")
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="文档内容")
    tags: Optional[List[str]] = Field(None, description="标签列表")


class HelpArticleResponse(BaseModel):
    """帮助文档响应"""
    id: int
    category: str
    title: str
    content: str
    tags: List[str]
    created_at: str


# ==================== API 端点 ====================

@router.get("/categories", summary="获取帮助分类列表")
async def get_help_categories():
    """获取所有帮助文档分类"""
    categories = {
        "quick_start": "快速入门",
        "user_guide": "用户指南",
        "business": "业务操作",
        "faq": "常见问题",
        "technical": "技术说明",
    }

    # 统计各分类文档数量
    category_counts = {}
    for article in _HELP_ARTICLES:
        cat = article["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return {
        "success": True,
        "data": {
            "categories": [
                {"key": k, "name": categories.get(k, k), "count": category_counts.get(k, 0)}
                for k in categories
            ],
        },
    }


@router.get("/articles", summary="获取帮助文档列表")
async def get_help_articles(
    category: Optional[str] = Query(None, description="按分类筛选"),
    keyword: Optional[str] = Query(None, description="按关键词搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    """获取帮助文档列表，支持分类筛选和关键词搜索"""
    articles = _HELP_ARTICLES

    if category:
        articles = [a for a in articles if a["category"] == category]

    if keyword:
        keyword_lower = keyword.lower()
        articles = [
            a for a in articles
            if keyword_lower in a["title"].lower()
            or keyword_lower in a["content"].lower()
            or any(keyword_lower in t.lower() for t in a.get("tags", []))
        ]

    total = len(articles)
    start = (page - 1) * page_size
    end = start + page_size
    items = articles[start:end]

    # 返回时移除完整内容，仅保留摘要
    result_items = []
    for article in items:
        summary = article["content"][:150] + "..." if len(article["content"]) > 150 else article["content"]
        result_items.append({
            "id": article["id"],
            "category": article["category"],
            "title": article["title"],
            "summary": summary,
            "tags": article.get("tags", []),
        })

    return {
        "success": True,
        "data": {
            "items": result_items,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/articles/{article_id}", summary="获取帮助文档详情")
async def get_help_article(article_id: int):
    """获取指定帮助文档的完整内容"""
    for article in _HELP_ARTICLES:
        if article["id"] == article_id:
            return {"success": True, "data": article}

    raise HTTPException(status_code=404, detail="帮助文档不存在")


@router.get("/search", summary="搜索帮助文档")
async def search_help_articles(
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50),
):
    """全文搜索帮助文档"""
    if not q.strip():
        return {"success": True, "data": {"items": [], "total": 0}}

    q_lower = q.lower()
    results = []
    for article in _HELP_ARTICLES:
        score = 0
        if q_lower in article["title"].lower():
            score += 10
        if q_lower in article["content"].lower():
            score += 5
        for tag in article.get("tags", []):
            if q_lower in tag.lower():
                score += 3
        if score > 0:
            snippet_start = article["content"].lower().find(q_lower)
            snippet = "..."
            if snippet_start >= 0:
                start = max(0, snippet_start - 30)
                end = min(len(article["content"]), snippet_start + len(q) + 50)
                snippet = article["content"][start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(article["content"]):
                    snippet = snippet + "..."
            results.append({
                "id": article["id"],
                "category": article["category"],
                "title": article["title"],
                "snippet": snippet,
                "tags": article.get("tags", []),
                "relevance_score": score,
            })

    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    results = results[:limit]

    return {
        "success": True,
        "data": {
            "items": results,
            "total": len(results),
        },
    }


@router.get("/system-info", summary="获取系统简介")
async def get_system_info():
    """获取军队乡村振兴管理系统简介"""
    return {
        "success": True,
        "data": {
            "name": "军队乡村振兴管理系统",
            "short_name": "军乡振兴",
            "version": "1.1.0",
            "description": (
                "军队乡村振兴管理系统是面向军队单位帮扶乡村工作的综合管理平台，"
                "实现帮扶村庄、学校、项目、资金的全流程信息化管理，"
                "助力军队单位高效开展乡村振兴帮扶工作。"
            ),
            "features": [
                "帮扶村基础信息管理",
                "帮扶项目全生命周期管理",
                "帮扶资金预算与审计",
                "离线地图分布可视化",
                "数据看板与统计分析",
                "多层级权限管理体系",
            ],
            "contact": {
                "technical_support": "请联系系统管理员获取技术支持",
                "feedback": "欢迎通过系统反馈功能提交建议和问题",
            },
        },
    }
