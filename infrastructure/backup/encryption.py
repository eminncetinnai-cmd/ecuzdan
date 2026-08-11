"""
Backup Encryption Service - AES-256-GCM şifreleme servisi
Phase 17: Security enhancement for backup/restore operations
"""

import hashlib
import json
import logging
import os
from typing import Optional, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class BackupEncryptionService:
    """AES-256-GCM şifreleme servisi"""

    def __init__(self):
        self.salt_length = 16  # 128 bits
        self.nonce_length = 12  # 96 bits (GCM standard)
        self.key_length = 32  # 256 bits
        self.iterations = 100000  # PBKDF2 iterations

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Şifreden anahtar türet (PBKDF2)

        Args:
            password: Şifre
            salt: Salt değeri

        Returns:
            256-bit anahtar
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_length,
            salt=salt,
            iterations=self.iterations,
            backend=default_backend()
        )
        return kdf.derive(password.encode('utf-8'))

    def encrypt_backup(self, data: bytes, password: str) -> bytes:
        """
        Yedeği AES-256-GCM ile şifrele

        Args:
            data: Şifrelenecek veri
            password: Şifre

        Returns:
            Şifrelenmiş veri (salt + nonce + ciphertext + tag)
        """
        try:
            # Rastgele salt ve nonce oluştur
            salt = os.urandom(self.salt_length)
            nonce = os.urandom(self.nonce_length)

            # Anahtar türet
            key = self._derive_key(password, salt)

            # Şifrele
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, data, None)

            # Format: salt (16) + nonce (12) + ciphertext (variable)
            encrypted_data = salt + nonce + ciphertext

            logger.info("Backup başarıyla şifrelendi")
            return encrypted_data

        except Exception as e:
            logger.error(f"Şifreleme hatası: {e}")
            raise

    def decrypt_backup(self, encrypted_data: bytes, password: str) -> bytes:
        """
        Şifrelenmiş yedeği deşifre et

        Args:
            encrypted_data: Şifrelenmiş veri
            password: Şifre

        Returns:
            Deşifre edilmiş veri
        """
        try:
            # Veriyi parçala
            salt = encrypted_data[:self.salt_length]
            nonce = encrypted_data[self.salt_length:self.salt_length + self.nonce_length]
            ciphertext = encrypted_data[self.salt_length + self.nonce_length:]

            # Anahtar türet
            key = self._derive_key(password, salt)

            # Deşifre et
            aesgcm = AESGCM(key)
            decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)

            logger.info("Backup başarıyla deşifre edildi")
            return decrypted_data

        except Exception as e:
            logger.error(f"Deşifre hatası: {e}")
            raise ValueError("Şifre doğrulaması başarısız. Lütfen şifrenizi kontrol edin.")

    def generate_checksum(self, data: bytes) -> str:
        """
        SHA-256 checksum oluştur

        Args:
            data: Veri

        Returns:
            Hex formatında checksum
        """
        return hashlib.sha256(data).hexdigest()

    def verify_checksum(self, data: bytes, expected_checksum: str) -> bool:
        """
        Checksum doğrula

        Args:
            data: Veri
            expected_checksum: Beklenen checksum

        Returns:
            True eşleşirse, False eşleşmezse
        """
        actual_checksum = self.generate_checksum(data)
        return actual_checksum == expected_checksum

    def encrypt_json(self, json_data: dict, password: str) -> Tuple[bytes, str]:
        """
        JSON verisini şifrele ve checksum ile birlikte döndür

        Args:
            json_data: JSON verisi
            password: Şifre

        Returns:
            (şifrelenmiş veri, checksum)
        """
        json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
        json_bytes = json_str.encode('utf-8')

        checksum = self.generate_checksum(json_bytes)
        encrypted_data = self.encrypt_backup(json_bytes, password)

        return encrypted_data, checksum

    def decrypt_json(self, encrypted_data: bytes, password: str, expected_checksum: Optional[str] = None) -> dict:
        """
        Şifrelenmiş JSON verisini deşifre et

        Args:
            encrypted_data: Şifrelenmiş veri
            password: Şifre
            expected_checksum: İsteğe bağlı checksum doğrulama

        Returns:
            JSON verisi
        """
        decrypted_bytes = self.decrypt_backup(encrypted_data, password)

        if expected_checksum:
            if not self.verify_checksum(decrypted_bytes, expected_checksum):
                raise ValueError("Checksum doğrulaması başarısız. VeriT bütünlüğü ihlali.")

        json_str = decrypted_bytes.decode('utf-8')
        return json.loads(json_str)

    def generate_backup_password(self, length: int = 32) -> str:
        """
        Güçlü yedek şifresi oluştur

        Args:
            length: Şifre uzunluğu

        Returns:
            Rastgele şifre
        """
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
