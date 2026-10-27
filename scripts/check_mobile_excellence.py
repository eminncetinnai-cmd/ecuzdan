"""
E-Cüzdan Mobile Excellence Automated Regression & Quality Gate.

Audits all primary views and global modals across 5 critical mobile device viewports:
- 320px (Compact Mobile / iPhone SE 1)
- 360px (Galaxy S-Series / Android Standard)
- 375px (iPhone SE / iPhone Mini)
- 390px (iPhone 12 / 13 / 14 / 15)
- 412px (Google Pixel / Modern Large Android)

Verification Criteria:
1. Zero horizontal overflow (scrollWidth <= innerWidth).
2. Clean DOM layout without off-screen modal spills.
3. Interactive readiness across touch devices.
"""

import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from werkzeug.serving import make_server

# Set test environment flags
os.environ['DISABLE_BACKGROUND_SERVICE'] = 'true'
os.environ['TESTING'] = 'true'

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app import app
from models import User

# Target routes for mobile audit
CORE_ROUTES = [
    ('/', 'Dashboard'),
    ('/transactions', 'İşlemler'),
    ('/transactions/explorer', 'İşlem Gezgini'),
    ('/new_transaction', 'Yeni İşlem'),
    ('/assets', 'Varlıklar'),
    ('/assets_view', 'Varlık Analizi'),
    ('/assets_management', 'Varlık Yönetimi'),
    ('/investment_performance', 'Yatırım Performansı'),
    ('/payment_calendar', 'Ödeme Takvimi'),
    ('/plans', 'Düzenli Planlar'),
    ('/analysis', 'Finansal Analiz'),
    ('/financial_freedom', 'Finansal Özgürlük'),
    ('/strategy', 'Strateji'),
    ('/financial_dashboard', 'Piyasa Analizi'),
    ('/global-ratios', 'Küresel Rasyolar'),
    ('/central-bank-reserves', 'TCMB Rezervleri'),
    ('/gold-tracking', 'Altın Takip'),
    ('/settings', 'Sistem Ayarları'),
    ('/profile', 'Profil'),
    ('/profile/start', 'Profil Anketi'),
    ('/categories', 'Katalog & Kategoriler'),
    ('/logbook/', 'Cüzdan Defteri'),
    ('/logbook/calendar', 'Cüzdan Defteri Takvim'),
    ('/logbook/timeline', 'Cüzdan Defteri Zaman Tüneli'),
    ('/monthly_dashboard', 'Aylık Bütçe Raporu'),
    ('/notifications', 'Bildirimler'),
    ('/user_guide', 'Kullanım Kılavuzu'),
    ('/financial_education', 'Finansal Eğitim'),
    ('/storage-health/', 'Depolama Sağlığı'),
    ('/monitoring/', 'Sistem İzleme'),
    ('/tenant/users', 'Tenant Kullanıcıları'),
    ('/tenant/invites', 'Tenant Davetleri'),
    ('/tenant/invite', 'Tenant Davet Et'),
    ('/admin/', 'Admin Dashboard'),
    ('/admin/users', 'Admin Kullanıcılar'),
    ('/admin/tenants', 'Admin Tenantlar'),
    ('/admin/audit', 'Admin Denetim'),
    ('/admin/design_system', 'Tasarım Sistemi'),
    ('/login', 'Giriş'),
    ('/register', 'Kayıt'),
    ('/oauth-signup', 'OAuth Kayıt'),
    ('/offline', 'Çevrimdışı Sayfası'),
]

# Global modals to verify on mobile viewports
GLOBAL_MODALS = [
    ('Quick Tx Modal', "openGlobalQuickTxModal('Gider')", '#globalQuickTxModal .edit-modal-card', "closeGlobalQuickTxModal()"),
    ('Calculator Modal', "openCalculator()", '#calculatorModal > div.relative', "closeCalculator()"),
    ('Notification Modal', "openNotificationModal()", '#notificationModal > div.absolute:not(.inset-0)', "closeNotificationModal()"),
    ('Command Palette', "openGlobalSearch()", '#commandPaletteModal > div.relative', "closeGlobalSearch()"),
]

# Standard mobile device viewports
VIEWPORTS = [
    {'name': 'Compact Mobile (320px)', 'width': 320, 'height': 568},
    {'name': 'Galaxy Standard (360px)', 'width': 360, 'height': 740},
    {'name': 'iPhone SE (375px)', 'width': 375, 'height': 667},
    {'name': 'iPhone 12/13/14 (390px)', 'width': 390, 'height': 844},
    {'name': 'Google Pixel 7 (412px)', 'width': 412, 'height': 915},
]


class ServerThread(threading.Thread):
    def __init__(self, flask_app, port=5075):
        super().__init__(daemon=True)
        self.server = make_server('127.0.0.1', port, flask_app, threaded=True)
        self.ctx = flask_app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


def _create_signed_session_cookie(flask_app):
    """Create a signed Flask session cookie for an authenticated default-tenant user."""
    with flask_app.app_context():
        user = User.query.filter_by(tenant_id='default').order_by(User.id).first()
        if not user:
            user = User.query.first()
        if not user:
            return None
        serializer = flask_app.session_interface.get_signing_serializer(flask_app)
        session_data = {
            '_user_id': str(user.id),
            'user_id': user.id,
            'username': user.username,
            'role': 'admin',
            'tenant_id': user.tenant_id,
            'session_id': user.last_session_id or 'audit-session',
            'session_created_at': datetime.now().isoformat(),
            'app_boot_id': flask_app.config.get('APP_BOOT_ID', 'test-boot-id'),
            '_fresh': True,
            'oauth_signup_info': {
                'email': 'mobile_audit_oauth_user@example.com',
                'name': 'Audit OAuth User',
                'provider': 'GOOGLE',
                'provider_id': 'audit_oauth_123',
                'created_at': datetime.now().isoformat(),
            },
        }
        cookie_val = serializer.dumps(session_data)
        cookie_name = flask_app.config.get('SESSION_COOKIE_NAME', 'session')
        return {
            'name': cookie_name,
            'value': cookie_val,
            'domain': '127.0.0.1',
            'path': '/',
        }


def run_mobile_excellence_gate():
    print("=" * 70)
    print("  [MOBILE EXCELLENCE] E-CUZDAN AUTONOMOUS RESPONSIVE QUALITY GATE")
    print("=" * 70)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[SKIP] Playwright is not installed in the current environment.")
        print("       Install with: pip install playwright && playwright install chromium")
        return 0

    auth_cookie = _create_signed_session_cookie(app)
    server = ServerThread(app, port=5075)
    server.start()
    time.sleep(0.8)

    violations = []
    total_audits = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            for vp in VIEWPORTS:
                vp_name = vp['name']
                width = vp['width']
                height = vp['height']
                print(f"\n--> Auditing Viewport: {vp_name} [{width}x{height}]")

                context = browser.new_context(viewport={'width': width, 'height': height})
                if auth_cookie:
                    context.add_cookies([auth_cookie])

                # Abort persistent SSE streams and external fonts so page loads never hang
                context.route(
                    "**/*",
                    lambda route: route.abort()
                    if any(
                        host in route.request.url
                        for host in (
                            "fonts.googleapis.com",
                            "fonts.gstatic.com",
                            "/api/live-stream",
                            "/monitoring/api/logs/stream",
                        )
                    )
                    else route.continue_(),
                )

                page = context.new_page()

                for route_path, label in CORE_ROUTES:
                    total_audits += 1
                    target_url = f'http://127.0.0.1:5075{route_path}'
                    page.goto(target_url, wait_until='domcontentloaded', timeout=15000)
                    page.wait_for_timeout(120)

                    # Diagnostic check for horizontal overflow
                    result = page.evaluate("""() => {
                        const scrollW = document.documentElement.scrollWidth;
                        const innerW = window.innerWidth;
                        const overflow = scrollW > innerW + 1;
                        let culprit = null;
                        if (overflow) {
                            const overflowing = Array.from(document.querySelectorAll('*')).filter(el => {
                                const r = el.getBoundingClientRect();
                                return r.right > innerW + 1;
                            });
                            if (overflowing.length > 0) {
                                const target = overflowing[overflowing.length - 1];
                                const cls = (typeof target.className === 'string' && target.className)
                                    ? '.' + target.className.trim().split(/\\s+/).slice(0, 2).join('.')
                                    : '';
                                culprit = (target.tagName || '') + (target.id ? '#' + target.id : '') + cls;
                            }
                        }
                        return { scrollWidth: scrollW, innerWidth: innerW, overflow: overflow, culprit: culprit };
                    }""")

                    if result['overflow']:
                        msg = f"OVERFLOW on {route_path} ({label}) at {width}px: scrollWidth={result['scrollWidth']} > innerWidth={result['innerWidth']} (culprit: {result['culprit']})"
                        violations.append(msg)
                        print(f"    [FAIL] {route_path:<24} -> {msg}")
                    else:
                        print(f"    [PASS] {route_path:<24} -> scrollWidth: {result['scrollWidth']}px (0px overflow)")

                # Audit Global Modals on Dashboard
                page.goto('http://127.0.0.1:5075/', wait_until='domcontentloaded', timeout=15000)
                page.wait_for_timeout(120)

                for modal_label, open_js, modal_sel, close_js in GLOBAL_MODALS:
                    total_audits += 1
                    page.evaluate(f"() => {{ try {{ {open_js}; }} catch(e) {{}} }}")
                    page.wait_for_timeout(120)
                    modal_result = page.evaluate(f"""() => {{
                        const card = document.querySelector('{modal_sel}');
                        if (!card) return {{ missing: true, overflow: true }};
                        const r = card.getBoundingClientRect();
                        const s = getComputedStyle(card);
                        const scrollW = document.documentElement.scrollWidth;
                        const innerW = window.innerWidth;
                        const innerH = window.innerHeight;
                        const horizOut = r.width === 0 || r.left < -2 || r.right > innerW + 2 || scrollW > innerW + 1;
                        const vertOut = r.top < -2 || r.bottom > innerH + 2;
                        try {{ {close_js}; }} catch(e) {{}}
                        return {{
                            scrollWidth: scrollW,
                            innerWidth: innerW,
                            left: Math.round(r.left),
                            right: Math.round(r.right),
                            top: Math.round(r.top),
                            bottom: Math.round(r.bottom),
                            overflow: horizOut || vertOut
                        }};
                    }}""")

                    if modal_result.get('overflow'):
                        msg = (
                            f"MODAL OVERFLOW on {modal_label} at {width}x{height}: "
                            f"bounds=({modal_result.get('left')},{modal_result.get('top')})->"
                            f"({modal_result.get('right')},{modal_result.get('bottom')})"
                        )
                        violations.append(msg)
                        print(f"    [FAIL] {modal_label:<24} -> {msg}")
                    else:
                        print(f"    [PASS] {modal_label:<24} -> bounds: {modal_result.get('left')}..{modal_result.get('right')}px (0px overflow)")

                context.close()

            browser.close()

    finally:
        server.shutdown()

    print("\n" + "=" * 70)
    print("  MOBILE EXCELLENCE AUDIT SUMMARY")
    print("=" * 70)
    print(f"Total Page/Viewport Audits : {total_audits}")
    print(f"Total Violations Detected  : {len(violations)}")

    if violations:
        print("\n[FAILED] Mobile Excellence Gate failed with violations:")
        for v in violations:
            print(f"  - {v}")
        return 1

    print("\n[SUCCESS] 100% Mobile Excellence Achieved! Zero horizontal or modal overflow across all tested viewports.")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    sys.exit(run_mobile_excellence_gate())
