# E-Cüzdan v15 - PythonAnywhere Dağıtım Rehberi
## (Hiç Bilmeyenler İçin Adım Adım Rehber)

Bu rehber, E-Cüzdan v15 projesini PythonAnywhere ücretsiz sunucusuna yüklemek için her adımı detaylı şekilde anlatır. Bilgisayar bilgisi gerektirmez, sadece talimatları takip etmeniz yeterli.

---

## KISIM 1: GitHub'a Proje Yükleme (Bilgisayarınızda)

### Adım 1: GitHub Hesabı Oluşturma

1. Tarayıcınızda [https://github.com](https://github.com) adresine gidin
2. Sağ üstte "Sign up" butonuna tıklayın
3. Formu doldurun:
   - Username: Kullanıcı adınız (örn: ahmet123)
   - Email: E-posta adresiniz
   - Password: Güçlü bir şifre
4. "Create account" butonuna tıklayın
5. E-posta adresinize gelen doğrulama linkine tıklayın

### Adım 2: GitHub'da Yeni Repository Oluşturma

1. GitHub'da giriş yapın
2. Sağ üstte yeşil "+" butonuna tıklayın
3. "New repository" seçeneğini seçin
4. Repository ismi olarak `e-cuzdan-v15` yazın
5. "Public" seçeneğini seçin
6. "Create repository" butonuna tıklayın

### Adım 3: Projenizi GitHub'a Yükleme

1. Bilgisayarınızda proje klasörünü açın (e-cuzdan-v15)
2. Klasör içinde boş bir yere sağ tıklayın
3. "Git Bash Here" seçeneğini seçin (Git yüklü değilse önce Git'i indirin)
4. Açılan siyah ekrana sırayla şu komutları yazın ve Enter'a basın:

```bash
git init
git add .
git commit -m "İlk yükleme"
git remote add origin https://github.com/KULLANICI_ADINIZ/e-cuzdan-v15.git
git branch -M main
git push -u origin main
```

**ÖNEMLİ:** `KULLANICI_ADINIZ` kısmını kendi GitHub kullanıcı adınızla değiştirin!

5. GitHub kullanıcı adı ve şifrenizi sorulduğunda girin
6. Yükleme tamamlandığında "Success" mesajını göreceksiniz

---

## KISIM 2: PythonAnywhere Hesabı Oluşturma

### Adım 4: PythonAnywhere Kayıt

1. Tarayıcınızda [https://www.pythonanywhere.com](https://www.pythonanywhere.com) adresine gidin
2. Sağ üstte "Pricing & signup" butonuna tıklayın
3. "Create a free account" (Beginner account) seçeneğini seçin
4. Formu doldurun:
   - Username: Kullanıcı adınız (örn: ahmetcuzdan)
   - Email: E-posta adresiniz
   - Password: Güçlü bir şifre
5. "Create account" butonuna tıklayın
6. E-posta adresinize gelen doğrulama linkine tıklayın
7. PythonAnywhere'e giriş yapın

---

## KISIM 3: PythonAnywhere'de Kurulum

### Adım 5: Web Uygulaması Oluşturma

1. PythonAnywhere panelinde üst menüden **"Web"** sekmesine tıklayın
2. **"Add a new web app"** (mavi buton) butonuna tıklayın
3. **"Flask"** seçeneğini seçin ve **"Next"** butonuna tıklayın
4. **"Python 3.10"** seçeneğini seçin (veya mevcut en son sürüm)
5. **"Next"** butonuna tıklayın
6. **"Manual configuration"** (Manuel konfigürasyon) seçeneğini seçin
7. **"Next"** butonuna tıklayın
8. Sonraki sayfada domain adınızı not alın (örn: ahmetcuzdan.pythonanywhere.com)
9. **"Next"** ile devam edin

### Adım 6: Proje Dosyalarını İndirme

1. PythonAnywhere panelinde üst menüden **"Files"** sekmesine tıklayın
2. **"Open a bash console"** (mavi buton) butonuna tıklayın
3. Açılan siyah ekrana şu komutu yazın ve Enter'a basın:

```bash
git clone https://github.com/KULLANICI_ADINIZ/e-cuzdan-v15.git
```

**ÖNEMLİ:** `KULLANICI_ADINIZ` kısmını kendi GitHub kullanıcı adınızla değiştirin!

4. Proje indirildikten sonra şu komutu yazın:

```bash
cd e-cuzdan-v15
```

5. Şu komutla dosyaların geldiğini kontrol edin:

```bash
ls
```

`app.py`, `requirements.txt` gibi dosyaları görmelisiniz.

### Adım 7: Virtual Environment Oluşturma

Virtual environment, projenizin kütüphanelerini izole tutan özel bir alandır.

1. Aynı bash ekranında şu komutu yazın:

```bash
python3 -m venv venv
```

Bu işlem birkaç saniye sürebilir.

2. Virtual environment'ı aktifleştirin:

```bash
source venv/bin/activate
```

Komut satırının başında `(venv)` yazısını görmelisiniz.

3. Projenin gerektirdiği kütüphaneleri yükleyin:

```bash
pip install -r requirements.txt
```

Bu işlem 1-2 dakika sürebilir. Bekleyin ve tamamlanınca devam edin.

### Adım 8: .env Dosyası Oluşturma

.env dosyası, uygulamanın gizli ayarlarını tutan önemli bir dosyadır.

1. Aynı bash ekranında şu komutu yazın:

```bash
cp .env.example .env
```

2. .env dosyasını düzenlemek için şu komutu yazın:

```bash
nano .env
```

3. Açılan editörde şu değişiklikleri yapın:

```
SECRET_KEY=buraya_cok_guvenli_rastgele_bir_anahtar_girin
SESSION_TIMEOUT_HOURS=2
```

**ÖNEMLİ NOTLAR:**
- `SECRET_KEY` kısmına rastgele karakterler yazın (örn: x7k9m2p5q8r3t6)
- `DATABASE_URL` satırını SİLİN (artık gerekli değil, kod otomatik hallediyor)
- Diğer satırları olduğu gibi bırakın

4. Dosyayı kaydetmek için:
   - `Ctrl + X` tuşlarına basın
   - `Y` tuşuna basın
   - `Enter` tuşuna basın

### Adım 9: WSGI Dosyasını Düzenleme

WSGI dosyası, PythonAnywhere'in uygulamanızı nasıl çalıştıracağını belirler.

1. PythonAnywhere panelinde **"Files"** sekmesine geri dönün
2. `e-cuzdan-v15` klasörüne tıklayın
3. `pythonanywhere_wsgi.py` dosyasını bulun
4. Dosya adının yanındaki kalem ikonuna tıklayarak düzenleyin
5. `project_home` satırını bulun ve şu şekilde değiştirin:

```python
project_home = '/home/KULLANICI_ADINIZ/e-cuzdan-v15'
```

**ÖNEMLİ:** `KULLANICI_ADINIZ` kısmını kendi PythonAnywhere kullanıcı adınızla değiştirin!

6. Dosyayı kaydedmek için sağ üstteki "Save" butonuna tıklayın

### Adım 10: Web Uygulaması Konfigürasyonu

1. PythonAnywhere panelinde **"Web"** sekmesine geri dönün
2. **"WSGI configuration file"** kısmına tıklayın
3. Dosya yolunu şu şekilde ayarlayın:

```
/home/KULLANICI_ADINIZ/e-cuzdan-v15/pythonanywhere_wsgi.py
```

**ÖNEMLİ:** `KULLANICI_ADINIZ` kısmını kendi PythonAnywhere kullanıcı adınızla değiştirin!

4. **"Virtualenv"** kısmına tıklayın
5. Virtual environment yolunu şu şekilde ayarlayın:

```
/home/KULLANICI_ADINIZ/e-cuzdan-v15/venv
```

6. **"Save"** butonuna tıklayın

### Adım 11: Static Files Konfigürasyonu

Static files, CSS, JavaScript ve resim gibi dosyalardır.

1. **"Web"** sekmesinde **"Static files"** kısmına gidin
2. **"Enter a new static files entry"** kısmına şu bilgileri girin:

   - **URL**: `/static/`
   - **Directory**: `/home/KULLANICI_ADINIZ/e-cuzdan-v15/static`

3. **"Save"** butonuna tıklayın

4. İkinci bir static files entry ekleyin:

   - **URL**: `/uploads/`
   - **Directory**: `/home/KULLANICI_ADINIZ/e-cuzdan-v15/static/uploads`

5. **"Save"** butonuna tıklayın

**ÖNEMLİ:** Her iki yerde de `KULLANICI_ADINIZ` kısmını kendi PythonAnywhere kullanıcı adınızla değiştirin!

### Adım 12: Uygulamayı Başlatma

1. **"Web"** sekmesinde **"Reload"** butonuna tıklayın
2. Birkaç saniye bekleyin
3. Sayfanın üstündeki yeşil "Running" yazısını görmelisiniz
4. Domain adınıza tıklayarak uygulamanızı açın:
   - Örnek: `https://ahmetcuzdan.pythonanywhere.com`

---

## KISIM 4: Test ve Kontrol

### Adım 13: Uygulamayı Test Etme

1. Açılan sayfada login ekranını görmelisiniz
2. Kullanıcı adı: `emin`
3. Şifre: `1`
4. "Giriş Yap" butonuna tıklayın
5. Dashboard sayfasını görmelisiniz
6. Başarılı! 🎉

---

## SIK KARŞILAŞILAN SORUNLAR VE ÇÖZÜMLERİ

### Sorun 1: "ModuleNotFoundError" Hatası

**Hata:** Uygulama çalışmıyor, modül bulunamıyor diyor.

**Çözüm:**
1. PythonAnywhere panelinde **"Files"** sekmesine gidin
2. **"Open a bash console"** butonuna tıklayın
3. Şu komutları sırayla yazın:

```bash
cd e-cuzdan-v15
source venv/bin/activate
pip install -r requirements.txt
```

4. **"Web"** sekmesine dönün ve **"Reload"** butonuna tıklayın

### Sorun 2: "500 Internal Server Error" Hatası

**Hata:** Sayfa açılmıyor, 500 hatası veriyor.

**Çözüm:**
1. **"Web"** sekmesinde **"Error log"** linkine tıklayın
2. Hata mesajını okuyun
3. Çoğu zaman .env dosyası veya WSGI dosyası hatasıdır
4. Bu dosyaları kontrol edin ve düzeltin
5. **"Reload"** butonuna tıklayın

### Sorun 3: Veritabanı Hatası

**Hata:** Veritabanı ile ilgili hatalar.

**Çözüm:**
1. Bash console'da şu komutu yazın:

```bash
cd e-cuzdan-v15
rm e_cuzdan_v15.db
```

2. Uygulamayı yeniden açın, veritabanı otomatik oluşturulacaktır

### Sorun 4: Login Yapılamıyor

**Hata:** Kullanıcı adı veya şifre hatalı diyor.

**Çözüm:**
- Kullanıcı adı: `emin`
- Şifre: `1`
- Bu varsayılan bilgilerdir, değiştirmeyin

---

## GÜVENLİK İPUÇLARI

1. **SECRET_KEY'i asla paylaşmayın** - Bu uygulamanızın ana anahtarıdır
2. **.env dosyasını GitHub'a yüklemeyin** - Zaten .gitignore dosyasında korunuyor
3. **Ücretsiz hesapta SSL sertifikası otomatik verilir** - HTTPS kullanın
4. **Düzenli yedek alın** - Veritabanı dosyasını indirin
5. **Güçlü şifre kullanın** - PythonAnywhere ve GitHub şifrelerinizi güçlü tutun

---

## PROJEYİ GÜNCELLEME

Eğer projeyi güncellerseniz (yeni özellikler eklerseniz):

1. Bilgisayarınızda değişiklikleri GitHub'a yükleyin:

```bash
git add .
git commit -m "Güncelleme"
git push origin main
```

2. PythonAnywhere'de bash console açın:

```bash
cd e-cuzdan-v15
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
```

3. **"Web"** sekmesinde **"Reload"** butonuna tıklayın

---

## BAŞARI KONTROL LİSTESİ

- [ ] GitHub hesabı oluşturuldu
- [ ] GitHub repository oluşturuldu
- [ ] Proje GitHub'a yüklendi
- [ ] PythonAnywhere hesabı oluşturuldu
- [ ] Web uygulaması oluşturuldu
- [ ] Proje PythonAnywhere'e indirildi
- [ ] Virtual environment oluşturuldu
- [ ] Kütüphaneler yüklendi
- [ ] .env dosyası oluşturuldu
- [ ] WSGI dosyası düzenlendi
- [ ] Web uygulaması konfigüre edildi
- [ ] Static files ayarlandı
- [ ] Uygulama başlatıldı
- [ ] Login test edildi
- [ ] Dashboard görüldü

---

## DESTEK VE YARDIM

Eğer sorun yaşarsanız:

1. **Error log kontrolü:** PythonAnywhere'de "Web" sekmesinde "Error log" linkine tıklayın
2. **Log dosyası:** Bash console'da `tail -f e_cuzdan.log` komutu ile uygulama loglarını görün
3. **PythonAnywhere forumları:** https://www.pythonanywhere.com/forums/
4. **GitHub Issues:** Proje repository'sinde issue açabilirsiniz

---

## TEBRİKLER! 🎉

Her şey doğru yapılandırıldıysa, uygulamanız şu adreste erişilebilir:

```
https://KULLANICI_ADINIZ.pythonanywhere.com
```

E-Cüzdan v15 uygulamanız artık internette çalışıyor!

---

## EK BİLGİ: ARKA PLAN VERİ GÜNCELLEME SERVİSİ (V15+)

E-Cüzdan v15, sayfa yükleme sürelerini sıfıra indirmek için asenkron bir Arka Plan Servisi (`BackgroundService`) barındırır:
1. **Çalışma Prensibi:** Uygulama başladığında otomatik olarak arka planda çalışmaya başlayan bir Daemon Thread, dış servislerden (`yfinance`, `wttr.in`, `doviz.com`) döviz, hava durumu ve makroekonomik verileri çekerek `instance/` klasörü altına `live_data_cache.json` ve `market_data_cache.json` formatında önbelleğe alır. Sayfalar yüklendiğinde dış ağ istekleri beklenmez, anında bu önbellek sunulur.
2. **Çevrimdışı Mod (Graceful Degradation):** İnternet bağlantısı koptuğunda veya dış servisler çöktüğünde, sistem hata vermez ve diskteki son başarılı önbellek verileriyle kesintisiz çalışmaya devam eder.
3. **PythonAnywhere Dosya Yetkileri:** PythonAnywhere üzerinde `instance/` klasörünün yazma yetkileri açık olmalıdır (sistem tarafından otomatik oluşturulur).
4. **Temiz Mimari:** v15 sürümünde kullanılmayan eski geliştirici kalıntıları (`_arsiv/` dizini), geçici vbs scriptleri ve mükerrer veritabanı dosyaları kaldırılmış; proje tamamen stabilize edilmiştir.
