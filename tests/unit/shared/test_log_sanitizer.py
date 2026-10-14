"""
Unit Tests - Log Sanitizer
shared/log_sanitizer.py fonksiyonları için kapsamlı testler.
"""

import pytest

from shared.log_sanitizer import (
    mask_bearer,
    mask_email,
    mask_provider_id,
    redact_dict,
    redact_url_params,
)

# ── mask_email ─────────────────────────────────────────────────────────────────

class TestMaskEmail:
    @pytest.mark.unit
    def test_normal_email_masked(self):
        assert mask_email("john@example.com") == "j***@example.com"

    @pytest.mark.unit
    def test_single_char_local_masked(self):
        assert mask_email("a@x.com") == "a***@x.com"

    @pytest.mark.unit
    def test_none_returns_redacted(self):
        assert mask_email(None) == "[REDACTED]"

    @pytest.mark.unit
    def test_empty_string_returns_redacted(self):
        assert mask_email("") == "[REDACTED]"

    @pytest.mark.unit
    def test_no_at_sign_returns_redacted(self):
        assert mask_email("notanemail") == "[REDACTED]"

    @pytest.mark.unit
    def test_domain_preserved(self):
        result = mask_email("user@gmail.com")
        assert result.endswith("@gmail.com")

    @pytest.mark.unit
    def test_first_char_preserved(self):
        result = mask_email("alice@domain.org")
        assert result.startswith("a")


# ── mask_provider_id ───────────────────────────────────────────────────────────

class TestMaskProviderId:
    @pytest.mark.unit
    def test_long_id_truncated(self):
        result = mask_provider_id("1234567890")
        assert result == "123...890"

    @pytest.mark.unit
    def test_short_id_fully_masked(self):
        assert mask_provider_id("123") == "***"

    @pytest.mark.unit
    def test_none_returns_redacted(self):
        assert mask_provider_id(None) == "[REDACTED]"

    @pytest.mark.unit
    def test_empty_string_returns_redacted(self):
        assert mask_provider_id("") == "[REDACTED]"

    @pytest.mark.unit
    def test_original_value_not_exposed(self):
        provider_id = "SUPERSECRETGOOGLEID123456"
        result = mask_provider_id(provider_id)
        assert provider_id not in result
        assert "SUP" in result
        assert "456" in result


# ── mask_bearer ────────────────────────────────────────────────────────────────

class TestMaskBearer:
    @pytest.mark.unit
    def test_long_token_masked(self):
        result = mask_bearer("eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature")
        assert result == "eyJh***"

    @pytest.mark.unit
    def test_short_token_fully_masked(self):
        assert mask_bearer("tok") == "***"

    @pytest.mark.unit
    def test_none_returns_redacted(self):
        assert mask_bearer(None) == "[REDACTED]"

    @pytest.mark.unit
    def test_empty_string_returns_redacted(self):
        assert mask_bearer("") == "[REDACTED]"

    @pytest.mark.unit
    def test_full_token_not_in_result(self):
        token = "supersecrettoken12345"
        result = mask_bearer(token)
        assert token not in result


# ── redact_dict ────────────────────────────────────────────────────────────────

class TestRedactDict:
    @pytest.mark.unit
    def test_password_field_redacted(self):
        data = {'username': 'john', 'password': 'hunter2'}
        result = redact_dict(data)
        assert result['password'] == '[REDACTED]'
        assert result['username'] == 'john'

    @pytest.mark.unit
    def test_token_field_redacted(self):
        data = {'access_token': 'eyJ...', 'user_id': '42'}
        result = redact_dict(data)
        assert result['access_token'] == '[REDACTED]'
        assert result['user_id'] == '42'

    @pytest.mark.unit
    def test_state_field_redacted(self):
        data = {'state': 'csrf-state-value', 'code': 'auth-code-value'}
        result = redact_dict(data)
        assert result['state'] == '[REDACTED]'
        assert result['code'] == '[REDACTED]'

    @pytest.mark.unit
    def test_authorization_header_redacted(self):
        data = {'Authorization': 'Bearer eyJhb...', 'Content-Type': 'application/json'}
        result = redact_dict(data)
        assert result['Authorization'] == '[REDACTED]'
        assert result['Content-Type'] == 'application/json'

    @pytest.mark.unit
    def test_api_key_redacted(self):
        data = {'api_key': 'secret-key', 'page': '1'}
        result = redact_dict(data)
        assert result['api_key'] == '[REDACTED]'

    @pytest.mark.unit
    def test_non_sensitive_fields_preserved(self):
        data = {'page': '2', 'sort': 'asc', 'category': 'food'}
        result = redact_dict(data)
        assert result == {'page': '2', 'sort': 'asc', 'category': 'food'}

    @pytest.mark.unit
    def test_empty_dict_returns_empty(self):
        assert redact_dict({}) == {}

    @pytest.mark.unit
    def test_long_value_truncated(self):
        data = {'description': 'x' * 300}
        result = redact_dict(data, max_value_len=200)
        assert len(result['description']) < 300
        assert result['description'].endswith('...[truncated]')

    @pytest.mark.unit
    def test_returns_string_values(self):
        data = {'count': 42, 'active': True}
        result = redact_dict(data)
        for v in result.values():
            assert isinstance(v, str)

    @pytest.mark.unit
    def test_case_insensitive_key_matching(self):
        data = {'PASSWORD': 'secret', 'Token': 'tok123'}
        result = redact_dict(data)
        assert result['PASSWORD'] == '[REDACTED]'
        assert result['Token'] == '[REDACTED]'

    @pytest.mark.unit
    def test_partial_key_match(self):
        """'access_token' 'token' içerdiği için maskelenmeli."""
        data = {'access_token': 'abc', 'refresh_token': 'xyz'}
        result = redact_dict(data)
        assert result['access_token'] == '[REDACTED]'
        assert result['refresh_token'] == '[REDACTED]'


# ── redact_url_params ──────────────────────────────────────────────────────────

class TestRedactUrlParams:
    @pytest.mark.unit
    def test_code_and_state_redacted(self):
        url = "/callback?code=abc123&state=xyz789"
        result = redact_url_params(url)
        assert "abc123" not in result
        assert "xyz789" not in result
        assert "code=[REDACTED]" in result
        assert "state=[REDACTED]" in result

    @pytest.mark.unit
    def test_non_sensitive_params_preserved(self):
        url = "/search?q=python&page=2&sort=asc"
        result = redact_url_params(url)
        assert "python" in result
        assert "page=2" in result

    @pytest.mark.unit
    def test_mixed_url_redacted(self):
        url = "/callback?provider=google&code=secret_code&page=1"
        result = redact_url_params(url)
        assert "secret_code" not in result
        assert "page=1" in result

    @pytest.mark.unit
    def test_empty_url_unchanged(self):
        assert redact_url_params("") == ""

    @pytest.mark.unit
    def test_url_without_params_unchanged(self):
        url = "/dashboard"
        assert redact_url_params(url) == url

    @pytest.mark.unit
    def test_token_in_url_redacted(self):
        url = "/verify?token=eyJhbGci&redirect=/"
        result = redact_url_params(url)
        assert "eyJhbGci" not in result
        assert "redirect=/" in result
