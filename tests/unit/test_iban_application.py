"""Unit tests for IbanApplicationService."""

from unittest.mock import Mock
import pytest

from application.analysis.iban_application import IbanApplicationService


@pytest.mark.unit
def test_iban_application_service_create():
    mock_repo = Mock()
    mock_domain = Mock()
    mock_domain.clean_iban.return_value = "TR330006200511123456789012"
    mock_domain.validate_iban.return_value = (True, "")
    mock_domain.detect_bank_name.return_value = "Garanti BBVA"

    app_svc = IbanApplicationService(
        iban_repository=mock_repo,
        iban_domain_service=mock_domain,
    )

    app_svc.create_iban(
        tenant_id="default",
        user_id=1,
        title="Garanti Hesabım",
        iban="TR33 0006 2005 1112 3456 7890 12",
    )

    assert mock_repo.create_iban.called
    args, kwargs = mock_repo.create_iban.call_args
    assert kwargs["bank_name"] == "Garanti BBVA"
    assert kwargs["iban"] == "TR330006200511123456789012"


@pytest.mark.unit
def test_iban_application_service_create_invalid():
    mock_repo = Mock()
    mock_domain = Mock()
    mock_domain.clean_iban.return_value = "INVALID"
    mock_domain.validate_iban.return_value = (False, "Geçersiz IBAN formatı.")

    app_svc = IbanApplicationService(
        iban_repository=mock_repo,
        iban_domain_service=mock_domain,
    )

    with pytest.raises(ValueError, match="Geçersiz IBAN"):
        app_svc.create_iban(
            tenant_id="default",
            user_id=1,
            title="Hatalı",
            iban="INVALID",
        )
    assert not mock_repo.create_iban.called


@pytest.mark.unit
def test_iban_application_service_list_and_delete():
    mock_repo = Mock()
    mock_repo.list_ibans.return_value = ["item1", "item2"]
    mock_repo.delete_iban.return_value = True

    app_svc = IbanApplicationService(iban_repository=mock_repo)

    result = app_svc.list_ibans("default", category="kendi_hesabim")
    assert result == ["item1", "item2"]

    deleted = app_svc.delete_iban(1, "default")
    assert deleted is True


@pytest.mark.unit
def test_iban_application_service_get_and_toggle_favorite():
    mock_repo = Mock()
    mock_repo.get_iban.return_value = "mock_iban"
    mock_repo.toggle_favorite.return_value = "mock_toggled"

    app_svc = IbanApplicationService(iban_repository=mock_repo)

    assert app_svc.get_iban(1, "default") == "mock_iban"
    assert app_svc.toggle_favorite(1, "default") == "mock_toggled"
    mock_repo.toggle_favorite.assert_called_once_with(1, "default")


@pytest.mark.unit
def test_iban_application_service_update():
    mock_repo = Mock()
    mock_domain = Mock()
    mock_domain.clean_iban.return_value = "TR330006200511123456789012"
    mock_domain.validate_iban.return_value = (True, "")
    mock_domain.detect_bank_name.return_value = "Garanti BBVA"
    mock_repo.update_iban.return_value = "mock_updated"

    app_svc = IbanApplicationService(
        iban_repository=mock_repo,
        iban_domain_service=mock_domain,
    )

    res = app_svc.update_iban(
        iban_id=1,
        tenant_id="default",
        title="Yeni Başlık",
        iban="TR33 0006 2005 1112 3456 7890 12",
        is_favorite=True,
        easy_address_type="Telefon",
        easy_address="0532 111 22 33",
    )
    assert res == "mock_updated"
    assert mock_repo.update_iban.called
    args, kwargs = mock_repo.update_iban.call_args
    assert kwargs["title"] == "Yeni Başlık"
    assert kwargs["is_favorite"] is True
    assert kwargs["easy_address"] == "0532 111 22 33"
