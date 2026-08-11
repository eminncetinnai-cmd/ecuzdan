import json
import os

from flask import g, request, session


class I18n:
    def __init__(self, app=None):
        self.app = app
        self.translations = {}
        self.default_lang = 'tr'
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.translation_folder = os.path.join(app.root_path, 'translations')
        self.load_translations()
        app.before_request(self.before_request)
        app.context_processor(self.inject_gettext)

    def load_translations(self):
        for filename in os.listdir(self.translation_folder):
            if filename.endswith('.json'):
                lang_code = filename.split('.')[0]
                filepath = os.path.join(self.translation_folder, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)

    def get_locale(self):
        # 1. Session'da kayıtlı dil tercihi (En yüksek öncelik - anlık değişim için)
        if 'lang' in session:
            return session['lang']

        # 2. Kullanıcı veritabanında kayıtlı dil tercihi
        if 'user_id' in session:
            from models import User, db
            user = db.session.get(User, session['user_id'])
            if user and user.language:
                session['lang'] = user.language
                return user.language
        # 3. Tarayıcıdan gelen Accept-Language başlığı
        browser_lang = request.accept_languages.best_match(self.translations.keys())
        if browser_lang:
            return browser_lang
        # 4. Varsayılan dil
        return self.default_lang

    def before_request(self):
        g.lang = self.get_locale()
        session['lang'] = g.lang # Dil tercihini session'da da tut

    def gettext(self, key, **variables):
        lang = g.get('lang', self.default_lang)
        translation = self.translations.get(lang, {}).get(key, self.translations.get(self.default_lang, {}).get(key, key))
        return translation.format(**variables)

    def inject_gettext(self):
        return dict(_=self.gettext, get_locale=self.get_locale)

i18n = I18n() # Global i18n objesi
