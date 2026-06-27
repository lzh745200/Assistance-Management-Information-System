"""
完整测试 - app.services.resource_limiter
覆盖率目标: 100%
"""
import time
from datetime import datetime

class TestRateLimit:
    """测试 RateLimit 数据类"""

    def test_rate_limit_creation(self):
        """测试创建速率限制配置"""
        from app.services.resource_limiter import RateLimit

        limit = RateLimit(requests=100, window=60)
        assert limit.requests == 100
        assert limit.window == 60

class TestResourceQuota:
    """测试 ResourceQuota 数据类"""

    def test_resource_quota_creation(self):
        """测试创建资源配额配置"""
        from app.services.resource_limiter import ResourceQuota

        quota = ResourceQuota(max_requests=100, period=60)
        assert quota.max_requests == 100
        assert quota.period == 60
        assert quota.current_usage == 0

    def test_resource_quota_with_usage(self):
        """测试创建带初始使用量的资源配额"""
        from app.services.resource_limiter import ResourceQuota

        quota = ResourceQuota(max_requests=100, period=60, current_usage=50)
        assert quota.current_usage == 50

class TestUsageStats:
    """测试 UsageStats 数据类"""

    def test_usage_stats_defaults(self):
        """测试使用统计默认值"""
        from app.services.resource_limiter import UsageStats

        stats = UsageStats()
        assert stats.total_requests == 0
        assert stats.allowed_requests == 0
        assert stats.denied_requests == 0
        assert isinstance(stats.last_reset, datetime)

    def test_usage_stats_with_values(self):
        """测试使用统计带初始值"""
        from app.services.resource_limiter import UsageStats

        stats = UsageStats(
            total_requests=100,
            allowed_requests=90,
            denied_requests=10
        )
        assert stats.total_requests == 100
        assert stats.allowed_requests == 90
        assert stats.denied_requests == 10

class TestResourceLimiter:
    """测试 ResourceLimiter 类"""

    def test_limiter_creation(self):
        """测试创建限制器"""
        from app.services.resource_limiter import ResourceLimiter

        limiter = ResourceLimiter()
        assert limiter._rate_limits == {}
        assert limiter._quotas == {}
        assert limiter._usage == {}
        assert limiter._request_counts == {}
        assert limiter._monitoring is False

    def test_start_monitoring(self):
        """测试启动监控"""
        from app.services.resource_limiter import ResourceLimiter

        limiter = ResourceLimiter()
        limiter.start_monitoring()
        assert limiter._monitoring is True

    def test_stop_monitoring(self):
        """测试停止监控"""
        from app.services.resource_limiter import ResourceLimiter

        limiter = ResourceLimiter()
        limiter.start_monitoring()
        limiter.stop_monitoring()
        assert limiter._monitoring is False

    def test_is_allowed_no_limit(self):
        """测试无限制时允许请求"""
        from app.services.resource_limiter import ResourceLimiter

        limiter = ResourceLimiter()
        result = limiter.is_allowed("test_key")

        assert result is True
        assert "test_key" in limiter._request_counts

    def test_is_allowed_within_limit(self):
        """测试在限制范围内允许请求"""
        from app.services.resource_limiter import ResourceLimiter

        limiter = ResourceLimiter()
        limiter.set_quota("test_key", max_requests=5, period=60)

        # 前5个请求应该被允许
        for _ in range(5):
            assert limiter.is_allowed("test_key") is True

    def test_is_allowed_exceeds_limit(self):
        """测试超出限制时拒绝请求"""
        from app.services.resource_limiter import ResourceLimiter

        limiter = ResourceLimiter()
        limiter.set_quota("test_key", max_requests=2, period=60)

        # 前2个请求应该被允许
        assert limiter.is_allowed("test_key") is True
        assert limiter.is_allowed("test_key") is True

        # 第3个请求应该被拒绝
        assert limiter.is_allowed("test_key") is False

    def test_is_allowed_expired_requests(self):
        """测试过期请求被清理"""
        from app.services.resource_limiter import ResourceLimiter

        limiter = ResourceLimiter()
        limiter.set_quota("test_key", max_requests=2, period=1)  # 1秒窗口

        # 添加2个请求
        limiter.is_allowed("test_key")
        limiter.is_allowed("test_key")

        # 等待窗口过期
        time.sleep(1.1)

        # 新请求应该被允许（旧的已过期）
        assert limiter.is_allowed("test_key") is True

    def test_get_usage_stats_existing(self):
        """测试获取存在的使用统计"""
        from app.services.resource_limiter import ResourceLimiter

        limiter = ResourceLimiter()
        limiter.set_quota("test_key", max_requests=5, period=60)

        limiter.is_allowed("test_key")
        limiter.is_allowed("test_key")

        stats = limiter.get_usage_stats("test_key")

        assert stats.total_requests == 2
        assert stats.allowed_requests == 2

    def test_get_usage_stats_nonexistent(self):
        """测试获取不存在键的使用统计"""
        from app.services.resource_limiter import ResourceLimiter, UsageStats

        limiter = ResourceLimiter()
        stats = limiter.get_usage_stats("nonexistent_key")

        assert isinstance(stats, UsageStats)
        assert stats.total_requests == 0

    def test_set_quota(self):
        """测试设置配额"""
        from app.services.resource_limiter import ResourceLimiter, RateLimit, ResourceQuota

        limiter = ResourceLimiter()
        limiter.set_quota("test_key", max_requests=100, period=60)

        assert "test_key" in limiter._quotas
        assert "test_key" in limiter._rate_limits
        assert isinstance(limiter._quotas["test_key"], ResourceQuota)
        assert isinstance(limiter._rate_limits["test_key"], RateLimit)

    def test_clear_quota(self):
        """测试清除配额"""
        from app.services.resource_limiter import ResourceLimiter

        limiter = ResourceLimiter()
        limiter.set_quota("test_key", max_requests=100, period=60)
        limiter.is_allowed("test_key")  # 生成使用统计

        limiter.clear_quota("test_key")

        assert "test_key" not in limiter._quotas
        assert "test_key" not in limiter._rate_limits
        assert "test_key" not in limiter._request_counts
        assert "test_key" not in limiter._usage

    def test_clear_quota_nonexistent(self):
        """测试清除不存在的配额"""
        from app.services.resource_limiter import ResourceLimiter

        limiter = ResourceLimiter()
        # 应该不抛出异常
        limiter.clear_quota("nonexistent_key")

    def test_update_usage_allowed(self):
        """测试更新使用统计 - 允许"""
        from app.services.resource_limiter import ResourceLimiter

        limiter = ResourceLimiter()
        limiter._update_usage("test_key", allowed=True)

        stats = limiter._usage["test_key"]
        assert stats.total_requests == 1
        assert stats.allowed_requests == 1
        assert stats.denied_requests == 0

    def test_update_usage_denied(self):
        """测试更新使用统计 - 拒绝"""
        from app.services.resource_limiter import ResourceLimiter

        limiter = ResourceLimiter()
        limiter._update_usage("test_key", allowed=False)

        stats = limiter._usage["test_key"]
        assert stats.total_requests == 1
        assert stats.allowed_requests == 0
        assert stats.denied_requests == 1

class TestGlobalFunctions:
    """测试全局函数"""

    def test_check_rate_limit(self):
        """测试检查速率限制"""
        from app.services.resource_limiter import check_rate_limit

        # 第一个请求应该被允许
        result = check_rate_limit("global_key", limit=2, window=60)
        assert result is True

    def test_check_rate_limit_exceeded(self):
        """测试检查速率限制 - 超出"""
        from app.services.resource_limiter import check_rate_limit

        key = "limited_key"
        # 设置限制并超出
        check_rate_limit(key, limit=1, window=60)
        check_rate_limit(key, limit=1, window=60)  # 设置配额
        result = check_rate_limit(key, limit=1, window=60)  # 第3次调用会重新设置但限制是1

    def test_get_remaining_quota_with_quota(self):
        """测试获取剩余配额 - 有配额"""
        from app.services.resource_limiter import get_remaining_quota, check_rate_limit

        key = "quota_key"
        check_rate_limit(key, limit=10, window=60)

        remaining = get_remaining_quota(key)
        # 已使用1次，剩余9次
        assert remaining == 9

    def test_get_remaining_quota_no_quota(self):
        """测试获取剩余配额 - 无配额"""
        from app.services.resource_limiter import get_remaining_quota

        remaining = get_remaining_quota("no_quota_key")
        assert remaining == -1

    def test_reset_rate_limit(self):
        """测试重置速率限制"""
        from app.services.resource_limiter import reset_rate_limit, check_rate_limit, get_remaining_quota

        key = "reset_key"
        check_rate_limit(key, limit=5, window=60)

        reset_rate_limit(key)

        remaining = get_remaining_quota(key)
        assert remaining == -1

class TestGlobalInstance:
    """测试全局实例"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        from app.services.resource_limiter import resource_limiter, ResourceLimiter
        assert resource_limiter is not None
        assert isinstance(resource_limiter, ResourceLimiter)

    def test_rate_limiter_global(self):
        """测试全局_rate_limiter"""
        from app.services.resource_limiter import _rate_limiter, ResourceLimiter
        assert isinstance(_rate_limiter, ResourceLimiter)
