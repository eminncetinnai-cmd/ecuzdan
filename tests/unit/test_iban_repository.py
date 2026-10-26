"""Unit tests for IbanRepository."""

from unittest.mock import Mock, patch
import pytest

from repositories.iban_repository import IbanRepository
from repositories.base import TenantScopedRepository


@pytest.mark.unit
def test_iban_repository_inheritance():
    assert issubclass(IbanRepository, TenantScopedRepository)


@pytest.mark.unit
def test_iban_repository_init():
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    repo = IbanRepository(database=mock_db)
    assert repo.session == mock_session


@pytest.mark.unit
def test_iban_repository_list_ibans():
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = []

    repo = IbanRepository(database=mock_db)
    result = repo.list_ibans(tenant_id="default", category="kendi_hesabim", search="Garanti")
    assert result == []
    assert mock_session.query.called


@pytest.mark.unit
def test_iban_repository_get_iban():
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None

    repo = IbanRepository(database=mock_db)
    result = repo.get_iban(iban_id=1, tenant_id="default")
    assert result is None


@pytest.mark.unit
def test_iban_repository_create_iban():
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None

    repo = IbanRepository(database=mock_db)
    item = repo.create_iban(
        tenant_id="default",
        user_id=1,
        title="Maaş Hesabı",
        iban="TR330006200511123456789012",
        bank_name="Garanti BBVA",
        category="kendi_hesabim",
    )
    assert item.title == "Maaş Hesabı"
    assert item.iban == "TR330006200511123456789012"
    assert mock_session.add.called
    assert mock_session.commit.called


@pytest.mark.unit
def test_iban_repository_create_iban_duplicate():
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    existing_record = Mock(title="Maaş Hesabı", iban="TR330006200511123456789012")
    mock_query.first.return_value = existing_record

    repo = IbanRepository(database=mock_db)
    item = repo.create_iban(
        tenant_id="default",
        user_id=1,
        title="Maaş Hesabı",
        iban="TR330006200511123456789012",
        bank_name="Garanti BBVA",
        category="kendi_hesabim",
    )
    assert item == existing_record
    assert not mock_session.add.called


@pytest.mark.unit
def test_iban_repository_delete_iban():
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query

    mock_record = Mock()
    mock_query.first.return_value = mock_record

    repo = IbanRepository(database=mock_db)
    success = repo.delete_iban(iban_id=1, tenant_id="default")
    assert success is True
    assert mock_session.delete.called
    assert mock_session.commit.called


@pytest.mark.unit
def test_iban_repository_toggle_favorite():
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query

    mock_record = Mock()
    mock_record.is_favorite = False
    mock_query.first.return_value = mock_record

    repo = IbanRepository(database=mock_db)
    updated = repo.toggle_favorite(iban_id=1, tenant_id="default")
    assert updated is not None
    assert mock_record.is_favorite is True
    assert mock_session.commit.called
