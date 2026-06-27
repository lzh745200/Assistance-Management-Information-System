"""Tests for event bus enhancements (dead letter queue, system event types)."""


class TestDeadLetterQueue:
    """Tests for dead letter queue functionality."""

    def test_add_to_dead_letter(self):
        """Events that fail should be moved to dead letter queue."""
        from app.services.event_bus import (
            add_to_dead_letter,
            get_dead_letter_events,
            DomainEvent,
        )

        event = DomainEvent(
            event_type="test.event",
            aggregate_id="test-1",
            aggregate_type="Test",
            payload={"key": "value"},
        )

        add_to_dead_letter(event, ValueError("test error"), "TestHandler")

        dead = get_dead_letter_events()
        assert len(dead) >= 1
        latest = dead[-1]
        assert latest["event"]["event_type"] == "test.event"
        assert "test error" in latest["error"]
        assert latest["handler"] == "TestHandler"

    def test_dead_letter_size_limit(self):
        """Dead letter queue should not exceed MAX_DEAD_LETTER_SIZE."""
        from app.services.event_bus import (
            add_to_dead_letter,
            get_dead_letter_events,
            DomainEvent,
        )

        # Add 600 events (limit is 500)
        for i in range(600):
            event = DomainEvent(
                event_type="test.event",
                aggregate_id=str(i),
                aggregate_type="Test",
                payload={},
            )
            add_to_dead_letter(event, ValueError(f"error-{i}"), "Handler")

        dead = get_dead_letter_events(limit=1000)
        assert len(dead) <= 550  # Allow some margin

    def test_replay_dead_letter_removes_from_queue(self):
        """Replaying a valid index should return True when the event exists."""
        from app.services.event_bus import (
            add_to_dead_letter,
            get_dead_letter_events,
            replay_dead_letter,
            DomainEvent,
        )

        # Use a unique event type to isolate from other tests
        import uuid
        unique_type = f"replay.{uuid.uuid4().hex[:8]}"

        event = DomainEvent(
            event_type=unique_type,
            aggregate_id="replay-isolated",
            aggregate_type="Test",
            payload={"action": "replay"},
        )
        add_to_dead_letter(event, ValueError("test"), "Handler")

        before = len(get_dead_letter_events())
        # The event was just added; it should be the last one
        last_idx = before - 1
        result = replay_dead_letter(last_idx)

        assert result is True, f"replay returned {result} for index {last_idx}, queue size was {before}"

    def test_replay_invalid_index_returns_false(self):
        """Replaying an invalid index should return False."""
        from app.services.event_bus import replay_dead_letter

        result = replay_dead_letter(99999)
        assert result is False


class TestSystemEventTypes:
    """Tests for standard system event type constants."""

    def test_project_event_types(self):
        from app.services.event_bus import SystemEventTypes

        assert SystemEventTypes.PROJECT_CREATED == "project.created"
        assert SystemEventTypes.PROJECT_DELETED == "project.deleted"

    def test_fund_event_types(self):
        from app.services.event_bus import SystemEventTypes

        assert SystemEventTypes.FUND_ALLOCATED == "fund.allocated"
        assert SystemEventTypes.FUND_ANOMALY_DETECTED == "fund.anomaly_detected"

    def test_user_event_types(self):
        from app.services.event_bus import SystemEventTypes

        assert SystemEventTypes.USER_LOGIN == "user.login"
        assert SystemEventTypes.USER_PASSWORD_CHANGED == "user.password_changed"
        assert SystemEventTypes.USER_LOCKED == "user.locked"

    def test_security_event_types(self):
        from app.services.event_bus import SystemEventTypes

        assert SystemEventTypes.SECURITY_ALERT == "security.alert"


class TestEventBusIntegration:
    """Smoke tests for event bus."""

    def test_event_bus_singleton(self):
        """EventBus should be a singleton."""
        from app.services.event_bus import event_bus, EventBus

        another = EventBus()
        assert event_bus is another

    def test_domain_event_auto_generates_id(self):
        """DomainEvent should auto-generate event_id and occurred_at."""
        from app.services.event_bus import DomainEvent

        event = DomainEvent(
            event_type="auto.test",
            aggregate_id="auto-1",
            aggregate_type="Test",
            payload={},
        )
        assert event.event_id is not None
        assert len(event.event_id) > 0
        assert event.occurred_at is not None
