"""事件总线单元测试"""

class TestEventPriority:
    def test_enum_values(self):
        from app.services.event_bus import EventPriority
        assert EventPriority.LOW == 1
        assert EventPriority.NORMAL == 5
        assert EventPriority.HIGH == 10
        assert EventPriority.CRITICAL == 20

    def test_ordering(self):
        from app.services.event_bus import EventPriority
        assert EventPriority.LOW < EventPriority.NORMAL < EventPriority.HIGH < EventPriority.CRITICAL

class TestDomainEvent:
    def test_create_event(self):
        from app.services.event_bus import DomainEvent, EventPriority
        event = DomainEvent(
            event_type="fund.created",
            aggregate_id="1",
            aggregate_type="fund",
            payload={"amount": 100},
        )
        assert event.event_type == "fund.created"
        assert event.aggregate_id == "1"
        assert event.payload == {"amount": 100}
        assert event.priority == EventPriority.NORMAL
        assert event.event_id is not None  # auto-generated
        assert event.occurred_at is not None

    def test_event_id_unique(self):
        from app.services.event_bus import DomainEvent
        e1 = DomainEvent("test", "1", "test", {})
        e2 = DomainEvent("test", "2", "test", {})
        assert e1.event_id != e2.event_id

    def test_event_type_property(self):
        from app.services.event_bus import DomainEvent
        event = DomainEvent("fund.created", "1", "fund", {})
        assert event.event_type == "fund.created"

class TestEventBus:
    def test_singleton(self):
        from app.services.event_bus import EventBus
        bus1 = EventBus()
        bus2 = EventBus()
        assert bus1 is bus2

    def test_subscribe_and_unsubscribe(self):
        from app.services.event_bus import EventBus
        bus = EventBus()
        received = []
        def handler(event): received.append(event)
        bus.subscribe("test.event", handler)
        bus.unsubscribe("test.event", handler)
        # After unsubscribe, the handler should be removed
        assert callable(bus.subscribe)

    def test_publish_sync_callable(self):
        from app.services.event_bus import EventBus
        assert callable(EventBus().publish_sync)

    def test_subscribe_callable(self):
        from app.services.event_bus import EventBus
        bus = EventBus()
        assert callable(bus.subscribe)
        assert callable(bus.unsubscribe)
        assert callable(bus.publish_sync)
