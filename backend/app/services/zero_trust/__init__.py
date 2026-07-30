"""
零信任安全模块

提供设备指纹识别、风险评估、动态权限评估等功能。

本模块统一从 ``device_fingerprint.py`` 导出真实的设备指纹服务实现，
同时提供向后兼容的便捷方法（``generate_fingerprint_from_request``、
``assess_risk``、``is_trusted``）供中间件和旧式调用方使用。
"""

from app.services.zero_trust.device_fingerprint import (
    DeviceFingerprint,
    DeviceFingerprintService as _RealDeviceFingerprintService,
    DeviceRiskLevel,
    device_fingerprint_service as _real_service,
)

__all__ = [
    "DeviceFingerprint",
    "DeviceFingerprintService",
    "DeviceRiskLevel",
    "device_fingerprint_service",
]


class DeviceFingerprintService(_RealDeviceFingerprintService):
    """设备指纹服务（向后兼容封装）。

    继承真实的 ``DeviceFingerprintService``，增加以下便捷方法以兼容
    旧式调用接口（中间件 / __init__ 导入方）：

    - ``generate_fingerprint_from_request(request)`` — 从 ASGI/FastAPI 请求
      对象中提取 User-Agent、IP 等信息生成指纹。
    - ``assess_risk(fingerprint_id)`` — 根据设备信任评分返回风险等级。
    - ``is_trusted(fingerprint_id)`` — 快速判断设备是否可信（信任分 ≥ 0.5
      且未被封禁）。
    """

    # ── 向后兼容方法 ──────────────────────────────────────────────

    @staticmethod
    def generate_fingerprint_from_request(request) -> str:
        """从请求对象中生成设备指纹。

        兼容旧式 ``generate_fingerprint(request)`` 调用。从 request.headers
        和 request.client 中提取特征，委托给真实的
        ``generate_fingerprint(user_agent, ip_address)`` 方法。

        Args:
            request: FastAPI/Starlette Request 对象，需具有 ``headers``
                和 ``client`` 属性。

        Returns:
            32 字符的 SHA-256 指纹 ID。
        """
        ua = ""
        ip = "unknown"
        try:
            ua = request.headers.get("user-agent", "")
            ip = request.client.host if request.client else "unknown"
        except (AttributeError, TypeError):
            pass
        return _RealDeviceFingerprintService.generate_fingerprint(ua, ip)

    def assess_risk(self, fingerprint_id: str) -> DeviceRiskLevel:
        """评估设备风险等级。

        根据设备信任评分返回对应的风险等级。未知设备默认返回
        :attr:`DeviceRiskLevel.LOW`（向后兼容旧行为）。

        Args:
            fingerprint_id: 设备指纹 ID。

        Returns:
            风险等级枚举值。
        """
        device = self.get_device(fingerprint_id)
        if device is None:
            return DeviceRiskLevel.LOW
        return device.risk_level

    def is_trusted(self, fingerprint_id: str) -> bool:
        """检查设备是否受信任。

        设备信任评分 ≥ 0.5 且未被列入封禁列表时返回 ``True``。

        Args:
            fingerprint_id: 设备指纹 ID。

        Returns:
            ``True`` 表示设备可信。
        """
        if self.is_device_blocked(fingerprint_id):
            return False
        return self.get_trust_score(fingerprint_id) >= 0.5


# 模块级单例（使用向后兼容封装类）
device_fingerprint_service = DeviceFingerprintService()
