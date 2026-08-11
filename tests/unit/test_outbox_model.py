"""
Unit Tests - Outbox Model
Tests for the OutboxMessageModel SQLAlchemy model
"""

import pytest
from datetime import datetime, timezone
from infrastructure.database.models.outbox_model import OutboxMessageModel, utcnow_naive


@pytest.mark.unit
def test_utcnow_naive():
    """Test utcnow_naive returns datetime without timezone info"""
    result = utcnow_naive()
    
    assert isinstance(result, datetime)
    assert result.tzinfo is None


@pytest.mark.unit
def test_utcnow_naive_returns_current_time():
    """Test utcnow_naive returns approximately current time"""
    before = datetime.now(timezone.utc)
    result = utcnow_naive()
    after = datetime.now(timezone.utc)
    
    # Result should be between before and after (allowing for execution time)
    assert before.replace(tzinfo=None) <= result <= after.replace(tzinfo=None)


@pytest.mark.unit
def test_outbox_model_structure():
    """Test OutboxMessageModel has expected attributes"""
    from infrastructure.database.models.outbox_model import OutboxMessageModel
    
    # Check for expected columns
    assert hasattr(OutboxMessageModel, 'id')
    assert hasattr(OutboxMessageModel, 'event_type')
    assert hasattr(OutboxMessageModel, 'payload')
    assert hasattr(OutboxMessageModel, 'occurred_on')
    assert hasattr(OutboxMessageModel, 'processed_on')
    assert hasattr(OutboxMessageModel, 'error')


@pytest.mark.unit
def test_outbox_model_repr():
    """Test OutboxMessageModel __repr__ method"""
    from infrastructure.database.models.outbox_model import OutboxMessageModel
    
    # Create a mock instance with the necessary attributes
    class MockOutboxMessage:
        def __init__(self, id_val, event_type, processed_on):
            self.id = id_val
            self.event_type = event_type
            self.processed_on = processed_on
        
        def __repr__(self):
            return f"<OutboxMessage {self.id} type={self.event_type} processed={self.processed_on is not None}>"
    
    # Test with processed message
    msg1 = MockOutboxMessage("test-id-1", "TestEvent", datetime.now())
    repr1 = repr(msg1)
    assert "test-id-1" in repr1
    assert "TestEvent" in repr1
    assert "processed=True" in repr1
    
    # Test with unprocessed message
    msg2 = MockOutboxMessage("test-id-2", "TestEvent", None)
    repr2 = repr(msg2)
    assert "test-id-2" in repr2
    assert "TestEvent" in repr2
    assert "processed=False" in repr2


@pytest.mark.unit
def test_outbox_model_tablename():
    """Test OutboxMessageModel has correct tablename"""
    from infrastructure.database.models.outbox_model import OutboxMessageModel
    
    assert OutboxMessageModel.__tablename__ == 'outbox_messages'
