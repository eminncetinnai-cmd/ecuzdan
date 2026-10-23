"""Calendar Feed Service (iCalendar RFC 5545 Generator & Subscription Token Handler).

Pure business logic service for generating standard iCalendar (.ics) feeds
and secure HMAC subscription tokens for Apple Calendar, Google Calendar, and Outlook.
"""

from datetime import date, datetime, timedelta
import hashlib
import hmac
from typing import Any, Dict, List, Optional, Tuple


def generate_calendar_token(user_id: int, tenant_id: str, secret_key: str) -> str:
    """Generates a secure, deterministic HMAC token for live calendar subscription feed."""
    msg = f"{user_id}:{tenant_id or 'default'}"
    sig = hmac.new(
        secret_key.encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:24]
    return f"{user_id}.{sig}"


def verify_calendar_token(token: str, secret_key: str, get_user_fn: Any) -> Optional[Tuple[int, str]]:
    """Verifies HMAC calendar token and returns (user_id, tenant_id) if valid."""
    if not token or "." not in token:
        return None
    try:
        parts = token.split(".", 1)
        user_id = int(parts[0])
        user = get_user_fn(user_id)
        if not user:
            return None
        tenant_id = getattr(user, "tenant_id", "default")
        expected = generate_calendar_token(user_id, tenant_id, secret_key)
        if hmac.compare_digest(token, expected):
            return user_id, tenant_id
        return None
    except Exception:
        return None


def escape_ical_text(text: Optional[str]) -> str:
    """Escapes special characters in text according to RFC 5545."""
    if not text:
        return ""
    text = str(text).replace("\r\n", "\n").replace("\r", "\n")
    # Escape backslash first, then semicolon, comma, and newline
    text = text.replace("\\", "\\\\")
    text = text.replace(";", r"\;")
    text = text.replace(",", r"\,")
    text = text.replace("\n", r"\n")
    return text


def format_ical_date(d: Any) -> str:
    """Converts a date object or ISO string to YYYYMMDD."""
    if isinstance(d, (date, datetime)):
        return d.strftime("%Y%m%d")
    s = str(d).strip()
    if len(s) >= 10:
        return s[:10].replace("-", "")
    return datetime.now().strftime("%Y%m%d")


def add_days_to_date_str(date_str: str, days: int = 1) -> str:
    """Calculates end date for all-day iCal event (DTEND = DTSTART + 1 day)."""
    try:
        s = date_str[:10]
        dt = datetime.strptime(s, "%Y-%m-%d").date()
        return (dt + timedelta(days=days)).strftime("%Y%m%d")
    except Exception:
        return format_ical_date(date_str)


class CalendarFeedService:
    """Generates standard iCalendar (RFC 5545) feeds from domain events."""

    @staticmethod
    def build_feed(events: List[Dict[str, Any]], cal_name: str = "E-Cüzdan Ödeme & Hatırlatıcı Takvimi") -> str:
        """Constructs an RFC 5545 compliant VCALENDAR document."""
        now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//E-Cuzdan//Personal Finance Calendar//TR",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:{escape_ical_text(cal_name)}",
            "X-WR-TIMEZONE:Europe/Istanbul",
            "REFRESH-INTERVAL;VALUE=DURATION:P1D",
            "X-PUBLISHED-TTL:P1D",
        ]

        for ev in events:
            uid = ev.get("uid") or f"ev-{hashlib.md5(str(ev).encode('utf-8')).hexdigest()[:16]}@e-cuzdan"
            summary = escape_ical_text(ev.get("summary", "Hatırlatıcı"))
            desc = escape_ical_text(ev.get("description", ""))
            start_date_iso = ev.get("date") or datetime.now().strftime("%Y-%m-%d")
            dtstart = format_ical_date(start_date_iso)
            dtend = add_days_to_date_str(start_date_iso, 1)

            event_lines = [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now_stamp}",
                f"DTSTART;VALUE=DATE:{dtstart}",
                f"DTEND;VALUE=DATE:{dtend}",
                f"SUMMARY:{summary}",
            ]
            if desc:
                event_lines.append(f"DESCRIPTION:{desc}")
            if ev.get("category"):
                event_lines.append(f"CATEGORIES:{escape_ical_text(ev['category'])}")

            event_lines.extend([
                "STATUS:CONFIRMED",
                "TRANSP:TRANSPARENT",
                "END:VEVENT",
            ])
            lines.extend(event_lines)

        lines.append("END:VCALENDAR")
        lines.append("")  # Trailing CRLF
        return "\r\n".join(lines)
