from datetime import date
from domain.planning.services.calendar_feed_service import (
    CalendarFeedService,
    add_days_to_date_str,
    escape_ical_text,
    format_ical_date,
    generate_calendar_token,
    verify_calendar_token,
)


def test_generate_and_verify_calendar_token():
    secret = "test-super-secret-key-12345"

    class FakeUser:
        def __init__(self, uid, tenant_id):
            self.id = uid
            self.tenant_id = tenant_id

    users = {
        42: FakeUser(42, "tenant-alpha"),
        99: FakeUser(99, "default"),
    }

    token = generate_calendar_token(42, "tenant-alpha", secret)
    assert token.startswith("42.")

    # Verification success
    verified = verify_calendar_token(token, secret, lambda uid: users.get(uid))
    assert verified == (42, "tenant-alpha")

    # Tampered token
    tampered = token[:-2] + "xx"
    assert verify_calendar_token(tampered, secret, lambda uid: users.get(uid)) is None

    # Unknown user
    assert verify_calendar_token("999.invalidtoken", secret, lambda uid: users.get(uid)) is None

    # Invalid format
    assert verify_calendar_token("", secret, lambda uid: users.get(uid)) is None
    assert verify_calendar_token("invalid", secret, lambda uid: users.get(uid)) is None


def test_escape_ical_text():
    raw = "Ev Kirası; Ayın 15'i, Not: Dikkat\\Önemli\nİkinci satır"
    escaped = escape_ical_text(raw)
    assert r"\;" in escaped
    assert r"\," in escaped
    assert r"\\" in escaped
    assert r"\n" in escaped
    assert "\r" not in escaped


def test_format_ical_date_and_add_days():
    assert format_ical_date("2026-11-15") == "20261115"
    assert format_ical_date(date(2026, 12, 1)) == "20261201"
    assert add_days_to_date_str("2026-11-15", 1) == "20261116"
    assert add_days_to_date_str("2026-12-31", 1) == "20270101"


def test_build_feed_valid_rfc5545():
    events = [
        {
            "uid": "rem-1@e-cuzdan",
            "summary": "🎂 Ali Doğum Günü",
            "description": "Özel Gün Hatırlatıcısı",
            "date": "2026-11-05",
            "category": "Doğum Günü",
        },
        {
            "uid": "plan-10-20261115@e-cuzdan",
            "summary": "💳 Ev Kirası (15.000,00 ₺)",
            "description": "Kira ödemesi",
            "date": "2026-11-15",
            "category": "Konut",
        },
    ]

    feed = CalendarFeedService.build_feed(events, cal_name="E-Cüzdan Test Takvimi")

    assert "BEGIN:VCALENDAR" in feed
    assert "VERSION:2.0" in feed
    assert "PRODID:-//E-Cuzdan//Personal Finance Calendar//TR" in feed
    assert "X-WR-CALNAME:E-Cüzdan Test Takvimi" in feed
    assert "BEGIN:VEVENT" in feed
    assert "UID:rem-1@e-cuzdan" in feed
    assert "SUMMARY:🎂 Ali Doğum Günü" in feed
    assert "DTSTART;VALUE=DATE:20261105" in feed
    assert "DTEND;VALUE=DATE:20261106" in feed
    assert "UID:plan-10-20261115@e-cuzdan" in feed
    assert "SUMMARY:💳 Ev Kirası (15.000\\,00 ₺)" in feed
    assert "END:VEVENT" in feed
    assert "END:VCALENDAR" in feed
    assert feed.endswith("\r\n")
