"""
Admin Şifre Sıfırlama Script'i
Emin kullanıcısının şifresini güvenli şekilde değiştirmek için
"""

import getpass
import re

from werkzeug.security import generate_password_hash

from app import app
from models import User, db


def validate_password(password):
    """
    Şifre güçlülük kontrolü
    - Minimum 8 karakter
    - En az 1 rakam
    - En az 1 büyük harf
    """
    if len(password) < 8:
        return False, "Şifre en az 8 karakter olmalıdır."
    if not re.search(r'\d', password):
        return False, "Şifre en az 1 rakam içermelidir."
    if not re.search(r'[A-Z]', password):
        return False, "Şifre en az 1 büyük harf içermelidir."
    return True, "Şifre geçerli."

def reset_admin_password():
    """
    Emin kullanıcısının şifresini sıfırlar
    """
    with app.app_context():
        # Emin kullanıcısını bul
        admin_user = User.query.filter_by(username='emin').first()

        if not admin_user:
            print("❌ HATA: 'emin' kullanıcısı bulunamadı.")
            return False

        print(f"✓ Kullanıcı bulundu: {admin_user.username}")
        print(f"✓ Mevcut rol: {admin_user.role}")
        print(f"✓ Tenant ID: {admin_user.tenant_id}")

        # Yeni şifre al
        print("\n" + "="*60)
        print("YENİ ŞİFRE GİRİŞİ")
        print("="*60)

        while True:
            password = getpass.getpass("Yeni şifre: ")
            confirm_password = getpass.getpass("Şifre tekrar: ")

            if password != confirm_password:
                print("❌ Şifreler eşleşmiyor. Tekrar deneyin.")
                continue

            is_valid, message = validate_password(password)
            if not is_valid:
                print(f"❌ {message}")
                continue

            break

        # Şifreyi hash'le ve güncelle
        hashed_password = generate_password_hash(password)
        admin_user.password = hashed_password
        admin_user.password_changed_at = app.config.get('CURRENT_DATETIME', None)

        try:
            db.session.commit()
            print("\n" + "="*60)
            print("✓ ŞİFRE BAŞARIYLA DEĞİŞTİRİLDİ")
            print("="*60)
            print(f"✓ Kullanıcı: {admin_user.username}")
            print(f"✓ Şifre değiştirme tarihi: {admin_user.password_changed_at}")
            print("\n⚠ Lütfen yeni şifrenizi güvenli bir yerde saklayın.")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ HATA: Şifre değiştirilemedi - {e}")
            return False

if __name__ == '__main__':
    print("="*60)
    print("E-CÜZDAN - ADMIN ŞİFRE SIFIRLAMA")
    print("="*60)
    print()

    try:
        success = reset_admin_password()
        if success:
            print("\n✓ İşlem tamamlandı.")
        else:
            print("\n❌ İşlem başarısız.")
    except KeyboardInterrupt:
        print("\n\n❌ İşlem kullanıcı tarafından iptal edildi.")
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
