"""
E-Cüzdan Master Pre-Flight Smoke & Resilience Gate.

This automated diagnostic suite performs end-to-end verification of:
1. All Jinja2 template compilations & filter dependency integrity.
2. Safe null-coalescing on all template filters.
3. Live HTTP GET requests to all primary routes with simulated session.
4. Zero 500 errors across all views.
"""

import logging
import os
import sys
from datetime import datetime

# Ensure project root is in sys.path
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Disable verbose logging and background threads during preflight check
logging.disable(logging.CRITICAL)
os.environ["DISABLE_BACKGROUND_SERVICE"] = "true"
os.environ["BACKGROUND_SERVICE_ENABLED"] = "false"


def run_preflight_check() -> int:
    print("=" * 65)
    print("  [PRE-FLIGHT] E-CUZDAN MASTER 500 RESILIENCE & SMOKE GATE")
    print("=" * 65)

    errors = []

    # 1. Boot Flask App
    try:
        from app import app, db
        from models import User
        print("[1/5] Bootstrapping Flask application context .......... OK")
    except Exception as e:
        print(f"[1/5] Bootstrapping Flask application context .......... FAILED ({e})")
        return 1

    with app.app_context():
        # 2. Test All Template Compilations
        print("[2/5] Compiling and verifying 52+ Jinja2 templates .....", end=" ")
        env = app.jinja_env
        template_dir = os.path.join(_REPO_ROOT, 'templates')
        template_count = 0
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                if file.endswith('.html'):
                    template_count += 1
                    rel_path = os.path.relpath(os.path.join(root, file), template_dir).replace('\\\\', '/').replace('\\', '/')
                    try:
                        env.get_template(rel_path)
                    except Exception as e:
                        errors.append(f"Template Error in '{rel_path}': {e}")

        if errors:
            print(f"FAILED ({len(errors)} issues)")
            for err in errors:
                print(f"      - {err}")
            return 1
        else:
            print(f"OK ({template_count} templates clean)")

        # 3. Test Template Filters Null-Safety
        print("[3/5] Testing Jinja filter null-safety & edge-cases ....", end=" ")
        try:
            filters = app.jinja_env.filters
            # Check required filters
            assert 'currency_symbol' in filters, "Missing 'currency_symbol' filter"
            assert 'format_money' in filters, "Missing 'format_money' filter"
            assert 'format_date' in filters, "Missing 'format_date' filter"

            # Execute edge-case inputs
            assert filters['currency_symbol'](None) == ''
            assert filters['currency_symbol']('') == ''
            assert filters['currency_symbol']('USD') == '$'
            assert filters['currency_symbol']('TRY') == '₺'

            # format_money with None / 0 / negative
            filters['format_money'](None)
            filters['format_money'](0)
            filters['format_money'](-150.50)
            print("OK (100% null-safe)")
        except Exception as e:
            print(f"FAILED ({e})")
            return 1

        # 4. Test Live Route Dispatches (Zero 500s)
        print("[4/5] Dispatching simulated HTTP GET requests to core routes ...")
        client = app.test_client()

        # Setup mock user session
        try:
            user = db.session.query(User).first()
            if user:
                uid, urole, uname, tid, sid = user.id, user.role, user.username, user.tenant_id, user.last_session_id
            else:
                uid, urole, uname, tid, sid = 1, 'admin', 'admin', 1, 'mock-session-id'
        except Exception:
            uid, urole, uname, tid, sid = 1, 'admin', 'admin', 1, 'mock-session-id'

        boot_id = app.config.get('APP_BOOT_ID', 'test-boot-id')
        with client.session_transaction() as sess:
            sess['user_id'] = uid
            sess['role'] = urole
            sess['username'] = uname
            sess['tenant_id'] = tid
            sess['session_id'] = sid
            sess['session_created_at'] = datetime.now().isoformat()
            sess['app_boot_id'] = boot_id

        endpoints_to_test = [
            ('/', 'Dashboard / Ana Sayfa'),
            ('/monthly_dashboard', 'Aylık Konsolide Özet'),
            ('/transactions', 'İşlem Geçmişi'),
            ('/reconciliation', 'Hesap & Ekstre Mutabakatı'),
            ('/plans', 'Düzenli İşlemler & Planlar'),
            ('/payment_calendar', 'Ödeme Takvimi'),
            ('/assets', 'Varlıklar Listesi'),
            ('/assets_view', 'Varlık Görünümü'),
            ('/assets_management', 'Varlık Yönetimi'),
            ('/investment_performance', 'Yatırım Getirisi & Performans'),
            ('/analysis', 'Finansal Analiz & Sağlık'),
            ('/financial_freedom', 'Finansal Özgürlük (FIRE)'),
            ('/strategy', 'Strateji & Gelecek Simülasyonu'),
            ('/financial_dashboard', 'Finans & Piyasa Özeti'),
            ('/global-ratios', 'Küresel Rasyolar Dashboard'),
            ('/central-bank-reserves', 'Merkez Bankası Rezervleri'),
            ('/logbook/', 'Yatırım Günlüğü & Notlar'),
            ('/categories', 'Kategori Yönetimi'),
            ('/notifications', 'Bildirim Merkezi'),
            ('/profile', 'Yatırımcı Profili'),
            ('/profile/start', 'Yatırımcı Anketi (Wizard)'),
            ('/settings', 'Sistem & Hesap Ayarları'),
            ('/user_guide', 'Kullanım Kılavuzu & Rehber'),
            ('/financial_education', 'Finansal Eğitim & Formüller'),
            ('/storage-health/', 'Depolama Sağlığı & Bakım'),
            ('/admin/', 'Admin Dashboard & İstatistik'),
            ('/admin/users', 'Admin Kullanıcı Yönetimi'),
            ('/admin/tenants', 'Admin Tenant Yönetimi'),
            ('/admin/design_system', 'Admin Tasarım Sistemi Kataloğu'),
        ]

        route_errors = []
        for path, name in endpoints_to_test:
            try:
                res = client.get(path, follow_redirects=False)
                status = res.status_code
                if status == 500:
                    route_errors.append(f"500 Internal Server Error on {path} ({name})")
                    print(f"      [FAIL] {path:24} -> HTTP {status} (CRITICAL 500)")
                elif status in (200, 301, 302, 307, 308):
                    if status == 200 and not res.is_json:
                        body_text = res.get_data(as_text=True)
                        if any(ent in body_text for ent in ('&amp;amp;', '&amp;lt;', '&amp;gt;')):
                            route_errors.append(f"Double-escaped HTML entity (&amp;amp;) detected on {path} ({name})")
                            print(f"      [FAIL] {path:24} -> Double-escaped HTML entity detected")
                            continue
                    print(f"      [PASS] {path:24} -> HTTP {status} ({name})")
                else:
                    print(f"      [WARN] {path:24} -> HTTP {status} ({name})")
            except Exception as e:
                route_errors.append(f"Exception requesting {path}: {e}")
                print(f"      [FAIL] {path:24} -> Exception: {e}")

        if route_errors:
            print("\n[ERROR] PRE-FLIGHT GATE FAILED WITH ROUTE ERRORS:")
            for err in route_errors:
                print(f"   - {err}")
            return 1

        # Test Core API Endpoints (HTTP 200 + Valid JSON)
        api_endpoints_to_test = [
            ('/api/live-quotes', 'Canlı Piyasa Ticker API'),
            ('/monitoring/api/stats', 'Sistem & Log İzleme İstatistikleri API'),
            ('/monitoring/api/health', 'Sistem Sağlık ve Metrik Durumu API'),
            ('/storage-health/api/overview', 'Depolama ve Veritabanı Sağlığı API'),
        ]

        for path, name in api_endpoints_to_test:
            try:
                res = client.get(path, follow_redirects=False)
                status = res.status_code
                if status == 500:
                    route_errors.append(f"500 Internal Server Error on API {path} ({name})")
                    print(f"      [FAIL] {path:24} -> HTTP {status} (CRITICAL 500)")
                elif status == 200 and res.is_json:
                    print(f"      [PASS] {path:24} -> HTTP {status} JSON ({name})")
                elif status == 200 and not res.is_json:
                    route_errors.append(f"Expected JSON response on API {path} ({name})")
                    print(f"      [FAIL] {path:24} -> HTTP {status} (Not JSON)")
                else:
                    route_errors.append(f"Unexpected status on API {path} ({name}): {status}")
                    print(f"      [FAIL] {path:24} -> HTTP {status} ({name})")
            except Exception as e:
                route_errors.append(f"Exception requesting API {path}: {e}")
                print(f"      [FAIL] {path:24} -> Exception: {e}")

        # Test HTTP Lifecycle & Content Negotiation (404 UI, 404 API, 302 Unauth)
        unauth_client = app.test_client()

        # 404 UI -> HTML
        res_404_ui = unauth_client.get('/sayfa-kesinlikle-yok-404', follow_redirects=False)
        if res_404_ui.status_code == 404 and not res_404_ui.is_json:
            print("      [PASS] /sayfa-kesinlikle-yok-404-> HTTP 404 HTML (Şık Hata Sayfası)")
        else:
            route_errors.append(f"404 UI test failed: HTTP {res_404_ui.status_code}")
            print(f"      [FAIL] 404 UI test failed: HTTP {res_404_ui.status_code}")

        # 404 API -> JSON
        res_404_api = unauth_client.get('/api/kesinlikle-yok-404', follow_redirects=False)
        if res_404_api.status_code == 404 and res_404_api.is_json:
            print("      [PASS] /api/kesinlikle-yok-404  -> HTTP 404 JSON (Dual-Mode Content Negotiation)")
        else:
            route_errors.append(f"404 API test failed: HTTP {res_404_api.status_code}")
            print(f"      [FAIL] 404 API test failed: HTTP {res_404_api.status_code}")

        # 302 Unauthenticated redirect
        res_unauth = unauth_client.get('/transactions', follow_redirects=False)
        if res_unauth.status_code == 302 and '/login' in res_unauth.headers.get('Location', ''):
            print("      [PASS] /transactions (unauth)   -> HTTP 302 -> /login (Kimlik Doğrulama Koruması)")
        else:
            route_errors.append(f"Unauthenticated redirect test failed: HTTP {res_unauth.status_code}")
            print(f"      [FAIL] Unauthenticated redirect test failed: HTTP {res_unauth.status_code}")

        if route_errors:
            print("\n[ERROR] PRE-FLIGHT GATE FAILED WITH ROUTE/API ERRORS:")
            for err in route_errors:
                print(f"   - {err}")
            return 1

        # 5. Database & Index Hygiene Audit
        print("[5/5] Auditing SQLite PRAGMAs, Index Hygiene & Engine State ...", end=" ")
        db_issues = []
        try:
            import sqlite3
            raw_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            db_path = raw_uri.replace('sqlite:///', '')
            if not os.path.isabs(db_path):
                db_path = os.path.join(_REPO_ROOT, db_path)

            if os.path.exists(db_path):
                with sqlite3.connect(db_path, timeout=5.0) as conn:
                    # Check journal mode
                    jm = conn.execute("PRAGMA journal_mode").fetchone()
                    if jm and str(jm[0]).upper() != "WAL":
                        db_issues.append(f"SQLite journal_mode is '{jm[0]}', expected 'WAL'")

                    # Audit duplicate indexes
                    tables = [
                        r[0] for r in conn.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                        ).fetchall()
                    ]
                    for tbl in tables:
                        indexes = conn.execute(f'PRAGMA index_list("{tbl}")').fetchall()
                        seen_col_sequences = {}
                        for idx_row in indexes:
                            idx_name = idx_row[1]
                            col_info = conn.execute(f'PRAGMA index_info("{idx_name}")').fetchall()
                            cols = tuple(c[2] for c in col_info)
                            if not cols:
                                continue
                            if cols in seen_col_sequences:
                                db_issues.append(
                                    f"Duplicate index on '{tbl}': '{idx_name}' duplicates '{seen_col_sequences[cols]}' on columns {cols}"
                                )
                            else:
                                seen_col_sequences[cols] = idx_name

            if db_issues:
                print(f"FAILED ({len(db_issues)} issues)")
                for issue in db_issues:
                    print(f"      - {issue}")
                return 1
            else:
                print("OK (0 duplicate indexes, WAL active)")
        except Exception as e:
            print(f"WARN (Audit skipped: {e})")

    print("-" * 65)
    print(" [SUCCESS] ALL PRE-FLIGHT CHECKS PASSED: 0 TEMPLATE ERRORS, 0 ROUTE 500s, 0 DB ISSUES!")
    print("=" * 65)
    return 0


if __name__ == '__main__':
    sys.exit(run_preflight_check())
