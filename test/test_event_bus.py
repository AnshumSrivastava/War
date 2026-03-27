"""
test/test_event_bus.py
QA tests for services.event_bus

Validates the publish/subscribe system: delivery, unsubscribe,
error isolation between subscribers, and clear().
"""
import pytest
from services import event_bus


@pytest.fixture(autouse=True)
def reset_bus():
    """Guarantee a clean bus for every test — no cross-test subscriber leakage."""
    event_bus.clear()
    yield
    event_bus.clear()


# ---------------------------------------------------------------------------
# Basic pub/sub
# ---------------------------------------------------------------------------

class TestSubscribeAndEmit:
    def test_subscriber_receives_payload(self):
        received = []
        event_bus.subscribe("test_event", received.append)
        event_bus.emit("test_event", {"value": 42})
        assert received == [{"value": 42}]

    def test_multiple_subscribers_all_receive(self):
        log_a, log_b = [], []
        event_bus.subscribe("tick", log_a.append)
        event_bus.subscribe("tick", log_b.append)
        event_bus.emit("tick", "data")
        assert log_a == ["data"]
        assert log_b == ["data"]

    def test_emit_no_subscribers_does_not_crash(self):
        event_bus.emit("nonexistent_event", {"any": "data"})  # Must not raise

    def test_emit_none_payload(self):
        received = []
        event_bus.subscribe("null_event", received.append)
        event_bus.emit("null_event", None)
        assert received == [None]

    def test_different_events_isolated(self):
        log_a, log_b = [], []
        event_bus.subscribe("event_a", log_a.append)
        event_bus.subscribe("event_b", log_b.append)
        event_bus.emit("event_a", 1)
        assert log_a == [1]
        assert log_b == []   # event_b subscriber not called

    def test_emit_called_multiple_times_accumulates(self):
        received = []
        event_bus.subscribe("multi", received.append)
        for i in range(5):
            event_bus.emit("multi", i)
        assert received == [0, 1, 2, 3, 4]


# ---------------------------------------------------------------------------
# Unsubscribe
# ---------------------------------------------------------------------------

class TestUnsubscribe:
    def test_unsubscribe_stops_delivery(self):
        received = []
        handler = received.append
        event_bus.subscribe("ev", handler)
        event_bus.emit("ev", 1)
        event_bus.unsubscribe("ev", handler)
        event_bus.emit("ev", 2)
        assert received == [1]  # Only first emit received

    def test_unsubscribe_nonexistent_does_not_crash(self):
        def dummy(_): pass
        event_bus.unsubscribe("no_such_event", dummy)   # Must not raise

    def test_unsubscribe_only_removes_matching_callback(self):
        log_a, log_b = [], []
        event_bus.subscribe("shared", log_a.append)
        event_bus.subscribe("shared", log_b.append)
        event_bus.unsubscribe("shared", log_a.append)
        event_bus.emit("shared", "ping")
        assert log_a == []
        assert log_b == ["ping"]


# ---------------------------------------------------------------------------
# Error isolation
# ---------------------------------------------------------------------------

class TestErrorIsolation:
    def test_broken_subscriber_does_not_crash_emitter(self):
        """A subscriber that raises must not propagate its exception."""
        def bad_handler(_):
            raise RuntimeError("Subscriber blew up!")

        good_log = []
        event_bus.subscribe("safe_event", bad_handler)
        event_bus.subscribe("safe_event", good_log.append)
        event_bus.emit("safe_event", "hello")   # Must not raise
        assert good_log == ["hello"]


# ---------------------------------------------------------------------------
# Clear
# ---------------------------------------------------------------------------

class TestClear:
    def test_clear_all_removes_all_subscribers(self):
        received = []
        event_bus.subscribe("a", received.append)
        event_bus.subscribe("b", received.append)
        event_bus.clear()
        event_bus.emit("a", 1)
        event_bus.emit("b", 2)
        assert received == []

    def test_clear_single_event(self):
        log_a, log_b = [], []
        event_bus.subscribe("a", log_a.append)
        event_bus.subscribe("b", log_b.append)
        event_bus.clear("a")
        event_bus.emit("a", 1)
        event_bus.emit("b", 2)
        assert log_a == []
        assert log_b == [2]
