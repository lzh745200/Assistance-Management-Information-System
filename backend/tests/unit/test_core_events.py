import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.core.events import EventBus, event_bus


@pytest.fixture(autouse=True)
def clear_event_bus():
    event_bus.clear()
    yield


class TestEventBus:
    def test_on_register_handler(self):
        bus = EventBus()
        handler = MagicMock()
        bus.on("test_event", handler)
        assert bus.listener_count("test_event") == 1
        assert "test_event" in bus.events()

    def test_on_multiple_handlers(self):
        bus = EventBus()
        h1 = MagicMock()
        h2 = MagicMock()
        bus.on("e", h1)
        bus.on("e", h2)
        assert bus.listener_count("e") == 2

    def test_once_handler(self):
        bus = EventBus()
        handler = MagicMock()
        bus.once("e", handler)
        bus.emit("e")
        handler.assert_called_once()
        assert bus.listener_count("e") == 0

    def test_once_fires_only_once(self):
        bus = EventBus()
        handler = MagicMock()
        bus.once("e", handler)
        bus.emit("e")
        bus.emit("e")
        handler.assert_called_once()

    def test_off_removes_handler(self):
        bus = EventBus()
        handler = MagicMock()
        bus.on("e", handler)
        bus.off("e", handler)
        assert bus.listener_count("e") == 0

    def test_off_unknown_event_no_error(self):
        bus = EventBus()
        bus.off("nonexistent", lambda: None)

    def test_off_removes_from_once(self):
        bus = EventBus()
        handler = MagicMock()
        bus.once("e", handler)
        bus.off("e", handler)
        bus.emit("e")
        handler.assert_not_called()

    def test_emit_sync_handler(self):
        bus = EventBus()
        results = []

        def handler(arg):
            results.append(arg)

        bus.on("e", handler)
        bus.emit("e", 42)
        assert results == [42]

    @pytest.mark.asyncio
    async def test_emit_async_handler_with_running_loop(self):
        bus = EventBus()
        results = []

        async def handler(arg):
            results.append(arg)

        bus.on("e", handler)
        bus.emit("e", 99)
        await asyncio.sleep(0)
        assert results == [99]

    def test_emit_async_handler_no_running_loop(self):
        bus = EventBus()
        results = []

        async def handler(arg):
            results.append(arg)

        bus.on("e", handler)
        with patch.object(asyncio, "get_running_loop", side_effect=RuntimeError):
            bus.emit("e", 77)
        assert results == [77]

    def test_emit_handler_raises_exception(self):
        bus = EventBus()
        error_handler = MagicMock(side_effect=ValueError("oops"))
        good_handler = MagicMock()
        bus.on("e", error_handler)
        bus.on("e", good_handler)
        bus.emit("e")
        error_handler.assert_called_once()
        good_handler.assert_called_once()

    def test_emit_async_handler_raises_exception(self):
        bus = EventBus()

        async def bad_handler():
            raise ValueError("async oops")

        good_handler = MagicMock()
        bus.on("e", bad_handler)
        bus.on("e", good_handler)
        bus.emit("e")
        good_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_emit_async_sync_handler(self):
        bus = EventBus()
        results = []

        def sync_handler(arg):
            results.append(arg)

        bus.on("e", sync_handler)
        await bus.emit_async("e", 55)
        assert results == [55]

    @pytest.mark.asyncio
    async def test_emit_async_async_handler(self):
        bus = EventBus()
        results = []

        async def async_handler(arg):
            results.append(arg)

        bus.on("e", async_handler)
        await bus.emit_async("e", 33)
        assert results == [33]

    @pytest.mark.asyncio
    async def test_emit_async_handler_raises_exception(self):
        bus = EventBus()
        good = MagicMock()

        async def bad():
            raise RuntimeError("boom")

        bus.on("e", bad)
        bus.on("e", good)
        await bus.emit_async("e")
        good.assert_called_once()

    def test_emit_no_handlers(self):
        bus = EventBus()
        bus.emit("nonexistent")

    def test_listener_count_empty(self):
        bus = EventBus()
        assert bus.listener_count("anything") == 0

    def test_events_empty(self):
        bus = EventBus()
        assert bus.events() == []

    def test_events_returns_sorted_names(self):
        bus = EventBus()
        bus.on("z", lambda: None)
        bus.once("a", lambda: None)
        assert bus.events() == ["a", "z"]

    def test_clear_removes_all(self):
        bus = EventBus()
        bus.on("a", lambda: None)
        bus.once("b", lambda: None)
        bus.clear()
        assert bus.events() == []
        assert bus.listener_count("a") == 0
        assert bus.listener_count("b") == 0

    def test_global_event_bus_instance(self):
        assert isinstance(event_bus, EventBus)
        assert event_bus.listener_count("any") == 0
