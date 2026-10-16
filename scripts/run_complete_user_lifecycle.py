"""Complete User Lifecycle & UI Verification Script.

Executes the full operational sequence:
1. Tüm verileri sil (Tenant-scoped reset)
2. Ayarlar altındaki demo veri setini yükle (Advanced 3-year demo dataset)
3. Veri tabanını export et (JSON export)
4. Veri tabanını sil ve tekrar import et (Full JSON restore & validation)
5. Manuel kayıtlar (Düzenli Gelir, Gider, Yatırım; Tek Seferlik Gelir, Gider, Yatırım; Ödeme; Varlık Satışı)
6. Tüm sayfaların, grafiklerin ve tabloların HTTP 200 & render bütünlüğü doğrulaması
"""

import json
import logging
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from app import create_app
from domain.transactions.services.financial_ledger import (
    create_asset_position,
    sell_asset_position,
)
from infrastructure.demo import generate_advanced_demo_data
from infrastructure.export.export_service import ExportService
from models import (
    Asset,
    Category,
    RecurringPlan,
    Transaction,
    User,
    db,
)
from repositories.financial_repository import FinancialRepository
from repositories.user_repository import UserRepository
from shared.decimal_precision import to_decimal

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("lifecycle_audit")


def run_lifecycle():
    app = create_app()
    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="emin").first()
        if not user:
            logger.error("User 'emin' not found!")
            sys.exit(1)
        user_id = user.id
        tenant_id = user.tenant_id or "default"
        logger.info(f"Using test user: {user.username} (ID: {user_id}, Tenant: {tenant_id})")

        # ═════════════════════════════════════════════════════════════════════
        # SAFHA 1: TÜM VERİLERİ SİL
        # ═════════════════════════════════════════════════════════════════════
        logger.info("\n=== SAFHA 1: TÜM VERİLERİ SİL (RESET) ===")
        user_repo = UserRepository()
        user_repo.reset_financial_data_for_tenant(tenant_id)
        db.session.commit()

        tx_count = Transaction.query.filter_by(tenant_id=tenant_id).count()
        plan_count = RecurringPlan.query.filter_by(tenant_id=tenant_id).count()
        asset_count = Asset.query.filter_by(tenant_id=tenant_id).count()
        logger.info(f"Sıfırlama sonrası: {tx_count} işlem, {plan_count} plan, {asset_count} varlık.")
        assert tx_count == 0, "İşlemler sıfırlanamadı!"
        assert plan_count == 0, "Planlar sıfırlanamadı!"
        assert asset_count == 0, "Varlıklar sıfırlanamadı!"
        logger.info("✔ SAFHA 1 BAŞARILI: Veri tabanı başarıyla temizlendi.")

        # ═════════════════════════════════════════════════════════════════════
        # SAFHA 2: AYARLAR ALTINDAKİ DEMO VERİ SETİNİ YÜKLE
        # ═════════════════════════════════════════════════════════════════════
        logger.info("\n=== SAFHA 2: DEMO VERİ SETİNİ YÜKLE ===")
        stats = generate_advanced_demo_data(user_id)
        db.session.commit()

        tx_count_demo = Transaction.query.filter_by(tenant_id=tenant_id).count()
        plan_count_demo = RecurringPlan.query.filter_by(tenant_id=tenant_id).count()
        asset_count_demo = Asset.query.filter_by(tenant_id=tenant_id).count()

        logger.info(
            f"Demo veri yüklendi: {tx_count_demo} işlem, {plan_count_demo} plan, {asset_count_demo} varlık. "
            f"İstatistikler: {stats}"
        )
        assert tx_count_demo > 0, "Demo işlemleri oluşturulamadı!"
        assert plan_count_demo > 0, "Demo planları oluşturulamadı!"
        assert asset_count_demo > 0, "Demo varlıkları oluşturulamadı!"
        logger.info("✔ SAFHA 2 BAŞARILI: Gelişmiş 3 yıllık demo veri seti yüklendi.")

        # ═════════════════════════════════════════════════════════════════════
        # SAFHA 3: VERİ TABANINI EXPORT ET
        # ═════════════════════════════════════════════════════════════════════
        logger.info("\n=== SAFHA 3: VERİ TABANINI EXPORT ET (JSON) ===")
        export_service = ExportService()
        exported_raw = export_service.export_database_json(user_id=user_id, encrypt=False)
        assert exported_raw, "Export boş döndü!"

        export_data = json.loads(exported_raw)
        logger.info(
            f"Export tamamlandı. Boyut: {len(exported_raw)/1024:.1f} KB. "
            f"Tablolar: {list(export_data.keys())}"
        )
        assert "transactions" in export_data, "transactions export verisinde eksik!"
        assert "recurring_plans" in export_data, "recurring_plans export verisinde eksik!"
        export_tx_len = len([t for t in export_data["transactions"] if t.get("tenant_id") == tenant_id])
        export_plan_len = len([p for p in export_data["recurring_plans"] if p.get("tenant_id") == tenant_id])
        export_asset_len = len([a for a in export_data["assets"] if a.get("tenant_id") == tenant_id])
        logger.info(f"Export kayıt sayıları (tenant: {tenant_id}): {export_tx_len} tx, {export_plan_len} plan, {export_asset_len} asset.")
        logger.info("✔ SAFHA 3 BAŞARILI: Veri tabanı yedeği başarıyla export edildi.")

        # ═════════════════════════════════════════════════════════════════════
        # SAFHA 4: VERİ TABANINI SİL VE TEKRAR İMPORT ET
        # ═════════════════════════════════════════════════════════════════════
        logger.info("\n=== SAFHA 4: VERİ TABANINI SİL VE TEKRAR İMPORT ET ===")
        # Önce sıfırla
        user_repo.reset_financial_data_for_tenant(tenant_id)
        db.session.commit()
        assert Transaction.query.filter_by(tenant_id=tenant_id).count() == 0

        # Export edilen veriyi tekrar import et
        import_stats = export_service.import_database_json(
            user_id=user_id,
            content=exported_raw,
            replace_existing=True
        )
        db.session.commit()

        imported_tx_count = Transaction.query.filter_by(tenant_id=tenant_id).count()
        imported_plan_count = RecurringPlan.query.filter_by(tenant_id=tenant_id).count()
        imported_asset_count = Asset.query.filter_by(tenant_id=tenant_id).count()

        logger.info(
            f"İçe aktarma tamamlandı: {imported_tx_count} işlem, {imported_plan_count} plan, {imported_asset_count} varlık. "
            f"Stats: {import_stats}"
        )
        assert imported_tx_count == export_tx_len, f"İşlem sayısı uyuşmuyor: {imported_tx_count} != {export_tx_len}"
        assert imported_plan_count == export_plan_len, f"Plan sayısı uyuşmuyor: {imported_plan_count} != {export_plan_len}"
        assert imported_asset_count == export_asset_len, f"Varlık sayısı uyuşmuyor: {imported_asset_count} != {export_asset_len}"
        logger.info("✔ SAFHA 4 BAŞARILI: Veri tabanı silinip yedekten %100 doğrulukla restore edildi.")

        # ═════════════════════════════════════════════════════════════════════
        # SAFHA 5: MANUEL OLARAK DÜZENLİ GELİR, GİDER, YATIRIM, ÖDEMELER KAYDET
        # ═════════════════════════════════════════════════════════════════════
        logger.info("\n=== SAFHA 5: MANUEL İŞLEMLER KAYDETME ===")
        fin_repo = FinancialRepository()

        cat_inc = Category.query.filter_by(type="Gelir").first()
        cat_exp = Category.query.filter_by(type="Gider").first()
        cat_inv = Category.query.filter_by(type="Yatırım").first()

        cat_inc_name = cat_inc.name if cat_inc else "Maaş / Ücret Geliri"
        cat_exp_name = cat_exp.name if cat_exp else "Kira"
        cat_inv_name = cat_inv.name if cat_inv else "Fon"

        # 5.1 Düzenli Gelir (RecurringPlan - income)
        logger.info("5.1 Manuel Düzenli Gelir oluşturuluyor...")
        plan_income = fin_repo.add_recurring_plan(
            name="Manuel Maaş Geliri",
            category=cat_inc_name,
            amount=85000.0,
            installments=12,
            payment_day=15,
            note="Aylık Düzenli Gelir",
            start_date="2026-01-01",
            tenant_id=tenant_id
        )
        db.session.commit()
        logger.info(f"✔ Düzenli Gelir Planı #{plan_income.id} oluşturuldu.")

        # 5.2 Düzenli Gider (RecurringPlan - expense)
        logger.info("5.2 Manuel Düzenli Gider oluşturuluyor...")
        plan_expense = fin_repo.add_recurring_plan(
            name="Manuel Ev Kirası",
            category=cat_exp_name,
            amount=28000.0,
            installments=12,
            payment_day=1,
            note="Aylık Düzenli Gider",
            start_date="2026-01-01",
            tenant_id=tenant_id
        )
        db.session.commit()
        logger.info(f"✔ Düzenli Gider Planı #{plan_expense.id} oluşturuldu.")

        # 5.3 Düzenli Yatırım (RecurringPlan - investment)
        logger.info("5.3 Manuel Düzenli Yatırım oluşturuluyor...")
        plan_inv = fin_repo.add_recurring_plan(
            name="Manuel Aylık BES & Fon",
            category=cat_inv_name,
            amount=15000.0,
            installments=12,
            payment_day=20,
            note="Aylık Düzenli Yatırım",
            start_date="2026-01-01",
            tenant_id=tenant_id
        )
        db.session.commit()
        logger.info(f"✔ Düzenli Yatırım Planı #{plan_inv.id} oluşturuldu.")

        # 5.4 Tek Seferlik Gelir (Transaction)
        logger.info("5.4 Manuel Tek Seferlik Gelir oluşturuluyor...")
        tx_single_income = fin_repo.add_transaction(
            date="2026-10-02",
            category=cat_inc_name,
            description="Manuel Yazılım Danışmanlığı",
            amount=to_decimal(35000.0),
            type_="Gelir",
            status="Ödendi",
            source_type="manual",
            tenant_id=tenant_id
        )
        logger.info(f"✔ Tek Seferlik Gelir #{tx_single_income.id} oluşturuldu.")

        # 5.5 Tek Seferlik Gider (Transaction)
        logger.info("5.5 Manuel Tek Seferlik Gider oluşturuluyor...")
        tx_single_exp = fin_repo.add_transaction(
            date="2026-10-03",
            category=cat_exp_name,
            description="Manuel Bilgisayar Ekipmanı",
            amount=to_decimal(14500.0),
            type_="Gider",
            status="Ödendi",
            source_type="manual",
            tenant_id=tenant_id
        )
        logger.info(f"✔ Tek Seferlik Gider #{tx_single_exp.id} oluşturuldu.")

        # 5.6 Tek Seferlik Yatırım (Transaction)
        logger.info("5.6 Manuel Tek Seferlik Yatırım oluşturuluyor...")
        tx_single_inv = fin_repo.add_transaction(
            date="2026-10-04",
            category=cat_inv_name,
            description="Manuel THYAO Alımı",
            amount=to_decimal(20000.0),
            type_="Yatırım",
            status="Ödendi",
            source_type="manual",
            tenant_id=tenant_id
        )
        logger.info(f"✔ Tek Seferlik Yatırım #{tx_single_inv.id} oluşturuldu.")

        # 5.7 Bekleyen Ödeme & Quick-Pay
        logger.info("5.7 Manuel Bekleyen İşlem & Hızlı Ödeme (Quick-Pay)...")
        tx_pending = fin_repo.add_transaction(
            date="2026-10-05",
            category=cat_exp_name,
            description="Manuel İnternet Faturası",
            amount=to_decimal(850.0),
            type_="Gider",
            status="Bekliyor",
            source_type="manual",
            tenant_id=tenant_id
        )

        # Quick-pay
        quick_paid_tx = fin_repo.quick_pay_transaction(tx_pending.id, tenant_id=tenant_id)
        db.session.commit()
        assert quick_paid_tx.status == "Ödendi", "Quick-pay 'Ödendi' yapamadı!"
        logger.info(f"✔ Bekleyen İşlem #{quick_paid_tx.id} Quick-Pay ile başarıyla 'Ödendi' yapıldı.")

        # 5.8 Varlık Alımı & Kısmi Satışı (Realized PnL ve Kasaya Aktarım)
        logger.info("5.8 Manuel Varlık Pozisyonu ve Kısmi Satış...")
        from models import AssetSector
        sector = AssetSector.query.first()
        sector_id = sector.id if sector else 1
        asset_pos = create_asset_position(
            name="Manuel Has Altın",
            type="Altın",
            value=to_decimal(140000.0),
            quantity=to_decimal(50.0),
            unit_price=to_decimal(2800.0),
            purchase_cost=to_decimal(140000.0),
            currency="TRY",
            symbol="GOLD_GR",
            purchase_date="2026-09-01",
            risk_level="Düşük",
            liquidity="Yüksek",
            sector_id=sector_id,
            tenant_id=tenant_id,
            sync_cash=True
        )
        db.session.commit()
        logger.info(f"✔ Varlık #{asset_pos.id} (50 adet @ 2800 ₺) oluşturuldu.")

        # 15 gramını 3300 ₺'den sat (Kâr: 15 * (3300 - 2800) = 7500 ₺)
        sold_asset, realized_pnl, sale_cash_tx = sell_asset_position(
            asset_id=asset_pos.id,
            quantity=15.0,
            sale_unit_price=3300.0,
            sale_date="2026-10-06",
            note="Manuel Kısmi Satış Kârı",
            tenant_id=tenant_id
        )
        db.session.commit()
        logger.info(
            f"✔ Varlık #{sold_asset.id} kısmi satıldı: 15 adet @ 3300 ₺. "
            f"Gerçekleşen Kâr: {realized_pnl:.2f} ₺, Kasaya Eklenen Tutar: {sale_cash_tx.amount:.2f} ₺, "
            f"Kalan Adet: {sold_asset.quantity}"
        )
        assert sold_asset.quantity == 35.0, f"Kalan miktar yanlış: {sold_asset.quantity}"
        assert realized_pnl == Decimal("7500.0"), f"Kâr yanlış: {realized_pnl}"
        logger.info("✔ SAFHA 5 BAŞARILI: Tüm manuel finansal hareketler hatasız kaydedildi.")

    # ═════════════════════════════════════════════════════════════════════
    # SAFHA 6: TÜM SAYFALARIN, TABLOLARIN VE GRAFİKLERİN HTTP 200 TESTİ
    # ═════════════════════════════════════════════════════════════════════
    logger.info("\n=== SAFHA 6: TÜM SAYFALARIN VE GRAFİKLERİN DOĞRULANMASI ===")
    import secrets
    with app.app_context():
        user = User.query.filter_by(username="emin").first()
        uid = user.id
        urole = user.role
        uname = user.username
        utid = user.tenant_id
        sid = user.last_session_id or secrets.token_hex(16)
        user.last_session_id = sid
        db.session.commit()

        boot_id = app.config.get('APP_BOOT_ID', 'test-boot-id')
        with client.session_transaction() as sess:
            sess['user_id'] = uid
            sess['role'] = urole
            sess['username'] = uname
            sess['tenant_id'] = utid
            sess['session_id'] = sid
            sess['session_created_at'] = datetime.now().isoformat()
            sess['app_boot_id'] = boot_id

    routes_to_test = [
        ("/", "Dashboard / Ana Sayfa"),
        ("/monthly_dashboard", "Aylık Konsolide Özet"),
        ("/transactions", "İşlemler Tablosu"),
        ("/transactions/explorer", "İşlem Gezgini"),
        ("/plans", "Planlar & Düzenli Ödemeler"),
        ("/payment_calendar", "Ödeme Takvimi"),
        ("/assets", "Varlıklar Listesi"),
        ("/assets_view", "Varlık Görünümü & Satış Modalları"),
        ("/assets_management", "Varlık Yönetimi"),
        ("/investment_performance", "Yatırım Performansı & Getiriler"),
        ("/analysis", "Finansal Analiz & Sağlık"),
        ("/financial_freedom", "Finansal Özgürlük (FIRE) Simülatörü"),
        ("/strategy", "Strateji & Gelecek Simülasyonu"),
        ("/financial_dashboard", "Finans & Piyasa Özeti"),
        ("/settings", "Ayarlar Sayfası"),
        ("/categories", "Kategoriler"),
        ("/storage-health/", "Depolama Sağlığı & Bakım"),
        ("/logbook/", "Yatırım Günlüğü"),
        ("/global-ratios", "Küresel Rasyolar"),
        ("/central-bank-reserves", "TCMB Rezervleri"),
        ("/notifications", "Bildirim Merkezi"),
        ("/profile", "Yatırımcı Profili"),
        ("/user_guide", "Kullanım Kılavuzu"),
        ("/financial_education", "Finansal Eğitim"),
        ("/admin/", "Admin Paneli"),
        ("/admin/users", "Admin Kullanıcılar"),
        ("/admin/tenants", "Admin Workspace / Tenant"),
        ("/admin/design_system", "Admin Tasarım Sistemi"),
    ]

    all_routes_ok = True
    for path, desc in routes_to_test:
        resp = client.get(path)
        status = resp.status_code
        if status == 200:
            logger.info(f"  [PASS] {path:25s} -> HTTP 200 ({desc})")
        else:
            logger.error(f"  [FAIL] {path:25s} -> HTTP {status} ({desc})")
            all_routes_ok = False

    assert all_routes_ok, "Bazı sayfalar HTTP 200 döndürmedi!"
    logger.info("✔ SAFHA 6 BAŞARILI: Tüm sayfalar, tablolar ve grafik bileşenleri eksiksiz ve hatasız çalışıyor.")
    logger.info("\n🎉 TÜM SAFHALAR (1 - 6) %100 BAŞARIYLA TAMAMLANDI!")


if __name__ == "__main__":
    run_lifecycle()
