"""Unit tests for SpecialCodeService (domain/users/services/special_code_service.py).

Tests code fingerprinting, config loading error fallbacks, redemption limits,
expiration dates, tenant scoping, and role upgrade validation.
"""

import pytest
from unittest.mock import MagicMock, patch
from domain.users.services.special_code_service import (
    SpecialCodeService,
    get_special_code_service,
)


@pytest.fixture
def service():
    srv = SpecialCodeService()
    # Mock config with controlled test codes
    srv._codes_config = {
        "VIP_2026": {
            "role": "vip",
            "description": "VIP Access",
            "max_uses": 5,
            "expires_at": "2099-12-31",
            "metadata": {"source": "campaign"},
        },
        "EXPIRED_CODE": {
            "role": "pro",
            "description": "Expired Promo",
            "expires_at": "2020-01-01",
        },
        "BAD_DATE_CODE": {
            "role": "standard",
            "description": "Bad Date Promo",
            "expires_at": "invalid-date",
        },
        "TENANT_ONLY": {
            "role": "enterprise",
            "description": "Enterprise Tenant",
            "tenant_specific": True,
        },
        "LIMITED_CODE": {
            "role": "tester",
            "description": "One time use",
            "max_uses": 1,
        },
    }
    return srv


def test_code_fingerprint():
    fp = SpecialCodeService.code_fingerprint("MY_SECRET_CODE")
    assert isinstance(fp, str)
    assert len(fp) == 16
    # None or empty code fallback
    fp_empty = SpecialCodeService.code_fingerprint("")
    assert len(fp_empty) == 16


def test_get_code_info_for_stored(service):
    # Direct raw code
    info1 = service.get_code_info_for_stored("VIP_2026")
    assert info1 is not None
    assert info1["role"] == "vip"

    # Fingerprint matching
    fp = SpecialCodeService.code_fingerprint("VIP_2026")
    info2 = service.get_code_info_for_stored(fp)
    assert info2 is not None
    assert info2["role"] == "vip"

    # Unknown code
    assert service.get_code_info_for_stored("UNKNOWN") is None


def test_validate_code_invalid(service):
    res = service.validate_code("NON_EXISTENT", user_id=1)
    assert res["valid"] is False
    assert "Geçersiz" in res["error"]


def test_validate_code_expired(service):
    res = service.validate_code("EXPIRED_CODE", user_id=1)
    assert res["valid"] is False
    assert "süresi dolmuş" in res["error"]


def test_validate_code_tenant_restriction(service):
    # Missing tenant_id
    res_no_tenant = service.validate_code("TENANT_ONLY", user_id=1, tenant_id=None)
    assert res_no_tenant["valid"] is False
    assert "tenant" in res_no_tenant["error"]

    # With tenant_id
    res_with_tenant = service.validate_code("TENANT_ONLY", user_id=1, tenant_id="tenant_abc")
    assert res_with_tenant["valid"] is True
    assert res_with_tenant["role"] == "enterprise"


def test_validate_code_max_uses_exhausted(service, monkeypatch):
    monkeypatch.setattr(SpecialCodeService, "_redemption_count", lambda *args, **kwargs: 2)
    res = service.validate_code("LIMITED_CODE", user_id=1)
    assert res["valid"] is False
    assert "kullanım hakkı dolmuş" in res["error"]


def test_validate_code_success(service, monkeypatch):
    monkeypatch.setattr(SpecialCodeService, "_redemption_count", lambda *args, **kwargs: 0)
    res = service.validate_code("VIP_2026", user_id=1)
    assert res["valid"] is True
    assert res["role"] == "vip"
    assert res["description"] == "VIP Access"
    assert res["metadata"]["source"] == "campaign"


def test_validate_code_bad_date_format_ignores_error(service, monkeypatch):
    monkeypatch.setattr(SpecialCodeService, "_redemption_count", lambda *args, **kwargs: 0)
    res = service.validate_code("BAD_DATE_CODE", user_id=1)
    assert res["valid"] is True
    assert res["role"] == "standard"


def test_list_and_get_code_info(service):
    all_codes = service.list_available_codes()
    assert "VIP_2026" in all_codes
    assert service.get_code_info("VIP_2026")["role"] == "vip"
    assert service.get_code_info("UNKNOWN") is None


def test_config_loading_error_handling(tmp_path):
    srv = SpecialCodeService()
    srv._config_path = str(tmp_path / "non_existent.yaml")
    cfg = srv._load_config()
    assert cfg == {}

    # Corrupted YAML file
    corrupt_file = tmp_path / "corrupt.yaml"
    corrupt_file.write_text("invalid: [yaml: unclosed", encoding="utf-8")
    srv._codes_config = None
    srv._config_path = str(corrupt_file)
    cfg2 = srv._load_config()
    assert cfg2 == {}

    # Valid YAML file
    valid_file = tmp_path / "valid.yaml"
    valid_file.write_text("codes:\n  TEST_CODE:\n    role: vip\n", encoding="utf-8")
    srv._codes_config = None
    srv._config_path = str(valid_file)
    cfg3 = srv._load_config()
    assert "TEST_CODE" in cfg3
    assert cfg3["TEST_CODE"]["role"] == "vip"


def test_validate_code_invalid_max_uses_type(service, monkeypatch):
    monkeypatch.setattr(SpecialCodeService, "_redemption_count", lambda *args, **kwargs: 0)
    service._codes_config["BAD_MAX_USES"] = {
        "role": "vip",
        "max_uses": "not-an-integer",
    }
    res = service.validate_code("BAD_MAX_USES", user_id=1)
    assert res["valid"] is True
    assert res["role"] == "vip"


def test_redemption_count_real_and_exception(app):
    with app.app_context():
        # With active app context, calling _redemption_count with empty table returns 0
        count = SpecialCodeService._redemption_count("UNKNOWN_CODE", "UNKNOWN_FP")
        assert count == 0

        # Trigger exception path in _redemption_count
        with patch("models.User.query", create=True) as mock_q:
            mock_q.filter.side_effect = RuntimeError("DB down")
            err_count = SpecialCodeService._redemption_count("CODE", "FP")
            assert err_count == 0



def test_singleton_accessor():
    s1 = get_special_code_service()
    s2 = get_special_code_service()
    assert s1 is s2

