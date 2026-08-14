# E-Cüzdan Log Analizi ve Aksiyon Planı

**Belge sürümü:** 2.1  
**Analiz tarihi:** 14 Ağustos 2026  
**Güncelleme nedeni:** Yatırımcı profili testi tamamlanırken `/profile/api/submit` isteğinin CSRF doğrulamasından geçememesi.

## 1. Yönetici Özeti

Profil testi ekranında cevaplar JSON gövdesiyle gönderilirken CSRF token isteğe aktarılmıyordu. Uygulamanın güvenlik middleware’i, durum değiştiren isteklerde tokenı form alanından veya `X-CSRF-Token` header’ından beklediği için istek doğru biçimde reddediliyor; ancak kullanıcı deneyimi açısından profil testi tamamlanamıyordu.

Kök neden ürün mimarisinde değil, **istemci ile güvenlik middleware’i arasındaki sözleşmenin eksik uygulanmasındadır**. Düzeltme, CSRF kontrolünü gevşetmeden yapılmıştır: global layout’a session tokenını taşıyan meta etiketi eklenmiş, profil wizard’ının JSON `POST` çağrısına `X-CSRF-Token` header’ı eklenmiş ve bu sözleşme için regresyon testleri oluşturulmuştur.

> Güvenlik açısından logda görülen “CSRF verification failed” mesajı korumanın çalıştığını gösterir; sorun, meşru profil isteğinin token taşımadan gönderilmesidir.

## 2. Olay Kaydı ve Etki Analizi

| Alan | Bulgular |
|---|---|
| Etkilenen akış | Yatırımcı profili testi tamamlandıktan sonraki AJAX gönderimi |
| Etkilenen endpoint | `POST /profile/api/submit` |
| Gözlenen log | `CSRF verification failed: token is missing from request to /profile/api/submit` |
| Kullanıcı etkisi | Profil sonucu oluşturulamadığı için test tamamlanamıyor |
| Veri güvenliği etkisi | Yetkisiz istek kabul edilmedi; veri kaybısı tespit edilmedi |
| Öncelik | Kritik kullanıcı akışı / yüksek güvenlik önemi |
| Durum | Düzeltildi ve hedefli testlerle doğrulandı |

## 3. Kök Neden Analizi

CSRF middleware’i [1] durum değiştiren isteklerde önce `csrf_token` form alanını, ardından `X-CSRF-Token` header’ını kontrol etmektedir. Profil wizard’ı ise [2] yalnızca `Content-Type: application/json` header’ını gönderiyor ve tokenı ne JSON gövdesine ne de beklenen HTTP header’ına ekliyordu. Bu nedenle session içinde geçerli token bulunsa bile middleware isteği “token missing” olarak değerlendiriyordu.

| Katman | Önceki davranış | Risk veya sonuç |
|---|---|---|
| Session | Token üretiliyor ve session’da tutuluyor | Tek başına yeterli değil |
| HTML | Tokenın ortak bir DOM sözleşmesi yoktu | JavaScript tokenı güvenilir şekilde okuyamıyordu |
| Profil wizard AJAX | Sadece JSON content type gönderiyordu | Middleware token bulamıyordu |
| CSRF middleware | Form alanı veya `X-CSRF-Token` arıyordu | Meşru istek 400 ile reddediliyordu |

## 4. Uygulanan Düzeltmeler

### 4.1. Ortak token sözleşmesi

`templates/layout.html` içine aşağıdaki ortak meta etiketi eklendi. Böylece layout kullanan tüm sayfalar session tokenına aynı DOM sözleşmesi üzerinden erişebilir:

```html
<meta name="csrf-token" content="{{ session.get('csrf_token', '') }}">
```

Bu yaklaşım güvenlik kontrolünü devre dışı bırakmaz ve tokenı URL parametresine taşımadığı için sızıntı yüzeyini büyütmez.

### 4.2. Profil wizard AJAX çağrısı

`templates/profile_wizard.html` içindeki `POST /profile/api/submit` çağrısı artık middleware’in beklediği header’ı gönderiyor:

```javascript
headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
}
```

Token bulunamazsa boş değer gönderilmesi, güvenlik kontrolünü gevşetmez; middleware isteği reddeder. Bu, sessizce güvenlik açığı üretmek yerine yapılandırma hatasını güvenli biçimde görünür kılar.

### 4.3. Regresyon testleri

`tests/integration/test_profile_csrf_contract.py` ile iki sözleşme test edildi. İlk test, profil sayfasının session tokenını meta etiketiyle yayınladığını ve JavaScript’in `X-CSRF-Token` header’ını kullandığını doğrulamaktadır. İkinci test, doğru session/header eşleşmesinin middleware tarafından CSRF hatası olarak reddedilmediğini doğrulamaktadır.

Ayrıca daha önce hatalı `conftest` importu içeren profil API entegrasyon testi temizlenmiş, route’ların gerçek login ve canonical-slash yönlendirmeleri olan `302`/`308` yanıtları test sözleşmesine doğru biçimde eklenmiştir. Bu değişiklikler uygulama davranışını değiştirmemekte, testlerin gerçek route sözleşmesini yansıtmasını sağlamaktadır.

## 5. Doğrulama Sonuçları

| Doğrulama | Sonuç |
|---|---:|
| CSRF regresyon testi | **2 geçti** |
| Profil API entegrasyon testleri | **8 geçti** |
| Birleşik profil test paketi | **10 geçti / 10 toplam** |
| Birleşik koşu süresi | **4,70 saniye** |
| CSRF bypass yapıldı mı? | **Hayır** |
| Profil endpoint’i doğru header ile CSRF tarafından reddedildi mi? | **Hayır** |

Çalıştırılan doğrulama komutu:

```bash
.venv\Scripts\python.exe -m pytest \
  tests/integration/test_profile_csrf_contract.py \
  tests/integration/test_profile_api_integration.py \
  -q --disable-warnings --no-cov
```

## 6. Önceki Log ve Kalite Aksiyonlarının Durumu

| Aksiyon | Durum | Teknik not |
|---|---|---|
| Veritabanı tablo eksikliği | İzleniyor / mevcut runtime şeması doğrulandı | `category` tablosu mevcut veritabanında bulunuyor; bootstrap ve migration izlenmeye devam etmeli |
| Test coverage ve koleksiyon | Kısmen tamamlandı | Eksik `forensic` marker eklendi, `pytest.ini` BOM sorunu giderildi; global test koşusu ayrıca izlenmeli |
| EVDS API | Güvenli fallback ile çalışıyor | `.env.example` içine `EVDS_API_KEY` placeholder’ı eklendi; gerçek secret repoya yazılmamalı |
| Log encoding | Uygulandı ve doğrulandı | Rotating file handler’larda `encoding='utf-8'` korunuyor |
| CI workflow | Yenilendi | Test, PII, observability ve coverage adımları geçerli YAML yapısında toplandı |
| Profil CSRF sözleşmesi | **Tamamlandı** | Meta token, header aktarımı ve regresyon testleri eklendi |

## 7. Yayına Alma ve İzleme Planı

Değişiklikler yayınlanmadan önce profil wizard’ı gerçek tarayıcıda giriş yapılmış bir kullanıcıyla tamamlanmalı ve Network panelinde `POST /profile/api/submit` isteğinin `X-CSRF-Token` header’ı taşıdığı görülmelidir. Yanıtın başarılı profil sonucu veya beklenen iş kuralı doğrulama yanıtı olması gerekir; CSRF kaynaklı 400 yanıtı görülmemelidir.

Yayın sonrasında ilk 24 saat boyunca `/profile/api/submit` için CSRF hata sayısı, 4xx oranı ve profil oluşturma başarı oranı izlenmelidir. CSRF hataları devam ederse token üretimi, session cookie kapsamı, proxy header aktarımı ve sayfanın cache’lenip cache’lenmediği incelenmelidir. Tokenı güvenlik gerekçesiyle loglamamak gerekir.

## 8. Kabul Kriterleri

| Kriter | Kabul koşulu |
|---|---|
| Kullanıcı akışı | Kullanıcı profili testi tamamlayabilmeli ve sonuç ekranına ulaşabilmeli |
| Güvenlik | Tokenı olmayan veya yanlış tokenlı istekler reddedilmeye devam etmeli |
| İstemci sözleşmesi | Profil submit isteği `X-CSRF-Token` header’ı taşımalı |
| Test | CSRF sözleşme testleri ve profil API testleri yeşil olmalı |
| Geriye dönük uyumluluk | Form tabanlı mevcut POST akışları etkilenmemeli |
| Gözlemlenebilirlik | CSRF hataları token değerini ifşa etmeden loglanmalı |

## 9. Geri Alma Planı

Sorun tekrarlanırsa önce yalnızca `templates/profile_wizard.html` içindeki header değişikliği geri alınmamalı; çünkü bu durumda kullanıcı akışı yeniden kırılır. Geri alma gerekiyorsa `layout.html`, wizard JavaScript’i ve regresyon testleri aynı değişiklik kümesi olarak geri alınmalı, ardından middleware’in mevcut davranışını doğrulayan güvenlik testleri çalıştırılmalıdır. En güvenli operasyonel yaklaşım, düzeltmeyi geri almak yerine istemci header’ının tarayıcı Network kaydından ve session cookie durumundan teşhis edilmesidir.

## 10. Referanslar

[1]: `routes/__init__.py` — CSRF middleware ve `X-CSRF-Token` doğrulama sözleşmesi.  
[2]: `templates/profile_wizard.html` — Profil testi JSON submit çağrısı.  
[3]: `templates/layout.html` — Ortak CSRF meta token sözleşmesi.  
[4]: `tests/integration/test_profile_csrf_contract.py` — CSRF regresyon testleri.  
[5]: `tests/integration/test_profile_api_integration.py` — Profil API entegrasyon testleri.

## 11. fullsuite-resume Takılma Analizi ve Kalıcı Çözüm

İlk tam koşu gerçek bir deadlock değil, yanlış pozisyonel parametre aktarımı ve sınıflandırılmamış uzun entegrasyon testlerinin birleşiminden oluşan bir süre problemiydi. Demo testleri `generate_advanced_demo_data(test_user.tenant_id, test_user.id)` çağrısıyla `tenant_id` değerini `user_id`, kullanıcı id’sini ise `start_year` olarak geçiriyordu. Kullanıcı id’sinin başlangıç yılına dönüşmesi, üretim döngüsünü yaklaşık iki bin yıla genişletebildiği için test görünürde takılı kalıyordu.

Düzeltme, çağrının public API sözleşmesine uygun hale getirilmesiyle yapıldı:

```python
generate_advanced_demo_data(
    test_user.id,
    start_year=2025,
    end_year=2027,
)
```

Bu değişiklikten sonra demo veri üretim testleri **3 geçti / 3 toplam** ve yaklaşık **11 saniyede** tamamlandı. Testin `success` alanını beklemesi de kaldırıldı; public orchestrator sözleşmesi istatistik sözlüğü döndürmektedir: `transactions`, `recurring_plans`, `assets` ve `asset_valuations`.

### 11.1. Test katmanları

Uzun süren final ve strategy entegrasyon sınıfları `slow` marker’ı ile ayrıştırıldı. Strategy entegrasyon testleri yaklaşık 273 saniye, final integration testleri yaklaşık 166 saniye sürdüğü için bu testler hızlı kalite kapısına dahil edilmemekte; ayrı bir timeout korumalı katmanda çalıştırılmaktadır. Böylece hızlı geri bildirim ile kapsamlı stabilite koşusu birbirinden ayrılmıştır.

| Koşu | Sonuç |
|---|---:|
| Demo veri üretimi | **3 geçti, 11,05 saniye** |
| Profil CSRF ve API paketi | **10 geçti** |
| Veri bütünlüğü ve HTTP regresyonları | **20 geçti** |
| Non-slow integration paketi | **265 geçti, 42 skip** |
| Unit paketi, 4 xdist worker | **2.241 geçti, 109 skip** |
| Tüm non-slow paket, 4 xdist worker | **2.696 geçti, 151 skip** |
| Slow test seçimi | **18 test doğru seçildi** |
| Strategy slow paketi | **16 geçti, 273,57 saniye** |
| Final integration slow paketi | **5 geçti, 166,46 saniye** |

### 11.2. CI güvenlik ve süre kapıları

CI workflow artık schema health-check adımını, non-slow testleri dört izole worker ile çalıştıran hızlı kalite kapısını ve slow testleri 300 saniyelik test timeout’u ile çalıştıran ayrı adımı içermektedir. Job timeout’u 30 dakikaya yükseltilmiştir. Bu ayrım, suite’in sınırsız beklemesini önlerken uzun süreli stabilite testlerinin tamamen devre dışı bırakılmasını da engeller.

Paralel koşuda benchmark testlerinin otomatik olarak devre dışı bırakılması beklenen bir davranıştır; benchmark sonuçları güvenilir biçimde yalnızca seri koşuda alınmalıdır. Bu nedenle xdist, benchmark doğrulamasının yerine geçmez ve CI’de benchmark raporu ayrı bir seri iş olarak ele alınmalıdır.

### 11.3. Opsiyonel OpenTelemetry davranışı

OpenTelemetry paketleri `requirements-observability.txt` içinde opsiyonel tutulmaktadır. Bu paketler kurulu değilken tracing modülü no-op davranışına geçer. Tracing unit testleri artık `OTEL_ENABLED` aktif değilse skip olur; böylece opsiyonel bir özelliğin kurulu olmaması temel test paketini hatalı biçimde kırmaz. Gözlemlenebilirlik doğrulaması ise ayrı CI adımı olarak çalışmaya devam eder.

## 12. Güncel Kabul Kriterleri

| Kriter | Son durum |
|---|---|
| Demo testleri sınırsız yıl döngüsüne girmemeli | **Tamamlandı** |
| Public demo API parametreleri keyword-safe kullanılmalı | **Tamamlandı** |
| Uzun integration sınıfları slow katmanında izole edilmeli | **Tamamlandı** |
| Non-slow testler xdist ile tekrarlanabilir çalışmalı | **Doğrulandı: 2.696 geçti** |
| Slow testler timeout korumasıyla çalışmalı | **CI workflow’a eklendi** |
| Opsiyonel OTel eksikliği temel suite’i kırmamalı | **Tamamlandı** |
| CI schema health-check çalıştırmalı | **Workflow’a eklendi** |

## 13. Final doğrulama kaydı (14 Ağustos 2026)

Bu kapanış kaydı, planın mevcut Flask, SQLAlchemy, SQLite, pytest ve GitHub Actions mimarisi korunarak tamamlandığını belgelemektedir.

Bağımlılık ve çalışma zamanı: Flask-Limiter 4.1.1 kuruldu. Uygulama memory storage ile aktif başlıyor ve fallback uyarısı üretmiyor. pip check sonucu No broken requirements found oldu. Runtime schema kontrolü 34 tabloyu doğruladı.

Seed ve regresyon doğrulaması: Seed scriptindeki NameError düzeltildi ve 24 standart kategori başarıyla eklendi. Kritik paket 38 test ile geçti. Tam non-slow paket dört xdist worker ile 2696 geçti ve 151 skip sonucunu 174,06 saniyede verdi.

CI kalite kapıları: pytest-timeout hem CI kurulumuna hem requirements.txt dosyasına eklendi. Non-slow testler 180 saniye, slow testler 300 saniye timeout ile ayrı katmanlarda çalışır. İş seviyesi süre sınırı 30 dakikadır. OpenTelemetry kurulmadığında tracing testleri açıkça skip edilir.

Operasyonel sınırlar ve kabul kararı: Rate-limit depolaması mevcut yapılandırmada bellek içidir; çoklu worker veya yatay üretimde RATELIMIT_STORAGE_URI değerinin Redis gibi paylaşımlı bir depoya alınması gerekir. EVDS ve OpenTelemetry opsiyoneldir. Kritik güvenlik, test güvenilirliği, schema sağlığı, rate limiting ve CI kalite kapıları için kabul kriterleri karşılanmıştır.

## v2.2 KontrollÃ¼ Log ve Test Ä°zolasyonu GeliÅŸtirmeleri

Bu sÃ¼rÃ¼mde mevcut mimari korunarak fail-open structured logging contract gÃ¼Ã§lendirildi. StructuredLogger.exception() artÄ±k gerÃ§ek exc_info bilgisini logging katmanÄ±na iletir ve sink yazma hatalarÄ±nÄ±n uygulama akÄ±ÅŸÄ±na sÄ±zmadÄ±ÄŸÄ± iki regresyon testiyle doÄŸrulanÄ±r.

Demo veri Ã¼retimindeki SQLAlchemy legacy Query.get() Ã§aÄŸrÄ±larÄ± db.session.get() ile yenilendi. Yeni asset kaydÄ±ndan hemen sonra db.session.flush() uygulanarak primary key oluÅŸmadan valuation sorgulanmasÄ± engellendi. Notification repository ve model katmanÄ±ndaki deprecated datetime.utcnow() kullanÄ±mlarÄ± mevcut utcnow_naive() sÃ¶zleÅŸmesine taÅŸÄ±ndÄ±.

Startup sÄ±rasÄ± dÃ¼zeltildi: init_database(app) tamamlandÄ±ktan sonra demo data validation Ã§alÄ±ÅŸÄ±yor. BÃ¶ylece schema hazÄ±r olmadan category tablosuna eriÅŸilmesi ve baÅŸlangÄ±Ã§ warningâ€™i oluÅŸmasÄ± engellendi. Test fixtureâ€™Ä± xdist/thread yarÄ±ÅŸlarÄ±nÄ± Ã¶nlemek iÃ§in worker baÅŸÄ±na dosya tabanlÄ± SQLite DB, QueuePool, check_same_thread=False ve teardownâ€™da dispose/dosya temizliÄŸi kullanÄ±yor. CI non-slow komutunda xdist benchmark warningâ€™ini Ã¶nlemek iÃ§in --benchmark-disable eklendi.

Final doÄŸrulama kapÄ±larÄ±: kritik route/HTTP/CSRF/demo paketi **38 passed**, coverage **%31,32** ve minimum eÅŸik **%25**; monitoring/login yarÄ±ÅŸ kapsamÄ± **62 passed**; tam non-slow suite -W error --benchmark-disable ile **2.698 passed, 151 skipped**. pip check, syntax compilation, diff whitespace kontrolÃ¼ ve deÄŸiÅŸen dosyalardaki gÃ¼venli Ruff kontrolleri baÅŸarÄ±lÄ±dÄ±r. App/models iÃ§indeki E402/I001/F811 bulgularÄ± Ã¶nceki commitâ€™te de mevcut olan yapÄ±sal import borcudur ve bu kapsamda mimariyi bozacak ÅŸekilde yeniden dÃ¼zenlenmemiÅŸtir.

AyrÄ±ntÄ±lÄ± 5N1K kÃ¶k neden kaydÄ±, final teslimat ekindeki RCA raporunda tutulmuÅŸtur. Ãœretim rate-limit storage ve veritabanÄ± davranÄ±ÅŸÄ± deÄŸiÅŸtirilmemiÅŸtir; dosya tabanlÄ± SQLite izolasyonu yalnÄ±zca test fixtureâ€™Ä±na aittir.
