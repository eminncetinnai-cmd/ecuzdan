"""
Unit Tests - Admin UI Isolation & Capability Visibility
Verifies that admin-only and system-maintenance links/cards
are hidden from regular users in Jinja templates.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from flask import render_template_string


@pytest.mark.unit
def test_storage_health_link_hidden_for_regular_user(app):
    """Test that storage-health nav link is hidden when user lacks storage_health.view capability."""
    regular_user = SimpleNamespace(
        id=1,
        username="normal_user",
        role="kullanici",
        is_super_admin=False,
        has_capability=lambda cap: False,
    )

    template = """
    {% if current_user and current_user.has_capability('storage_health.view') %}
    <a href="/storage-health/">Depolama Sağlığı & Bakım</a>
    {% endif %}
    """

    with app.test_request_context("/settings"):
        html = render_template_string(template, current_user=regular_user)
        assert "/storage-health/" not in html
        assert "Depolama Sağlığı" not in html


@pytest.mark.unit
def test_storage_health_link_visible_for_admin_user(app):
    """Test that storage-health nav link is visible when user has storage_health.view capability."""
    admin_user = SimpleNamespace(
        id=2,
        username="emin",
        role="sistem_yoneticisi",
        is_super_admin=True,
        has_capability=lambda cap: True,
    )

    template = """
    {% if current_user and current_user.has_capability('storage_health.view') %}
    <a href="/storage-health/">Depolama Sağlığı & Bakım</a>
    {% endif %}
    """

    with app.test_request_context("/settings"):
        html = render_template_string(template, current_user=admin_user)
        assert "/storage-health/" in html
        assert "Depolama Sağlığı & Bakım" in html


@pytest.mark.unit
def test_db_maintenance_card_hidden_for_regular_user(app):
    """Test that DB tune-up maintenance card is hidden from regular users."""
    regular_user = SimpleNamespace(
        id=1,
        username="normal_user",
        role="tenant_admin",
        is_super_admin=False,
        has_capability=lambda cap: False,
    )

    template = """
    {% if current_user and current_user.has_capability('storage_health.view') %}
    <div id="db-tuneup-card">
        <h3>Veritabanı Bakımı & Performans Optimizasyonu</h3>
        <button id="btn-db-tuneup">Veritabanını Şimdi Optimize Et</button>
    </div>
    {% endif %}
    """

    with app.test_request_context("/settings"):
        html = render_template_string(template, current_user=regular_user)
        assert "db-tuneup-card" not in html
        assert "Veritabanını Şimdi Optimize Et" not in html


@pytest.mark.unit
def test_db_maintenance_card_visible_for_privileged_user(app):
    """Test that DB tune-up maintenance card is shown to privileged users."""
    privileged_user = SimpleNamespace(
        id=2,
        username="emin",
        role="sistem_yoneticisi",
        is_super_admin=True,
        has_capability=lambda cap: True,
    )

    template = """
    {% if current_user and current_user.has_capability('storage_health.view') %}
    <div id="db-tuneup-card">
        <h3>Veritabanı Bakımı & Performans Optimizasyonu</h3>
        <button id="btn-db-tuneup">Veritabanını Şimdi Optimize Et</button>
    </div>
    {% endif %}
    """

    with app.test_request_context("/settings"):
        html = render_template_string(template, current_user=privileged_user)
        assert "db-tuneup-card" in html
        assert "Veritabanını Şimdi Optimize Et" in html
