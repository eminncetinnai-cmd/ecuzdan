"""
Sprint 04 — GL Kodu Normalizasyon Migration
===========================================
Amaç: Mevcut kategorilerin GL kodlarını TDMS/IFRS standartlarına uygun hesap
      grubu aralıklarına taşımak ve eksik standart kategorileri eklemek.

GL Kodu Aralıkları (Türk Muhasebe Standartları + IFRS):
  GLR-6xxx → Gelir   (Gelir Tablosu — 600 hesap grubu)
  GDR-7xxx → Gider   (Gider Tablosu — 700 hesap grubu)
  YTR-1xxx → Yatırım (Bilanço Varlık — 100 hesap grubu)

Çalıştırma:
  python database/migrations/sprint04_gl_code_normalization.py
"""

import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from shared.db import db
from models import Category

logger = logging.getLogger("Migration_Sprint04")
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


# ---------------------------------------------------------------------------
# Standart Kategori Kataloğu (Sabit GL Kodlarıyla)
# ---------------------------------------------------------------------------
STANDARD_CATEGORIES = [
    # ── GELİR (GLR-6xxx) ────────────────────────────────────────────────────
    ('Maaş / Ücret Geliri',          'Gelir',    'GLR-6001'),
    ('Serbest Meslek / Danışmanlık', 'Gelir',    'GLR-6002'),
    ('Kira Geliri',                  'Gelir',    'GLR-6003'),
    ('Temettü Geliri',               'Gelir',    'GLR-6004'),
    ('Faiz Geliri',                  'Gelir',    'GLR-6005'),
    ('Yatırım / Sermaye Kazancı',    'Gelir',    'GLR-6006'),
    ('Ek Gelir / Yan İş',            'Gelir',    'GLR-6007'),
    ('Prim & İkramiye',              'Gelir',    'GLR-6008'),
    ('Avans',                        'Gelir',    'GLR-6009'),
    ('Sosyal Yardım & Destek',       'Gelir',    'GLR-6010'),
    ('Diğer Gelirler',               'Gelir',    'GLR-6011'),

    # ── GİDER (GDR-7xxx) ────────────────────────────────────────────────────
    ('Konut & Kira',                 'Gider',    'GDR-7001'),
    ('Faturalar (Elektrik/Su/Gaz)',  'Gider',    'GDR-7002'),
    ('Market & Gıda',                'Gider',    'GDR-7003'),
    ('Ulaşım & Yakıt',               'Gider',    'GDR-7004'),
    ('Sağlık & Eczane',              'Gider',    'GDR-7005'),
    ('Eğitim & Kurslar',             'Gider',    'GDR-7006'),
    ('Giyim & Aksesuar',             'Gider',    'GDR-7007'),
    ('Eğlence & Restoran',           'Gider',    'GDR-7008'),
    ('Sigorta Primleri',             'Gider',    'GDR-7009'),
    ('Kredi Ödemeleri',              'Gider',    'GDR-7010'),
    ('Kredi Kartı Ödemesi',          'Gider',    'GDR-7011'),
    ('Abonelikler',                  'Gider',    'GDR-7012'),
    ('Kişisel Bakım',                'Gider',    'GDR-7013'),
    ('Vergi & Devlet Ödemeleri',     'Gider',    'GDR-7014'),
    ('Bağış & Yardım',               'Gider',    'GDR-7015'),
    ('Aylık Sabit Gider',            'Gider',    'GDR-7016'),
    ('Çocuk & Aile Giderleri',       'Gider',    'GDR-7017'),
    ('Seyahat & Konaklama',          'Gider',    'GDR-7018'),
    ('Teknoloji & Elektronik',       'Gider',    'GDR-7019'),
    ('Diğer Giderler',               'Gider',    'GDR-7020'),

    # ── YATIRIM (YTR-1xxx) ──────────────────────────────────────────────────
    ('Yatırıma Aktarılan',           'Yatırım',  'YTR-1001'),
    ('Hisse Senedi Alımı',           'Yatırım',  'YTR-1002'),
    ('Fon & BES Alımı',              'Yatırım',  'YTR-1003'),
    ('Altın Alımı',                  'Yatırım',  'YTR-1004'),
    ('Kripto Para Alımı',            'Yatırım',  'YTR-1005'),
    ('Gayrimenkul Alımı',            'Yatırım',  'YTR-1006'),
    ('Nakit & Mevduat',              'Yatırım',  'YTR-1007'),
    ('Diğer Yatırımlar',             'Yatırım',  'YTR-1008'),
]

# Eski addan yeni ada eşleme (backward compatibility)
LEGACY_NAME_MAP = {
    'Maaş':          'Maaş / Ücret Geliri',
    'Ek Gelir':      'Ek Gelir / Yan İş',
    'Kira':          'Kira Geliri',
    'Vergi':         'Vergi & Devlet Ödemeleri',
    'Kredi':         'Kredi Ödemeleri',
    'Kredi Kartı':   'Kredi Kartı Ödemesi',
}


def _is_standard_gl(code: str) -> bool:
    """Kodun TDMS/IFRS standartına uygun olup olmadığını kontrol eder."""
    if not code:
        return False
    return (
        code.startswith('GLR-6') or
        code.startswith('GDR-7') or
        code.startswith('YTR-1')
    )


def run_sprint04_migration():
    """GL Kodu Normalizasyon ve Standart Kategori Ekleme Migration'ı"""
    logger.info("=" * 60)
    logger.info("Sprint 04 — GL Kodu Normalizasyon Migration Başlatılıyor")
    logger.info("=" * 60)

    created = 0
    updated = 0
    skipped = 0

    # 1. Standart kategorileri ekle / GL kodlarını güncelle
    for cat_name, cat_type, gl_code in STANDARD_CATEGORIES:
        existing = Category.query.filter_by(name=cat_name).first()

        if not existing:
            # Eski adıyla mı var?
            old_name = next((k for k, v in LEGACY_NAME_MAP.items() if v == cat_name), None)
            if old_name:
                existing = Category.query.filter_by(name=old_name).first()
                if existing:
                    logger.info(f"  ♻️  Eski kategori taşınıyor: '{old_name}' → '{cat_name}'")
                    existing.name = cat_name
                    existing.type = cat_type
                    existing.code = gl_code
                    updated += 1
                    continue

            # Yoksa yeni oluştur
            new_cat = Category(name=cat_name, type=cat_type, code=gl_code)
            db.session.add(new_cat)
            logger.info(f"  ✅ Yeni kategori oluşturuldu: {gl_code} — {cat_name} ({cat_type})")
            created += 1
        else:
            if not _is_standard_gl(existing.code):
                old_code = existing.code
                existing.code = gl_code
                existing.type = cat_type  # tip tutarsızlığını da düzelt
                logger.info(f"  🔄 GL kodu güncellendi: '{cat_name}': {old_code} → {gl_code}")
                updated += 1
            else:
                skipped += 1

    db.session.commit()

    # 2. Geri kalan eski formatlı kodları düzelt (GLR-xxxx → GLR-6xxx vb.)
    all_cats = Category.query.all()
    bulk_fixed = 0
    for cat in all_cats:
        if not _is_standard_gl(cat.code):
            if cat.type == 'Gelir':
                base, prefix = 6000, 'GLR'
            elif cat.type == 'Gider':
                base, prefix = 7000, 'GDR'
            else:
                base, prefix = 1000, 'YTR'

            old_code = cat.code
            cat.code = f"{prefix}-{base + cat.id}"
            logger.info(f"  🔧 Bulk fix: '{cat.name}': {old_code} → {cat.code}")
            bulk_fixed += 1

    db.session.commit()

    logger.info("=" * 60)
    logger.info(f"Migration Tamamlandı:")
    logger.info(f"  ✅ Yeni oluşturulan kategori : {created}")
    logger.info(f"  🔄 Güncellenen kategori      : {updated}")
    logger.info(f"  🔧 Bulk GL kodu düzeltmesi   : {bulk_fixed}")
    logger.info(f"  ⏭️  Zaten uygun (atlandı)     : {skipped}")
    logger.info("=" * 60)


if __name__ == "__main__":
    from app import app
    with app.app_context():
        run_sprint04_migration()
