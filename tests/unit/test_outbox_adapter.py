"""
Unit Tests - Outbox Adapter
SQLAlchemy adapter for OutboxPort tests
"""

from unittest.mock import Mock, patch

import pytest

from application.ports.outbox_port import OutboxPort
from domain.common.events import DomainEvent
from infrastructure.database.outbox_adapter import SqlAlchemyOutboxAdapter


@pytest.mark.unit
def test_outbox_adapter_module_imports():
    """Test outbox_adapter module can be imported"""
    from infrastructure.database.outbox_adapter import SqlAlchemyOutboxAdapter
    assert SqlAlchemyOutboxAdapter is not None


@pytest.mark.unit
def test_outbox_adapter_module_structure():
    """Test outbox_adapter module structure"""
    import infrastructure.database.outbox_adapter as adapter_module

    # Check for expected class
    assert hasattr(adapter_module, 'SqlAlchemyOutboxAdapter')


@pytest.mark.unit
def test_sql_alchemy_outbox_adapter_inherits_from_outbox_port():
    """Test SqlAlchemyOutboxAdapter inherits from OutboxPort"""
    assert issubclass(SqlAlchemyOutboxAdapter, OutboxPort)


@pytest.mark.unit
def test_sql_alchemy_outbox_adapter_init():
    """Test SqlAlchemyOutboxAdapter initialization"""
    adapter = SqlAlchemyOutboxAdapter()
    assert adapter is not None


@pytest.mark.unit
def test_sql_alchemy_outbox_adapter_has_save_method():
    """Test SqlAlchemyOutboxAdapter has save method"""
    adapter = SqlAlchemyOutboxAdapter()
    assert hasattr(adapter, 'save')
    assert callable(adapter.save)


@pytest.mark.unit
def test_save_event():
    """Test save method writes event to outbox"""
    mock_event = Mock(spec=DomainEvent)
    mock_event.__class__.__name__ = 'TestEvent'
    mock_event.data = 'test_data'

    mock_outbox_model = Mock()
    mock_session = Mock()
    mock_db = Mock()
    mock_db.session = mock_session

    with patch('infrastructure.database.outbox_adapter.db', mock_db):
        with patch('infrastructure.database.outbox_adapter.OutboxMessageModel') as mock_model_class:
            with patch('infrastructure.database.outbox_adapter.asdict') as mock_asdict:
                mock_asdict.return_value = {'data': 'test_data'}
                mock_model_class.return_value = mock_outbox_model

                adapter = SqlAlchemyOutboxAdapter()
                adapter.save(mock_event)

                mock_session.add.assert_called_once_with(mock_outbox_model)


@pytest.mark.unit
def test_save_event_generates_uuid():
    """Test save method generates UUID for outbox message"""
    mock_event = Mock(spec=DomainEvent)
    mock_event.__class__.__name__ = 'TestEvent'
    mock_event.data = 'test_data'

    mock_outbox_model = Mock()
    mock_session = Mock()
    mock_db = Mock()
    mock_db.session = mock_session

    with patch('infrastructure.database.outbox_adapter.db', mock_db):
        with patch('infrastructure.database.outbox_adapter.OutboxMessageModel') as mock_model_class:
            with patch('infrastructure.database.outbox_adapter.asdict') as mock_asdict:
                with patch('infrastructure.database.outbox_adapter.uuid') as mock_uuid:
                    mock_uuid.uuid4.return_value = 'test-uuid-123'
                    mock_asdict.return_value = {'data': 'test_data'}
                    mock_model_class.return_value = mock_outbox_model

                    adapter = SqlAlchemyOutboxAdapter()
                    adapter.save(mock_event)

                    mock_model_class.assert_called_once()
                    call_kwargs = mock_model_class.call_args[1]
                    assert call_kwargs['id'] == 'test-uuid-123'


@pytest.mark.unit
def test_save_event_sets_event_type():
    """Test save method sets event_type from event class name"""
    mock_event = Mock(spec=DomainEvent)
    mock_event.__class__.__name__ = 'TestEvent'
    mock_event.data = 'test_data'

    mock_outbox_model = Mock()
    mock_session = Mock()
    mock_db = Mock()
    mock_db.session = mock_session

    with patch('infrastructure.database.outbox_adapter.db', mock_db):
        with patch('infrastructure.database.outbox_adapter.OutboxMessageModel') as mock_model_class:
            with patch('infrastructure.database.outbox_adapter.asdict') as mock_asdict:
                mock_asdict.return_value = {'data': 'test_data'}
                mock_model_class.return_value = mock_outbox_model

                adapter = SqlAlchemyOutboxAdapter()
                adapter.save(mock_event)

                call_kwargs = mock_model_class.call_args[1]
                assert call_kwargs['event_type'] == 'TestEvent'


@pytest.mark.unit
def test_save_event_serializes_payload():
    """Test save method serializes event with json.dumps"""
    mock_event = Mock(spec=DomainEvent)
    mock_event.__class__.__name__ = 'TestEvent'
    mock_event.data = 'test_data'

    mock_outbox_model = Mock()
    mock_session = Mock()
    mock_db = Mock()
    mock_db.session = mock_session

    with patch('infrastructure.database.outbox_adapter.db', mock_db):
        with patch('infrastructure.database.outbox_adapter.OutboxMessageModel') as mock_model_class:
            with patch('infrastructure.database.outbox_adapter.asdict') as mock_asdict:
                with patch('infrastructure.database.outbox_adapter.json') as mock_json:
                    mock_json.dumps.return_value = '{"data": "test_data"}'
                    mock_asdict.return_value = {'data': 'test_data'}
                    mock_model_class.return_value = mock_outbox_model

                    adapter = SqlAlchemyOutboxAdapter()
                    adapter.save(mock_event)

                    mock_json.dumps.assert_called_once()
                    call_kwargs = mock_model_class.call_args[1]
                    assert 'payload' in call_kwargs


@pytest.mark.unit
def test_save_event_no_commit():
    """Test save method does not commit to database"""
    mock_event = Mock(spec=DomainEvent)
    mock_event.__class__.__name__ = 'TestEvent'
    mock_event.data = 'test_data'

    mock_outbox_model = Mock()
    mock_session = Mock()
    mock_db = Mock()
    mock_db.session = mock_session

    with patch('infrastructure.database.outbox_adapter.db', mock_db):
        with patch('infrastructure.database.outbox_adapter.OutboxMessageModel') as mock_model_class:
            with patch('infrastructure.database.outbox_adapter.asdict') as mock_asdict:
                mock_asdict.return_value = {'data': 'test_data'}
                mock_model_class.return_value = mock_outbox_model

                adapter = SqlAlchemyOutboxAdapter()
                adapter.save(mock_event)

                assert not mock_session.commit.called


@pytest.mark.unit
def test_save_event_uses_asdict():
    """Test save method uses asdict to convert event"""
    mock_event = Mock(spec=DomainEvent)
    mock_event.__class__.__name__ = 'TestEvent'
    mock_event.data = 'test_data'

    mock_outbox_model = Mock()
    mock_session = Mock()
    mock_db = Mock()
    mock_db.session = mock_session

    with patch('infrastructure.database.outbox_adapter.db', mock_db):
        with patch('infrastructure.database.outbox_adapter.OutboxMessageModel') as mock_model_class:
            with patch('infrastructure.database.outbox_adapter.asdict') as mock_asdict:
                mock_asdict.return_value = {'data': 'test_data'}
                mock_model_class.return_value = mock_outbox_model

                adapter = SqlAlchemyOutboxAdapter()
                adapter.save(mock_event)

                mock_asdict.assert_called_once_with(mock_event)
