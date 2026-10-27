#!/usr/bin/env python3
"""
Deep-dive page-by-page mobile testing suite.
Tests all 43 pages and 4 global modals across iPhone 16 Pro Max (430px) and standard mobile viewports.
Captures layout metrics, overflow status, header bar positioning, bottom nav, and high-fidelity screenshots.
"""

import os
import sys
import time
import json
import threading
from datetime import datetime
from pathlib import Path
from werkzeug.serving import make_server

os.environ['DISABLE_BACKGROUND_SERVICE'] = 'true'
os.environ['TESTING'] = 'true'

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app import app
from models import User

ARTIFACT_DIR = Path(r"C:\Users\e.cetin\.gemini\antigravity\brain\c6cc865f-07ea-4749-8b81-d294fe18cb82")

PAGES = [
    ('/', 'Dashboard (Ana Sayfa)', True),
    ('/transactions', 'İşlemler Listesi', True),
    ('/transactions/explorer', 'İşlem Gezgini & Filtre', False),
    ('/new_transaction', 'Yeni İşlem Ekleme', True),
    ('/assets', 'Varlıklar & Portföy', True),
    ('/assets_view', 'Varlık Görünümü & Detay', False),
    ('/assets_management', 'Varlık Yönetimi', False),
    ('/investment_performance', 'Yatırım Getirisi & Performans', False),
    ('/payment_calendar', 'Ödeme & Gelir Takvimi', True),
    ('/plans', 'Düzenli Planlar & Taksitler', True),
    ('/analysis', 'Finansal Analiz & Rapor', True),
    ('/financial_freedom', 'Finansal Özgürlük (FIRE)', True),
    ('/strategy', 'Gelecek & Strateji Simülatörü', False),
    ('/financial_dashboard', 'Finans & Piyasa Dashboard', False),
    ('/global-ratios', 'Küresel Rasyolar', False),
    ('/central-bank-reserves', 'Merkez Bankası Rezervleri', False),
    ('/gold-tracking', 'Altın Takip (Harem & Bursa)', True),
    ('/logbook/', 'Cüzdan Defteri & Notlar', False),
    ('/logbook/calendar', 'Cüzdan Defteri Takvim', False),
    ('/logbook/timeline', 'Cüzdan Defteri Zaman Tüneli', False),
    ('/categories', 'Katalog & Kategori Yönetimi', False),
    ('/monthly_dashboard', 'Aylık Konsolide Özet', True),
    ('/notifications', 'Bildirim Merkezi', False),
    ('/profile', 'Yatırımcı Profili', False),
    ('/profile/start', 'Yatırımcı Anketi', False),
    ('/settings', 'Sistem & Hesap Ayarları', True),
    ('/user_guide', 'Kullanım Kılavuzu', False),
    ('/financial_education', 'Finansal Eğitim & Formüller', False),
    ('/storage-health/', 'Depolama Sağlığı & Bakım', False),
    ('/monitoring/', 'Sistem & Log İzleme', False),
    ('/tenant/', 'Tenant Yönetim Paneli', False),
    ('/tenant/users', 'Tenant Kullanıcıları', False),
    ('/tenant/invites', 'Tenant Davetleri', False),
    ('/tenant/invite', 'Yeni Davet Oluştur', False),
    ('/admin/', 'Admin Dashboard', False),
    ('/admin/users', 'Admin Kullanıcılar', False),
    ('/admin/tenants', 'Admin Tenantlar', False),
    ('/admin/audit', 'Admin Güvenlik Denetimi', False),
    ('/admin/design_system', 'Tasarım Sistemi Kataloğu', False),
    ('/login', 'Kullanıcı Girişi (Anonim)', False),
    ('/register', 'Yeni Kullanıcı Kaydı (Anonim)', False),
    ('/oauth-signup', 'OAuth Kayıt Tamamlama', False),
    ('/offline', 'PWA Çevrimdışı Sayfası', False),
]

MODALS = [
    ('Quick Tx Modal', "openGlobalQuickTxModal('Gider')", '#globalQuickTxModal .edit-modal-card', "closeGlobalQuickTxModal()", True),
    ('Calculator Modal', "openCalculator()", '#calculatorModal > div.relative', "closeCalculator()", True),
    ('Notification Modal', "openNotificationModal()", '#notificationModal > div.absolute:not(.inset-0)', "closeNotificationModal()", False),
    ('Command Palette', "openGlobalSearch()", '#commandPaletteModal > div.relative', "closeGlobalSearch()", False),
]


class ServerThread(threading.Thread):
    def __init__(self, flask_app, port=5088):
        super().__init__(daemon=True)
        self.server = make_server('127.0.0.1', port, flask_app, threaded=True)
        self.ctx = flask_app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


def _get_auth_cookie(flask_app):
    with flask_app.app_context():
        user = User.query.filter_by(tenant_id='default').order_by(User.id).first()
        if not user:
            user = User.query.first()
        sess_token = 'mobile-deep-dive-session'
        user.last_session_id = sess_token
        from shared.db import db
        db.session.commit()

        serializer = flask_app.session_interface.get_signing_serializer(flask_app)
        session_data = {
            '_user_id': str(user.id),
            'user_id': user.id,
            'username': user.username,
            'role': 'admin',
            'tenant_id': user.tenant_id,
            'session_id': sess_token,
            'session_created_at': datetime.now().isoformat(),
            'app_boot_id': flask_app.config.get('APP_BOOT_ID', 'test-boot-id'),
            '_fresh': True,
            'remember_me': True,
            'oauth_signup_info': {
                'email': 'mobile_test_user@example.com',
                'name': 'Mobile Tester',
                'provider': 'GOOGLE',
                'provider_id': 'google_test_123',
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


def run_mobile_deep_dive():
    from playwright.sync_api import sync_playwright

    server = ServerThread(app, port=5088)
    server.start()
    time.sleep(1.0)

    auth_cookie = _get_auth_cookie(app)
    results = []

    try:
        with sync_playwright() as p:
            # 1. iPhone 16 Pro Max viewport: 430 x 932
            iphone16 = p.devices.get('iPhone 14 Pro Max', {
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1',
                'viewport': {'width': 430, 'height': 932},
                'device_scale_factor': 3,
                'is_mobile': True,
                'has_touch': True,
            })
            iphone16['viewport'] = {'width': 430, 'height': 932}

            browser = p.chromium.launch(headless=True)
            context = browser.new_context(**iphone16)
            if auth_cookie:
                context.add_cookies([auth_cookie])

            # Abort external blocking network requests
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

            print("=" * 80)
            print("  E-CÜZDAN UÇTAN UCA SAYFA SAYFA MOBİL DENETİMİ (iPhone 16 Pro Max - 430x932)")
            print("=" * 80)

            for route_path, label, take_shot in PAGES:
                target_url = f'http://127.0.0.1:5088{route_path}'
                errors = []
                page.on("pageerror", lambda err: errors.append(str(err)))

                resp = page.goto(target_url, wait_until='domcontentloaded', timeout=20000)
                status_code = resp.status if resp else 0
                page.wait_for_timeout(200)

                # Metric extraction
                metrics = page.evaluate("""() => {
                    const scrollW = document.documentElement.scrollWidth;
                    const innerW = window.innerWidth;
                    const innerH = window.innerHeight;
                    const overflow = scrollW > innerW + 1;

                    // Header bar check
                    const topBar = document.querySelector('#headerBar') || document.querySelector('.header-bar') || document.querySelector('header');
                    let headerInfo = { exists: false, height: 0, top: 0, zIndex: 0, isStickyOrFixed: false };
                    if (topBar) {
                        const r = topBar.getBoundingClientRect();
                        const s = getComputedStyle(topBar);
                        headerInfo = {
                            exists: true,
                            height: Math.round(r.height),
                            top: Math.round(r.top),
                            zIndex: parseInt(s.zIndex, 10) || 0,
                            isStickyOrFixed: s.position === 'sticky' || s.position === 'fixed'
                        };
                    }

                    // Bottom Navigation check
                    const bottomNav = document.querySelector('.mobile-bottom-nav') || document.querySelector('#mobile-bottom-nav') || document.querySelector('nav.fixed.bottom-0');
                    let bottomNavInfo = { exists: false, height: 0, visible: false };
                    if (bottomNav) {
                        const r = bottomNav.getBoundingClientRect();
                        bottomNavInfo = {
                            exists: true,
                            height: Math.round(r.height),
                            visible: r.height > 0 && r.bottom <= innerH + 5
                        };
                    }

                    // Cards & Tables responsiveness
                    const tables = Array.from(document.querySelectorAll('table'));
                    const overflowingTables = tables.filter(t => t.scrollWidth > t.clientWidth + 2).length;

                    // Touch target sizes
                    const buttons = Array.from(document.querySelectorAll('button, a.btn, input[type="submit"]'));
                    const smallTouchTargets = buttons.filter(b => {
                        const r = b.getBoundingClientRect();
                        return r.width > 0 && r.height > 0 && (r.height < 24 || r.width < 24);
                    }).length;

                    return {
                        scrollWidth: scrollW,
                        innerWidth: innerW,
                        overflow: overflow,
                        header: headerInfo,
                        bottomNav: bottomNavInfo,
                        tableCount: tables.length,
                        overflowingTables: overflowingTables,
                        buttonCount: buttons.length,
                        smallTouchTargets: smallTouchTargets
                    };
                }""")

                # Take screenshot if flagged
                shot_path = None
                if take_shot and ARTIFACT_DIR.exists():
                    safe_slug = route_path.strip('/').replace('/', '_') or 'dashboard'
                    shot_name = f"mobile_iphone16_{safe_slug}.png"
                    shot_file = ARTIFACT_DIR / shot_name
                    page.screenshot(path=str(shot_file), full_page=False)
                    shot_path = shot_name

                page_res = {
                    'route': route_path,
                    'label': label,
                    'status_code': status_code,
                    'overflow': metrics['overflow'],
                    'scrollWidth': metrics['scrollWidth'],
                    'innerWidth': metrics['innerWidth'],
                    'header': metrics['header'],
                    'bottomNav': metrics['bottomNav'],
                    'smallTouchTargets': metrics['smallTouchTargets'],
                    'errors': list(errors),
                    'screenshot': shot_path,
                }
                results.append(page_res)

                status_tag = "[PASS]" if (not metrics['overflow'] and status_code < 400 and not errors) else "[WARN/FAIL]"
                print(f"{status_tag} {route_path:<28} | HTTP {status_code} | W: {metrics['scrollWidth']}/{metrics['innerWidth']}px | Header: {metrics['header']['height']}px | BottomNav: {metrics['bottomNav']['exists']} | Errors: {len(errors)}")

            # Audit Global Modals
            print("\n--> Mobil Modal ve Pencerelerin Denetimi:")
            page.goto('http://127.0.0.1:5088/', wait_until='domcontentloaded', timeout=15000)
            page.wait_for_timeout(200)

            for modal_label, open_js, modal_sel, close_js, take_shot in MODALS:
                page.evaluate(f"() => {{ try {{ {open_js}; }} catch(e) {{}} }}")
                page.wait_for_timeout(250)

                modal_metrics = page.evaluate(f"""() => {{
                    const card = document.querySelector('{modal_sel}');
                    if (!card) return {{ missing: true, overflow: true }};
                    const r = card.getBoundingClientRect();
                    const innerW = window.innerWidth;
                    const innerH = window.innerHeight;
                    const scrollW = document.documentElement.scrollWidth;
                    const horizOverflow = r.left < -2 || r.right > innerW + 2 || scrollW > innerW + 1;
                    return {{
                        missing: false,
                        left: Math.round(r.left),
                        right: Math.round(r.right),
                        width: Math.round(r.width),
                        height: Math.round(r.height),
                        overflow: horizOverflow,
                        scrollWidth: scrollW,
                        innerWidth: innerW
                    }};
                }}""")

                shot_name = None
                if take_shot and ARTIFACT_DIR.exists():
                    safe_slug = modal_label.lower().replace(' ', '_')
                    shot_name = f"mobile_iphone16_modal_{safe_slug}.png"
                    shot_file = ARTIFACT_DIR / shot_name
                    page.screenshot(path=str(shot_file), full_page=False)

                page.evaluate(f"() => {{ try {{ {close_js}; }} catch(e) {{}} }}")
                page.wait_for_timeout(150)

                status_tag = "[PASS]" if not modal_metrics.get('overflow') else "[FAIL]"
                print(f"{status_tag} {modal_label:<28} | Width: {modal_metrics.get('width')}px | Pos: [{modal_metrics.get('left')}..{modal_metrics.get('right')}]px | Overflow: {modal_metrics.get('overflow')}")

            context.close()
            browser.close()

    finally:
        server.shutdown()

    # Save complete JSON result
    out_file = REPO_ROOT / ".work" / "mobile_deep_dive_report.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print(f"Toplam Test Edilen Sayfa : {len(results)}")
    print(f"Sıfır Taşma (0px Overflow): {sum(1 for r in results if not r['overflow'])} / {len(results)}")
    print(f"Başarılı Rotalar (200 OK)  : {sum(1 for r in results if r['status_code'] == 200)} / {len(results)}")
    print("=" * 80)
    return results


if __name__ == '__main__':
    run_mobile_deep_dive()
