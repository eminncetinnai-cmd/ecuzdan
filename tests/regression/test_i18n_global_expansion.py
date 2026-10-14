"""Regression coverage for the global four-language i18n expansion."""

from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
LANGUAGES = ("tr", "en", "de", "it")
PLACEHOLDER_RE = re.compile(r"\{([^{}]+)\}")


def _catalogs() -> dict[str, dict[str, str]]:
    return {
        language: json.loads(
            (ROOT / "translations" / f"{language}.json").read_text(encoding="utf-8")
        )
        for language in LANGUAGES
    }


@pytest.mark.regression
def test_four_language_catalogs_have_exact_key_parity():
    """Every supported locale must expose exactly the same translation keys."""
    catalogs = _catalogs()
    key_sets = {language: set(catalog) for language, catalog in catalogs.items()}
    expected = key_sets["tr"]

    assert all(keys == expected for keys in key_sets.values())
    assert len(expected) >= 2017
    assert sum(key.startswith("ui_auto_") for key in expected) >= 1170
    guide_keys = {key for key in expected if key.startswith(("ug_", "ug2_"))}
    assert len(guide_keys) == 241
    for language in LANGUAGES:
        assert all(catalogs[language][key].strip() for key in guide_keys)


@pytest.mark.regression
def test_user_guide_catalog_has_four_language_parity():
    """The user guide content must be complete in every supported locale."""
    catalogs = _catalogs()
    guide_sets = {
        language: {key for key in catalog if key.startswith(("ug_", "ug2_"))}
        for language, catalog in catalogs.items()
    }
    expected = guide_sets["tr"]
    assert all(keys == expected for keys in guide_sets.values())
    assert len(expected) == 241


@pytest.mark.regression
def test_auto_keys_are_nonempty_and_preserve_placeholders():
    """Generated UI translations must be present and preserve format variables."""
    catalogs = _catalogs()
    auto_keys = [key for key in catalogs["tr"] if key.startswith("ui_auto_")]

    for key in auto_keys:
        source_placeholders = set(PLACEHOLDER_RE.findall(catalogs["tr"][key]))
        for language in LANGUAGES:
            value = catalogs[language][key]
            assert isinstance(value, str) and value.strip(), (language, key)
            assert set(PLACEHOLDER_RE.findall(value)) == source_placeholders, (
                language,
                key,
            )


@pytest.mark.regression
def test_inject_gettext_exposes_active_translation_catalog():
    """Templates and browser code receive the selected locale's full catalog."""
    from infrastructure.i18n import I18n

    instance = I18n()
    instance.translations = {"tr": {"sample": "Örnek"}}

    payload = instance.inject_gettext()

    assert payload["translation_catalog"] == {"sample": "Örnek"}
    assert payload["available_languages"] == ("tr",)


@pytest.mark.regression
def test_gettext_falls_back_to_default_locale_without_flask_context():
    """A missing selected-locale key must resolve through the default locale."""
    from infrastructure.i18n import I18n

    instance = I18n()
    instance.translations = {"tr": {"sample": "Örnek"}, "en": {}}
    mocked_g = Mock()
    mocked_g.get.return_value = "en"

    with patch("infrastructure.i18n.g", mocked_g):
        assert instance.gettext("sample") == "Örnek"
        assert instance.gettext("missing") == "missing"
