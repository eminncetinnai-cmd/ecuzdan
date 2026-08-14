# Planlı Gelir Gider Sistemi Analiz Raporu

## Tarih
2026-08-11

## Özet
Planlı gelir gider sistemi için kapsamlı durum analizi, test analizi ve kod kalitesi değerlendirmesi.

---

## 1. Modül Yapısı

### 1.1 Domain Layer

**`domain/planning/services/plan_service.py` (174 satır)**
- Ana plan servisi
- Fonksiyonlar:
  - `save_plan()` - Plan kaydetme/güncelleme
  - `plans_context()` - Plan listesi context
  - `payment_calendar_context()` - Ödeme takvimi
  - `month_data()` - Aylık veriler
  - `daily_balance()` - Günlük bakiye
  - `add_payment()` - Ödeme ekleme

**`domain/planning/services/goal_based_planning.py` (390 satır)**
- Hedef tabanlı yatırım planlama servisi
- Fonksiyonlar:
  - `calculate_goal_progress()` - Hedef ilerlemesi
  - `calculate_required_savings()` - Gerekli tasarruf hesaplama
  - `optimize_goal_achievement()` - Hedef optimizasyonu
  - `create_goal_template()` - Hedef şablonu
  - `get_portfolio_goal_alignment()` - Portföy-hedef uyumu

### 1.2 Application Layer

**`application/planning/planning_application.py` (36 satır)**
- Application service wrapper
- Sadece `PlanService` metodlarını çağırıyor
- Thin wrapper, doğrudan kullanılabilir

### 1.3 Routes Layer

**`routes/plans.py` (210 satır)**
- Route handler
- 7 route:
  - `/plans` - Ana plan sayfası
  - `/payment_calendar` - Ödeme takvimi
  - `/payment_calendar/month_data` - Aylık veri API
  - `/payment_calendar/daily_balance` - Günlük bakiye API
  - `/<int:id>/check-delete` - Silme kontrolü
  - `/<int:id>/delete` - Plan silme
  - `/add_payment` - Ödeme ekleme

---

## 2. Test Analizi

### 2.1 Mevcut Testler

**`tests/unit/test_plan_service.py` (8 test)**
- ✅ `test_plan_service_payment_calendar_context` - Ödeme takvimi context
- ✅ `test_plan_service_month_data` - Aylık veri
- ✅ `test_plan_service_daily_balance` - Günlük bakiye
- ✅ `test_plan_service_add_payment_plan_not_found` - Plan bulunamama hatası
- ✅ `test_plan_service_add_payment_invalid_installment` - Geçersiz taksit
- ✅ `test_plan_service_add_payment_dca_plan` - DCA planı
- ✅ `test_plan_service_plans_context` - Plan context

**`tests/unit/test_plans_routes.py` (10 test)**
- ✅ `test_plans_route_registration_calls_service` - Route kaydı
- ✅ `test_plans_route_save_plan_calls_service` - Plan kaydetme
- ✅ `test_plans_route_error_handling_rollback` - Hata yönetimi
- ✅ `test_payment_calendar_route_calls_service` - Ödeme takvimi
- ✅ `test_month_data_route_validates_params` - Parametre validasyonu
- ✅ `test_delete_plan_route_calls_service` - Plan silme
- ✅ `test_add_payment_route_calls_service` - Ödeme ekleme
- ✅ `test_add_payment_route_validation_error_handling` - Validasyon hatası
- ✅ `test_plans_routes_have_error_handling` - Error handling kontrolü
- ✅ `test_plans_routes_use_jsonify_for_ajax` - AJAX yanıtları

**`tests/unit/demo/test_recurring_plan_factory.py` (8 test)**
- ✅ Factory pattern testleri
- Demo data generation için

### 2.2 Test Coverage Durumu

**Eksik Testler:**
- ❌ `goal_based_planning.py` için hiç test yok
- ❌ `planning_application.py` için hiç test yok
- ❌ Integration test yok
- ❌ Edge case testleri eksik
- ❌ DCA asset transfer logic için detaylı test yok

**Test Kalitesi:**
- ✅ Mock kullanımı doğru
- ✅ Unit test yapısı uygun
- ⚠️ Test coverage düşük (~%30 tahmini)

---

## 3. Gereksiz Kod ve Tekrarlar

### 3.1 Kullanılmayan Kod

**`goal_based_planning.py` (390 satır)**
- ❌ Hiçbir route'da kullanılmıyor
- ❌ Application service'de referans yok
- ❌ UI'da entegrasyon yok
- 💡 Öneri: Kaldır veya entegre et

### 3.2 Thin Wrapper

**`planning_application.py` (36 satır)**
- ❌ Sadece `PlanService` metodlarını çağırıyor
- ❌ Ek işlevsellik yok
- 💡 Öneri: Kaldır, doğrudan `PlanService` kullan

### 3.3 Tekrar Eden Kod

**`MONTH_NAMES_TR` Sabiti**
- `plan_service.py` içinde tanımlı
- Diğer modüllerde benzer sabitler olabilir
- 💡 Öneri: `shared/constants.py`'e taşı

**Mock Setup Tekrarları**
- Testlerde aynı mock setup kodları tekrarlanıyor
- 💡 Öneri: Fixture veya helper function kullan

**Error Handling Pattern**
- Her route'da aynı try-except pattern
- 💡 Öneri: Decorator veya middleware kullan

### 3.4 Tenant ID Handling

**Tutarsız Tenant ID Kullanımı**
- `plan_service.py`: `g.get('tenant_id')` ve parametre
- `routes/plans.py`: `g.get('tenant_id')` ve parametre
- 💡 Öneri: Tek bir helper function kullan

---

## 4. Geliştirme Noktaları

### 4.1 Kritik Öncelik

1. **Goal-Based Planning Entegrasyonu**
   - `goal_based_planning.py` kullanılmıyor
   - UI entegrasyonu gerekli
   - Route'lar eklenebilir

2. **Test Coverage Artırma**
   - `goal_based_planning.py` testleri eksik
   - Integration testler gerekli
   - Edge case testleri ekle

3. **DCA Logic Ayrıştırma**
   - `add_payment()` içinde karmaşık DCA logic
   - Ayrı service'e alınabilir
   - Test edilebilirlik artar

### 4.2 Orta Öncelik

4. **Error Handling Standardizasyonu**
   - Tutarsız error handling
   - Decorator pattern kullan
   - Centralized error handler

5. **Constants Consolidation**
   - `MONTH_NAMES_TR` sabiti
   - `shared/constants.py`'e taşı
   - Tekrarı önle

6. **Application Service Kaldırma**
   - `planning_application.py` thin wrapper
   - Doğrudan `PlanService` kullan
   - Katman azaltma

### 4.3 Düşük Öncelik

7. **Code Duplication Azaltma**
   - Mock setup fixture'ları
   - Helper functions
   - DRY principle

8. **Tenant ID Helper**
   - Tek bir helper function
   - Tutarsızlık giderme
   - Consistency sağla

9. **Documentation**
   - Docstring eksikleri
   - Type hints ekle
   - API documentation

---

## 5. Kod Kalitesi Metrikleri

### 5.1 Modül Boyutları

| Modül | Satır | Durum |
|-------|-------|-------|
| plan_service.py | 174 | ✅ Uygun |
| goal_based_planning.py | 390 | ⚠️ Büyük (kullanılmıyor) |
| planning_application.py | 36 | ⚠️ Thin wrapper |
| routes/plans.py | 210 | ✅ Uygun |

### 5.2 Test Coverage

| Modül | Test Sayısı | Coverage |
|-------|-------------|----------|
| plan_service.py | 8 | ~%40 |
| goal_based_planning.py | 0 | 0% |
| planning_application.py | 0 | 0% |
| routes/plans.py | 10 | ~%35 |

### 5.3 Code Complexity

- `plan_service.py`: Orta karmaşıklık
- `goal_based_planning.py`: Yüksek karmaşıklık (matematiksel hesaplamalar)
- `routes/plans.py`: Orta karmaşıklık

---

## 6. Önerilen Eylem Planı

### Faz 1: Kritik (1-2 hafta)
1. `goal_based_planning.py` entegrasyonu veya kaldırma
2. Test coverage artırma (%60+ hedef)
3. DCA logic ayrıştırma

### Faz 2: Orta (2-3 hafta)
4. Error handling standardizasyonu
5. Constants consolidation
6. Application service kaldırma

### Faz 3: Düşük (1-2 hafta)
7. Code duplication azaltma
8. Tenant ID helper
9. Documentation güncelleme

---

## 7. Risk Analizi

### 7.1 Yüksek Risk
- `goal_based_planning.py` kaldırılırsa gelecekte kullanım ihtiyacı
- DCA logic değişikliği mevcut ödemeleri etkileyebilir

### 7.2 Orta Risk
- Application service kaldırma breaking change olabilir
- Constants consolidation migration gerektirir

### 7.3 Düşük Risk
- Test eklemeleri
- Documentation güncellemeleri
- Code refactoring

---

## 8. Sonuç

Planlı gelir gider sistemi genel olarak sağlam ancak geliştirme potansiyeli var:

**Güçlü Yönler:**
- ✅ Temiz domain layer
- ✅ Uygun route yapısı
- ✅ Temel testler mevcut

**Zayıf Yönler:**
- ❌ Kullanılmayan kod (`goal_based_planning.py`)
- ❌ Düşük test coverage
- ❌ Code duplication
- ❌ Tutarsız error handling

**Öncelikli Eylemler:**
1. `goal_based_planning.py` entegrasyonu veya kaldırma
2. Test coverage artırma
3. Code duplication azaltma

Sistem stabil ancak optimizasyon ve test coverage artırma gerekiyor.
