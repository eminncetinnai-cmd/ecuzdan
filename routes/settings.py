"""Settings routes."""

import logging
import os
import time
from datetime import datetime
from decimal import Decimal
from threading import Lock, Thread

from flask import current_app, flash, g, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from bootstrap.container import get_container  # noqa: F401
from infrastructure.demo import clear_admin_demo_data, generate_advanced_demo_data
from infrastructure.i18n import (
    SESSION_LANGUAGE_KEY,
    SESSION_LANGUAGE_SOURCE_EXPLICIT,
    SESSION_LANGUAGE_SOURCE_KEY,
    i18n,
)
from utils.audit import (
    ACTION_CAPABILITY_DENIED,
    ACTION_SPECIAL_CODE_APPLIED,
    ACTION_SPECIAL_CODE_FAILED,
    audit_log,
)
from utils.capabilities import Capability
from utils.db_session import rollback_session
from utils.decorators import login_required

logger = logging.getLogger(__name__)


def _get_standard_category_codes():
    """
    Standart kategori kodlarını veritabanından çeker.
    Tek kaynak yönetimi için scripts/seed_standard_categories.py kullanılır.
    """
    from repositories import CategoryRepository
    standard_categories = CategoryRepository().get_standard_categories()
    return {cat.code: cat.name for cat in standard_categories}


def _get_settings_service():
    from bootstrap.container import get_container  # noqa: F811

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
        from flask import session

        from repositories import CategoryRepository
        category_repo = CategoryRepository()

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
        user_categories = category_repo.get_tenant_categories(tenant_id)

        deleted_count = 0
        for category in user_categories:
            # Eğer kategori standart kodlardan birine sahip değilse sil
            if category.code not in standard_codes:
                try:
                    category_repo.delete_category(category)
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
                action = request.form.get('action', '')
                try:
                    _handle_settings_action(current_user, settings_service)
                except (ValueError, PermissionError, LookupError) as action_error:
                    rollback_session()
                    flash(str(action_error), 'error')
                target_tab = SETTINGS_ACTION_TAB_MAP.get(action, '')
                redirect_url = url_for('settings.settings') + (f"#{target_tab}" if target_tab else "")
                return redirect(redirect_url)

            return render_template('settings.html', **_with_currency_context(context))
        except Exception as e:

            logger.exception(f"Settings page error: {e}")
            rollback_session()
            flash(i18n.gettext('settings_settings_error'), 'error')
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
            flash(i18n.gettext('settings_other_sessions_closed'), 'success')
        except Exception as e:
            logger.exception(f"Logout other devices error: {e}")
            rollback_session()
            flash(i18n.gettext('settings_sessions_close_error'), 'error')
        return redirect(url_for('settings.settings'))

    @bp.route('/toggle_privacy_mode', methods=['POST'])
    @login_required
    def toggle_privacy_mode():
        """Gizlilik modunu anında açıp kapatır (üst bardaki hızlı düğme)."""
        try:
            preference = settings_service.get_preferences(session['user_id'])
            enabled = ((request.form.get('privacy_mode') or '').strip().lower() in {'on', 'true', '1', 'yes'}) if 'privacy_mode' in request.form else not (preference.privacy_mode if preference else False)
            settings_service.set_privacy_mode(session['user_id'], enabled)
            return {'success': True, 'privacy_mode': enabled}
        except Exception as e:
            logger.exception(f"Privacy mode toggle error: {e}")
            rollback_session()
            return {'success': False, 'message': i18n.gettext('settings_privacy_toggle_error')}, 500

    @bp.route('/save_theme_preference', methods=['POST'])
    @login_required
    def save_theme_preference():
        """Persist the selected theme for the authenticated user."""
        try:
            payload = request.get_json(silent=True) or {}
            theme = payload.get('theme') or request.form.get('theme', '')
            theme = str(theme).strip().lower()
            if theme not in ('light', 'dark', 'system'):
                return {'success': False, 'message': i18n.gettext('settings_theme_save_error')}, 400
            settings_service.change_theme(session['user_id'], theme)
            return {'success': True, 'theme': theme}
        except (ValueError, LookupError) as error:
            rollback_session()
            return {'success': False, 'message': str(error)}, 400
        except Exception:
            logger.exception('Theme preference save error')
            rollback_session()
            return {'success': False, 'message': i18n.gettext('settings_theme_save_error')}, 500

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
            settings_service.commit()

            flash(i18n.gettext('settings_reset_success'), 'success')
            logger.warning(f"=== RESET DATA SUCCESS === performed by {current_user.username}, tenant_id: {current_user.tenant_id}, categories cleaned: {deleted_categories}")

        except PermissionError as e:
            logger.error(f"=== RESET DATA PERMISSION ERROR === {e}")
            rollback_session()
            flash(str(e), 'error')
        except Exception as e:
            logger.error(f"=== RESET DATA EXCEPTION === {type(e).__name__}: {e}")
            logger.exception("Full exception traceback:")
            rollback_session()
            flash(i18n.gettext('settings_reset_error'), 'error')

        from flask import Response
        return Response(status=302, headers={'Location': '/settings#data'})




#: Baz para birimi olarak arayüzde sunulan fiat set. Servis katmanı
#: CurrencyManager.SUPPORTED_CURRENCIES'in tamamına karşı doğrular; burada
#: yalnızca raporlama için anlamlı olanları gösteriyoruz (XAU/BTC vb. hariç).
BASE_CURRENCY_CHOICES = ('TRY', 'USD', 'EUR', 'GBP')

SETTINGS_ACTION_TAB_MAP = {
    'update_profile': 'profile',
    'change_pw': 'profile',
    'apply_special_code': 'profile',
    'change_base_currency': 'finance',
    'update_preferences': 'finance',
    'update_notifications': 'finance',
    'change_language': 'locale',
    'change_theme': 'locale',
    'set_privacy_mode': 'locale',
    'admin_advanced_fill': 'data',
    'admin_clear_data': 'data',
}

_DB_STATS_CACHE = {
    'data': None,
    'last_updated': 0,
}
_DB_STATS_CACHE_TTL = 60  # 60 saniye önbellek


def _get_db_stats(force_refresh=False):
    now = time.time()
    cached = _DB_STATS_CACHE.get('data')
    last_updated = _DB_STATS_CACHE.get('last_updated', 0)
    if not force_refresh and cached is not None and (now - last_updated) < _DB_STATS_CACHE_TTL:
        return cached

    try:
        from application.storage_health import StorageHealthApplicationService
        root_path = current_app.root_path if current_app else '.'
        stats = StorageHealthApplicationService(root_path).db_maintenance.get_stats()
        data = {
            'size_mb': round(stats.size_bytes / (1024 * 1024), 2),
            'wal_kb': round(stats.wal_size_bytes / 1024, 1),
            'total_mb': round(stats.total_size_bytes / (1024 * 1024), 2),
            'integrity_status': stats.integrity_status,
            'foreign_key_violations': stats.foreign_key_violations,
            'freelist_count': stats.freelist_count,
            'reclaimable_kb': round(stats.reclaimable_bytes / 1024, 1),
        }
        _DB_STATS_CACHE['data'] = data
        _DB_STATS_CACHE['last_updated'] = now
        return data
    except Exception as exc:
        logger.debug("Failed to get db_stats for settings: %s", exc)
        return None

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
    context['db_stats'] = _get_db_stats()

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
            from utils.profile_image import ALLOWED_EXTENSIONS, delete_profile_image, optimize_image_file

            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                ext = '.jpg'

            old_image = current_user.profile_image
            filename = secure_filename(f"user_{current_user.id}_{int(time.time())}{ext}")
            upload_path = os.path.join('static', 'uploads', 'profiles')
            abs_upload_dir = os.path.join(current_app.root_path, upload_path)
            os.makedirs(abs_upload_dir, exist_ok=True)
            target_filepath = os.path.join(abs_upload_dir, filename)

            if not optimize_image_file(file, target_filepath, max_dim=400, quality=85):
                file.seek(0)
                file.save(target_filepath)

            new_image_url = f"/{upload_path}/{filename}".replace('\\', '/')
            settings_service.update_profile_image(current_user.id, new_image_url)

            if old_image and old_image.startswith('/static/uploads/profiles/'):
                try:
                    delete_profile_image(old_image)
                except Exception as e:
                    logger.debug("Old profile image cleanup ignored: %s", e)

            flash(i18n.gettext('settings_profile_updated'), 'success')
        return

    if action == 'change_pw':
        current_pw = request.form.get('current_pw', '').strip()
        new_pw = request.form.get('new_pw', '')
        if getattr(current_user, 'password', None) and not current_pw:
            raise ValueError("Lütfen mevcut şifrenizi girin.")
        settings_service.change_password(
            current_user.id,
            new_pw,
            current_password=current_pw if getattr(current_user, 'password', None) else None,
        )
        flash(i18n.gettext('settings_password_updated'), 'success')
        logger.info(f"User {current_user.username} changed password")
        return

    if action == 'change_base_currency':
        new_currency = request.form.get('base_currency', '').strip().upper()
        if new_currency not in BASE_CURRENCY_CHOICES:
            raise ValueError(i18n.gettext('settings_currency_invalid', value=new_currency))
        settings_service.change_base_currency(current_user.id, new_currency)
        flash(i18n.gettext('settings_currency_updated', currency=new_currency), 'success')
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
        flash(i18n.gettext('settings_preferences_updated'), 'success')
        logger.info(f"User {current_user.username} updated financial preferences")
        return

    if action == 'change_theme':
        settings_service.change_theme(current_user.id, request.form.get('theme', 'light').strip())
        flash(i18n.gettext('settings_theme_updated'), 'success')
        return

    if action == 'update_notifications':
        settings_service.update_notification_preferences(
            current_user.id,
            request.form.get('notify_budget') == 'on',
            request.form.get('notify_payments') == 'on',
            _parse_optional(request.form.get('payment_reminder_days'), int),
        )
        flash(i18n.gettext('settings_notifications_updated'), 'success')
        return

    if action == 'set_privacy_mode':
        settings_service.set_privacy_mode(
            current_user.id, request.form.get('privacy_mode') == 'on'
        )
        flash(i18n.gettext('settings_privacy_updated'), 'success')
        return

    if action == 'apply_special_code':

        from domain.users.services.special_code_service import get_special_code_service

        special_code = request.form.get('special_code', '').strip()

        if not special_code:
            flash(i18n.gettext('settings_special_code_required'), 'error')
            return

        # Check if user already used a special code
        if current_user.special_code_used_at:
            flash(i18n.gettext('settings_special_code_already_used'), 'error')
            logger.warning(f"User {current_user.username} attempted to use another special code")
            return

        # Validate the special code
        special_code_service = get_special_code_service()
        code_fingerprint = special_code_service.code_fingerprint(special_code)
        validation_result = special_code_service.validate_code(

            special_code,
            current_user.id,
            current_user.tenant_id
        )

        if not validation_result['valid']:
            reason = validation_result['error']
            flash(reason, 'error')
            logger.warning(
                "User %s attempted invalid special code (fingerprint=%s)",
                current_user.username,
                code_fingerprint,
            )
            audit_log(
                ACTION_SPECIAL_CODE_FAILED,
                user_id=current_user.id,
                username=current_user.username,
                tenant_id=current_user.tenant_id,
                details={'code_fingerprint': code_fingerprint, 'reason': reason},
            )
            settings_service.commit()
            return

        # Upgrade user role
        new_role = validation_result['role']
        old_role = current_user.role

        settings_service.apply_special_code(current_user.id, new_role, code_fingerprint)

        audit_log(
            ACTION_SPECIAL_CODE_APPLIED,
            user_id=current_user.id,
            username=current_user.username,
            tenant_id=current_user.tenant_id,
            details={
                'code_fingerprint': code_fingerprint,
                'old_role': old_role,
                'new_role': new_role,
                'capabilities': validation_result.get('metadata', {}).get('capabilities', []),
                'grants_all_capabilities': bool(
                    validation_result.get('metadata', {}).get('grants_all_capabilities')
                ),
            },
        )
        settings_service.commit()
        logger.info(
            "User %s upgraded role from %s to %s using special code fingerprint=%s",
            current_user.username,
            old_role,
            new_role,
            code_fingerprint,
        )
        flash(i18n.gettext('settings_role_upgraded', role=new_role, description=validation_result.get('description', '')), 'success')

        return

    if action == 'change_language':
        new_lang = i18n.normalize_locale(request.form.get('language', 'tr'))
        if not new_lang:
            raise ValueError(i18n.gettext('language_not_supported'))
        settings_service.change_language(current_user.id, new_lang)
        session[SESSION_LANGUAGE_KEY] = new_lang
        session[SESSION_LANGUAGE_SOURCE_KEY] = SESSION_LANGUAGE_SOURCE_EXPLICIT
        session.modified = True
        g.lang = new_lang
        flash(i18n.gettext('language_changed_success'), 'success')
        return

    if action in ['admin_clear_data', 'admin_advanced_fill']:
        if not current_user.has_capability(Capability.DEMO_DATA_WRITE):
            audit_log(
                ACTION_CAPABILITY_DENIED,
                user_id=current_user.id,
                username=current_user.username,
                tenant_id=current_user.tenant_id,
                details={'capability': Capability.DEMO_DATA_WRITE.value, 'action': action},
            )
            settings_service.commit()
            flash(i18n.gettext("ui_auto_c10b76eef09c"), 'error')
            return

        from werkzeug.security import check_password_hash

        admin_password = request.form.get('admin_pass', '').strip()
        if not current_user.password:
            # OAuth hesaplarının lokal parolası yok; şifreyle onay verilemez.
            flash(i18n.gettext("ui_auto_95672e864cbe"), 'error')
            return
        if not check_password_hash(current_user.password, admin_password):
            flash(i18n.gettext("ui_auto_ad7b8e896061"), 'error')
            return
        if action == 'admin_clear_data':
            try:
                clear_admin_demo_data(tenant_id=current_user.tenant_id)
                flash('Demo verileri temizlendi.', 'success')
            except Exception as e:
                logger.error(f"Error clearing demo data: {e}")
                flash('Demo verileri temizlenirken hata oluştu.', 'error')
        elif action == 'admin_advanced_fill':
            try:
                stats = generate_advanced_demo_data(current_user.id)
                flash(f'Geliştirilmiş 3 yıllık demo veri seti oluşturuldu: {stats.get("transactions", 0)} işlem, {stats.get("recurring_plans", 0)} plan, {stats.get("assets", 0)} varlık, {stats.get("bank_accounts", 0)} banka hesabı.', 'success')
            except Exception as e:
                logger.error(f"Error generating demo data: {e}")
                flash('Demo verileri oluşturulurken hata oluştu.', 'error')
