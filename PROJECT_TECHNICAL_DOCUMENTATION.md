# E-Cüzdan Proje Teknik Dokümantasyonu

## Yönetici Özeti

E-Cüzdan, çoklu kiracı mimarisi, OAuth kimlik doğrulaması, finansal analiz motorları ve kişisel finans yönetimi için kapsamlı alan modellemesi içeren Flask ile oluşturulmuş kapsamlı bir finansal yönetim uygulamasıdır.

**Proje Kök Dizini:** `c:\Users\e.cetin\Desktop\e-cuzdan`

**Teknoloji Yığını:**
- **Backend:** Flask (Python)
- **Veritabanı:** SQLAlchemy ORM ile SQLite
- **Kimlik Doğrulama:** OAuth 2.0 (Google), oturum tabanlı kimlik doğrulama
- **Finansal Veriler:** yfinance, piyasa veri servisleri
- **Test:** Pytest ile %54.45 kapsama (1959 test)
- **Mimari:** Katmanlı (Domain-Driven Design ile bağımlılık enjeksiyonu)

---

## Mimari Genel Bakış

### Katmanlı Mimari

Uygulama, endişelerin net bir ayrımı ile temiz bir katmanlı mimariyi takip eder:

```
┌─────────────────────────────────────────────────────────┐
│                    Sunum Katmanı                         │
│  (Flask Routes: auth, dashboard, transactions, etc.)   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Uygulama Katmanı                        │
│  (Application Services: orchestration, use cases)        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                    Domain Katmanı                        │
│  (Business Logic: Services, Domain Models, Events)      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                Altyapı Katmanı                           │
│  (Repositories, External APIs, Background Services)      │
└─────────────────────────────────────────────────────────┘
```

### Bağımlılık Enjeksiyon Konteyneri

**Dosya:** `bootstrap/container.py`

Uygulama, lazy-singleton paterni ile bir bağımlılık enjeksiyon konteyneri kullanır:

- **RepositoryProvider:** Veri erişim katmanı (UserRepository, FinancialRepository, CatalogRepository)
- **DomainProvider:** İş mantığı servisleri (AuthService, CatalogService, AssetService)
- **ApplicationProvider:** Kullanım durumu orkestrasyonu (AuthApplicationService, CatalogApplicationService)
- **InfrastructureProvider:** Dış entegrasyonlar (GoogleOAuthProvider, BackgroundService, EventBus)

---

## Temel Domain Modelleri

### Çoklu Kiracı

**Tenant Modeli:**
- `id`: String tabanlı kiracı tanımlayıcısı
- `name`: Kiracı adı
- `status`: Aktif/inaktif durumu
- `base_currency`: Varsayılan para birimi (TRY, USD, vb.)

**User Modeli:**
- Rol tabanlı erişim kontrolü ile çoklu kiracı kullanıcı
- OAuth entegrasyon alanları (auth_provider, oauth_id)
- Kişisel bilgiler (gender, birthdate, country, city, phone)
- Rol yükseltmeleri için özel kod sistemi
- Özellikler: `is_super_admin`, `has_admin_access`, `is_tenant_admin`

### Finansal Modeller

**Transaction Modeli:**
- Tüm nakit akışları için tek tablo tasarımı
- Tek seferlik ve düzenli işlemleri destekler
- Transfer özel alanları (transfer_from, transfer_to)
- Soft delete desteği (is_deleted, deleted_at)
- Tekilleştirme kısıtlaması (tenant_id, date, category, description, amount)

**RecurringPlan Modeli:**
- Düzenli gelir/giderler için pozisyon katmanı
- Plan tipleri: Taksit, Abonelik, DCA, Kira
- Durum takibi: Aktif, Tamamlandı, İptal
- DCA planları için hedef varlık bağlantısı

**Asset Modeli:**
- Profesyonel yatırım takibi
- Maliyet yöntemleri: FIFO, LIFO, WEIGHTED_AVERAGE, HIFO
- Özellikler: weighted_average_cost, roi, total_gain_loss, realized_gain, unrealized_gain
- Kiracı izolasyonu ile portföy ağırlığı hesaplaması
- Maliyet tabanı takibi için işlem geçmişi

### Katalog Modelleri

**Category Modeli:**
- Ebeveyn-çocuk ilişkileri ile hiyerarşik kategoriler
- GL kodu entegrasyonu (account_id FK)
- Çoklu dil desteği (names, description JSON alanları)
- Kiracıya özel vs global kategoriler (tenant_id NULL = global)
- Bütçe limitleri ve vergi oranları

**AssetType & AssetSector:**
- Hiyerarşik varlık sınıflandırması
- Risk profilleri, vergi muamelesi, likidite profilleri
- Sektörler için GICS/ICB kodu desteği

### Defter Modelleri

**Account Modeli:**
- Hesap Planı (CoA) uygulaması
- Tipler: Asset, Liability, Equity, Revenue, Expense
- parent_id ile hiyerarşik yapı

**JournalEntry & LedgerLine:**
- Çift taraflı defter tutma desteği
- Değişmez defter için hash zinciri (hash, previous_hash)
- Para birimi desteği ile borç/alacak takibi

---

## Route Haritalaması

### Kimlik Doğrulama Route'ları (`routes/auth.py`)
- `/login` - Kullanıcı girişi
- `/logout` - Kullanıcı çıkışı
- `/register` - Kullanıcı kaydı
- `/oauth_login/<provider>` - OAuth başlatma (Google)
- `/oauth_callback/<provider>` - OAuth callback işleme
- `/oauth_signup` - OAuth kullanıcı tamamlama kaydı
- `/register_with_invite/<token>` - Davet tabanlı kayıt

### Dashboard Route'ları (`routes/dashboard.py`)
- `/` - Ana dashboard
- `/quick_transfer` - Hızlı nakit transferi
- `/financial_analysis` - Finansal analiz görünümü
- `/financial_freedom` - Finansal özgürlük analizi
- `/monthly_dashboard/<month>` - Aylık dashboard görünümü

### İşlem Route'ları (`routes/transactions.py`)
- `/transactions` - İşlem listesi ve yönetimi
- Tek seferlik işlemler için CRUD işlemleri

### Varlık Route'ları (`routes/assets.py`)
- `/assets` - Varlık listesi görünümü
- `/assets/management` - Varlık yönetimi arayüzü
- Portföy entegrasyonu ile varlık CRUD

### Kategori Route'ları (`routes/categories.py`)
- `/categories` - Kategori yönetimi
- Varlık tipi ve sektör yönetimi

### Yönetici Route'ları (`routes/admin.py`)
- `/users` - Kullanıcı yönetimi (sistem yöneticisi)
- Kiracı yönetim fonksiyonları

### Ayarlar Route'ları (`routes/settings.py`)
- `/settings` - Ayarlar sayfası
- Profil yönetimi, veri dışa aktarma/içe aktarma
- Demo veri oluşturma

### Ek Route'lar
- **Profile Routes:** Yatırımcı profili testi ve yönetimi
- **Export Routes:** PDF dışa aktarma, JSON yedekleme/geri yükleme
- **Logbook Routes:** Finansal günlük girdileri
- **Strategy Routes:** Yatırım stratejisi planlama
- **Financial Education Routes:** Quiz sistemi, ilerleme takibi
- **Monitoring Routes:** Log izleme ve sağlık kontrolleri
- **Notification Routes:** Uygulama içi bildirim merkezi
- **Analysis Routes:** Finansal analiz API'leri
- **Tenant Routes:** Kiracı kullanıcı yönetimi

---

## Veritabanı Şeması

### Temel Tablolar

**tenant**
- id (PK), name, status, base_currency

**user**
- id (PK), username, email, password_hash, tenant_id (FK)
- auth_provider, oauth_id, role
- gender, birthdate, country, city, phone
- special_code, special_code_used_at
- Indexler: username, email, oauth_id, tenant_id

**transaction**
- id (PK), date, category, description, note
- type (Gelir/Gider/Yatırım/Transfer), status (Ödendi/Bekliyor)
- amount (Numeric 19,4), installment_number
- source_id, source_type
- transfer_from, transfer_to
- tenant_id (FK)
- Soft delete: is_deleted, deleted_at, deleted_by
- Indexler: date, type, status, tenant_id, category

**recurring_plan**
- id (PK), name, category, flow_type, amount
- installments, payment_day, start_date, end_date
- plan_type (Taksit/Abonelik/DCA/Kira), frequency, status
- target_asset_id (FK)
- tenant_id (FK)

**asset**
- id (PK), type, name, value (Numeric 19,4)
- purchase_date, purchase_cost, quantity, unit_price
- currency, symbol, risk_level, liquidity
- sector_id (FK), tenant_id (FK)
- is_closed, closed_at, cost_method
- İlişkiler: AssetTransaction, AssetUpdate

**payment**
- id (PK), plan_id (FK), amount, payment_date
- installment_number, notes, tenant_id (FK)
- transaction_id (FK)

### Katalog Tabloları

**category**
- id (PK), code, name, names (JSON), description (JSON)
- type, subcategory, parent_id (FK), level, path
- account_id (FK), budget_limit, tax_rate
- icon, color, is_active, tenant_id (FK)
- Denetim alanları: version, created_by, created_at, updated_by, updated_at

**asset_type**
- id (PK), name, parent_id (FK), level
- risk_profile, tax_treatment, min_holding_period
- default_currency, liquidity_profile, volatility_range

**asset_sector**
- id (PK), name, parent_id (FK), level
- code, region, regulatory_class, cyclical_type, beta_range

### Defter Tabloları

**account**
- id (PK), tenant_id (FK), name, type
- currency, parent_id (FK), is_active, created_at

**journal_entry**
- id (PK), tenant_id (FK), date, description
- hash, previous_hash, status
- created_at, created_by (FK)

**ledger_line**
- id (PK), journal_entry_id (FK), account_id (FK)
- debit (Numeric 19,4), credit (Numeric 19,4), currency

### Destekleyici Tablolar

**user_preference**
- FIRE hedefleri, analiz varsayımları
- Theme, privacy_mode, bildirim tercihleri

**notification**
- Teslimat takibi ile uygulama içi bildirimler
- Kategoriler: budget, payment, system, asset
- Şiddet seviyeleri, öncelik, son kullanma

**audit_log**
- Sadece ekleme güvenlik denetim izi
- Eylemler: LOGIN, LOGOUT, REGISTER, DATA_EXPORT, vb.
- IP adresi, user agent takibi

**backup_metadata**
- Yedek sürümleme ve meta veriler
- Şema sürümü, checksum, şifreleme durumu
- Kayıt sayıları, yedek tipi (full/incremental)

**quiz_question, quiz_attempt, user_achievement**
- Finansal eğitim oyunlaştırma sistemi

**logbook_entry**
- Finansal günlük girdileri
- Kategoriler: Finansal, Yatırım, Ödeme, Kilometre Taşı, Fikir

**investor_profile, investor_profile_answer, profile_question**
- Risk değerlendirmesi ve yatırımcı profilleme

---

## Güvenlik Mimarisi

### Kimlik Doğrulama ve Yetkilendirme

**OAuth Entegrasyonu:**
- Google OAuth 2.0 sağlayıcısı (`infrastructure/auth/google_provider.py`)
- State parametresi ile CSRF koruması
- E-posta doğrulama gereksinimi
- 2 saat zaman aşımı ile oturum tabanlı kimlik doğrulama

**Rol Tabanlı Erişim Kontrolü:**
- Roller: sistem_yoneticisi, yonetici, tenant_admin, kullanici
- Dekoratörler: `@login_required`, `@require_role`, `@superadmin_required`, `@tenant_admin_required`
- Geriye dönük uyumluluk için rol normalizasyonu

**Oturum Güvenliği:**
- `SESSION_COOKIE_HTTPONLY`: True
- `SESSION_COOKIE_SAMESITE`: Lax
- `SESSION_COOKIE_SECURE`: Yapılandırılabilir (HTTPS zorlama)
- `SESSION_REFRESH_EACH_REQUEST`: True
- 2 saatlik oturum zaman aşımı

### Denetim İzi

**Denetim Log Sistemi (`utils/audit.py`):**
- Sadece ekleme tasarımı (güncelleme/silme yok)
- Kanonik eylem sabitleri (LOGIN, LOGOUT, REGISTER, vb.)
- Otomatik IP adresi ve user agent yakalama
- Sessiz hata (ana akışı bozmaz)
- Kiracı izolasyonu desteği

### Şifreleme

**Yedek Şifreleme (`infrastructure/backup/encryption.py`):**
- AES-256-GCM şifreleme
- PBKDF2 anahtar türetme (100.000 iterasyon)
- SHA-256 checksum doğrulama
- Salt ve nonce oluşturma
- Yedekler için şifre oluşturma

### Güvenlik Loglama

**Özel Güvenlik Logu:**
- Ayrı log dosyası: `logs/e_cuzdan_security.log`
- Anahtar kelime filtreleme: authentication, unauthorized, security, login, logout, permission, access
- Döndürülen dosya işleyicisi (5MB, 5 yedek)

---

## Yapılandırma

### Uygulama Yapılandırması (`config.py`)

**Ortam Değişkenleri:**
- `SECRET_KEY`: Flask secret key (production için gerekli)
- `SQLALCHEMY_DATABASE_URI`: Veritabanı bağlantı dizesi
- `GOOGLE_CLIENT_ID`: OAuth client ID
- `GOOGLE_CLIENT_SECRET`: OAuth client secret
- `SUPER_ADMIN_USERNAME`: Süper yönetici kullanıcı adı

**Oturum Yapılandırması:**
- `SESSION_TIMEOUT_HOURS`: 2 (varsayılan)
- `SESSION_COOKIE_HTTPONLY`: True
- `SESSION_COOKIE_SAMESITE`: Lax
- `SESSION_COOKIE_SECURE`: True (production)
- `HTTPS_ENFORCED`: True (production)

**Finansal Yapılandırma:**
- `DEFAULT_CURRENCY`: TRY
- `DEFAULT_INFLATION_RATE`: 0.45 (%45)
- `DECIMAL_PRECISION`: 4

### Loglama Yapılandırması (`utils/logging_config.py`)

**Log Dosyaları:**
- `logs/e_cuzdan.log`: Ana uygulama logu (10MB, 10 yedek)
- `logs/e_cuzdan_errors.log`: Sadece ERROR/CRITICAL (5MB, 5 yedek)
- `logs/e_cuzdan_security.log`: Sadece güvenlik olayları (5MB, 5 yedek)
- Yapılandırılmış loglama (JSON formatı) mevcut
- Yüksek hacimli senaryolar için log örnekleme

**OpenTelemetry Entegrasyonu:**
- Trace context filtreleme
- Log mesajlarına Trace ID ve span ID enjeksiyonu

### Test Yapılandırması (`pytest.ini`)

**Kapsama Gereksinimleri:**
- Minimum kapsama: %25
- Mevcut kapsama: %54.45
- Dal kapsaması etkin
- HTML raporları `htmlcov/` içinde

**Test İşaretleyicileri:**
- unit, integration, regression, e2e
- slow, fast, performance
- auth, db, api, ui, financial, security

---

## Arka Plan Servisleri

### Background Service (`infrastructure/background/background_service.py`)

**Piyasa Verisi Güncellemeleri:**
- Saatlik veri yenileme (3600 saniye)
- Canlı veriler: hava durumu, USD, EUR, altın (doviz.com scraping)
- Piyasa verileri: yfinance entegrasyonu (10 yıllık geçmiş)
- API başarısızlıkları için fallback mekanizmaları
- `instance/` dizininde JSON cache kalıcılığı

**Takip Edilen Piyasa Varlıkları:**
- GC=F (Altın), SI=F (Gümüş), CL=F (Petrol)
- XU100.IS (BIST100), BTC-USD (Bitcoin)
- ^IXIC (Nasdaq)

### Event Bus

**Local Event Bus (`infrastructure/events/local_event_bus.py`):**
- Bellek içi senkron olay dağıtımı
- Subscribe/publish/unsubscribe pattern
- İşlem yaşam döngüsü için olay işleyicileri
- Loglama ile hata işleme

**Domain Olayları:**
- TransactionCreatedEvent, TransactionUpdatedEvent, TransactionDeletedEvent
- UserLoggedInEvent, UserCreatedEvent, UserLanguageChangedEvent
- TenantCreatedEvent
- AssetAddedEvent, AssetRemovedEvent, AssetUpdatedEvent

---

## Uluslararasılaştırma

**Çeviri Dosyaları:**
- `translations/tr.json`: Türkçe (birincil)
- `translations/en.json`: İngilizce
- `translations/de.json`: Almanca
- `translations/it.json`: İtalyanca

**i18n Altyapısı (`infrastructure/i18n`):**
- Dil algılama ve değiştirme
- Çeviri anahtarı çözümlemesi
- Kullanıcı başına dil tercihleri

---

## Test Mimarisi

### Test Yapısı

**Unit Testler (`tests/unit/`):**
- 80+ test dosyası
- İzole bileşen testi
- Mock ağırlıklı yaklaşım

**Entegrasyon Testleri (`tests/integration/`):**
- Bileşen etkileşim testi
- Veritabanı entegrasyonu
- API endpoint testi

**Regresyon Testleri (`tests/regression/`):**
- Hata düzeltme doğrulaması
- Veri bütünlüğü kontrolleri
- Bakiye değişmezleri

**Test İstatistikleri:**
- Toplam test: 1959
- Geçen: 1959
- Atlanan: 165
- XFailed: 1
- Kapsama: %54.45
- Süre: ~6 dakika

### Önemli Test Dosyaları

- `test_oauth_signup.py`: OAuth akışı testi
- `test_auth_routes.py`: Kimlik doğrulama route testi
- `test_financial_engine_regression.py`: Finansal hesaplama doğrulaması
- `test_balance_invariant.py`: Bakiye bütünlüğü kontrolleri
- `test_audit.py`: Denetim izi doğrulaması

---

## Dış Bağımlılıklar

### Python Paketleri (requirements.txt'ten)

**Çekirdek Framework:**
- Flask, Flask-SQLAlchemy, Werkzeug
- python-dotenv

**Finansal Veriler:**
- yfinance, pandas, numpy, scipy

**Web Scraping:**
- requests, BeautifulSoup4

**PDF Oluşturma:**
- xhtml2pdf, reportlab

**Veritabanı:**
- Alembic (migrations)

**Test:**
- pytest, pytest-cov

**Güvenlik:**
- cryptography (AES-256-GCM)

**Gözlemlenebilirlik:**
- OpenTelemetry entegrasyonu

---

## Temel Tasarım Desenleri

### Repository Pattern
- BaseRepository ile soyut veri erişimi
- Kiracı farkında repository'ler
- Sözleşme tabanlı test

### Domain Olayları
- Yan etkiler için olay odaklı mimari
- Güvenilir olay teslimatı için Outbox pattern
- Olay işleyicileri kaydı

### Bağımlılık Enjeksiyonu
- Konteyner tabanlı servis kompozisyonu
- Lazy-singleton pattern
- Mock için test geçersiz kılmaları

### Çoklu Kiracı
- Veritabanı seviyesinde kiracı izolasyonu
- Kiracı context propagasyonu
- Kiracı başına rol tabanlı erişim kontrolü

### Soft Delete
- İşlem soft delete desteği
- Denetim izi korunması
- Veri kurtarma yeteneği

---

## Performans Hususları

### Önbellekleme
- Background service piyasa verisi cache'i
- Flask `g` içinde kullanıcı context cache'i
- Uygulanabilir yerlerde repository seviyesi cache'leme

### Veritabanı Optimizasyonu
- Yabancı anahtarlar ve sorgu alanlarında stratejik indeksleme
- Büyük veri setleri için sayfalama
- İzolasyon için kiracı kapsamlı sorgular

### Asenkron İşleme
- Piyasa verileri için background worker
- Yan etkiler için event bus
- Güvenilir teslimat için Outbox pattern

---

## Dağıtım Hususları

### Gerekli Ortam Değişkenleri
- `SECRET_KEY` (production)
- `SQLALCHEMY_DATABASE_URI`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `SUPER_ADMIN_USERNAME`

### Dosya Sistemi Gereksinimleri
- Cache dosyaları için `instance/` dizini
- Log dosyaları için `logs/` dizini
- SQLite veritabanı için yazma izinleri

### Güvenlik Kontrol Listesi
- Production'da HTTPS etkin
- Oturum cookie güvenlik bayrakları yapılandırıldı
- SECRET_KEY güçlü rastgele değere ayarlandı
- OAuth kimlik bilgileri düzgün yapılandırıldı
- Şifreleme etkin veritabanı yedekleri

---

## Bilinen Geçici Dosyalar

### Temizleme Adayları (Güvenli Kaldırılabilir)

**Python Cache Dosyaları:**
- Tüm `__pycache__/` dizinleri
- Tüm `*.pyc` dosyaları
- Tüm `*.py,cover` dosyaları (coverage yapıtları)

**Coverage Raporları:**
- `htmlcov/` dizini
- `htmlcov_oauth/` dizini
- `htmlcov_oauth_only/` dizini

**Log Dosyaları:**
- `logs/*.log` dosyaları (dönen loglar)

**Instance Cache:**
- `instance/live_data_cache.json`
- `instance/market_data_cache.json`

**Migration Scriptleri:**
- `fix_oauth_user_email.py` (tek seferlik düzeltme scripti)

**Dokümantasyon:**
- `docs/` içindeki adli tespit raporları (tarihsel denetim yapıtları)

---

## Sonuç

E-Cüzdan, aşağıdaki özelliklere sahip iyi mimarilenmiş bir finansal yönetim uygulamasıdır:
- DDD prensipleri ile temiz katmanlı mimari
- Kapsamlı çoklu kiracı desteği
- OAuth ve denetim izleri ile güçlü güvenlik
- Kapsamlı finansal modelleme ve analiz yetenekleri
- Profesyonel test kapsaması (%54.45)
- Piyasa verileri için arka plan servisleri
- Genişletilebilirlik için olay odaklı mimari

Kod tabanı, kişisel finans yönetimi için net endişe ayrımı, bağımlılık enjeksiyonu ve kapsamlı domain modellemesi ile olgun mühendislik uygulamalarını sergilemektedir.
