import json
import os

from flask import g, has_request_context, request, session  # noqa: F401

DEFAULT_LANGUAGE = 'tr'
SESSION_LANGUAGE_KEY = 'lang'
SESSION_LANGUAGE_SOURCE_KEY = 'lang_source'
SESSION_LANGUAGE_SOURCE_EXPLICIT = 'explicit'
SESSION_LANGUAGE_SOURCE_USER = 'user'


class _PreserveMissingFormat(dict):
    """Keep untranslated format placeholders intact when no runtime value is supplied."""

    def __missing__(self, key):
        return "{" + key + "}"


class I18n:
    def __init__(self, app=None):
        self.app = app
        self.translations = {}
        self.default_lang = DEFAULT_LANGUAGE
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.translation_folder = os.path.join(app.root_path, 'translations')
        self.load_translations()

        # Flask, ilk istekten sonra yeni setup hook'u kaydetmeye izin vermez.
        # Testler ve uygulama factory'leri aynı Flask instance'ını yeniden
        # başlatabildiği için hook kaydını idempotent ve geç başlatmaya dayanıklı
        # tutuyoruz.
        extensions = getattr(app, 'extensions', {})
        if extensions.get('e_cuzdan_i18n') is self:
            return
        if not getattr(app, '_got_first_request', False):
            app.before_request(self.before_request)
            app.context_processor(self.inject_gettext)
        extensions['e_cuzdan_i18n'] = self

    def load_translations(self):
        for filename in os.listdir(self.translation_folder):
            if filename.endswith('.json'):
                lang_code = filename.split('.')[0]
                filepath = os.path.join(self.translation_folder, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)

    def normalize_locale(self, value):
        """Return a supported base locale, or ``None`` for invalid input."""
        candidate = str(value or '').strip().lower().replace('_', '-')
        if candidate in self.translations:
            return candidate
        base = candidate.split('-', 1)[0]
        return base if base in self.translations else None

    def _normalize_locale(self, value):
        """Return a supported base locale or the default language."""
        return self.normalize_locale(value) or self.default_lang

    def get_locale(self):
        """Resolve locale without allowing browser preferences to overwrite user intent.

        Order is intentionally explicit: an explicitly selected session locale wins,
        then the authenticated user's persisted preference, then the Turkish default.
        Browser ``Accept-Language`` is deliberately not used as an automatic
        preference because it made a first anonymous visit persist (for example)
        Italian and later mask the user's Turkish selection.
        """
        session_lang = session.get(SESSION_LANGUAGE_KEY)
        if session_lang and session.get(SESSION_LANGUAGE_SOURCE_KEY) == SESSION_LANGUAGE_SOURCE_EXPLICIT:
            return self._normalize_locale(session_lang)

        if 'user_id' in session:
            from models import User, db
            user = db.session.get(User, session['user_id'])
            if user and user.language:
                user_lang = self._normalize_locale(user.language)
                session[SESSION_LANGUAGE_KEY] = user_lang
                session[SESSION_LANGUAGE_SOURCE_KEY] = SESSION_LANGUAGE_SOURCE_USER
                return user_lang

        return self.default_lang

    def before_request(self):
        locale = self.get_locale()
        g.lang = locale
        if 'user_id' in session or session.get(SESSION_LANGUAGE_SOURCE_KEY) == SESSION_LANGUAGE_SOURCE_EXPLICIT:
            session[SESSION_LANGUAGE_KEY] = locale
        else:
            # Legacy/browser-derived session values must not become preferences.
            session.pop(SESSION_LANGUAGE_KEY, None)
            session.pop(SESSION_LANGUAGE_SOURCE_KEY, None)

    def gettext(self, key, **variables):
        lang = g.get('lang', self.default_lang)
        translation = self.translations.get(lang, {}).get(key, self.translations.get(self.default_lang, {}).get(key, key))
        return translation.format_map(_PreserveMissingFormat(variables))

    def inject_gettext(self):
        locale = self.get_locale() if has_request_context() else self.default_lang
        return dict(
            _=self.gettext,
            get_locale=self.get_locale,
            lang=locale,
            available_languages=tuple(sorted(self.translations)),
            translation_catalog=self.translations.get(locale, {}),
        )

i18n = I18n() # Global i18n objesi
