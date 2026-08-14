"""Settings routes."""

import logging
import os
import time
from datetime import datetime
from decimal import Decimal
from threading import Lock, Thread

from flask import current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from bootstrap.container import get_container
from infrastructure.i18n import i18n
from infrastructure.demo import clear_admin_demo_data, generate_advanced_demo_data
from utils.db_session import rollback_session
from utils.decorators import login_required

logger = logging.getLogger(__name__)


def _get_standard_category_codes():
    """
    Standart kategori kodlarını veritabanından çeker.
    Tek kaynak yönetimi için scripts/seed_standard_categories.py kullanılır.
    """
    from models import Category
    standard_categories = Category.query.filter_by(tenant_id=None).all()
    return {cat.code: cat.name for cat in standard_categories}


def _get_settings_service():
    from bootstrap.container import get_container
    return get_container().applications.settings()


def _cleanup_non_standard_categories(user_id):
    """
    Kullanıcının oluşturduğu standart olmayan kategorileri temizler.
    
    Args:
        user_id: Kullanıcı ID
        
    Returns:
        Silinen kategori sayısı
    """
    try:
        from models import Category, db
        from flask import session
        
        tenant_id = session.get('tenant_id')
        if not tenant_id:
            logger.debug("Tenant ID bulunamadı, kategori temizleme atlanıyor")
            return 0
        
        # Standart kategori kodlarını veritabanından çek
        standard_codes = set(_get_standard_category_codes().keys())
        
        if not standard_codes:
            logger.debug("Standart kategori bulunamadı, temizleme atlanıyor")
            return 0
        
        # Kullanıcının tenant'ına ait (tenant_id != None) kategorileri bul
        user_categories = Category.query.filter_by(tenant_id=tenant_id).all()
        
        deleted_count = 0
        for category in user_categories:
            # Eğer kategori standart kodlardan birine sahip değilse sil
            if category.code not in standard_codes:
                try:
                    db.session.delete(category)
                    deleted_count += 1
                except Exception as e:
                    logger.debug(f"Kategori silinemedi (ID: {category.id}): {e}")
        
        logger.debug(f"{deleted_count} standart olmayan kategori silindi (tenant: {tenant_id}) - commit bekliyor")
        return deleted_count
            
    except Exception as e:
        logger.exception(f"Standart olmayan kategori temizleme hatası: {e}")
        # Exception fırlatma - ana reset işlemi başarılı sayılsın
        # Cleanup başarısız olsa bile finansal veriler silindi
        return 0


def register_settings_routes(bp):
    settings_service = _get_settings_service()

    @bp.route('/settings', methods=['GET', 'POST'])
    @login_required
    def settings():
        try:
            user_id = session.get('user_id')
            if not user_id:
                return redirect(url_for('auth.login'))

            context = settings_service.page_context(user_id)
            current_user = context['current_user']
            if not current_user:
                session.clear()
                return redirect(url_for('auth.login'))

            if request.method == 'POST':
                try:
                    _handle_settings_action(current_user, settings_service)
                except (ValueError, PermissionError, LookupError) as action_error:
                    rollback_session()
                    flash(str(action_error), 'error')
                return redirect(url_for('settings.settings'))

            return render_template('settings.html', **_with_currency_context(context))
        except Exception as e:
            logger.exception(f"Settings page error: {e}")
            rollback_session()
            flash('Ayarlar işlemi sırasında bir hata oluştu.', 'error')
            return render_template(
                'settings.html',
                **_with_currency_context(settings_service.page_context(session.get('user_id')))
            )

    @bp.route('/logout_other_devices', methods=['POST'])
    @login_required
    def logout_other_devices():
        """
        Mevcut oturumu koruyup diğerlerini geçersiz kılar.

        Uygulama tek-oturum politikası uyguluyor (routes/__init__.py:329):
        User.last_session_id ile session'daki kimlik uyuşmazsa oturum kapanır.
        Bu yüzden last_session_id'yi BU oturumun kimliğine sabitlemek, başka
        yerde açık kalmış bir oturumu bir sonraki isteğinde düşürür.
        """
        try:
            settings_service.pin_session(session['user_id'], session.get('session_id'))
            flash('Diğer cihazlardaki oturumlar kapatıldı.', 'success')
        except Exception as e:
            logger.exception(f"Logout other devices error: {e}")
            rollback_session()
            flash('Oturumlar kapatılamadı.', 'error')
        return redirect(url_for('settings.settings'))

    @bp.route('/toggle_privacy_mode', methods=['POST'])
    @login_required
    def toggle_privacy_mode():
        """Gizlilik modunu anında açıp kapatır (üst bardaki hızlı düğme)."""
        try:
            preference = settings_service.get_preferences(session['user_id'])
            enabled = not (preference.privacy_mode if preference else False)
            settings_service.set_privacy_mode(session['user_id'], enabled)
            return {'success': True, 'privacy_mode': enabled}
        except Exception as e:
            logger.exception(f"Privacy mode toggle error: {e}")
            rollback_session()
            return {'success': False, 'message': 'Gizlilik modu değiştirilemedi.'}, 500

    @bp.route('/reset_data', methods=['POST'])
    @login_required
    def reset_data():
        try:
            user_id = session.get('user_id')
            if not user_id:
                logger.warning("reset_data called without user_id in session")
                from flask import Response
                return Response(status=302, headers={'Location': '/login'})

            logger.info(f"=== RESET DATA START === user_id: {user_id}")
            
            # Password validation ve tenant-scoped delete
            current_user = settings_service.reset_data(
                user_id,
                request.form.get('reset_pass', '').strip(),
            )
            
            logger.info(f"Password validation successful for user: {current_user.username}, tenant_id: {current_user.tenant_id}")
            
            # Standart olmayan kategorileri temizle (aynı transaction içinde)
            logger.info("Starting cleanup of non-standard categories")
            deleted_categories = _cleanup_non_standard_categories(user_id)
            logger.info(f"Cleanup of non-standard categories completed: {deleted_categories} deleted")
            
            # Tek commit - transaction bütünlüğü
            from shared.db import db
            db.session.commit()
            
            flash('Tüm finansal verileriniz ve portföy geçmişiniz sıfırlandı. Standart olmayan kategoriler temizlendi.', 'success')
            logger.warning(f"=== RESET DATA SUCCESS === performed by {current_user.username}, tenant_id: {current_user.tenant_id}, categories cleaned: {deleted_categories}")
            
        except PermissionError as e:
            logger.error(f"=== RESET DATA PERMISSION ERROR === {e}")
            rollback_session()
            flash(str(e), 'error')
        except Exception as e:
            logger.error(f"=== RESET DATA EXCEPTION === {type(e).__name__}: {e}")
            logger.exception("Full exception traceback:")
            rollback_session()
            flash('Veri sıfırlama sırasında hata oluştu.', 'error')
        
        from flask import Response
        return Response(status=302, headers={'Location': '/settings'})




#: Baz para birimi olarak arayüzde sunulan fiat set. Servis katmanı
#: CurrencyManager.SUPPORTED_CURRENCIES'in tamamına karşı doğrular; burada
#: yalnızca raporlama için anlamlı olanları gösteriyoruz (XAU/BTC vb. hariç).
BASE_CURRENCY_CHOICES = ('TRY', 'USD', 'EUR', 'GBP')

_ENGINE_DEFAULTS_CACHE = {
    'data': None,
    'last_updated': 0,
}
_ENGINE_DEFAULTS_CACHE_TTL = 3600  # 1 saat
_ENGINE_DEFAULTS_REFRESH_LOCK = Lock()
_ENGINE_DEFAULTS_REFRESH_IN_PROGRESS = False


def _parse_optional(raw, caster):
    """Boş bırakılan form alanını None'a, dolu olanı caster ile tipe çevirir."""
    raw = (raw or '').strip()
    if not raw:
        return None
    try:
        return caster(raw.replace(',', '.'))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"'{raw}' geçerli bir sayı değil.") from exc


def _with_currency_context(context):
    """Ayarlar context'ine baz para birimi ve finansal tercih verilerini ekler."""
    from domain.analysis.services import CurrencyManager

    current_user = context.get('current_user')
    context['base_currency_choices'] = [
        (code, CurrencyManager.SUPPORTED_CURRENCIES[code])
        for code in BASE_CURRENCY_CHOICES
        if code in CurrencyManager.SUPPORTED_CURRENCIES
    ]
    if current_user:
        context['current_base_currency'] = (
            current_user.base_currency
            if getattr(current_user, 'base_currency', None)
            else CurrencyManager.get_base_currency(tenant_id=current_user.tenant_id)
        )
        preferences = context.get('preferences')
        if preferences is None:
            preferences = getattr(current_user, 'preference', None)
        if preferences is None:
            preferences = _get_settings_service().get_preferences(current_user.id)
    else:
        context['current_base_currency'] = 'TRY'
        preferences = None

    context['preferences'] = preferences
    context['engine_defaults'] = _engine_defaults(preferences)
    context['current_year'] = datetime.now().year
    context['can_reset_data'] = _get_settings_service().can_reset_data(current_user) if current_user else False
    return context


def _apply_preferences_to_engine_defaults(defaults, preferences):
    if preferences is None:
        return defaults

    if getattr(preferences, 'risk_free_rate_mode', 'auto') == 'manual':
        manual_rate = getattr(preferences, 'risk_free_rate_manual', None)
        if manual_rate is not None:
            overridden = dict(defaults)
            overridden['risk_free_rate_pct'] = float(manual_rate) * 100
            return overridden

    return defaults


def _refresh_engine_defaults_cache():
    global _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS

    with _ENGINE_DEFAULTS_REFRESH_LOCK:
        if _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS:
            return
        _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS = True

    try:
        from engines.analysis_engine import get_dynamic_turkey_macro
        macro = get_dynamic_turkey_macro()
        if macro is None:
            return

        from engines.financial_engine import DEFAULT_EMERGENCY_FUND_MONTHS, SAFE_WITHDRAWAL_RATE
        updated_defaults = {
            'safe_withdrawal_rate_pct': SAFE_WITHDRAWAL_RATE * 100,
            'emergency_fund_months': DEFAULT_EMERGENCY_FUND_MONTHS,
            'risk_free_rate_pct': None,
        }
        if macro.get('risk_free_rate') is not None:
            updated_defaults['risk_free_rate_pct'] = macro['risk_free_rate'] * 100

        _ENGINE_DEFAULTS_CACHE['data'] = updated_defaults
        _ENGINE_DEFAULTS_CACHE['last_updated'] = time.time()
    except Exception as e:
        logger.warning(f"Engine defaults refresh failed: {e}")
    finally:
        with _ENGINE_DEFAULTS_REFRESH_LOCK:
            _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS = False


def _engine_defaults(preferences=None):
    """Tercih girilmediğinde motorların kullandığı varsayılanlar (UI'da ipucu olarak gösterilir)."""
    from engines.financial_engine import DEFAULT_EMERGENCY_FUND_MONTHS, SAFE_WITHDRAWAL_RATE

    now = time.time()
    cached_defaults = _ENGINE_DEFAULTS_CACHE.get('data')
    last_updated = _ENGINE_DEFAULTS_CACHE.get('last_updated', 0)

    if cached_defaults and (now - last_updated) < _ENGINE_DEFAULTS_CACHE_TTL:
        return _apply_preferences_to_engine_defaults(cached_defaults, preferences)

    defaults = cached_defaults or {
        'safe_withdrawal_rate_pct': SAFE_WITHDRAWAL_RATE * 100,
        'emergency_fund_months': DEFAULT_EMERGENCY_FUND_MONTHS,
        'risk_free_rate_pct': None,
    }

    if not _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS:
        Thread(target=_refresh_engine_defaults_cache, daemon=True).start()

    return _apply_preferences_to_engine_defaults(defaults, preferences)


def _handle_settings_action(current_user, settings_service):
    action = request.form.get('action', '')

    if action == 'update_profile':
        file = request.files.get('profile_image')
        if file and file.filename:
            filename = secure_filename(f"user_{current_user.id}_{file.filename}")
            upload_path = os.path.join('static', 'uploads', 'profiles')
            os.makedirs(os.path.join(current_app.root_path, upload_path), exist_ok=True)
            file.save(os.path.join(current_app.root_path, upload_path, filename))
            settings_service.update_profile_image(current_user.id, f"/{upload_path}/{filename}")
            flash('Profil resminiz başarıyla güncellendi.', 'success')
        return

    if action == 'change_pw':
        settings_service.change_password(current_user.id, request.form.get('new_pw', ''))
        flash('Şifreniz başarıyla güncellendi.', 'success')
        logger.info(f"User {current_user.username} changed password")
        return

    if action == 'change_base_currency':
        new_currency = request.form.get('base_currency', '').strip().upper()
        if new_currency not in BASE_CURRENCY_CHOICES:
            raise ValueError(f"'{new_currency}' geçerli bir baz para birimi değil.")
        settings_service.change_base_currency(current_user.id, new_currency)
        flash(f'Ana para biriminiz {new_currency} olarak güncellendi.', 'success')
        logger.info(f"User {current_user.username} changed base currency to {new_currency}")
        return

    if action == 'update_preferences':
        mode = request.form.get('risk_free_rate_mode', 'auto').strip()
        manual_pct = _parse_optional(request.form.get('risk_free_rate_manual'), float)
        swr_pct = _parse_optional(request.form.get('safe_withdrawal_rate'), float)
        settings_service.update_preferences(current_user.id, {
            'birth_year': _parse_optional(request.form.get('birth_year'), int),
            'target_retirement_age': _parse_optional(request.form.get('target_retirement_age'), int),
            'target_monthly_passive_income': _parse_optional(
                request.form.get('target_monthly_passive_income'), Decimal
            ),
            'emergency_fund_target_months': _parse_optional(
                request.form.get('emergency_fund_target_months'), int
            ),
            # Formda yüzde olarak girilir, oran olarak saklanır.
            'safe_withdrawal_rate': None if swr_pct is None else Decimal(str(swr_pct)) / 100,
            'risk_free_rate_mode': mode,
            'risk_free_rate_manual': None if manual_pct is None else Decimal(str(manual_pct)) / 100,
        })
        flash('Finansal tercihleriniz güncellendi.', 'success')
        logger.info(f"User {current_user.username} updated financial preferences")
        return

    if action == 'change_theme':
        settings_service.change_theme(current_user.id, request.form.get('theme', 'light').strip())
        flash('Görünüm tercihiniz güncellendi.', 'success')
        return

    if action == 'update_notifications':
        settings_service.update_notification_preferences(
            current_user.id,
            request.form.get('notify_budget') == 'on',
            request.form.get('notify_payments') == 'on',
            _parse_optional(request.form.get('payment_reminder_days'), int),
        )
        flash('Bildirim tercihleriniz güncellendi.', 'success')
        return

    if action == 'set_privacy_mode':
        settings_service.set_privacy_mode(
            current_user.id, request.form.get('privacy_mode') == 'on'
        )
        flash('Gizlilik modu tercihiniz güncellendi.', 'success')
        return

    if action == 'apply_special_code':
        from domain.users.services.special_code_service import get_special_code_service
        from models import User, db
        from datetime import datetime

        special_code = request.form.get('special_code', '').strip()

        if not special_code:
            flash('Özel kod gereklidir.', 'error')
            return

        # Check if user already used a special code
        if current_user.special_code_used_at:
            flash('Zaten bir özel kod kullandınız.', 'error')
            logger.warning(f"User {current_user.username} attempted to use another special code")
            return

        # Validate the special code
        special_code_service = get_special_code_service()
        validation_result = special_code_service.validate_code(
            special_code,
            current_user.id,
            current_user.tenant_id
        )

        if not validation_result['valid']:
            flash(validation_result['error'], 'error')
            logger.warning(f"User {current_user.username} attempted invalid special code: {special_code}")
            return

        # Upgrade user role
        new_role = validation_result['role']
        old_role = current_user.role

        current_user.role = new_role
        current_user.special_code = special_code
        current_user.special_code_used_at = datetime.now()

        db.session.commit()

        logger.info(f"User {current_user.username} upgraded role from {old_role} to {new_role} using special code {special_code}")
        flash(f'Rolünüz "{new_role}" olarak yükseltildi! {validation_result.get("description", "")}', 'success')
        return

    if action == 'change_language':
        new_lang = request.form.get('language', 'tr').strip()
        settings_service.change_language(current_user.id, new_lang)
        session['lang'] = new_lang
        flash(i18n.gettext('language_changed_success'), 'success')
        return

    if action in ['admin_clear_data', 'admin_advanced_fill'] and current_user.has_admin_access:
        from werkzeug.security import check_password_hash

        admin_password = request.form.get('admin_pass', '').strip()
        if not current_user.password:
            # OAuth hesaplarının lokal parolası yok; şifreyle onay verilemez.
            flash('Bu işlem şifre onayı gerektirir; OAuth hesapları için kullanılamaz.', 'error')
            return
        if not check_password_hash(current_user.password, admin_password):
            flash('Yetkilendirme Başarısız!', 'error')
            return
        if action == 'admin_clear_data':
            try:
                clear_admin_demo_data()
                flash('Demo verileri temizlendi.', 'success')
            except Exception as e:
                logger.error(f"Error clearing demo data: {e}")
                flash('Demo verileri temizlenirken hata oluştu.', 'error')
        elif action == 'admin_advanced_fill':
            try:
                stats = generate_advanced_demo_data(current_user.id)
                flash(f'Geliştirilmiş 3 yıllık demo veri seti oluşturuldu. {stats.get("transactions", 0)} işlem, {stats.get("recurring_plans", 0)} plan, {stats.get("assets", 0)} varlık.', 'success')
            except Exception as e:
                logger.error(f"Error generating demo data: {e}")
                flash('Demo verileri oluşturulurken hata oluştu.', 'error')
