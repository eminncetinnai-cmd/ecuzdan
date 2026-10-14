# Schema Migration & Backup Compatibility Guide

## 🎯 Overview

Bu guide, schema değişikliklerinin yedekleme sistemine etkisini minimize etmek ve profesyonel bir yaklaşım sunmak için tasarlanmıştır.

## 🏗️ Profesyonel Mimari Yaklaşımlar

### 1. **Schema Versioning System**

**Mevcut Durum:** ✅ İyi
- `database/schema_version.py` dosyasında tek kaynak
- SCHEMA_VERSION = "v25.1"
- BackupValidationService tarafından kullanılıyor

**İyileştirmeler:**
- Semantic versioning (Major.Minor.Patch)
- Migration history tracking
- Schema change log

### 2. **Automated Compatibility Testing**

**Yeni Dosyalar:**
- `tests/integration/test_schema_compatibility.py` - Otomatik uyumluluk testleri
- `.github/workflows/schema-compatibility.yml` - CI/CD integration

**Test Kapsamı:**
- Export/import round-trip testleri
- Encrypted backup compatibility
- Foreign key integrity
- Schema metadata completeness
- Replace mode compatibility

### 3. **Migration Strategy Pattern**

**Yeni Dosya:** `infrastructure/database/migration.py`

**Strateji Türleri:**
- `AddColumnMigration` - Yeni sütun ekleme (geriye uyumlu)
- `RemoveColumnMigration` - Sütun kaldırma (veri kaybı riski)
- `RenameColumnMigration` - Sütun yeniden adlandırma

**Kullanım:**
```python
migration_service.register_migration(
    AddColumnMigration("v25.0", "v25.1", {
        "users": ["email_verified", "auth_provider"],
        "transactions": ["source_type"]
    })
)
```

### 4. **Schema Change Detection**

**Yeni Scriptler:**
- `scripts/check_schema_version.py` - Otomatik değişiklik tespiti
- `scripts/generate_schema_report.py` - Detaylı raporlama

**CI/CD Integration:**
```bash
# Her push'ta otomatik çalışır
python scripts/check_schema_version.py
python scripts/generate_schema_report.py
```

### 5. **Pre-Deployment Checklist**

**Schema Değişikliği Öncesi:**
- [ ] SCHEMA_VERSION güncellendi mi?
- [ ] Migration stratejisi tanımlandı mı?
- [ ] Compatibility testleri geçti mi?
- [ ] Geriye uyumluluk test edildi mi?
- [ ] Yedekleme testi yapıldı mı?
- [ ] Rollback planı hazır mı?

## 🔄 Schema Değişikliği Süreci

### Adım 1: Değişiklik Planlama
```bash
# Mevcut schema incele
python scripts/generate_schema_report.py
```

### Adım 2: Version Güncelleme
```python
# database/schema_version.py
SCHEMA_VERSION = "v25.2"  # Minor version bump
```

### Adım 3: Migration Stratejisi
```python
# infrastructure/database/migration.py veya config
migration_service.register_migration(
    AddColumnMigration("v25.1", "v25.2", {
        "users": ["new_field"]
    })
)
```

### Adım 4: Test
```bash
# Compatibility testleri
pytest tests/integration/test_schema_compatibility.py -v

# Manual export/import test
python scripts/test_backup_roundtrip.py
```

### Adım 5: Deployment
```bash
# Pre-deployment check
python scripts/check_schema_version.py

# Deploy
git push origin main
```

## 🚨 Risk Senaryoları ve Çözümler

### Senaryo 1: Sütun Kaldırma
**Risk:** Veri kaybı
**Çözüm:** 
- Migration stratejisi ile eski yedeklerden data'yı preserve et
- Soft delete pattern kullan
- Migration log'u tut

### Senaryo 2: Tablo Yapısı Değişikliği
**Risk:** Foreign key violations
**Çözüm:**
- ValidationService FK kontrolü
- Migration'da data transformasyonu
- Atomic rollback guarantee

### Senaryo 3: Data Type Değişikliği
**Risk:** Data truncation/loss
**Çözüm:**
- Type coercion in validation
- Migration'da data conversion
- Fallback values

## 📊 Monitoring & Alerting

### Key Metrics:
- Schema version drift
- Backup compatibility rate
- Migration success rate
- Import failure reasons

### Alerts:
- Schema değişikliği tespiti
- Compatibility test failure
- Migration failure
- Unexpected schema validation errors

## 🛠️ Maintenance

### Weekly:
- Schema compatibility testleri çalıştır
- Migration log'larını review et
- Backup validation check

### Monthly:
- Schema version history review
- Migration stratejilerini optimize et
- Documentation update

### Quarterly:
- Full disaster recovery test
- Migration procedure audit
- Backup retention policy review

## 📝 Best Practices

1. **Never Breaking Changes:** Mümkün olduğunca geriye uyumlu değişiklikler yap
2. **Incremental Migrations:** Büyük değişiklikleri küçük adımlara böl
3. **Test Everything:** Her değişiklik otomatik test kapsamında olmalı
4. **Document Everything:** Migration stratejilerini dokümantasyonla
5. **Monitor Continuously:** Uyumluluk metriklerini izle

## 🔗 İlgili Dosyalar

- `database/schema_version.py` - Schema version management
- `infrastructure/backup/validation.py` - Validation service
- `infrastructure/database/migration.py` - Migration strategies
- `infrastructure/database/management.py` - Import/export logic
- `tests/integration/test_schema_compatibility.py` - Compatibility tests
- `scripts/check_schema_version.py` - Change detection
- `scripts/generate_schema_report.py` - Schema reporting

## 🆘 Troubleshooting

### Import Failure:
```bash
# Schema raporu oluştur
python scripts/generate_schema_report.py

# Validation testi
pytest tests/integration/test_schema_compatibility.py::test_current_schema_exports_and_imports_successfully -v
```

### Migration Failure:
```bash
# Migration loglarını kontrol et
tail -f logs/migration.log

# Manual migration test
python scripts/test_migration.py --from v25.0 --to v25.1
```

### Compatibility Issues:
```bash
# Full validation
python -c "
from infrastructure.backup.validation import BackupValidationService
from infrastructure.database.management import export_database_to_json
import json

data = json.loads(export_database_to_json(encrypt=False))
service = BackupValidationService()
print(service.validate_backup_compatibility(data))
"
```

---

Bu guide, profesyonel bir yaklaşım ile schema değişikliklerinin yedekleme sistemine etkisini minimize eder. Her değişiklik öncesi bu checklist'i takip etmek önerilir.