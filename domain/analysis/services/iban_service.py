"""Domain service for IBAN validation, normalization, formatting, and Turkish bank auto-detection.

Strictly follows domain purity: no Flask, routes, or UI dependencies.
"""

from __future__ import annotations

import re

# Turkish Bank Code to Bank Name Mapping (Characters 5 to 9 of TR IBAN)
TR_BANK_CODES: dict[str, str] = {
    "00010": "T.C. Ziraat Bankası",
    "00012": "Türkiye Halk Bankası (Halkbank)",
    "00015": "Türkiye Vakıflar Bankası (VakıfBank)",
    "00032": "Türk Ekonomi Bankası (TEB)",
    "00046": "Akbank",
    "00059": "Şekerbank",
    "00062": "Garanti BBVA",
    "00064": "Türkiye İş Bankası",
    "00067": "Yapı ve Kredi Bankası",
    "00099": "ING Bank",
    "00103": "Fibabanka",
    "00108": "Burgan Bank",
    "00111": "QNB Finansbank",
    "00123": "HSBC Bank",
    "00124": "Alternatif Bank",
    "00125": "Burgan Bank",
    "00134": "DenizBank",
    "00135": "Anadolubank",
    "00143": "Aktif Yatırım Bankası (Aktif Bank)",
    "00146": "Odeabank",
    "00203": "Albaraka Türk Katılım Bankası",
    "00205": "Kuveyt Türk Katılım Bankası",
    "00206": "Türkiye Finans Katılım Bankası",
    "00209": "Ziraat Katılım Bankası",
    "00210": "Vakıf Katılım Bankası",
    "00211": "Türkiye Emlak Katılım Bankası",
    "00801": "Papara",
    "00802": "Paycell",
    "00803": "İninal",
    "00804": "Enpara",
    "00805": "Hayhay",
    "00806": "PeP",
    "00807": "Param",
}


class IbanService:
    """Pure domain service for IBAN normalization, validation, and bank detection."""

    @staticmethod
    def clean_iban(raw_iban: str | None) -> str:
        """Strip all whitespace, dashes, and ensure uppercase.
        
        Example: 'tr33 0006-1005' -> 'TR3300061005'
        """
        if not raw_iban:
            return ""
        # Remove whitespace, dashes, and special formatting characters
        cleaned = re.sub(r"[\s\-_.:]+", "", str(raw_iban)).upper()
        return cleaned

    @staticmethod
    def format_iban(iban: str | None) -> str:
        """Format an IBAN into 4-character chunks for readability.
        
        Example: 'TR330006100511123456789012' -> 'TR33 0006 1005 1112 3456 7890 12'
        """
        cleaned = IbanService.clean_iban(iban)
        if not cleaned:
            return ""
        # Group into 4-character chunks
        chunks = [cleaned[i:i + 4] for i in range(0, len(cleaned), 4)]
        return " ".join(chunks)

    @staticmethod
    def detect_bank_name(iban: str | None) -> str | None:
        """Auto-detect Turkish bank name from the bank code in TR IBANs."""
        cleaned = IbanService.clean_iban(iban)
        if not cleaned or not cleaned.startswith("TR") or len(cleaned) < 9:
            return None
        # In TR IBAN:
        # Indices 0-1: 'TR'
        # Indices 2-3: Check digits (2 numeric)
        # Indices 4-8: Bank code (5 numeric)
        bank_code = cleaned[4:9]
        return TR_BANK_CODES.get(bank_code)

    @staticmethod
    def validate_iban(raw_iban: str | None) -> tuple[bool, str]:
        """Validate IBAN structure and length.
        
        Returns:
            (is_valid: bool, error_message_or_empty: str)
        """
        cleaned = IbanService.clean_iban(raw_iban)
        if not cleaned:
            return False, "IBAN numarası boş olamaz."

        # General IBAN regex: 2 letter country code + 2 check digits + up to 30 alphanumeric
        if not re.match(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{4,30}$", cleaned):
            return False, "Geçersiz IBAN formatı."

        if cleaned.startswith("TR"):
            if len(cleaned) != 26:
                return False, f"Türkiye IBAN numarası 26 karakter olmalıdır (Girilen: {len(cleaned)} karakter)."
            if not re.match(r"^TR\d{24}$", cleaned):
                return False, "Türkiye IBAN numarası 'TR' ve ardından gelen 24 rakamdan oluşmalıdır."

        return True, ""

    @staticmethod
    def generate_share_text(
        title: str,
        iban: str,
        bank_name: str | None = None,
        account_holder: str | None = None,
        easy_address_type: str | None = None,
        easy_address: str | None = None,
        note: str | None = None,
    ) -> str:
        """Generate structured text message suitable for WhatsApp / SMS sharing."""
        lines: list[str] = []
        if account_holder and account_holder.strip():
            lines.append(f"Alıcı / Hesap Sahibi: {account_holder.strip()}")
        elif title and title.strip():
            lines.append(f"Hesap: {title.strip()}")

        if bank_name and bank_name.strip():
            lines.append(f"Banka: {bank_name.strip()}")

        formatted = IbanService.format_iban(iban)
        lines.append(f"IBAN: {formatted}")

        if easy_address_type and easy_address and easy_address.strip():
            lines.append(f"FAST Kolay Adres ({easy_address_type.strip()}): {easy_address.strip()}")

        if note and note.strip():
            lines.append(f"Not: {note.strip()}")

        return "\n".join(lines)
