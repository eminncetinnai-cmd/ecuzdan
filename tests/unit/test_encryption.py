"""
Unit Tests - Backup Encryption
AES-256-GCM encryption service tests
"""

import pytest
from infrastructure.backup.encryption import BackupEncryptionService


@pytest.mark.unit
def test_encryption_module_imports():
    """Test encryption module can be imported"""
    from infrastructure.backup.encryption import BackupEncryptionService
    assert BackupEncryptionService is not None


@pytest.mark.unit
def test_backup_encryption_service_initialization():
    """Test BackupEncryptionService initialization"""
    service = BackupEncryptionService()
    
    assert service.salt_length == 16
    assert service.nonce_length == 12
    assert service.key_length == 32
    assert service.iterations == 100000


@pytest.mark.unit
def test_derive_key():
    """Test _derive_key method"""
    service = BackupEncryptionService()
    
    password = "test_password"
    salt = b"0123456789abcdef"
    
    key = service._derive_key(password, salt)
    
    assert len(key) == 32  # 256 bits
    assert isinstance(key, bytes)


@pytest.mark.unit
def test_derive_key_consistency():
    """Test _derive_key produces consistent results"""
    service = BackupEncryptionService()
    
    password = "test_password"
    salt = b"0123456789abcdef"
    
    key1 = service._derive_key(password, salt)
    key2 = service._derive_key(password, salt)
    
    assert key1 == key2


@pytest.mark.unit
def test_encrypt_backup():
    """Test encrypt_backup method"""
    service = BackupEncryptionService()
    
    data = b"test data to encrypt"
    password = "test_password"
    
    encrypted = service.encrypt_backup(data, password)
    
    assert len(encrypted) > len(data)
    assert isinstance(encrypted, bytes)


@pytest.mark.unit
def test_encrypt_backup_format():
    """Test encrypt_backup output format"""
    service = BackupEncryptionService()
    
    data = b"test data"
    password = "test_password"
    
    encrypted = service.encrypt_backup(data, password)
    
    # Format: salt (16) + nonce (12) + ciphertext
    assert len(encrypted) >= 28  # 16 + 12 + at least some ciphertext


@pytest.mark.unit
def test_decrypt_backup():
    """Test decrypt_backup method"""
    service = BackupEncryptionService()
    
    data = b"test data to encrypt"
    password = "test_password"
    
    encrypted = service.encrypt_backup(data, password)
    decrypted = service.decrypt_backup(encrypted, password)
    
    assert decrypted == data


@pytest.mark.unit
def test_decrypt_backup_wrong_password():
    """Test decrypt_backup with wrong password raises ValueError"""
    service = BackupEncryptionService()
    
    data = b"test data"
    password = "correct_password"
    
    encrypted = service.encrypt_backup(data, password)
    
    with pytest.raises(ValueError, match="Şifre doğrulaması başarısız"):
        service.decrypt_backup(encrypted, "wrong_password")


@pytest.mark.unit
def test_generate_checksum():
    """Test generate_checksum method"""
    service = BackupEncryptionService()
    
    data = b"test data"
    checksum = service.generate_checksum(data)
    
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA-256 hex length


@pytest.mark.unit
def test_generate_checksum_consistency():
    """Test generate_checksum produces consistent results"""
    service = BackupEncryptionService()
    
    data = b"test data"
    
    checksum1 = service.generate_checksum(data)
    checksum2 = service.generate_checksum(data)
    
    assert checksum1 == checksum2


@pytest.mark.unit
def test_verify_checksum_valid():
    """Test verify_checksum with valid checksum"""
    service = BackupEncryptionService()
    
    data = b"test data"
    checksum = service.generate_checksum(data)
    
    result = service.verify_checksum(data, checksum)
    
    assert result is True


@pytest.mark.unit
def test_verify_checksum_invalid():
    """Test verify_checksum with invalid checksum"""
    service = BackupEncryptionService()
    
    data = b"test data"
    wrong_checksum = "0" * 64
    
    result = service.verify_checksum(data, wrong_checksum)
    
    assert result is False


@pytest.mark.unit
def test_encrypt_json():
    """Test encrypt_json method"""
    service = BackupEncryptionService()
    
    json_data = {"key": "value", "number": 123}
    password = "test_password"
    
    encrypted, checksum = service.encrypt_json(json_data, password)
    
    assert isinstance(encrypted, bytes)
    assert isinstance(checksum, str)
    assert len(checksum) == 64


@pytest.mark.unit
def test_decrypt_json():
    """Test decrypt_json method"""
    service = BackupEncryptionService()
    
    json_data = {"key": "value", "number": 123}
    password = "test_password"
    
    encrypted, checksum = service.encrypt_json(json_data, password)
    decrypted = service.decrypt_json(encrypted, password)
    
    assert decrypted == json_data


@pytest.mark.unit
def test_decrypt_json_with_checksum():
    """Test decrypt_json with checksum verification"""
    service = BackupEncryptionService()
    
    json_data = {"key": "value", "number": 123}
    password = "test_password"
    
    encrypted, checksum = service.encrypt_json(json_data, password)
    decrypted = service.decrypt_json(encrypted, password, expected_checksum=checksum)
    
    assert decrypted == json_data


@pytest.mark.unit
def test_decrypt_json_invalid_checksum():
    """Test decrypt_json with invalid checksum raises ValueError"""
    service = BackupEncryptionService()
    
    json_data = {"key": "value"}
    password = "test_password"
    
    encrypted, _ = service.encrypt_json(json_data, password)
    
    with pytest.raises(ValueError, match="Checksum doğrulaması başarısız"):
        service.decrypt_json(encrypted, password, expected_checksum="wrong_checksum")


@pytest.mark.unit
def test_generate_backup_password():
    """Test generate_backup_password method"""
    service = BackupEncryptionService()
    
    password = service.generate_backup_password()
    
    assert isinstance(password, str)
    assert len(password) == 32


@pytest.mark.unit
def test_generate_backup_password_custom_length():
    """Test generate_backup_password with custom length"""
    service = BackupEncryptionService()
    
    password = service.generate_backup_password(length=16)
    
    assert isinstance(password, str)
    assert len(password) == 16


@pytest.mark.unit
def test_generate_backup_password_uniqueness():
    """Test generate_backup_password produces unique passwords"""
    service = BackupEncryptionService()
    
    password1 = service.generate_backup_password()
    password2 = service.generate_backup_password()
    
    assert password1 != password2


@pytest.mark.unit
def test_encrypt_decrypt_roundtrip():
    """Test complete encrypt/decrypt roundtrip"""
    service = BackupEncryptionService()
    
    original_data = b"This is a test message for encryption"
    password = "secure_password_123"
    
    encrypted = service.encrypt_backup(original_data, password)
    decrypted = service.decrypt_backup(encrypted, password)
    
    assert decrypted == original_data


@pytest.mark.unit
def test_encrypt_json_decrypt_json_roundtrip():
    """Test complete JSON encrypt/decrypt roundtrip"""
    service = BackupEncryptionService()
    
    original_json = {
        "user": "testuser",
        "data": [1, 2, 3],
        "nested": {"key": "value"}
    }
    password = "secure_password_123"
    
    encrypted, checksum = service.encrypt_json(original_json, password)
    decrypted_json = service.decrypt_json(encrypted, password, expected_checksum=checksum)
    
    assert decrypted_json == original_json
