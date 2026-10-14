"""
E-Cüzdan v15 - Kapsamlı Simülasyon Testi
Tüm sayfaları ve veri girişlerini test eden otomatik test scripti
"""
import json
import re
from datetime import datetime

import requests

BASE_URL = "http://127.0.0.1:5000"
session = requests.Session()

test_results = []

def log_test(test_name, status, details=""):
    """Test sonucunu kaydet"""
    result = {
        "test": test_name,
        "status": status,
        "details": details,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    test_results.append(result)
    status_symbol = "[PASS]" if status == "PASS" else "[FAIL]"
    print(f"{status_symbol} {test_name}: {status}")
    if details:
        print(f"   Details: {details}")

def test_homepage():
    """Ana sayfa testi"""
    try:
        response = session.get(BASE_URL)
        if response.status_code in [200, 302]:
            log_test("Ana Sayfa Erişimi", "PASS", f"Status: {response.status_code}")
            return True
        else:
            log_test("Ana Sayfa Erişimi", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Ana Sayfa Erişimi", "FAIL", str(e))
        return False

def test_login_page():
    """Login sayfası testi"""
    try:
        response = session.get(f"{BASE_URL}/login")
        if response.status_code == 200:
            log_test("Login Sayfası", "PASS", "Sayfa başarıyla yüklendi")
            return True
        else:
            log_test("Login Sayfası", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Login Sayfası", "FAIL", str(e))
        return False

def test_login():
    """Login işlemi testi"""
    try:
        # Önce login sayfasından CSRF token al
        csrf_token = get_csrf_token(f"{BASE_URL}/login")

        data = {
            "username": "emin",
            "password": "1"  # Veritabanında varsayılan şifre "1"
        }

        if csrf_token:
            data["csrf_token"] = csrf_token

        response = session.post(f"{BASE_URL}/login", data=data, allow_redirects=False)

        if response.status_code == 302:
            log_test("Login İşlemi", "PASS", "Kullanıcı başarıyla giriş yaptı")
            return True
        else:
            log_test("Login İşlemi", "FAIL", f"Status: {response.status_code}, expected 302 redirect")
            return False
    except Exception as e:
        log_test("Login İşlemi", "FAIL", str(e))
        return False

def test_dashboard():
    """Dashboard sayfası testi"""
    try:
        response = session.get(f"{BASE_URL}/")
        if response.status_code == 200:
            log_test("Dashboard Sayfası", "PASS", "Dashboard başarıyla yüklendi")
            return True
        else:
            log_test("Dashboard Sayfası", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Dashboard Sayfası", "FAIL", str(e))
        return False

def test_transactions_page():
    """İşlem sayfası testi"""
    try:
        response = session.get(f"{BASE_URL}/transactions")
        if response.status_code == 200:
            log_test("İşlem Sayfası", "PASS", "İşlem sayfası başarıyla yüklendi")
            return True
        else:
            log_test("İşlem Sayfası", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("İşlem Sayfası", "FAIL", str(e))
        return False

def get_csrf_token(url):
    """Sayfadan CSRF token al"""
    try:
        response = session.get(url)
        if response.status_code == 200:
            # Basit CSRF token extraction - HTML'den ara
            match = re.search(r'name="csrf_token"\s+value="([^"]+)"', response.text)
            if match:
                return match.group(1)
    except (requests.RequestException, re.error):
        pass
    return None

def test_add_transaction():
    """İşlem ekleme testi"""
    try:
        # Önce sayfayı al ve CSRF token al
        csrf_token = get_csrf_token(f"{BASE_URL}/transactions")

        data = {
            "description": "Test İşlemi",
            "amount": "100.50",
            "category": "Aylık Sabit Gider",  # Mevcut kategori kullan
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": "Ödendi",
            "note": "Test notu"
        }

        if csrf_token:
            data["csrf_token"] = csrf_token

        response = session.post(f"{BASE_URL}/new_transaction", data=data, allow_redirects=False)

        if response.status_code in [302, 200]:
            log_test("İşlem Ekleme", "PASS", "Test işlemi başarıyla eklendi")
            return True
        else:
            log_test("İşlem Ekleme", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("İşlem Ekleme", "FAIL", str(e))
        return False

def test_categories_page():
    """Kategori sayfası testi"""
    try:
        response = session.get(f"{BASE_URL}/categories")
        if response.status_code == 200:
            log_test("Kategori Sayfası", "PASS", "Kategori sayfası başarıyla yüklendi")
            return True
        else:
            log_test("Kategori Sayfası", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Kategori Sayfası", "FAIL", str(e))
        return False

def test_add_category():
    """Kategori ekleme testi"""
    try:
        # Önce sayfayı al ve CSRF token al
        csrf_token = get_csrf_token(f"{BASE_URL}/categories")

        # Benzersiz kategori adı oluştur
        import random
        unique_name = f"Test Kategori {random.randint(1000, 9999)}"

        data = {
            "action": "add_cat",
            "name": unique_name,
            "type": "Gider"
        }

        if csrf_token:
            data["csrf_token"] = csrf_token

        response = session.post(f"{BASE_URL}/categories", data=data, allow_redirects=False)

        if response.status_code in [302, 200]:
            log_test("Kategori Ekleme", "PASS", f"Test kategorisi başarıyla eklendi: {unique_name}")
            return True
        else:
            log_test("Kategori Ekleme", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Kategori Ekleme", "FAIL", str(e))
        return False

def test_assets_page():
    """Varlık sayfası testi"""
    try:
        response = session.get(f"{BASE_URL}/assets_management")
        if response.status_code == 200:
            log_test("Varlık Sayfası", "PASS", "Varlık sayfası başarıyla yüklendi")
            return True
        else:
            log_test("Varlık Sayfası", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Varlık Sayfası", "FAIL", str(e))
        return False

def test_add_asset():
    """Varlık ekleme testi"""
    try:
        # Önce sayfayı al ve CSRF token al
        csrf_token = get_csrf_token(f"{BASE_URL}/assets_management")

        # Benzersiz varlık adı oluştur
        import random
        unique_name = f"Test Varlık {random.randint(1000, 9999)}"

        data = {
            "type": "Nakit",
            "name": unique_name,
            "symbol": "TEST",
            "currency": "TRY",
            "description": "Test açıklama",
            "quantity": "10",
            "unit_price": "100",
            "value": "1000",
            "purchase_date": datetime.now().strftime("%Y-%m-%d"),
            "purchase_cost": "1000",
            "risk_level": "Orta",
            "liquidity": "Likit",
            "sector_id": "1",
            "sync_cash": "on"
        }

        if csrf_token:
            data["csrf_token"] = csrf_token

        response = session.post(f"{BASE_URL}/new_asset", data=data, allow_redirects=False)

        if response.status_code in [302, 200]:
            log_test("Varlık Ekleme", "PASS", f"Test varlığı başarıyla eklendi: {unique_name}")
            return True
        else:
            log_test("Varlık Ekleme", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Varlık Ekleme", "FAIL", str(e))
        return False

def test_plans_page():
    """Planlar sayfası testi"""
    try:
        response = session.get(f"{BASE_URL}/plans")
        if response.status_code == 200:
            log_test("Planlar Sayfası", "PASS", "Planlar sayfası başarıyla yüklendi")
            return True
        else:
            log_test("Planlar Sayfası", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Planlar Sayfası", "FAIL", str(e))
        return False

def test_settings_page():
    """Ayarlar sayfası testi"""
    try:
        response = session.get(f"{BASE_URL}/settings")
        if response.status_code == 200:
            log_test("Ayarlar Sayfası", "PASS", "Ayarlar sayfası başarıyla yüklendi")
            return True
        else:
            log_test("Ayarlar Sayfası", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Ayarlar Sayfası", "FAIL", str(e))
        return False

def test_language_switching():
    """Dil değiştirme testi"""
    try:
        # Türkçe
        response_tr = session.get(f"{BASE_URL}/set_language/tr")
        # İngilizce
        response_en = session.get(f"{BASE_URL}/set_language/en")

        if response_tr.status_code == 200 and response_en.status_code == 200:
            log_test("Dil Değiştirme", "PASS", "Dil değiştirme başarılı")
            return True
        else:
            log_test("Dil Değiştirme", "FAIL", f"TR: {response_tr.status_code}, EN: {response_en.status_code}")
            return False
    except Exception as e:
        log_test("Dil Değiştirme", "FAIL", str(e))
        return False

def test_logout():
    """Çıkış işlemi testi"""
    try:
        response = session.get(f"{BASE_URL}/logout", allow_redirects=False)
        if response.status_code in [302, 200]:
            log_test("Çıkış İşlemi", "PASS", "Çıkış başarılı")
            return True
        else:
            log_test("Çıkış İşlemi", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Çıkış İşlemi", "FAIL", str(e))
        return False

def generate_report():
    """Detaylı test raporu oluştur"""
    print("\n" + "="*60)
    print("E-CÜZDAN V15 - KAPSAMLI SİMÜLASYON TEST RAPORU")
    print("="*60)
    print(f"Test Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Toplam Test Sayısı: {len(test_results)}")

    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")

    print(f"Başarılı: {passed}")
    print(f"Başarısız: {failed}")
    print(f"Başarı Oranı: %{(passed/len(test_results)*100):.1f}" if test_results else "N/A")
    print("="*60)

    print("\nDetaylı Test Sonuçları:")
    print("-"*60)
    for result in test_results:
        status_symbol = "[PASS]" if result["status"] == "PASS" else "[FAIL]"
        print(f"{status_symbol} {result['test']}: {result['status']}")
        if result['details']:
            print(f"   - {result['details']}")
        print(f"   - Zaman: {result['timestamp']}")

    print("="*60)

    # Raporu dosyaya kaydet
    with open("test_report.json", "w", encoding="utf-8") as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)

    print("\nRapor 'test_report.json' dosyasına kaydedildi.")
    print("="*60)

def main():
    """Ana test fonksiyonu"""
    print("E-Cüzdan v15 - Kapsamlı Simülasyon Testi Başlatılıyor...")
    print("="*60)

    # Testleri sırasıyla çalıştır
    test_homepage()
    test_login_page()
    test_login()
    test_dashboard()
    test_transactions_page()
    test_add_transaction()
    test_categories_page()
    test_add_category()
    test_assets_page()
    test_add_asset()
    test_plans_page()
    test_settings_page()
    test_language_switching()
    test_logout()

    # Rapor oluştur
    generate_report()

if __name__ == "__main__":
    main()
