"""
村庄服务层 - 通用混入

提供村庄业务逻辑中常用的工具方法和混入类。
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class VillageQueryMixin:
    """
    村庄查询混入

    提供村庄查询中常用的过滤、排序方法。
    """

    @staticmethod
    def apply_region_filter(query, model, region_code: Optional[str] = None):
        """
        按行政区划过滤。

        Args:
            query: SQLAlchemy Query
            model: 模型类
            region_code: 行政区划编码

        Returns:
            过滤后的 Query
        """
        if not region_code:
            return query

        code_col = getattr(model, "region_code", None)
        county_col = getattr(model, "county", None)

        if code_col is not None:
            return query.filter(code_col == region_code)
        elif county_col is not None:
            return query.filter(county_col == region_code)

        return query

    @staticmethod
    def apply_keyword_search(query, model, keyword: Optional[str] = None):
        """
        关键词搜索（名称、编码）。

        Args:
            query: SQLAlchemy Query
            model: 模型类
            keyword: 搜索关键词

        Returns:
            过滤后的 Query
        """
        if not keyword:
            return query

        name_col = getattr(model, "name", None)
        code_col = getattr(model, "code", None)

        filters = []
        if name_col is not None:
            filters.append(name_col.ilike(f"%{keyword}%"))
        if code_col is not None:
            filters.append(code_col.ilike(f"%{keyword}%"))

        if filters:
            from sqlalchemy import or_

            return query.filter(or_(*filters))

        return query


class VillageExportMixin:
    """
    村庄导出混入

    提供村庄数据导出相关的方法。
    """

    @staticmethod
    def to_export_dict(village: Any) -> Dict[str, Any]:
        """
        将村庄对象转换为导出字典。

        Args:
            village: Village 模型实例

        Returns:
            适合导出的字典
        """
        return {
            "村庄名称": getattr(village, "name", ""),
            "村庄编码": getattr(village, "code", ""),
            "省份": getattr(village, "province", ""),
            "城市": getattr(village, "city", ""),
            "县/市": getattr(village, "county", ""),
            "乡镇": getattr(village, "township", ""),
            "民族属性": getattr(village, "ethnic_group", ""),
            "是否民族村寨": "是" if getattr(village, "is_ethnic_village", False) else "否",
            "经度": getattr(village, "longitude", ""),
            "纬度": getattr(village, "latitude", ""),
        }
