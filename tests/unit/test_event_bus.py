"""
Unit Tests - Event Bus
Local and async event bus implementations
"""

import pytest
from unittest.mock import Mock, patch
from infrastructure.events.local_event_bus import LocalEventBus
from infrastructure.events.async_local_event_bus import AsyncLocalEventBus
from domain.common.events import DomainEvent
from domain.common.event_bus import EventBus


def create_test_event():
    """Factory function to create test event."""
    class TestEvent(DomainEvent):
        """Test event for testing."""
        @property
        def event_name(self):
            return "TestEvent"
    return TestEvent


@pytest.mark.unit
def test_local_event_bus_init():
    """Test LocalEventBus initialization"""
    bus = LocalEventBus()
    assert bus._handlers is not None


@pytest.mark.unit
def test_local_event_bus_subscribe():
    """Test subscribing a handler to an event"""
    bus = LocalEventBus()
    TestEvent = create_test_event()
    
    called = []
    def handler(event):
        called.append(event)
    
    bus.subscribe(TestEvent, handler)
    
    assert handler in bus._handlers[TestEvent]


@pytest.mark.unit
def test_local_event_bus_subscribe_duplicate():
    """Test subscribing same handler twice doesn't duplicate"""
    bus = LocalEventBus()
    TestEvent = create_test_event()
    
    called = []
    def handler(event):
        called.append(event)
    
    bus.subscribe(TestEvent, handler)
    bus.subscribe(TestEvent, handler)
    
    assert bus._handlers[TestEvent].count(handler) == 1


@pytest.mark.unit
def test_local_event_bus_unsubscribe():
    """Test unsubscribing a handler"""
    bus = LocalEventBus()
    TestEvent = create_test_event()
    
    called = []
    def handler(event):
        called.append(event)
    
    bus.subscribe(TestEvent, handler)
    bus.unsubscribe(TestEvent, handler)
    
    assert handler not in bus._handlers[TestEvent]


@pytest.mark.unit
def test_local_event_bus_unsubscribe_nonexistent():
    """Test unsubscribing non-existent handler doesn't raise error"""
    bus = LocalEventBus()
    TestEvent = create_test_event()
    
    called = []
    def handler(event):
        called.append(event)
    
    # Should not raise error
    bus.unsubscribe(TestEvent, handler)


@pytest.mark.unit
def test_local_event_bus_publish():
    """Test publishing an event"""
    bus = LocalEventBus()
    TestEvent = create_test_event()
    
    called = []
    def handler(event):
        called.append(event)
    
    event = TestEvent()
    bus.subscribe(TestEvent, handler)
    bus.publish(event)
    
    assert len(called) == 1
    assert called[0] == event


@pytest.mark.unit
def test_local_event_bus_publish_multiple_handlers():
    """Test publishing to multiple handlers"""
    bus = LocalEventBus()
    TestEvent = create_test_event()
    
    called1 = []
    def handler1(event):
        called1.append(event)
    
    called2 = []
    def handler2(event):
        called2.append(event)
    
    event = TestEvent()
    bus.subscribe(TestEvent, handler1)
    bus.subscribe(TestEvent, handler2)
    bus.publish(event)
    
    assert len(called1) == 1
    assert len(called2) == 1


@pytest.mark.unit
def test_local_event_bus_publish_no_handlers():
    """Test publishing event with no handlers"""
    bus = LocalEventBus()
    TestEvent = create_test_event()
    event = TestEvent()
    
    # Should not raise error
    bus.publish(event)


@pytest.mark.unit
def test_local_event_bus_publish_handler_error():
    """Test publishing when handler raises error"""
    bus = LocalEventBus()
    TestEvent = create_test_event()
    
    def handler(event):
        raise Exception("Handler error")
    
    event = TestEvent()
    bus.subscribe(TestEvent, handler)
    
    # Should not raise error
    bus.publish(event)


@pytest.mark.unit
def test_async_local_event_bus_init():
    """Test AsyncLocalEventBus initialization"""
    bus = AsyncLocalEventBus()
    assert bus._handlers is not None
    assert bus._executor is not None


@pytest.mark.unit
def test_async_local_event_bus_init_custom_workers():
    """Test AsyncLocalEventBus initialization with custom workers"""
    bus = AsyncLocalEventBus(max_workers=8)
    assert bus._handlers is not None
    assert bus._executor is not None


@pytest.mark.unit
def test_async_local_event_bus_subscribe():
    """Test subscribing a handler to an event"""
    bus = AsyncLocalEventBus()
    TestEvent = create_test_event()
    
    called = []
    def handler(event):
        called.append(event)
    
    bus.subscribe(TestEvent, handler)
    
    assert handler in bus._handlers[TestEvent]


@pytest.mark.unit
def test_async_local_event_bus_subscribe_duplicate():
    """Test subscribing same handler twice doesn't duplicate"""
    bus = AsyncLocalEventBus()
    TestEvent = create_test_event()
    
    called = []
    def handler(event):
        called.append(event)
    
    bus.subscribe(TestEvent, handler)
    bus.subscribe(TestEvent, handler)
    
    assert bus._handlers[TestEvent].count(handler) == 1


@pytest.mark.unit
def test_async_local_event_bus_unsubscribe():
    """Test unsubscribing a handler"""
    bus = AsyncLocalEventBus()
    TestEvent = create_test_event()
    
    called = []
    def handler(event):
        called.append(event)
    
    bus.subscribe(TestEvent, handler)
    bus.unsubscribe(TestEvent, handler)
    
    assert handler not in bus._handlers[TestEvent]


@pytest.mark.unit
def test_async_local_event_bus_unsubscribe_nonexistent():
    """Test unsubscribing non-existent handler doesn't raise error"""
    bus = AsyncLocalEventBus()
    TestEvent = create_test_event()
    
    called = []
    def handler(event):
        called.append(event)
    
    # Should not raise error
    bus.unsubscribe(TestEvent, handler)


@pytest.mark.unit
def test_async_local_event_bus_publish():
    """Test publishing an event"""
    bus = AsyncLocalEventBus()
    TestEvent = create_test_event()
    
    called = []
    def handler(event):
        called.append(event)
    
    event = TestEvent()
    bus.subscribe(TestEvent, handler)
    bus.publish(event)
    
    # Wait for async execution
    import time
    time.sleep(0.1)  # Give thread pool time to execute
    
    assert len(called) == 1
    assert called[0] == event


@pytest.mark.unit
def test_async_local_event_bus_publish_multiple_handlers():
    """Test publishing event to multiple handlers asynchronously"""
    bus = AsyncLocalEventBus()
    TestEvent = create_test_event()
    
    called1 = []
    def handler1(event):
        called1.append(event)
    
    called2 = []
    def handler2(event):
        called2.append(event)
    
    event = TestEvent()
    bus.subscribe(TestEvent, handler1)
    bus.subscribe(TestEvent, handler2)
    bus.publish(event)
    
    # Wait for async execution
    import time
    time.sleep(0.1)  # Give thread pool time to execute
    
    assert len(called1) == 1
    assert len(called2) == 1


@pytest.mark.unit
def test_async_local_event_bus_publish_no_handlers():
    """Test publishing event with no handlers"""
    bus = AsyncLocalEventBus()
    TestEvent = create_test_event()
    event = TestEvent()
    
    # Should not raise error
    bus.publish(event)


@pytest.mark.unit
def test_async_local_event_bus_publish_handler_error():
    """Test publishing when handler raises error"""
    bus = AsyncLocalEventBus()
    TestEvent = create_test_event()
    
    def handler(event):
        raise Exception("Handler error")
    
    event = TestEvent()
    bus.subscribe(TestEvent, handler)
    bus.publish(event)
    
    # Wait for async execution
    import time
    time.sleep(0.1)  # Give thread pool time to execute


@pytest.mark.unit
def test_async_local_event_bus_shutdown():
    """Test shutting down the event bus"""
    bus = AsyncLocalEventBus()
    
    # Should not raise error
    bus.shutdown(wait=True)


@pytest.mark.unit
def test_async_local_event_bus_shutdown_no_wait():
    """Test shutting down the event bus without waiting"""
    bus = AsyncLocalEventBus()
    
    # Should not raise error
    bus.shutdown(wait=False)


@pytest.mark.unit
@pytest.mark.skip(reason="Requires opentelemetry module")
def test_async_local_event_bus_publish_with_tracing():
    """Test publishing with OpenTelemetry tracing"""
    bus = AsyncLocalEventBus()
    TestEvent = create_test_event()
    
    called = []
    def handler(event):
        called.append(event)
    
    event = TestEvent()
    bus.subscribe(TestEvent, handler)
    
    # Mock tracing to raise exception
    with patch('opentelemetry.trace.get_tracer', side_effect=Exception("No tracing")):
        bus.publish(event)
        
        # Wait for async execution
        import time
        time.sleep(0.1)  # Give thread pool time to execute
    
    # Handler should still be called even if tracing fails
    assert len(called) == 1
    assert called[0] == event


@pytest.mark.unit
@pytest.mark.skip(reason="Requires opentelemetry module")
def test_async_local_event_bus_publish_without_tracing():
    """Test publishing event when tracing is not available"""
    bus = AsyncLocalEventBus()
    TestEvent = create_test_event()
    
    called = []
    def handler(event):
        called.append(event)
    
    event = TestEvent()
    bus.subscribe(TestEvent, handler)
    
    bus.publish(event)
    
    # Wait for async execution
    import time
    time.sleep(0.1)  # Give thread pool time to execute
    
    assert len(called) == 1
    assert called[0] == event


@pytest.mark.unit
def test_local_event_bus_module_imports():
    """Test local_event_bus module can be imported"""
    from infrastructure.events.local_event_bus import LocalEventBus
    assert LocalEventBus is not None


@pytest.mark.unit
def test_local_event_bus_module_structure():
    """Test local_event_bus module structure"""
    import infrastructure.events.local_event_bus as event_bus_module
    
    # Check for expected class
    assert hasattr(event_bus_module, 'LocalEventBus')


@pytest.mark.unit
def test_local_event_bus_inheritance():
    """Test LocalEventBus inherits from EventBus"""
    from infrastructure.events.local_event_bus import LocalEventBus
    from domain.common.event_bus import EventBus
    
    assert issubclass(LocalEventBus, EventBus)


@pytest.mark.unit
def test_local_event_bus_handlers_dict():
    """Test _handlers is a defaultdict"""
    bus = LocalEventBus()
    
    from collections import defaultdict
    assert isinstance(bus._handlers, defaultdict)


@pytest.mark.unit
def test_subscribe_different_event_types():
    """Test subscribing handlers for different event types"""
    bus = LocalEventBus()
    TestEvent = create_test_event()
    
    class TestEvent2(DomainEvent):
        @property
        def event_name(self):
            return "TestEvent2"
    
    called1 = []
    def handler1(event):
        called1.append(event)
    
    called2 = []
    def handler2(event):
        called2.append(event)
    
    bus.subscribe(TestEvent, handler1)
    bus.subscribe(TestEvent2, handler2)
    
    assert handler1 in bus._handlers[TestEvent]
    assert handler2 in bus._handlers[TestEvent2]
    assert handler1 not in bus._handlers[TestEvent2]
    assert handler2 not in bus._handlers[TestEvent]


@pytest.mark.unit
def test_local_event_bus_has_required_methods():
    """Test LocalEventBus has required methods"""
    bus = LocalEventBus()
    
    assert hasattr(bus, 'subscribe')
    assert hasattr(bus, 'unsubscribe')
    assert hasattr(bus, 'publish')
    
    assert callable(bus.subscribe)
    assert callable(bus.unsubscribe)
    assert callable(bus.publish)


@pytest.mark.unit
def test_subscribe_logs_debug():
    """Test subscribe logs debug message"""
    bus = LocalEventBus()
    TestEvent = create_test_event()
    
    called = []
    def handler(event):
        called.append(event)
    
    with patch('infrastructure.events.local_event_bus.logger') as mock_logger:
        bus.subscribe(TestEvent, handler)
        mock_logger.debug.assert_called_once()


@pytest.mark.unit
def test_unsubscribe_logs_debug():
    """Test unsubscribe logs debug message"""
    bus = LocalEventBus()
    TestEvent = create_test_event()
    
    called = []
    def handler(event):
        called.append(event)
    
    bus.subscribe(TestEvent, handler)
    
    with patch('infrastructure.events.local_event_bus.logger') as mock_logger:
        bus.unsubscribe(TestEvent, handler)
        mock_logger.debug.assert_called_once()


@pytest.mark.unit
def test_publish_logs_info():
    """Test publish logs info message"""
    bus = LocalEventBus()
    TestEvent = create_test_event()
    
    called = []
    def handler(event):
        called.append(event)
    
    event = TestEvent()
    bus.subscribe(TestEvent, handler)
    
    with patch('infrastructure.events.local_event_bus.logger') as mock_logger:
        bus.publish(event)
        mock_logger.info.assert_called_once()


@pytest.mark.unit
def test_publish_logs_exception():
    """Test publish logs exception when handler fails"""
    bus = LocalEventBus()
    TestEvent = create_test_event()
    
    def handler(event):
        raise Exception("Handler error")
    
    event = TestEvent()
    bus.subscribe(TestEvent, handler)
    
    with patch('infrastructure.events.local_event_bus.logger') as mock_logger:
        bus.publish(event)
        mock_logger.exception.assert_called_once()


@pytest.mark.unit
def test_async_local_event_bus_module_imports():
    """Test async_local_event_bus module can be imported"""
    from infrastructure.events.async_local_event_bus import AsyncLocalEventBus
    assert AsyncLocalEventBus is not None


@pytest.mark.unit
def test_async_local_event_bus_module_structure():
    """Test async_local_event_bus module structure"""
    import infrastructure.events.async_local_event_bus as event_bus_module
    
    # Check for expected class
    assert hasattr(event_bus_module, 'AsyncLocalEventBus')


@pytest.mark.unit
def test_async_local_event_bus_inheritance():
    """Test AsyncLocalEventBus inherits from EventBus"""
    assert issubclass(AsyncLocalEventBus, EventBus)


@pytest.mark.unit
def test_async_local_event_bus_handlers_dict():
    """Test _handlers is a defaultdict"""
    bus = AsyncLocalEventBus()
    
    from collections import defaultdict
    assert isinstance(bus._handlers, defaultdict)


@pytest.mark.unit
def test_async_local_event_bus_subscribe_different_event_types():
    """Test subscribing handlers for different event types"""
    bus = AsyncLocalEventBus()
    TestEvent = create_test_event()
    
    class TestEvent2(DomainEvent):
        @property
        def event_name(self):
            return "TestEvent2"
    
    called1 = []
    def handler1(event):
        called1.append(event)
    
    called2 = []
    def handler2(event):
        called2.append(event)
    
    bus.subscribe(TestEvent, handler1)
    bus.subscribe(TestEvent2, handler2)
    
    assert handler1 in bus._handlers[TestEvent]
    assert handler2 in bus._handlers[TestEvent2]
    assert handler1 not in bus._handlers[TestEvent2]
    assert handler2 not in bus._handlers[TestEvent]


@pytest.mark.unit
def test_async_local_event_bus_has_required_methods():
    """Test AsyncLocalEventBus has required methods"""
    bus = AsyncLocalEventBus()
    
    assert hasattr(bus, 'subscribe')
    assert hasattr(bus, 'unsubscribe')
    assert hasattr(bus, 'publish')
    assert hasattr(bus, 'shutdown')
    assert hasattr(bus, '_run_handler')
    
    assert callable(bus.subscribe)
    assert callable(bus.unsubscribe)
    assert callable(bus.publish)
    assert callable(bus.shutdown)
    assert callable(bus._run_handler)


@pytest.mark.unit
def test_async_local_event_bus_run_handler_success():
    """Test _run_handler executes handler successfully"""
    bus = AsyncLocalEventBus()
    TestEvent = create_test_event()
    
    called = []
    def handler(event):
        called.append(event)
    
    event = TestEvent()
    bus._run_handler(handler, event)
    
    assert len(called) == 1
    assert called[0] == event


@pytest.mark.unit
def test_async_local_event_bus_run_handler_exception():
    """Test _run_handler catches handler exceptions"""
    bus = AsyncLocalEventBus()
    TestEvent = create_test_event()
    
    def handler(event):
        raise Exception("Handler error")
    
    event = TestEvent()
    
    # Should not raise error
    bus._run_handler(handler, event)
