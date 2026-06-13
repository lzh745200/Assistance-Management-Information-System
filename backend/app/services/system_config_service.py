"""
系统配置服务
"""

import json
from typing import Any, Dict, Optional
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.system_config import SystemConfig

# 配置键类型
ConfigKey = str


# 配置值类型
ConfigValue = str


@dataclass
class ConfigEntry:
    """配置条目"""

    key: ConfigKey
    value: ConfigValue
    description: str = ""


# 全局服务实例
_global_config_service: Optional["SystemConfigService"] = None


def get_config(key: str, default: Any = None) -> Optional[str]:
    """获取配置值（全局函数）"""
    if _global_config_service is None:
        return default
    return _global_config_service.get(key, default)


def set_config(key: str, value: Any, description: str = ""):
    """设置配置值（全局函数）"""
    if _global_config_service:
        _global_config_service.set(key, value, description)


def delete_config(key: str):
    """删除配置（全局函数）"""
    if _global_config_service:
        _global_config_service.delete(key)


def list_configs() -> Dict[str, str]:
    """列出所有配置（全局函数）"""
    if _global_config_service is None:
        return {}
    return _global_config_service.get_all()


class SystemConfigService:
    """系统配置服务"""

    # 默认配置
    DEFAULT_CONFIGS = {
        "system_id": {"value": "", "description": "系统唯一标识"},
        "organization_id": {"value": "", "description": "当前组织ID"},
        "initialized": {"value": "false", "description": "系统是否已初始化"},
        "data_package_encryption": {"value": "false", "description": "是否加密数据包"},
        "auto_backup": {"value": "false", "description": "是否自动备份（默认关闭，防止占用磁盘空间）"},
        "backup_interval_days": {"value": "30", "description": "备份间隔（天）"},
        "max_backup_count": {"value": "3", "description": "最大备份数量"},
        "data_retention_days": {"value": "365", "description": "数据保留天数"},
        "package_max_size_mb": {"value": "100", "description": "数据包最大大小（MB）"},
        "last_backup_time": {"value": "", "description": "最后备份时间"},
        "system_version": {"value": settings.PROJECT_VERSION, "description": "系统版本"},
        "anomaly_zscore_threshold": {"value": "3.0", "description": "异常检测 Z-Score 阈值"},
        "anomaly_overspend_threshold_pct": {"value": "20", "description": "超预算检测阈值（百分比）"},
        "anomaly_detection_enabled": {"value": "true", "description": "是否启用异常检测"},
    }

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def get(self, key: str, default: Any = None) -> Optional[str]:
        """
        获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        if self.db is None:
            # 如果db为None，返回默认值或预设默认值
            if key in self.DEFAULT_CONFIGS:
                return self.DEFAULT_CONFIGS[key]["value"]
            return default

        config = self.db.query(SystemConfig).filter(SystemConfig.key == key).first()

        if config:
            return config.value

        # 如果配置不存在，返回默认值
        if key in self.DEFAULT_CONFIGS:
            return self.DEFAULT_CONFIGS[key]["value"]

        return default

    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数配置值"""
        value = self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔配置值"""
        value = self.get(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    def get_json(self, key: str, default: Any = None) -> Any:
        """获取JSON配置值"""
        value = self.get(key)
        if value is None:
            return default
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default

    def set(self, key: str, value: Any, description: str = None):
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
            description: 配置说明
        """
        if self.db is None:
            return

        # 转换值为字符串
        if isinstance(value, bool):
            value = "true" if value else "false"
        elif isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        else:
            value = str(value)

        config = self.db.query(SystemConfig).filter(SystemConfig.key == key).first()

        if config:
            config.value = value
            if description:
                config.description = description
        else:
            config = SystemConfig(
                key=key,
                value=value,
                description=description or self.DEFAULT_CONFIGS.get(key, {}).get("description", ""),
            )
            self.db.add(config)

        self.db.commit()

    def get_all(self) -> Dict[str, str]:
        """
        获取所有配置

        Returns:
            配置字典
        """
        if self.db is None:
            return {k: v["value"] for k, v in self.DEFAULT_CONFIGS.items()}
        configs = self.db.query(SystemConfig).all()
        return {config.key: config.value for config in configs}

    def initialize_defaults(self):
        """初始化默认配置"""
        if self.db is None:
            return
        for key, config_data in self.DEFAULT_CONFIGS.items():
            # 检查配置是否已存在
            existing = self.db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if not existing:
                config = SystemConfig(
                    key=key,
                    value=config_data["value"],
                    description=config_data["description"],
                )
                self.db.add(config)

        self.db.commit()

    def is_initialized(self) -> bool:
        """检查系统是否已初始化"""
        return self.get_bool("initialized", False)

    def set_initialized(self, org_id: int, system_id: str = None):
        """设置系统已初始化"""
        import uuid

        if not system_id:
            system_id = f"SYS-{uuid.uuid4().hex[:8].upper()}"

        self.set("initialized", "true")
        self.set("organization_id", str(org_id))
        self.set("system_id", system_id)

    def delete(self, key: str) -> bool:
        """删除配置"""
        if self.db is None:
            return False
        config = self.db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if config:
            self.db.delete(config)
            self.db.commit()
            return True
        return False

    def reload(self):
        """重新加载配置"""
        # 清除缓存并重新加载
        if self.db:
            self.db.expire_all()

    def export_config(self) -> str:
        """导出配置为JSON字符串"""
        configs = self.get_all()
        return json.dumps(configs, ensure_ascii=False, indent=2)

    def import_config(self, config_json: str) -> bool:
        """从JSON字符串导入配置"""
        try:
            configs = json.loads(config_json)
            for key, value in configs.items():
                self.set(key, value)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
