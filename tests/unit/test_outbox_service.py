"""
Unit Tests - Outbox Service
Outbox database service tests
"""

from unittest.mock import Mock, patch

import pytest

from domain.common.events import DomainEvent
from infrastructure.database.outbox_service import save_to_outbox


@pytest.mark.unit
def test_outbox_service_module_imports():
    """Test outbox_service module can be imported"""
    from infrastructure.database.outbox_service import save_to_outbox
    assert save_to_outbox is not None


@pytest.mark.unit
def test_outbox_service_module_structure():
    """Test outbox_service module structure"""
    import infrastructure.database.outbox_service as outbox_module

    # Check for expected function
    assert hasattr(outbox_module, 'save_to_outbox')


@pytest.mark.unit
def test_save_to_outbox():
    """Test save_to_outbox function"""
    mock_event = Mock(spec=DomainEvent)
    mock_event.__class__.__name__ = 'TestEvent'
    mock_event.data = 'test_data'

    mock_outbox_model = Mock()
    mock_session = Mock()
    mock_db = Mock()
    mock_db.session = mock_session

    with patch('infrastructure.database.outbox_service.db', mock_db):
        with patch('infrastructure.database.outbox_service.OutboxMessageModel') as mock_model_class:
            with patch('infrastructure.database.outbox_service.asdict') as mock_asdict:
                mock_asdict.return_value = {'data': 'test_data'}
                mock_model_class.return_value = mock_outbox_model

                save_to_outbox(mock_event)

                mock_session.add.assert_called_once_with(mock_outbox_model)
                mock_model_class.assert_called_once()


@pytest.mark.unit
def test_save_to_outbox_generates_uuid():
    """Test save_to_outbox generates UUID for message"""
    mock_event = Mock(spec=DomainEvent)
    mock_event.__class__.__name__ = 'TestEvent'
    mock_event.data = 'test_data'

    mock_outbox_model = Mock()
    mock_session = Mock()
    mock_db = Mock()
    mock_db.session = mock_session

    with patch('infrastructure.database.outbox_service.db', mock_db):
        with patch('infrastructure.database.outbox_service.OutboxMessageModel') as mock_model_class:
            with patch('infrastructure.database.outbox_service.uuid') as mock_uuid:
                with patch('infrastructure.database.outbox_service.asdict') as mock_asdict:
                    mock_uuid.uuid4.return_value = 'test-uuid-123'
                    mock_asdict.return_value = {'data': 'test_data'}
                    mock_model_class.return_value = mock_outbox_model

                    save_to_outbox(mock_event)

                    mock_model_class.assert_called_once()
                    call_kwargs = mock_model_class.call_args[1]
                    assert call_kwargs['id'] == 'test-uuid-123'


@pytest.mark.unit
def test_save_to_outbox_sets_event_type():
    """Test save_to_outbox sets event type from class name"""
    mock_event = Mock(spec=DomainEvent)
    mock_event.__class__.__name__ = 'TestEvent'
    mock_event.data = 'test_data'

    mock_outbox_model = Mock()
    mock_session = Mock()
    mock_db = Mock()
    mock_db.session = mock_session

    with patch('infrastructure.database.outbox_service.db', mock_db):
        with patch('infrastructure.database.outbox_service.OutboxMessageModel') as mock_model_class:
            with patch('infrastructure.database.outbox_service.asdict') as mock_asdict:
                mock_asdict.return_value = {'data': 'test_data'}
                mock_model_class.return_value = mock_outbox_model

                save_to_outbox(mock_event)

                call_kwargs = mock_model_class.call_args[1]
                assert call_kwargs['event_type'] == 'TestEvent'


@pytest.mark.unit
def test_save_to_outbox_serializes_payload():
    """Test save_to_outbox serializes event to JSON payload"""
    mock_event = Mock(spec=DomainEvent)
    mock_event.__class__.__name__ = 'TestEvent'
    mock_event.data = 'test_data'

    mock_outbox_model = Mock()
    mock_session = Mock()
    mock_db = Mock()
    mock_db.session = mock_session

    with patch('infrastructure.database.outbox_service.db', mock_db):
        with patch('infrastructure.database.outbox_service.OutboxMessageModel') as mock_model_class:
            with patch('infrastructure.database.outbox_service.json') as mock_json:
                with patch('infrastructure.database.outbox_service.asdict') as mock_asdict:
                    mock_json.dumps.return_value = '{"data": "test_data"}'
                    mock_asdict.return_value = {'data': 'test_data'}
                    mock_model_class.return_value = mock_outbox_model

                    save_to_outbox(mock_event)

                    mock_json.dumps.assert_called_once()
                    call_kwargs = mock_model_class.call_args[1]
                    assert 'payload' in call_kwargs


@pytest.mark.unit
def test_save_to_outbox_does_not_commit():
    """Test save_to_outbox does not commit - caller responsible"""
    mock_event = Mock(spec=DomainEvent)
    mock_event.__class__.__name__ = 'TestEvent'
    mock_event.data = 'test_data'

    mock_outbox_model = Mock()
    mock_session = Mock()
    mock_db = Mock()
    mock_db.session = mock_session

    with patch('infrastructure.database.outbox_service.db', mock_db):
        with patch('infrastructure.database.outbox_service.OutboxMessageModel') as mock_model_class:
            with patch('infrastructure.database.outbox_service.asdict') as mock_asdict:
                mock_asdict.return_value = {'data': 'test_data'}
                mock_model_class.return_value = mock_outbox_model

                save_to_outbox(mock_event)

                assert not mock_session.commit.called


@pytest.mark.unit
def test_save_to_outbox_uses_asdict():
    """Test save_to_outbox uses asdict to convert event to dict"""
    mock_event = Mock(spec=DomainEvent)
    mock_event.__class__.__name__ = 'TestEvent'
    mock_event.data = 'test_data'

    mock_outbox_model = Mock()
    mock_session = Mock()
    mock_db = Mock()
    mock_db.session = mock_session

    with patch('infrastructure.database.outbox_service.db', mock_db):
        with patch('infrastructure.database.outbox_service.OutboxMessageModel') as mock_model_class:
            with patch('infrastructure.database.outbox_service.asdict') as mock_asdict:
                mock_asdict.return_value = {'data': 'test_data'}
                mock_model_class.return_value = mock_outbox_model

                save_to_outbox(mock_event)

                mock_asdict.assert_called_once_with(mock_event)


@pytest.mark.unit
def test_count_pending_outbox_messages():
    """Test count_pending_outbox_messages queries processed_on=None."""
    from infrastructure.database.outbox_service import count_pending_outbox_messages

    with patch('infrastructure.database.outbox_service.OutboxMessageModel') as mock_model:
        mock_filter = mock_model.query.filter_by.return_value
        mock_filter.count.return_value = 42

        count = count_pending_outbox_messages()

        assert count == 42
        mock_model.query.filter_by.assert_called_once_with(processed_on=None)

