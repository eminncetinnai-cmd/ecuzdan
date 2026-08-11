import json

from infrastructure.database.management import export_database_to_json, import_database_from_json
from models import Category, Transaction, db


def test_export_database(app):
    """Veritabanı dışa aktarma testini gerçekleştirir."""
    with app.app_context():
        # Örnek veri ekle
        cat = Category(name="Test Kategori", type="Gider")
        db.session.add(cat)
        db.session.commit()

        json_data = export_database_to_json()
        data = json.loads(json_data)

        assert "categories" in data
        assert any(c["name"] == "Test Kategori" for c in data["categories"])

def test_import_database(app):
    """Veritabanı içe aktarma testini gerçekleştirir."""
    with app.app_context():
        # Mevcut verileri temizle (test ortamında)
        Transaction.query.delete()
        Category.query.delete()
        db.session.commit()

        test_data = {
            "categories": [
                {"id": 999, "name": "Import Test", "type": "Gelir"}
            ],
            "transactions": [
                {
                    "id": 888,
                    "date": "2026-01-01",
                    "category": "Import Test",
                    "description": "Test İşlemi",
                    "type": "Gelir",
                    "status": "Ödendi",
                    "amount": 1500.0,
                    "tenant_id": "default"
                }
            ]
        }

        json_content = json.dumps(test_data)
        success, message = import_database_from_json(json_content)

        assert success is True

        # Veritabanından kontrol et
        cat = db.session.get(Category, 999)
        assert cat is not None
        assert cat.name == "Import Test"

        trans = db.session.get(Transaction, 888)
        assert trans is not None
        assert trans.amount == 1500.0

def test_import_export_integrity(app):
    """Dışa aktarılan verinin tekrar içe aktarıldığında tutarlılığını test eder."""
    with app.app_context():
        # 1. Durum: Veri oluştur
        cat = Category(name="Integrity Test", type="Yatırım")
        db.session.add(cat)
        db.session.commit()

        # 2. Durum: Dışa aktar
        exported_json = export_database_to_json()

        # 3. Durum: Veriyi sil
        db.session.delete(cat)
        db.session.commit()
        assert Category.query.filter_by(name="Integrity Test").first() is None

        # 4. Durum: Geri yükle
        success, _ = import_database_from_json(exported_json)
        assert success is True

        # 5. Durum: Kontrol et
        restored_cat = Category.query.filter_by(name="Integrity Test").first()
        assert restored_cat is not None
        assert restored_cat.type == "Yatırım"
