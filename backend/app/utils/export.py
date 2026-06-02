"""数据导出工具模块"""

import json
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session


class DataExporter:
    """数据导出器"""

    def __init__(self, db: Session):
        self.db = db

    def export_users_to_excel(self, filters: Optional[Dict[str, Any]] = None) -> bytes:
        """导出用户数据到Excel"""
        try:
            users = self._get_filtered_users(filters)
            return self._create_excel(users, "users")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

    def export_villages_to_excel(self, filters: Optional[Dict[str, Any]] = None) -> bytes:
        """导出村庄数据到Excel"""
        try:
            villages = self._get_filtered_villages(filters)
            return self._create_excel(villages, "villages")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

    def _get_filtered_users(self, filters: Optional[Dict[str, Any]]) -> List:
        """获取过滤后的用户数据"""
        from app.models.user import User

        query = self.db.query(User)
        if filters:
            if "role" in filters:
                query = query.filter(User.role == filters["role"])
        return query.all()

    def _get_filtered_villages(self, filters: Optional[Dict[str, Any]]) -> List:
        """获取过滤后的村庄数据"""
        from app.models.village import Village

        query = self.db.query(Village)
        if filters:
            if "status" in filters:
                query = query.filter(Village.status == filters["status"])
        return query.all()

    def _create_excel(self, data: List, data_type: str) -> bytes:
        """创建Excel文件"""
        return json.dumps([str(d) for d in data]).encode()
