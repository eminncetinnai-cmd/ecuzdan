"""Unit tests for IbanService domain logic."""

import pytest
from domain.analysis.services.iban_service import IbanService, TR_BANK_CODES


@pytest.mark.unit
def test_clean_iban():
    assert IbanService.clean_iban("tr33 0006 1005 1112 3456 7890 12") == "TR330006100511123456789012"
    assert IbanService.clean_iban("TR33-0006-1005") == "TR3300061005"
    assert IbanService.clean_iban(None) == ""
    assert IbanService.clean_iban("   ") == ""


@pytest.mark.unit
def test_format_iban():
    assert IbanService.format_iban("TR330006100511123456789012") == "TR33 0006 1005 1112 3456 7890 12"
    assert IbanService.format_iban("tr3300061005") == "TR33 0006 1005"
    assert IbanService.format_iban(None) == ""


@pytest.mark.unit
def test_detect_bank_name():
    # 00062 -> Garanti BBVA
    assert IbanService.detect_bank_name("TR330006200511123456789012") == "Garanti BBVA"
    # 00064 -> Türkiye İş Bankası
    assert IbanService.detect_bank_name("TR120006400511123456789012") == "Türkiye İş Bankası"
    # 00010 -> T.C. Ziraat Bankası
    assert IbanService.detect_bank_name("TR990001000511123456789012") == "T.C. Ziraat Bankası"
    # 00801 -> Papara
    assert IbanService.detect_bank_name("TR550080100511123456789012") == "Papara"
    # Unknown bank code
    assert IbanService.detect_bank_name("TR009999900511123456789012") is None
    # Invalid length or non-TR
    assert IbanService.detect_bank_name("DE1234") is None
    assert IbanService.detect_bank_name(None) is None


@pytest.mark.unit
def test_validate_iban():
    # Valid TR IBAN
    valid, err = IbanService.validate_iban("TR330006200511123456789012")
    assert valid is True
    assert err == ""

    # Valid with spaces
    valid, err = IbanService.validate_iban("TR33 0006 2005 1112 3456 7890 12")
    assert valid is True

    # Empty
    valid, err = IbanService.validate_iban("")
    assert valid is False
    assert "boş olamaz" in err

    # Short TR IBAN
    valid, err = IbanService.validate_iban("TR3300062")
    assert valid is False
    assert "26 karakter" in err

    # Invalid characters in TR IBAN
    valid, err = IbanService.validate_iban("TR33000620051112345678901X")
    assert valid is False

    # Valid International IBAN (e.g., DE or GB)
    valid, err = IbanService.validate_iban("DE89370400440532013000")
    assert valid is True
    assert err == ""


@pytest.mark.unit
def test_generate_share_text():
    text = IbanService.generate_share_text(
        title="Ev Kirası",
        iban="TR330006200511123456789012",
        bank_name="Garanti BBVA",
        account_holder="Ahmet Yılmaz",
        easy_address_type="Telefon",
        easy_address="0532 111 22 33",
        note="Her ayın 1'inde",
    )
    assert "Alıcı / Hesap Sahibi: Ahmet Yılmaz" in text
    assert "Banka: Garanti BBVA" in text
    assert "IBAN: TR33 0006 2005 1112 3456 7890 12" in text
    assert "FAST Kolay Adres (Telefon): 0532 111 22 33" in text
    assert "Not: Her ayın 1'inde" in text
