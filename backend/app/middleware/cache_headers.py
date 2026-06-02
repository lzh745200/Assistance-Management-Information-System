"""HTTP 缓存头中间件 — 对静态/低变化数据添加 Cache-Control 头。

减少重复 API 请求的数据库查询：浏览器和前端可缓存 30s-5min。
"""

from starlette.middleware.base import BaseHTTPMiddleware

# 缓存策略配置: (路径前缀, Cache-Control 值)
CACHE_RULES = [
    # 筛选选项 / 字典数据 — 5 分钟（极少变化）
    ("/api/v1/supported-villages/filter-options", "public, max-age=300"),
    ("/api/v1/organizations/tree", "public, max-age=300"),
    # 统计卡片 — 30 秒（有一定实时性要求）
    ("/api/v1/funds/statistics/overview", "public, max-age=30"),
    ("/api/v1/assessment/village-scores", "public, max-age=30"),
    # 静态资源 — 1 小时
    ("/assets/", "public, max-age=3600, immutable"),
    ("/images/", "public, max-age=3600, immutable"),
]


class CacheHeadersMiddleware(BaseHTTPMiddleware):
    """对匹配路径添加 Cache-Control 响应头。"""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        path = request.url.path
        for prefix, cache_value in CACHE_RULES:
            if path.startswith(prefix):
                response.headers["Cache-Control"] = cache_value
                break
        return response
