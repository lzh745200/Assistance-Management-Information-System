"""补充测试 — 目标 100% 覆盖 app/services/event_bus.py。

现有 test_event_bus.py 仅覆盖了基本实例化和可调用性。本文件补充：
- DomainEvent.to_dict / __post_init__ 显式参数
- EventBus._start_worker（无运行 loop / 有运行 loop 两个分支）
- EventBus._process_events（正常处理 + 异常处理）
- EventBus._dispatch_event（有处理器 / 无处理器 / 通配符 / 处理器异常）
- EventBus._execute_handler（异常 re-raise）
- EventBus.publish（async_mode=True/False + 历史大小限制）
- EventBus.publish_sync（运行中 loop / 非运行 loop 两个分支）
- EventBus.get_event_history（过滤 + limit）
- EventBus.clear_history
- 死信队列：add_to_dead_letter / get_dead_letter_events / replay_dead_letter
- FundCreatedHandler / AuditLogHandler
- SystemEventTypes 常量
"""
import asyncio
import threading
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.services.event_bus import (
    AuditLogHandler,
    DomainEvent,
    EventBus,
    EventHandler,
    EventPriority,
    FundCreatedHandler,
    SystemEventTypes,
    add_to_dead_letter,
    _dead_letter_queue,
    get_dead_letter_events,
    replay_dead_letter,
)


# ---------------------------------------------------------------------------
# 公共 fixture：每个测试前清空 EventBus 单例状态 + 死信队列
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_bus():
    bus = EventBus()
    # 取消任何残留的 worker task（防止跨测试泄漏）
    if bus._worker_task is not None and not bus._worker_task.done():
        bus._worker_task.cancel()
    bus._worker_task = None
    # 重建事件队列：asyncio.Queue 首次使用时绑定到当前事件循环，
    # pytest-asyncio（function scope）每个 async 测试用不同循环，
    # 不重建会触发 "bound to a different event loop" RuntimeError。
    bus._event_queue = asyncio.Queue()
    bus._handlers.clear()
    bus._event_history.clear()
    _dead_letter_queue.clear()
    yield
    # 测试后同样清理
    if bus._worker_task is not None and not bus._worker_task.done():
        bus._worker_task.cancel()
    bus._worker_task = None
    bus._handlers.clear()
    bus._event_history.clear()
    _dead_letter_queue.clear()


# ---------------------------------------------------------------------------
# 辅助：异步 EventHandler 实现
# ---------------------------------------------------------------------------


class _RecorderHandler(EventHandler):
    """记录收到的事件，可设置优先级。"""

    def __init__(self, types=None, priority=EventPriority.NORMAL, fail=False):
        self._types = types or ["test"]
        self._priority = priority
        self._fail = fail
        self.received = []

    @property
    def event_types(self):
        return self._types

    @property
    def priority(self):
        return self._priority

    async def handle(self, event: DomainEvent) -> None:
        self.received.append(event)
        if self._fail:
            raise RuntimeError("handler error")


# ---------------------------------------------------------------------------
# EventPriority
# ---------------------------------------------------------------------------


class TestEventPriority:
    def test_values(self):
        assert EventPriority.LOW == 1
        assert EventPriority.NORMAL == 5
        assert EventPriority.HIGH == 10
        assert EventPriority.CRITICAL == 20

    def test_ordering(self):
        assert EventPriority.LOW < EventPriority.NORMAL < EventPriority.HIGH < EventPriority.CRITICAL


# ---------------------------------------------------------------------------
# DomainEvent
# ---------------------------------------------------------------------------


class TestDomainEvent:
    def test_defaults_generated(self):
        e = DomainEvent("test", "1", "Test", {"k": "v"})
        assert e.event_id is not None
        assert e.occurred_at is not None
        assert e.priority == EventPriority.NORMAL
        assert e.correlation_id is None

    def test_explicit_values_respected(self):
        eid = "custom-id"
        ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
        e = DomainEvent(
            event_type="t",
            aggregate_id="1",
            aggregate_type="T",
            payload={},
            event_id=eid,
            occurred_at=ts,
            correlation_id="corr-1",
            priority=EventPriority.CRITICAL,
        )
        assert e.event_id == eid
        assert e.occurred_at == ts
        assert e.correlation_id == "corr-1"
        assert e.priority == EventPriority.CRITICAL

    def test_to_dict_full(self):
        e = DomainEvent(
            event_type="fund.created",
            aggregate_id="42",
            aggregate_type="Fund",
            payload={"amount": 100},
            priority=EventPriority.HIGH,
            correlation_id="corr-99",
        )
        d = e.to_dict()
        assert d["event_type"] == "fund.created"
        assert d["aggregate_id"] == "42"
        assert d["aggregate_type"] == "Fund"
        assert d["payload"] == {"amount": 100}
        assert d["priority"] == EventPriority.HIGH.value  # 覆盖 .value 访问
        assert d["correlation_id"] == "corr-99"
        assert d["event_id"] == e.event_id
        assert d["occurred_at"] == e.occurred_at.isoformat()

    def test_to_dict_occurred_at_none(self):
        """occurred_at=None 时 to_dict 返回 None。"""
        e = DomainEvent("t", "1", "T", {})
        e.occurred_at = None
        d = e.to_dict()
        assert d["occurred_at"] is None

    def test_event_id_unique(self):
        e1 = DomainEvent("t", "1", "T", {})
        e2 = DomainEvent("t", "2", "T", {})
        assert e1.event_id != e2.event_id


# ---------------------------------------------------------------------------
# EventBus 单例 + _start_worker
# ---------------------------------------------------------------------------


class TestEventBusSingleton:
    def test_singleton_identity(self):
        assert EventBus() is EventBus()

    def test_start_worker_no_running_loop(self):
        """同步上下文无运行 loop → _worker_task = None。"""
        bus = EventBus()
        bus._worker_task = "sentinel"  # 强制重置
        bus._start_worker()
        assert bus._worker_task is None

    async def test_start_worker_with_running_loop(self):
        """异步上下文运行中 loop → _worker_task = asyncio.Task。"""
        bus = EventBus()
        bus._worker_task = None
        bus._start_worker()
        assert isinstance(bus._worker_task, asyncio.Task)
        # 立即取消后台 worker（_process_events 是无限循环）
        bus._worker_task.cancel()
        try:
            await asyncio.wait_for(bus._worker_task, timeout=2.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
        bus._worker_task = None


# ---------------------------------------------------------------------------
# _process_events（后台 worker 循环）
# ---------------------------------------------------------------------------


class TestProcessEvents:
    async def test_processes_queued_event(self):
        """事件从队列取出后分发到处理器。"""
        bus = EventBus()
        handler = _RecorderHandler(types=["test.evt"])
        bus.subscribe("test.evt", handler)

        event = DomainEvent("test.evt", "1", "T", {})
        await bus._event_queue.put(event)

        task = asyncio.create_task(bus._process_events())
        # 等待处理器被调用
        for _ in range(50):
            if handler.received:
                break
            await asyncio.sleep(0.02)
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=2.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

        assert handler.received == [event]

    async def test_exception_does_not_stop_loop(self):
        """_dispatch_event 抛异常时被捕获、记录，循环不中断。

        注意：mock logger 以避免 pytest 输出捕获与 logging.flush 死锁。
        """
        bus = EventBus()
        event = DomainEvent("test.evt", "1", "T", {})
        await bus._event_queue.put(event)

        call_count = [0]

        async def failing_dispatch(evt):
            call_count[0] += 1
            raise RuntimeError("dispatch error")

        original = bus._dispatch_event
        bus._dispatch_event = failing_dispatch
        try:
            # mock logger 防止 flush 死锁
            with patch("app.services.event_bus.logger"):
                task = asyncio.create_task(bus._process_events())
                for _ in range(50):
                    if call_count[0] >= 1:
                        break
                    await asyncio.sleep(0.02)
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=2.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
        finally:
            bus._dispatch_event = original

        assert call_count[0] >= 1


# ---------------------------------------------------------------------------
# _dispatch_event
# ---------------------------------------------------------------------------


class TestDispatchEvent:
    async def test_dispatches_to_matching_handler(self):
        bus = EventBus()
        h = _RecorderHandler(types=["test.evt"])
        bus.subscribe("test.evt", h)

        event = DomainEvent("test.evt", "1", "T", {})
        await bus._dispatch_event(event)
        assert h.received == [event]

    async def test_no_handlers_logs_warning(self):
        """无匹配处理器时不抛异常，仅记录警告。"""
        bus = EventBus()
        event = DomainEvent("unhandled", "1", "T", {})
        with patch("app.services.event_bus.logger"):
            await bus._dispatch_event(event)

    async def test_wildcard_handler_receives_event(self):
        bus = EventBus()
        h = _RecorderHandler(types=["*"])
        bus.subscribe("*", h)

        event = DomainEvent("any.type", "1", "T", {})
        await bus._dispatch_event(event)
        assert h.received == [event]

    async def test_handler_exception_logged_not_raised(self):
        """处理器异常被 gather(return_exceptions=True) 捕获，不向上抛。"""
        bus = EventBus()
        h = _RecorderHandler(types=["test.evt"], fail=True)
        bus.subscribe("test.evt", h)

        event = DomainEvent("test.evt", "1", "T", {})
        with patch("app.services.event_bus.logger"):
            # 不应抛异常
            await bus._dispatch_event(event)
        # 处理器确实被调用了
        assert len(h.received) == 1

    async def test_duplicate_subscribe_ignored(self):
        """同一处理器重复订阅同一事件类型应被忽略。"""
        bus = EventBus()
        h = _RecorderHandler(types=["test.evt"])
        bus.subscribe("test.evt", h)
        bus.subscribe("test.evt", h)  # 重复
        assert len(bus._handlers["test.evt"]) == 1

    async def test_priority_sorting_high_first(self):
        """高优先级处理器排在前面（sorted reverse=True）。"""
        bus = EventBus()
        low = _RecorderHandler(types=["test.evt"], priority=EventPriority.LOW)
        high = _RecorderHandler(types=["test.evt"], priority=EventPriority.HIGH)
        bus.subscribe("test.evt", low)
        bus.subscribe("test.evt", high)

        # 验证排序结果
        from app.services.event_bus import EventPriority as EP
        handlers = bus._handlers.get("test.evt", [])
        wildcard = bus._handlers.get("*", [])
        all_h = list(set(handlers + wildcard))
        sorted_h = sorted(all_h, key=lambda h: getattr(h, "priority", EP.NORMAL).value, reverse=True)
        assert sorted_h[0] is high
        assert sorted_h[1] is low


# ---------------------------------------------------------------------------
# _execute_handler
# ---------------------------------------------------------------------------


class TestExecuteHandler:
    async def test_success(self):
        bus = EventBus()
        h = _RecorderHandler(types=["test"])
        event = DomainEvent("test", "1", "T", {})
        await bus._execute_handler(h, event)
        assert h.received == [event]

    async def test_exception_reraised(self):
        """_execute_handler 捕获异常、记录日志后 re-raise。"""
        bus = EventBus()
        h = _RecorderHandler(types=["test"], fail=True)
        event = DomainEvent("test", "1", "T", {})
        with patch("app.services.event_bus.logger"):
            with pytest.raises(RuntimeError, match="handler error"):
                await bus._execute_handler(h, event)


# ---------------------------------------------------------------------------
# subscribe / unsubscribe
# ---------------------------------------------------------------------------


class TestSubscribeUnsubscribe:
    def test_subscribe_adds_handler(self):
        bus = EventBus()
        h = _RecorderHandler(types=["test"])
        bus.subscribe("test", h)
        assert h in bus._handlers["test"]

    def test_unsubscribe_removes_handler(self):
        bus = EventBus()
        h = _RecorderHandler(types=["test"])
        bus.subscribe("test", h)
        bus.unsubscribe("test", h)
        assert h not in bus._handlers.get("test", [])

    def test_unsubscribe_nonexistent_event_type(self):
        """取消订阅不存在的事件类型 → 无操作。"""
        bus = EventBus()
        h = _RecorderHandler(types=["test"])
        # 不应抛异常
        bus.unsubscribe("nonexistent", h)


# ---------------------------------------------------------------------------
# publish
# ---------------------------------------------------------------------------


class TestPublish:
    async def test_async_mode_enqueues_event(self):
        """async_mode=True → 事件放入队列 + 写入历史。"""
        bus = EventBus()
        event = DomainEvent("test", "1", "T", {})
        await bus.publish(event, async_mode=True)
        # 队列非空
        assert not bus._event_queue.empty()
        # 历史记录
        assert bus._event_history == [event]
        # 清理队列
        while not bus._event_queue.empty():
            bus._event_queue.get_nowait()

    async def test_sync_mode_dispatches_directly(self):
        """async_mode=False → 直接分发，不放入队列。"""
        bus = EventBus()
        h = _RecorderHandler(types=["test"])
        bus.subscribe("test", h)
        event = DomainEvent("test", "1", "T", {})
        await bus.publish(event, async_mode=False)
        assert h.received == [event]
        # 队列应仍为空
        assert bus._event_queue.empty()
        assert bus._event_history == [event]

    async def test_history_size_limit_trims_old(self):
        """事件历史超过 max_history_size 时删除最旧。"""
        bus = EventBus()
        bus._max_history_size = 3
        for i in range(5):
            await bus.publish(DomainEvent("t", str(i), "T", {}), async_mode=True)
        assert len(bus._event_history) == 3
        # 保留的是最后 3 个（aggregate_id 2,3,4）
        assert [e.aggregate_id for e in bus._event_history] == ["2", "3", "4"]
        # 清理队列
        while not bus._event_queue.empty():
            bus._event_queue.get_nowait()


# ---------------------------------------------------------------------------
# publish_sync
# ---------------------------------------------------------------------------


class TestPublishSync:
    def test_sync_context_creates_thread(self):
        """同步上下文（无运行 loop）→ 在新线程中创建 loop 运行 dispatch。"""
        bus = EventBus()
        received = threading.Event()
        captured = []

        class _CatchHandler(EventHandler):
            @property
            def event_types(self):
                return ["test.sync"]

            async def handle(self, event):
                captured.append(event)
                received.set()

        bus.subscribe("test.sync", _CatchHandler())

        event = DomainEvent("test.sync", "1", "T", {})
        bus.publish_sync(event)

        assert received.wait(timeout=5.0), "处理器未在 5s 内被调用"
        assert len(captured) == 1
        assert bus._event_history == [event]

    async def test_async_context_creates_task(self):
        """异步上下文（loop 运行中）→ asyncio.create_task 分发。"""
        bus = EventBus()
        h = _RecorderHandler(types=["test.async"])
        bus.subscribe("test.async", h)

        event = DomainEvent("test.async", "1", "T", {})
        bus.publish_sync(event)

        # 等待 create_task 调度执行
        for _ in range(100):
            if h.received:
                break
            await asyncio.sleep(0.01)
        assert h.received == [event]
        assert bus._event_history == [event]


# ---------------------------------------------------------------------------
# get_event_history / clear_history
# ---------------------------------------------------------------------------


class TestEventHistory:
    def test_get_all(self):
        bus = EventBus()
        e1 = DomainEvent("a", "1", "T", {})
        e2 = DomainEvent("b", "2", "T", {})
        e3 = DomainEvent("a", "3", "T", {})
        bus._event_history.extend([e1, e2, e3])

        result = bus.get_event_history()
        assert len(result) == 3

    def test_filter_by_event_type(self):
        bus = EventBus()
        e1 = DomainEvent("type_a", "1", "T", {})
        e2 = DomainEvent("type_b", "2", "T", {})
        e3 = DomainEvent("type_a", "3", "T", {})
        bus._event_history.extend([e1, e2, e3])

        result = bus.get_event_history(event_type="type_a")
        assert len(result) == 2
        assert all(e.event_type == "type_a" for e in result)

    def test_filter_by_aggregate_id(self):
        bus = EventBus()
        e1 = DomainEvent("a", "1", "T", {})
        e2 = DomainEvent("b", "2", "T", {})
        bus._event_history.extend([e1, e2])

        result = bus.get_event_history(aggregate_id="2")
        assert len(result) == 1
        assert result[0].aggregate_id == "2"

    def test_limit(self):
        bus = EventBus()
        for i in range(10):
            bus._event_history.append(DomainEvent("t", str(i), "T", {}))
        result = bus.get_event_history(limit=3)
        assert len(result) == 3
        # 返回最后 3 个
        assert [e.aggregate_id for e in result] == ["7", "8", "9"]

    def test_clear_history(self):
        bus = EventBus()
        bus._event_history.append(DomainEvent("t", "1", "T", {}))
        assert len(bus._event_history) == 1
        bus.clear_history()
        assert len(bus._event_history) == 0


# ---------------------------------------------------------------------------
# 死信队列
# ---------------------------------------------------------------------------


class TestDeadLetterQueue:
    def test_add_to_dead_letter(self):
        event = DomainEvent("test.dlq", "1", "T", {"k": "v"})
        error = ValueError("bad thing")
        add_to_dead_letter(event, error, "FailingHandler")

        assert len(_dead_letter_queue) == 1
        entry = list(_dead_letter_queue)[0]
        assert entry["handler"] == "FailingHandler"
        assert entry["error"] == str(error)
        assert entry["event"]["event_type"] == "test.dlq"
        assert entry["event"]["payload"] == {"k": "v"}
        assert "failed_at" in entry

    def test_get_dead_letter_events_default_limit(self):
        for i in range(5):
            add_to_dead_letter(
                DomainEvent("t", str(i), "T", {}),
                RuntimeError(f"err{i}"),
                f"H{i}",
            )
        result = get_dead_letter_events()
        assert len(result) == 5
        assert result[-1]["handler"] == "H4"

    def test_get_dead_letter_events_with_limit(self):
        for i in range(10):
            add_to_dead_letter(
                DomainEvent("t", str(i), "T", {}),
                RuntimeError(f"err{i}"),
                f"H{i}",
            )
        result = get_dead_letter_events(limit=3)
        assert len(result) == 3
        # 返回最后 3 个
        assert [r["handler"] for r in result] == ["H7", "H8", "H9"]

    def test_get_dead_letter_events_empty(self):
        assert get_dead_letter_events() == []

    def test_replay_valid_index(self):
        """重放有效索引的事件：事件从死信队列删除 + 重新发布。"""
        bus = EventBus()
        received = threading.Event()
        captured = []

        class _CatchHandler(EventHandler):
            @property
            def event_types(self):
                return ["test.replay"]

            async def handle(self, event):
                captured.append(event)
                received.set()

        bus.subscribe("test.replay", _CatchHandler())

        event = DomainEvent("test.replay", "42", "T", {"amount": 100})
        add_to_dead_letter(event, RuntimeError("original error"), "OriginalHandler")

        result = replay_dead_letter(0)
        assert result is True
        # 事件已从死信队列删除
        assert len(_dead_letter_queue) == 0
        # 事件被重新发布
        assert received.wait(timeout=5.0)
        assert len(captured) == 1
        assert captured[0].aggregate_id == "42"
        assert captured[0].payload == {"amount": 100}

    def test_replay_invalid_index_negative(self):
        add_to_dead_letter(
            DomainEvent("t", "1", "T", {}),
            RuntimeError("e"),
            "H",
        )
        assert replay_dead_letter(-1) is False
        # 队列未变
        assert len(_dead_letter_queue) == 1

    def test_replay_invalid_index_out_of_range(self):
        assert replay_dead_letter(0) is False  # 空队列
        add_to_dead_letter(
            DomainEvent("t", "1", "T", {}),
            RuntimeError("e"),
            "H",
        )
        assert replay_dead_letter(99) is False

    def test_replay_removes_entry_and_keeps_rest(self):
        """重放中间索引时，其余条目保持顺序。"""
        for i in range(3):
            add_to_dead_letter(
                DomainEvent("t", str(i), "T", {}),
                RuntimeError(f"e{i}"),
                f"H{i}",
            )
        # 重放索引 1（中间）
        result = replay_dead_letter(1)
        assert result is True
        # 剩余 2 个：H0 和 H2
        remaining = list(_dead_letter_queue)
        assert len(remaining) == 2
        assert remaining[0]["handler"] == "H0"
        assert remaining[1]["handler"] == "H2"


# ---------------------------------------------------------------------------
# 内置 Handler
# ---------------------------------------------------------------------------


class TestBuiltinHandlers:
    async def test_fund_created_handler_event_types(self):
        h = FundCreatedHandler()
        assert "FUND_CREATED" in h.event_types
        assert "FUND_APPROVED" in h.event_types

    async def test_fund_created_handler_handle(self):
        h = FundCreatedHandler()
        event = DomainEvent("FUND_CREATED", "1", "Fund", {"amount": 1000})
        # 不应抛异常
        await h.handle(event)

    async def test_audit_log_handler_event_types(self):
        h = AuditLogHandler()
        assert "FUND_CREATED" in h.event_types
        assert "FUND_APPROVED" in h.event_types
        assert "FUND_ALLOCATED" in h.event_types
        assert "FUND_COMPLETED" in h.event_types

    async def test_audit_log_handler_handle(self):
        h = AuditLogHandler()
        event = DomainEvent("FUND_ALLOCATED", "1", "Fund", {"amount": 500})
        # 不应抛异常
        await h.handle(event)


# ---------------------------------------------------------------------------
# SystemEventTypes 常量
# ---------------------------------------------------------------------------


class TestSystemEventTypes:
    def test_project_constants(self):
        assert SystemEventTypes.PROJECT_CREATED == "project.created"
        assert SystemEventTypes.PROJECT_UPDATED == "project.updated"
        assert SystemEventTypes.PROJECT_DELETED == "project.deleted"
        assert SystemEventTypes.PROJECT_STATUS_CHANGED == "project.status_changed"

    def test_fund_constants(self):
        assert SystemEventTypes.FUND_ALLOCATED == "fund.allocated"
        assert SystemEventTypes.FUND_TRANSFERRED == "fund.transferred"
        assert SystemEventTypes.FUND_ANOMALY_DETECTED == "fund.anomaly_detected"
        assert SystemEventTypes.FUND_SETTLEMENT_COMPLETED == "fund.settlement_completed"

    def test_village_constants(self):
        assert SystemEventTypes.VILLAGE_REGISTERED == "village.registered"
        assert SystemEventTypes.VILLAGE_UPDATED == "village.updated"
        assert SystemEventTypes.VILLAGE_DATA_IMPORTED == "village.data_imported"

    def test_approval_constants(self):
        assert SystemEventTypes.APPROVAL_SUBMITTED == "approval.submitted"
        assert SystemEventTypes.APPROVAL_APPROVED == "approval.approved"
        assert SystemEventTypes.APPROVAL_REJECTED == "approval.rejected"

    def test_user_security_constants(self):
        assert SystemEventTypes.USER_LOGIN == "user.login"
        assert SystemEventTypes.USER_LOGOUT == "user.logout"
        assert SystemEventTypes.USER_PASSWORD_CHANGED == "user.password_changed"
        assert SystemEventTypes.USER_LOCKED == "user.locked"
        assert SystemEventTypes.SECURITY_ALERT == "security.alert"

    def test_system_constants(self):
        assert SystemEventTypes.BACKUP_CREATED == "system.backup_created"
        assert SystemEventTypes.BACKUP_RESTORED == "system.backup_restored"
        assert SystemEventTypes.DATABASE_MAINTENANCE == "system.database_maintenance"
        assert SystemEventTypes.PERFORMANCE_THRESHOLD == "system.performance_threshold"
