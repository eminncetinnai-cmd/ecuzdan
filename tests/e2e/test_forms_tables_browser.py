"""Browser tests for dynamic form validation and responsive table card views."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = ROOT_DIR / "static"
FORMS_JS = STATIC_DIR / "js" / "forms.js"
TABLES_JS = STATIC_DIR / "js" / "tables.js"
COMPONENTS_CSS = STATIC_DIR / "css" / "components.css"
TOKENS_CSS = STATIC_DIR / "css" / "design-tokens.css"

pytestmark = pytest.mark.e2e


def test_form_validation_engine_blocks_invalid_and_shows_feedback(page: Page) -> None:
    """Verifies that client-side form validation blocks invalid inputs, adds error classes and messages."""
    html_content = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="utf-8">
        <title>Test Form Validation</title>
    </head>
    <body>
        <div id="toast-container"></div>
        <form id="testForm" method="POST" action="/dummy-submit" data-validate="true">
            <div class="form-group">
                <label for="desc">Açıklama</label>
                <input type="text" id="desc" name="description" required>
            </div>
            <div class="form-group">
                <label for="amount">Tutar</label>
                <input type="number" id="amount" name="amount" step="0.01" required>
            </div>
            <button type="submit" id="submitBtn">Kaydet</button>
        </form>
        <script>
            window.showToast = function(msg, type) {
                window.__lastToast = { msg: msg, type: type };
            };
        </script>
    </body>
    </html>
    """
    page.set_content(html_content)
    page.add_style_tag(path=str(TOKENS_CSS))
    page.add_style_tag(path=str(COMPONENTS_CSS))
    page.add_script_tag(path=str(FORMS_JS), type="module")

    # Wait for forms.js module to execute and attach window.ECuzdanForms
    page.wait_for_function("() => window.ECuzdanForms !== undefined")

    desc_input = page.locator("#desc")
    amount_input = page.locator("#amount")
    submit_btn = page.locator("#submitBtn")

    # 1. Attempt submitting with completely empty fields
    submit_btn.click()

    # Form should have intercepted submission and marked desc as invalid
    expect(desc_input).to_have_class(re.compile(r"form-input-error"))
    error_msg = page.locator(".field-error-message")
    expect(error_msg.first).to_be_visible()

    # Toast should have fired
    last_toast = page.evaluate("window.__lastToast")
    assert last_toast is not None
    assert last_toast["type"] == "warning"

    # 2. Fill desc, but enter 0 for amount (financial field should require > 0)
    desc_input.fill("Market Alışverişi")
    amount_input.fill("0")
    submit_btn.click()

    expect(amount_input).to_have_class(re.compile(r"form-input-error"))
    amount_error = page.locator(".field-error-message .error-text")
    assert "0'dan büyük" in amount_error.inner_text()

    # 3. Enter valid positive amount
    amount_input.fill("150.50")

    # Error class should be removed on input
    expect(amount_input).not_to_have_class(re.compile(r"form-input-error"))


def test_responsive_tables_generates_data_labels_for_mobile(page: Page) -> None:
    """Verifies that responsive card tables receive data-label attributes and adapt on mobile."""
    html_content = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="utf-8">
        <title>Test Responsive Table</title>
    </head>
    <body>
        <div class="overflow-x-auto">
            <table id="testTable" class="responsive-card-table">
                <thead>
                    <tr>
                        <th>Tarih</th>
                        <th>Kategori</th>
                        <th>Tutar</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>01.10.2026</td>
                        <td>Gıda</td>
                        <td>250,00 ₺</td>
                    </tr>
                    <tr>
                        <td>02.10.2026</td>
                        <td>Ulaşım</td>
                        <td>75,00 ₺</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    page.set_content(html_content)
    page.add_style_tag(path=str(TOKENS_CSS))
    page.add_style_tag(path=str(COMPONENTS_CSS))
    page.add_script_tag(path=str(TABLES_JS), type="module")

    # Wait for tables.js module to execute and attach window.ECuzdanTables
    page.wait_for_function("() => window.ECuzdanTables !== undefined")

    # Check data-label attributes applied to tbody cells
    cells = page.locator("#testTable tbody tr:first-child td")
    expect(cells.nth(0)).to_have_attribute("data-label", "Tarih")
    expect(cells.nth(1)).to_have_attribute("data-label", "Kategori")
    expect(cells.nth(2)).to_have_attribute("data-label", "Tutar")

    # Test mobile viewport styling
    page.set_viewport_size({"width": 375, "height": 667})
    thead = page.locator("#testTable thead")
    # thead should be hidden on mobile viewport in CSS
    thead_display = thead.evaluate("el => window.getComputedStyle(el).display")
    assert thead_display == "none"

    # Row should be display: block on mobile viewport
    row = page.locator("#testTable tbody tr").first
    row_display = row.evaluate("el => window.getComputedStyle(el).display")
    assert row_display == "block"


def test_form_loading_spinner_on_valid_submit(page: Page) -> None:
    """Verifies that a valid form submission displays loading spinner and disables submit button."""
    html_content = """
    <!DOCTYPE html>
    <html lang="tr">
    <head><meta charset="utf-8"></head>
    <body>
        <form id="validForm" method="POST" action="javascript:void(0)" data-validate="true">
            <input type="text" id="itemName" name="item_name" value="Geçerli İsim" required>
            <input type="number" id="itemAmount" name="amount" value="50.00" required>
            <button type="submit" id="saveButton">Kaydet</button>
        </form>
    </body>
    </html>
    """
    page.set_content(html_content)
    page.add_style_tag(path=str(COMPONENTS_CSS))
    page.add_script_tag(path=str(FORMS_JS), type="module")
    page.wait_for_function("() => window.ECuzdanForms !== undefined")

    btn = page.locator("#saveButton")
    btn.click()

    expect(btn).to_have_class(re.compile(r"btn-loading"))
    assert btn.is_disabled()
    assert "Kaydediliyor..." in btn.inner_text()


def test_email_validation_and_form_reset(page: Page) -> None:
    """Verifies email regex validation and that resetForm clears errors."""
    html_content = """
    <!DOCTYPE html>
    <html lang="tr">
    <head><meta charset="utf-8"></head>
    <body>
        <form id="profileForm" method="POST" action="javascript:void(0)" data-validate="true">
            <input type="email" id="emailInput" name="email" required>
            <button type="submit" id="submitProfile">Gönder</button>
        </form>
    </body>
    </html>
    """
    page.set_content(html_content)
    page.add_style_tag(path=str(COMPONENTS_CSS))
    page.add_script_tag(path=str(FORMS_JS), type="module")
    page.wait_for_function("() => window.ECuzdanForms !== undefined")

    email_input = page.locator("#emailInput")
    email_input.fill("invalid-email-address")
    page.locator("#submitProfile").click()

    expect(email_input).to_have_class(re.compile(r"form-input-error"))
    err_text = page.locator(".field-error-message .error-text").inner_text()
    assert "e-posta" in err_text.lower()

    # Reset form
    page.evaluate("() => window.ECuzdanForms.resetForm('profileForm')")
    expect(email_input).not_to_have_class(re.compile(r"form-input-error"))
    assert page.locator(".field-error-message").count() == 0

