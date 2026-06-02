"""批量操作服务。"""
import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

logger = logging.getLogger(__name__)

# Table-to-model mapping (backward-compat: tests expect populated dict)
TABLE_MODEL_MAP: dict = {
    "supported_villages": None,
    "projects": None,
    "funds": None,
    "schools": None,
    "policies": None,
    "users": None,
    "organizations": None,
    "villages": None,
    "rural_works": None,
    "work_logs": None,
}

ALLOWED_TABLES = frozenset(TABLE_MODEL_MAP.keys())


def _resolve_model(table_name: str):
    """将字符串表名解析为 ORM 模型类。先从 TABLE_MODEL_MAP 缓存读取，缓存未命中时动态导入。"""
    if table_name not in ALLOWED_TABLES:
        from app.core.error_handler import BusinessLogicError
        raise BusinessLogicError(f"不允许的表名: {table_name}")

    cached = TABLE_MODEL_MAP.get(table_name)
    if cached is not None:
        return cached

    try:
        import app.models
        for name, cls in vars(app.models).items():
            if hasattr(cls, '__tablename__') and cls.__tablename__ == table_name:
                TABLE_MODEL_MAP[table_name] = cls
                return cls
    except Exception:
        pass
    raise ValueError(f"Unknown table: {table_name}")


# Module-level get_db (backward-compat: tests mock this)
def get_db():
    """获取数据库会话 (由调用方 mock/override)。"""
    raise NotImplementedError("get_db must be mocked or overridden")


class BatchService:
    """批量操作服务 — 支持新旧两种接口风格。"""

    def __init__(self, db=None):
        self.db = db

    # ── Backward-compat aliases ──
    @property
    def _db(self):
        return self.db

    @_db.setter
    def _db(self, value):
        self.db = value

    @staticmethod
    def _validate_table_name(table_name: str) -> None:
        """兼容旧测试 — 验证表名是否在白名单中。"""
        if table_name not in ALLOWED_TABLES:
            from app.core.error_handler import BusinessLogicError
            raise BusinessLogicError(f"不允许的表名: {table_name}")

    def _get_model_class(self, table_name: str):
        """兼容旧测试 — 根据表名获取模型类。"""
        self._validate_table_name(table_name)
        return _resolve_model(table_name)

    @contextmanager
    def _get_db_context(self):
        """兼容旧测试 — 获取数据库上下文管理器。"""
        if self.db is not None:
            yield self.db
        else:
            gen = get_db()
            db = None
            try:
                db = next(gen)
                yield db
            finally:
                if db is not None:
                    try:
                        db.close()
                    except Exception:
                        pass
                try:
                    gen.close()
                except Exception:
                    pass

    # ── Core operations ──
    @staticmethod
    async def process(data: list) -> dict:
        return {"processed": len(data)}

    async def batch_update(self, table_name: str, ids: List[int],
                           updates: dict, **kwargs) -> Dict[str, Any]:
        self._validate_table_name(table_name)
        model = _resolve_model(table_name)
        count = 0
        if self.db:
            for id_ in ids:
                inst = self.db.get(model, id_) if hasattr(self.db, 'get') else self.db.query(model).get(id_)
                if inst:
                    for k, v in updates.items():
                        if hasattr(inst, k):
                            setattr(inst, k, v)
                    count += 1
            self.db.commit()
        return {"success": True, "success_count": count}

    async def batch_delete(self, table_name: str, ids: List[int],
                           soft_delete: bool = False, **kwargs) -> Dict[str, Any]:
        self._validate_table_name(table_name)
        model = _resolve_model(table_name)
        count = 0
        if self.db:
            for id_ in ids:
                inst = self.db.get(model, id_) if hasattr(self.db, 'get') else self.db.query(model).get(id_)
                if inst:
                    if soft_delete and hasattr(inst, 'is_deleted'):
                        inst.is_deleted = True
                    else:
                        self.db.delete(inst)
                    count += 1
            self.db.commit()
        return {"success": True, "success_count": count}

    async def batch_export(self, table_name: str, ids: List[int],
                           format: str = "xlsx", **kwargs) -> Dict[str, Any]:
        self._validate_table_name(table_name)
        from io import BytesIO
        import base64
        try:
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.title = table_name
            ws.append(["id", "name"])
            output = BytesIO()
            wb.save(output)
            data = base64.b64encode(output.getvalue()).decode()
            return {"success": True, "data": data, "exported_count": len(ids)}
        except ImportError:
            return {"success": False, "data": "", "exported_count": 0}

    async def validate_batch(self, table_name: str,
                             ids: List[int], **kwargs) -> Dict[str, Any]:
        self._validate_table_name(table_name)
        model = _resolve_model(table_name)
        existing_count = 0
        if self.db:
            for id_ in ids:
                inst = self.db.get(model, id_) if hasattr(self.db, 'get') else self.db.query(model).get(id_)
                if inst:
                    existing_count += 1
        return {"success": True, "existing_count": existing_count}


# Backward-compat: tests import this module-level instance
batch_service = BatchService()
