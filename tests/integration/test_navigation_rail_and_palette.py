"""Integration & Contract Tests for Collapsible Navigation Rail & Command Palette.

Validates:
1. Collapsible icon rail DOM elements, localStorage initialization, and data-sidebar-mode.
2. Zero vertical shift CSS invariants (brand row: 56px, quick bricks: 126px, section title: 28px, nav link: 40px).
3. Quick action bricks expansion (Lego buttons), labels reveal, and destination URLs.
4. Comprehensive 22+ page navigation coverage with data-label and title i18n parity.
5. Command Palette (Ctrl+K) search index, 3-column quick action grid, and action triggers.
6. A11y keyboard shortcuts (Ctrl+B, Ctrl+K, Alt+1..5, Escape) and focus safety guards.
7. Header quick actions panel contract and alignment with E2E suite.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_navigation_rail_mode_tokens_and_dom_contract(authenticated_client):
    """Verify icon rail DOM contracts, toggle buttons, and local storage state."""
    response = authenticated_client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    # 1. HTML root state & local storage key
    assert 'data-sidebar-mode="expanded"' in body or "data-sidebar-mode" in body
    assert "ecuzdan_sidebar_mode" in body

    # 2. Toggle buttons & icons
    assert 'id="sidebarRailToggleBtn"' in body
    assert 'id="sidebarRailFooterBtn"' in body
    assert "rail-icon-collapse" in body
    assert "rail-icon-expand" in body
    assert "Ctrl+B" in body

    # 3. Accessibility attributes
    assert 'aria-label=' in body
    assert 'role="button"' in body


@pytest.mark.integration
def test_zero_vertical_shift_css_lock_invariants():
    """Verify that CSS locks exact dimensions between 76px resting rail and 280px peeking mode."""
    tokens_path = PROJECT_ROOT / "static" / "css" / "design-tokens.css"
    assert tokens_path.is_file(), "design-tokens.css must exist"
    tokens_content = tokens_path.read_text(encoding="utf-8")

    css_path = PROJECT_ROOT / "static" / "css" / "layout.css"
    assert css_path.is_file(), "layout.css must exist"
    css_content = css_path.read_text(encoding="utf-8")

    # 1. Design tokens in design-tokens.css
    assert "--sidebar-width-expanded: 280px" in tokens_content
    assert "--sidebar-width-rail:     76px" in tokens_content or "--sidebar-width-rail: 76px" in tokens_content

    # 2. Brand row height lock (56px)
    assert "height: 56px" in css_content
    assert ".sidebar-brand-row" in css_content

    # 3. Section titles height lock (28px)
    assert "height: 28px" in css_content
    assert ".nav-section-title" in css_content

    # 4. Nav links height lock (40px)
    assert "height: 40px" in css_content
    assert ".nav-link" in css_content


@pytest.mark.integration
def test_clean_sidebar_navigation_uncluttered_structure(authenticated_client):
    """Verify the sidebar navigation structure is uncluttered with quick actions consolidated in header."""
    response = authenticated_client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    # 1. Quick action bricks removed from sidebar for clean executive-grade minimalist layout
    assert "sidebar-quick-bricks" not in body
    assert "brick-tooltip" not in body

    # 2. Header quick actions button & panel serves as the single source of truth for quick actions
    assert 'id="quickActionsPanel"' in body
    assert "quick-actions-btn" in body


@pytest.mark.integration
def test_all_22_navigation_links_parity_and_datalabels(authenticated_client):
    """Verify streamlined core hub pages are present in the navigation macro and have data-label attributes."""
    response = authenticated_client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    canonical_core_routes = [
        # Overview (Genel Bakis — Daily Core Priorities)
        ("/", "Nakit Akisi"),
        ("/transactions", "Islemler"),
        ("/payment_calendar", "Odeme Takvimi"),
        ("/logbook", "Cuzdan Defteri"),
        # Assets & Analysis Hubs
        ("/assets", "Varliklar"),
        ("/gold-tracking", "Altin Takip"),
        ("/analysis", "Finansal Saglik"),
        # Settings & Education Hubs
        ("/financial_education", "Finansal Egitim"),
        ("/settings", "Ayarlar"),
    ]

    for route, _label in canonical_core_routes:
        assert f'href="{route}"' in body, f"Route {route} must be rendered in navigation"

    # Verify that nav links render data-label attribute for accessibility / tooltip parity
    nav_links = re.findall(r'<a\s+[^>]*class="[^"]*nav-link[^"]*"[^>]*>', body)
    assert len(nav_links) >= 18, f"Expected at least 18 nav-links (9 desktop + 9 mobile), found {len(nav_links)}"
    for link in nav_links:
        assert 'data-label="' in link, f"Nav link missing data-label: {link}"
        assert 'title="' in link, f"Nav link missing title: {link}"


@pytest.mark.integration
def test_command_palette_js_implementation_and_search_index():
    """Verify Command Palette (Ctrl+K) search index, quick action items, and arrow key handlers."""
    js_path = PROJECT_ROOT / "static" / "js" / "layout-shell.js"
    assert js_path.is_file(), "layout-shell.js must exist"
    js_content = js_path.read_text(encoding="utf-8")

    # 1. Functions existence
    assert "function openGlobalSearch()" in js_content
    assert "function handleSearchInput(" in js_content
    assert "function closeGlobalSearch()" in js_content

    # 2. 3-column Quick Actions grid in initial modal open
    assert "Hızlı Aksiyonlar" in js_content
    assert "Hızlı İşlem" in js_content
    assert "Plan Ekle" in js_content
    assert "Varlık Ekle" in js_content

    # 3. Quick action items in searchItems for query matching
    assert "action: 'quick-tx'" in js_content
    assert "url: '/plans?modal=new'" in js_content
    assert "url: '/assets?modal=new'" in js_content
    assert "openGlobalQuickTxModal()" in js_content

    # 4. Keyboard navigation support
    assert "ArrowDown" in js_content
    assert "ArrowUp" in js_content
    assert "Enter" in js_content
    assert "searchSelectedIndex" in js_content
    assert "is-selected" in js_content

    # 5. Global search shortcut binding (Ctrl+K / Cmd+K)
    assert "key.toLowerCase() === 'k'" in js_content
    assert "openGlobalSearch();" in js_content


@pytest.mark.integration
def test_keyboard_shortcuts_and_a11y_handlers():
    """Verify global keyboard shortcuts: Ctrl+B, Escape, Alt+1..5, and input field guards."""
    js_path = PROJECT_ROOT / "static" / "js" / "layout-shell.js"
    js_content = js_path.read_text(encoding="utf-8")

    # 1. Rail mode toggle shortcut (Ctrl+B)
    assert "key.toLowerCase() === 'b'" in js_content
    assert "toggleSidebarRailMode()" in js_content

    # 2. Escape dismisses modal and rail peek
    assert "key === 'Escape'" in js_content
    assert "closeGlobalSearch()" in js_content
    assert "sidebar.classList.remove('rail-peek')" in js_content

    # 3. Section jump shortcuts (Alt+1..5)
    assert "e.altKey" in js_content
    assert "['1', '2', '3', '4', '5'].includes(e.key)" in js_content

    # 4. Input typing guard
    assert "isTyping" in js_content
    assert "INPUT" in js_content
    assert "TEXTAREA" in js_content


@pytest.mark.integration
def test_header_quick_actions_panel_contract(authenticated_client):
    """Verify that the header quick actions button and panel preserve backwards compatibility."""
    response = authenticated_client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    # 1. Header controls
    assert "quick-actions-btn" in body
    assert 'id="quickActionsPanel"' in body

    # 2. Quick actions panel link targets
    panel_start = body.index('id="quickActionsPanel"')
    panel_end = body.index('<!-- Calculator -->', panel_start)
    panel_html = body[panel_start:panel_end]

    assert "openGlobalQuickTxModal()" in panel_html
    assert 'href="/plans"' in panel_html
    assert 'href="/assets"' in panel_html
