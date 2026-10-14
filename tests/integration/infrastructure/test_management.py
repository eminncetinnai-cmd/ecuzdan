"""Integration tests for database backup management boundaries."""

import json

import pytest

from infrastructure.database.management import (
    export_database_to_json,
    import_database_from_json,
)


@pytest.mark.unit
def test_export_database_to_json_exists():
    assert export_database_to_json is not None


@pytest.mark.unit
def test_import_database_from_json_exists():
    assert import_database_from_json is not None


@pytest.mark.unit
def test_module_structure():
    import infrastructure.database.management as mgmt_module

    assert hasattr(mgmt_module, 'export_database_to_json')
    assert hasattr(mgmt_module, 'import_database_from_json')


@pytest.mark.integration
def test_export_database_to_json_no_encrypt(app):
    with app.app_context():
        result = json.loads(export_database_to_json())

    assert result['schema_version']
    assert isinstance(result['users'], list)
    assert isinstance(result['transactions'], list)


@pytest.mark.integration
def test_export_database_to_json_encrypt_requires_password(app):
    with app.app_context(), pytest.raises(ValueError, match='Şifreleme için şifre gerekli'):
        export_database_to_json(encrypt=True)


@pytest.mark.integration
def test_import_database_from_json_invalid_json(app):
    with app.app_context():
        success, message = import_database_from_json('{invalid-json')

    assert success is False
    assert message.startswith('JSON format hatası:')


@pytest.mark.integration
def test_import_database_from_json_encrypted_requires_password(app):
    encrypted_payload = json.dumps({
        'encrypted': True,
        'data': 'not-used-without-password',
        'checksum': 'not-used-without-password',
        'schema_version': 'v22.0',
    })

    with app.app_context():
        success, message = import_database_from_json(encrypted_payload)

    assert success is False
    assert message == 'Şifreli yedek için şifre gerekli'


@pytest.mark.integration
def test_import_database_from_json_schema_incompatible(app):
    incompatible_payload = json.dumps({
        'schema_version': 'v0.0',
        'tenants': [],
    })

    with app.app_context():
        success, message = import_database_from_json(incompatible_payload)

    assert success is False
    assert 'Schema uyumsuz' in message
