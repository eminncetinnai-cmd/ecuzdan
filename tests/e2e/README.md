# Playwright E2E Testleri

Bu klasör, Monitoring panelinin browser seviyesindeki uçtan uca sözleşmesini doğrular. Testler Chromium üzerinde çalışır ve gerçek kullanıcı parolasını dosyada saklamaz; kimlik bilgileri yalnızca process environment değişkenlerinden okunur.

## Eksik `page` fixture hatasının kök nedeni

`page` fixture, `pytest-playwright` eklentisi tarafından sağlanır. Testler global Python yorumlayıcısıyla çalıştırıldığında eklenti kayıtlı değilse `fixture 'page' not found` hatası alınır. Proje sözleşmesi, testlerin proje sanal ortamındaki Python ile çalıştırılmasını gerektirir:

```powershell
.venv\Scripts\python.exe -m pytest tests/e2e --no-cov -rs
```

Eklentinin ve browser binary’sinin aynı ortamda kurulu olduğunu doğrulamak için:

```powershell
.venv\Scripts\python.exe -m pip show pytest-playwright playwright
.venv\Scripts\python.exe -m playwright install chromium
```

`page` fixture hatası giderildikten sonra testlerin uygulamaya erişebilmesi gerekir. Uygulama çalışmıyorsa bağlantı reddedilir; authenticated testler için ayrıca `ECUZDAN_E2E_USERNAME` ve `ECUZDAN_E2E_PASSWORD` değişkenleri gerekir. Bu değişkenler eksikse kimlik doğrulamalı testler bilinçli olarak `skip` edilir; bu bir uygulama hatası değildir.

## Kurulum

Kurulumu temiz bir sanal ortamda tekrarlamak için aşağıdaki adımlar uygulanır:

```powershell
.venv\Scripts\python.exe -m pip install -r configuration\dependencies\requirements-e2e.txt
.venv\Scripts\python.exe -m playwright install chromium
```

E2E kullanıcısı, yerel test veritabanında Monitoring paneline erişebilen ayrılmış bir kullanıcı olmalıdır. Kullanıcı adı ve parola commit edilmeden process environment üzerinden tanımlanır:

```powershell
$env:ECUZDAN_E2E_USERNAME = 'e2e_local_user'
$env:ECUZDAN_E2E_PASSWORD = 'parola'
```

## Önerilen çalıştırma

Uygulama zaten `127.0.0.1:5000` üzerinde çalışıyorsa:

```powershell
.\scripts\run_e2e.ps1
```

Uygulamayı runner’ın geçici olarak başlatıp test bitince durdurmasını istiyorsanız:

```powershell
.\scripts\run_e2e.ps1 -StartServer
```

Bağımlılıkları ve Chromium’u da kurmak için:

```powershell
.\scripts\run_e2e.ps1 -Install -StartServer
```

Runner yalnızca kendi başlattığı Flask sürecini durdurur. Kullanıcının zaten çalıştırdığı uygulama sürecine dokunmaz. Test çıktıları `test-results/`, `playwright-report/` veya `blob-report/` klasörlerinde oluşursa bunlar çalışma artığıdır ve sürüm kontrolüne alınmaz.

## Test kapsamı

`test_monitoring_browser.py` kimlik doğrulama yönlendirmesini, temel Monitoring bölgelerini, filtre etkileşimlerini, SSE bağlantı durumunu, desteklenmeyen dosya yükleme reddini, responsive görünümü, browser console error yokluğunu ve görsel DOM/CSS sözleşmesini doğrular. Login route’unun başarılı redirect’i uygulama sözleşmesi gereği `/` olduğu için helper önce bu redirect’i bekler, ardından `/monitoring/` sayfasına gider.

Beklenen yerel sonuç, kimlik bilgileri ve uygulama sağlıklı olduğunda **8 başarılı testtir**. Kimlik bilgileri olmadan yalnızca authentication gerektirmeyen test çalışır; kalan testlerin skip edilmesi açıkça raporlanır.

## Sonuçların yorumlanması

`page` fixture bulunamıyorsa önce yanlış Python yorumlayıcısını kullandığınız kontrol edilir. `Connection refused` görülüyorsa uygulama başlatılır veya `-StartServer` kullanılır. Login sonrası URL beklemesi timeout oluyorsa test helper’ı uygulamanın gerçek redirect sözleşmesiyle karşılaştırılır. Browser console error görülüyorsa mesaj, kaynak JavaScript dosyasına kadar izlenir; test yalnızca gevşetilmez.

E2E çalışmasından sonra geçici `test-results/`, `playwright-report/`, `blob-report/`, log ve cache çıktıları gözden geçirilir. Yalnızca üretim veya audit amacı olmayan çalışma artıkları silinir; rollback yedekleri, kaynak kod, veritabanı ve audit raporları korunur.
