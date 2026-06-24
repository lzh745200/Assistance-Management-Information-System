# app/core/prophet_status.py
import os
import logging

logger = logging.getLogger(__name__)

# 从环境变量读取是否强制禁用（用于32位构建）
FORCE_DISABLE = os.getenv("PROPHET_UNAVAILABLE", "false").lower() == "true"
PROPHET_AVAILABLE = False

if not FORCE_DISABLE:
    try:
        from prophet import Prophet  # noqa: F401  尝试导入
        PROPHET_AVAILABLE = True
        logger.info("Prophet 已成功加载，AI预测功能可用")
    except ImportError as e:
        logger.warning(f"Prophet 导入失败: {e}，AI预测功能将不可用")
    except Exception as e:
        logger.error(f"Prophet 初始化异常: {e}")
else:
    logger.info("根据环境变量 PROPHET_UNAVAILABLE，强制禁用 Prophet")


def is_prophet_available() -> bool:
    """外部调用检查 Prophet 是否可用"""
    return PROPHET_AVAILABLE
