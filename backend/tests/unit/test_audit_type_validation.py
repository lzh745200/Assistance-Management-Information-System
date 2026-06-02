"""
审计日志参数类型验证单元测试

覆盖范围：
- BatchDeleteRequest Pydantic schema 类型验证和 coerce 逻辑
- ids 字段：字符串 → int 自动转换；非法值的错误提示
- actions 字段：归一化、空值处理
- action / before_date 字段向后兼容
- log_id 路径参数类型（路由层）
"""

import pytest
from pydantic import ValidationError

from app.api.v1.system.audit import BatchDeleteRequest

# ==================== BatchDeleteRequest.ids 类型验证 ====================

class TestBatchDeleteRequestIds:
    """ids 字段：自动将字符串 coerce 为 int；非法值抛出 ValidationError"""

    def test_ids_as_integers(self):
        """正常整数列表"""
        req = BatchDeleteRequest(ids=[1, 2, 3])
        assert req.ids == [1, 2, 3]

    def test_ids_as_strings_coerced_to_int(self):
        """字符串 ID 应被自动转为整数（前端可能以字符串传递）"""
        req = BatchDeleteRequest(ids=["1", "2", "100"])
        assert req.ids == [1, 2, 100]

    def test_ids_mixed_types(self):
        """混合类型：int 和 str 同时存在"""
        req = BatchDeleteRequest(ids=[1, "2", 3, "42"])
        assert req.ids == [1, 2, 3, 42]

    def test_ids_none(self):
        """ids 为 None 时不触发验证"""
        req = BatchDeleteRequest(ids=None)
        assert req.ids is None

    def test_ids_empty_list(self):
        """空列表"""
        req = BatchDeleteRequest(ids=[])
        assert req.ids == []

    def test_ids_invalid_string_raises(self):
        """非法字符串（如 'batch', 'abc'）应引发 ValidationError 并包含友好提示"""
        with pytest.raises(ValidationError) as exc_info:
            BatchDeleteRequest(ids=["batch"])
        errors = exc_info.value.errors()
        assert any("log_id 必须为整数" in (e.get("msg") or "") for e in errors), (
            f"期望错误信息含 'log_id 必须为整数'，实际 errors={errors}"
        )

    def test_ids_invalid_none_element_raises(self):
        """None 元素无法转换为 int，应引发 ValidationError"""
        with pytest.raises(ValidationError):
            BatchDeleteRequest(ids=[None])

    def test_ids_float_string_raises(self):
        """浮点字符串不能转整数（'1.5' → int 会失败）"""
        with pytest.raises(ValidationError):
            BatchDeleteRequest(ids=["1.5"])

    def test_ids_zero(self):
        """0 是合法的整数 ID（即使语义上不存在）"""
        req = BatchDeleteRequest(ids=[0])
        assert req.ids == [0]

    def test_ids_large_number(self):
        """超大整数"""
        req = BatchDeleteRequest(ids=["9999999999"])
        assert req.ids == [9999999999]

# ==================== BatchDeleteRequest.actions 字段 ====================

class TestBatchDeleteRequestActions:
    """actions 字段：多类型操作列表"""

    def test_actions_list(self):
        """正常字符串列表"""
        req = BatchDeleteRequest(actions=["create", "update", "delete"])
        assert req.actions == ["create", "update", "delete"]

    def test_actions_none(self):
        req = BatchDeleteRequest(actions=None)
        assert req.actions is None

    def test_actions_empty(self):
        req = BatchDeleteRequest(actions=[])
        assert req.actions == []

    def test_actions_strips_whitespace(self):
        """normalize_actions 应去除首尾空格"""
        req = BatchDeleteRequest(actions=["  create  ", " delete"])
        assert req.actions == ["create", "delete"]

    def test_actions_filters_none_elements(self):
        """None 元素应被过滤"""
        req = BatchDeleteRequest(actions=["create", None, "delete"])
        assert req.actions == ["create", "delete"]

    def test_data_operation_types_full_list(self):
        """模拟前端发送的完整操作类型列表"""
        DATA_OPERATION_TYPES = ["create", "update", "delete", "import", "export", "backup", "restore"]
        req = BatchDeleteRequest(actions=DATA_OPERATION_TYPES)
        assert req.actions == DATA_OPERATION_TYPES

# ==================== BatchDeleteRequest.action 向后兼容 ====================

class TestBatchDeleteRequestAction:
    """action 字段（单值，向后兼容）"""

    def test_single_action_string(self):
        req = BatchDeleteRequest(action="export")
        assert req.action == "export"
        assert req.actions is None

    def test_action_and_actions_both_set(self):
        """action 和 actions 同时存在时不报错（路由层按优先级处理）"""
        req = BatchDeleteRequest(action="delete", actions=["create", "delete"])
        assert req.action == "delete"
        assert req.actions == ["create", "delete"]

# ==================== BatchDeleteRequest.before_date 字段 ====================

class TestBatchDeleteRequestBeforeDate:
    def test_before_date_string(self):
        req = BatchDeleteRequest(before_date="2026-01-01")
        assert req.before_date == "2026-01-01"

    def test_before_date_none(self):
        req = BatchDeleteRequest()
        assert req.before_date is None

# ==================== BatchDeleteRequest 完整场景 ====================

class TestBatchDeleteRequestScenarios:
    """模拟前端实际请求场景"""

    def test_clear_all_data_ops_scenario(self):
        """前端 handleClearLogs 发送的请求体"""
        DATA_OPERATION_TYPES = ["create", "update", "delete", "import", "export", "backup", "restore"]
        req = BatchDeleteRequest(actions=DATA_OPERATION_TYPES)
        assert req.ids is None
        assert len(req.actions) == 7
        assert req.action is None

    def test_delete_by_ids_from_frontend_strings(self):
        """前端表格行 ID 可能以字符串形式传递"""
        req = BatchDeleteRequest(ids=["101", "102", "103"])
        assert req.ids == [101, 102, 103]

    def test_empty_request_body(self):
        """空请求体：所有字段均为 None"""
        req = BatchDeleteRequest()
        assert req.ids is None
        assert req.actions is None
        assert req.action is None
        assert req.before_date is None

    def test_ids_take_priority(self):
        """ids 和 actions 同时存在时，Pydantic 层均接受（优先级由路由层决定）"""
        req = BatchDeleteRequest(ids=[1, 2], actions=["create"])
        assert req.ids == [1, 2]
        assert req.actions == ["create"]

# ==================== log_id 路径参数语义（文档测试） ====================

class TestLogIdPathParam:
    """
    log_id 路径参数测试（文档说明）

    FastAPI 对路径参数的 int 验证发生在路由层，无需在业务代码中手动转换。
    若 DELETE /audit/logs/batch 路由注册在 DELETE /audit/logs/{log_id} 之后，
    FastAPI 会尝试将 "batch" 解析为 int，引发 422 错误。

    这里通过检查路由注册顺序来验证修复是否正确。
    """

    def test_batch_route_registered_before_log_id_route(self):
        """
        验证 DELETE /logs/batch 在 DELETE /logs/{log_id} 之前注册。
        通过检查 router.routes 的顺序来确认。
        """
        from app.api.v1.system.audit import router
        from fastapi.routing import APIRoute

        delete_routes = [
            r for r in router.routes
            if isinstance(r, APIRoute) and "DELETE" in r.methods
        ]

        # 兼容两种情况：带 /audit 前缀（router 定义了 prefix） 或不带前缀
        paths = [r.path for r in delete_routes]
        batch_path  = next((p for p in paths if p.endswith("/logs/batch")), None)
        log_id_path = next((p for p in paths if p.endswith("/logs/{log_id}")), None)

        assert batch_path  is not None, f"缺少 DELETE */logs/batch 路由，实际路由: {paths}"
        assert log_id_path is not None, f"缺少 DELETE */logs/{{log_id}} 路由，实际路由: {paths}"

        batch_idx  = paths.index(batch_path)
        log_id_idx = paths.index(log_id_path)

        assert batch_idx < log_id_idx, (
            f"路由顺序错误！DELETE {batch_path} (index={batch_idx}) 必须在 "
            f"DELETE {log_id_path} (index={log_id_idx}) 之前注册，"
            f"否则 'batch' 会被当作整数解析导致 422 错误。\n"
            f"当前路由顺序: {paths}"
        )

    def test_all_delete_routes_present(self):
        """确认系统中存在所有预期的 DELETE 路由"""
        from app.api.v1.system.audit import router
        from fastapi.routing import APIRoute

        delete_paths = {
            r.path
            for r in router.routes
            if isinstance(r, APIRoute) and "DELETE" in r.methods
        }

        # 兼容带 /audit 前缀或不带前缀两种注册方式
        assert any(p.endswith("/logs/batch")      for p in delete_paths), f"缺少 */logs/batch 路由，实际: {delete_paths}"
        assert any(p.endswith("/logs/{log_id}")   for p in delete_paths), f"缺少 */logs/{{log_id}} 路由，实际: {delete_paths}"
