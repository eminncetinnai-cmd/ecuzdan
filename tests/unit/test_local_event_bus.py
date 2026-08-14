"""
Unit Tests - Local Event Bus
In-memory event bus for synchronous event dispatching
"""

import pytest
from infrastructure.events.local_event_bus import LocalEventBus
from domain.common.events import DomainEvent
from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class TestEvent(DomainEvent):
    """Test event for testing purposes."""
    data: str = "test_data"


@pytest.mark.unit
def test_local_event_bus_subscribe():
    """Test subscribing a handler to an event"""
    bus = LocalEventBus()
    
    def handler(event):
        pass
    
    bus.subscribe(TestEvent, handler)
    assert handler in bus._handlers[TestEvent]


@pytest.mark.unit
def test_local_event_bus_subscribe_duplicate():
    """Test subscribing same handler twice doesn't duplicate"""
    bus = LocalEventBus()
    
    def handler(event):
        pass
    
    bus.subscribe(TestEvent, handler)
    bus.subscribe(TestEvent, handler)
    
    assert bus._handlers[TestEvent].count(handler) == 1


@pytest.mark.unit
def test_local_event_bus_unsubscribe():
    """Test unsubscribing a handler from an event"""
    bus = LocalEventBus()
    
    def handler(event):
        pass
    
    bus.subscribe(TestEvent, handler)
    bus.unsubscribe(TestEvent, handler)
    
    assert handler not in bus._handlers[TestEvent]


@pytest.mark.unit
def test_local_event_bus_publish():
    """Test publishing an event to handlers"""
    bus = LocalEventBus()
    
    results = []
    
    def handler(event):
        results.append(event.data)
    
    bus.subscribe(TestEvent, handler)
    event = TestEvent(data="test_data")
    bus.publish(event)
    
    assert len(results) == 1
    assert results[0] == "test_data"


@pytest.mark.unit
def test_local_event_bus_publish_multiple_handlers():
    """Test publishing to multiple handlers"""
    bus = LocalEventBus()
    
    results = []
    
    def handler1(event):
        results.append("handler1")
    
    def handler2(event):
        results.append("handler2")
    
    bus.subscribe(TestEvent, handler1)
    bus.subscribe(TestEvent, handler2)
    
    event = TestEvent(data="test_data")
    bus.publish(event)
    
    assert len(results) == 2
    assert "handler1" in results
    assert "handler2" in results


@pytest.mark.unit
def test_local_event_bus_publish_no_handlers():
    """Test publishing event with no registered handlers"""
    bus = LocalEventBus()
    
    event = TestEvent(data="test_data")
    # Should not raise an error
    bus.publish(event)


@pytest.mark.unit
def test_local_event_bus_publish_handler_exception():
    """Test that handler exceptions are caught and logged"""
    bus = LocalEventBus()
    
    def failing_handler(event):
        raise ValueError("Test error")
    
    def working_handler(event):
        pass
    
    bus.subscribe(TestEvent, failing_handler)
    bus.subscribe(TestEvent, working_handler)
    
    event = TestEvent(data="test_data")
    # Should not raise an error, exception should be caught
    bus.publish(event)


@pytest.mark.unit
def test_local_event_bus_multiple_event_types():
    """Test handling different event types"""
    bus = LocalEventBus()
    
    @dataclass(frozen=True, kw_only=True)
    class Event1(DomainEvent):
        value: str = "event1"
    
    @dataclass(frozen=True, kw_only=True)
    class Event2(DomainEvent):
        value: str = "event2"
    
    results = []
    
    def handler1(event):
        results.append("event1")
    
    def handler2(event):
        results.append("event2")
    
    bus.subscribe(Event1, handler1)
    bus.subscribe(Event2, handler2)
    
    bus.publish(Event1())
    bus.publish(Event2())
    
    assert "event1" in results
    assert "event2" in results
