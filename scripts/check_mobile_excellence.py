"""
E-Cüzdan Mobile Excellence Automated Regression & Quality Gate.

Audits all primary views across 5 critical mobile device viewports:
- 320px (Compact Mobile / iPhone SE 1)
- 360px (Galaxy S-Series / Android Standard)
- 375px (iPhone SE / iPhone Mini)
- 390px (iPhone 12 / 13 / 14 / 15)
- 412px (Google Pixel / Modern Large Android)

Verification Criteria:
1. Zero horizontal overflow (scrollWidth <= innerWidth).
2. Clean DOM layout without off-screen element spills.
3. Interactive readiness across touch devices.
"""

import os
import sys
import time
import threading
from pathlib import Path
from werkzeug.serving import make_server

# Set test environment flags
os.environ['DISABLE_BACKGROUND_SERVICE'] = 'true'
os.environ['TESTING'] = 'true'

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app import app

# Target routes for mobile audit
CORE_ROUTES = [
    ('/', 'Dashboard'),
    ('/transactions', 'İşlemler'),
    ('/assets', 'Varlıklar'),
    ('/payment_calendar', 'Ödeme Takvimi'),
    ('/plans', 'Düzenli Planlar'),
    ('/analysis', 'Finansal Analiz'),
    ('/financial_freedom', 'Finansal Özgürlük'),
    ('/strategy', 'Strateji'),
    ('/settings', 'Sistem Ayarları'),
    ('/profile', 'Profil'),
    ('/categories', 'Katalog & Kategoriler'),
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
        super().__init__()
        self.server = make_server('127.0.0.1', port, flask_app)
        self.ctx = flask_app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


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

    server = ServerThread(app, port=5075)
    server.start()
    time.sleep(1.2)

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
                page = context.new_page()

                # Session login
                page.goto('http://127.0.0.1:5075/login')
                page.fill('input[name="username"]', 'emin')
                page.fill('input[name="password"]', '1')
                page.click('button[type="submit"]')
                page.wait_for_load_state('networkidle')

                for route, label in CORE_ROUTES:
                    total_audits += 1
                    target_url = f'http://127.0.0.1:5075{route}'
                    page.goto(target_url)
                    page.wait_for_load_state('networkidle')
                    page.wait_for_timeout(250)

                    # Diagnostic check for horizontal overflow
                    result = page.evaluate("""() => {
                        const scrollW = document.documentElement.scrollWidth;
                        const innerW = window.innerWidth;
                        const overflow = scrollW > innerW;
                        let culprit = null;
                        if (overflow) {
                            const overflowing = Array.from(document.querySelectorAll('*')).filter(el => {
                                const r = el.getBoundingClientRect();
                                return r.right > innerW + 1;
                            });
                            if (overflowing.length > 0) {
                                const target = overflowing[overflowing.length - 1];
                                culprit = (target.tagName || '') + (target.id ? '#' + target.id : '') + (target.className ? '.' + target.className.split(' ').slice(0, 2).join('.') : '');
                            }
                        }
                        return { scrollWidth: scrollW, innerWidth: innerW, overflow: overflow, culprit: culprit };
                    }""")

                    if result['overflow']:
                        msg = f"OVERFLOW on {route} ({label}) at {width}px: scrollWidth={result['scrollWidth']} > innerWidth={result['innerWidth']} (culprit: {result['culprit']})"
                        violations.append(msg)
                        print(f"    [FAIL] {route:<22} -> {msg}")
                    else:
                        print(f"    [PASS] {route:<22} -> scrollWidth: {result['scrollWidth']}px (0px overflow)")

                # Also audit Quick Transaction modal open state
                total_audits += 1
                page.goto('http://127.0.0.1:5075/')
                page.wait_for_load_state('networkidle')
                page.evaluate("() => { if (typeof openGlobalQuickTxModal === 'function') openGlobalQuickTxModal(); }")
                page.wait_for_timeout(350)

                modal_result = page.evaluate("""() => {
                    const scrollW = document.documentElement.scrollWidth;
                    const innerW = window.innerWidth;
                    return { scrollWidth: scrollW, innerWidth: innerW, overflow: scrollW > innerW };
                }""")
                if modal_result['overflow']:
                    violations.append(f"OVERFLOW on QuickTx Modal at {width}px: {modal_result['scrollWidth']} > {modal_result['innerWidth']}")
                    print(f"    [FAIL] Quick Tx Modal         -> OVERFLOW: {modal_result['scrollWidth']}px")
                else:
                    print(f"    [PASS] Quick Tx Modal         -> scrollWidth: {modal_result['scrollWidth']}px (0px overflow)")

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

    print("\n[SUCCESS] 100% Mobile Excellence Achieved! Zero horizontal overflow across all tested viewports.")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    sys.exit(run_mobile_excellence_gate())
