"""
Background Service — infrastructure/background/background_service.py

Canlı piyasa verilerini (FX, Altın, Hava Durumu) arka planda çeken daemon thread.

Ana Sınıf: BackgroundService
  .get_live_data()         → dict: {usd, eur, gold, weather, last_updated}
  .get_market_data()       → dict: {GC=F, SI=F, CL=F, XU100.IS, BTC-USD, ^IXIC}
  .get_provider_status()   → dict: hangi provider'ın kullanıldığı

Güncelleme Döngüsü:
  _update_live_data()      → FX/gold: doviz.com → TCMB → Frankfurter → GoldAPI → yfinance
  _update_market_data()    → Tarihsel piyasa: yfinance (10y, 1mo interval)
  _update_weather()        → OpenWeatherMap API

Önbellekleme:
  instance/live_data_cache.json      → Disk önbelleği (sunucu yeniden başlarsa okunur)
  instance/market_data_cache.json    → Tarihsel piyasa önbelleği

Singleton: get_background_service() → tek örnek döner
Erişim: engines/financial_engine.py → get_live_data() → BackgroundService.get_live_data()
"""

import concurrent.futures
import json
import logging
import math
import os
import threading
import time
from datetime import datetime

import requests


# ── Lazy heavy dependencies ─────────────────────────────────────────
# pandas + yfinance cost ~0.8s at import time. They are loaded on first use.
# NOTE: A module-level __getattr__ is only consulted for *external* attribute
# access (module.pd); bare global lookups inside functions bypass it and raise
# NameError. Code in this module must therefore call _pd() / _yf().
# The helpers read globals() first so unittest.mock.patch on the module
# attribute keeps working.
def _pd():
    mod = globals().get('pd')
    if mod is None:
        import pandas as mod
        globals()['pd'] = mod
    return mod


def _yf():
    mod = globals().get('yf')
    if mod is None:
        import yfinance as mod
        globals()['yf'] = mod
        try:
            import logging
            logging.getLogger('yfinance').setLevel(logging.CRITICAL)
            if hasattr(mod, 'utils') and hasattr(mod.utils, 'get_yf_logger'):
                mod.utils.get_yf_logger().setLevel(logging.CRITICAL)
        except Exception:
            pass
    return mod


def __getattr__(name):
    if name == 'pd':
        return _pd()
    if name == 'yf':
        return _yf()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


from domain.analysis.services.fx_metals_provider import FX_KEYS, fetch_resilient_live_quotes

logger = logging.getLogger(__name__)

# Önbellek dosyaları
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
LIVE_CACHE_FILE = os.path.join(INSTANCE_DIR, 'live_data_cache.json')
MARKET_CACHE_FILE = os.path.join(INSTANCE_DIR, 'market_data_cache.json')

# Varsayılan gösterge referans verileri (Soğuk başlangıç veya ağ kesintisi koruması)
DEFAULT_INDICATIVE_RATES = {
    "weather": "+14°C",
    "usd": "49.42",
    "eur": "55.55",
    "gold": "6602.00",
    "last_updated": "2026-10-15 12:00:00",
    "is_stale": True,
}

# Ticker listesi
MARKET_ASSETS = {
    'GC=F': {'name': 'Altın', 'currency': 'USD'},
    'SI=F': {'name': 'Gümüş', 'currency': 'USD'},
    'CL=F': {'name': 'Petrol', 'currency': 'USD'},
    'XU100.IS': {'name': 'BIST100', 'currency': 'TRY'},
    'BTC-USD': {'name': 'Bitcoin', 'currency': 'USD'},
    '^IXIC': {'name': 'Nasdaq', 'currency': 'USD'}
}

class BackgroundService:
    def __init__(self, flask_app=None):
        self._flask_app = flask_app
        self._lock = threading.Lock()
        self._yf_lock = threading.Lock()
        self._live_data = {"weather": "--°C", "usd": "--", "eur": "--", "gold": "--", "last_updated": "", "is_stale": False}
        self._live_provider_status = {
            "provider_by_field": {},
            "fallback_used": False,
            "provider_error_count": 0,
            "missing_fields": list(FX_KEYS),
            "quality_status": "not_fetched",
        }
        self._market_data = {}
        self._market_df_cache = {}
        self._stop_event = threading.Event()
        self._thread = None

        # instance klasörünü oluştur
        if self._flask_app is not None and hasattr(self._flask_app, 'instance_path'):
            self._instance_dir = self._flask_app.instance_path
        else:
            self._instance_dir = INSTANCE_DIR
        os.makedirs(self._instance_dir, exist_ok=True)

        # Önbellekten yükle
        self._load_cache()

    @property
    def is_running(self) -> bool:
        """Return True if background worker thread is active and alive."""
        return self._thread is not None and self._thread.is_alive() and not self._stop_event.is_set()

    def start(self, flask_app=None):
        """Servisi başlat."""
        if flask_app is not None:
            self._flask_app = flask_app
        if self._thread is not None and self._thread.is_alive():
            logger.debug("BackgroundService zaten çalışıyor.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="ECuzdanBackgroundWorker")
        self._thread.start()
        logger.debug("BackgroundService daemon thread olarak başlatıldı.")

    def stop(self):
        """Servisi durdur"""
        self._stop_event.set()
        if self._thread:
            try:
                self._thread.join(timeout=3)
            except Exception:
                pass

    def _run(self):
        """Periyodik güncelleme döngüsü"""
        # İlk açılışta veriler boşsa veya eskiyse hemen güncelle
        logger.debug("BackgroundService ilk güncellemeyi başlatıyor...")
        self._update_all()

        # Döngü - Piyasa cache’i ve depolama saatlik, alert taraması 60 saniye.
        # self._stop_event.wait() sayesinde gereksiz 1 saniyelik CPU uyanmaları ve bağlam değişimleri önlenir,
        # durdurma sinyali (stop_event) geldiğinde ise thread gecikmesiz olarak sonlanır.
        check_interval = 3600.0
        alert_check_interval = 60.0
        storage_maint_check_interval = 3600.0

        now = time.time()
        next_update_all = now + check_interval
        next_alert_check = now + alert_check_interval
        next_storage_maint = now + storage_maint_check_interval

        while not self._stop_event.is_set():
            now = time.time()
            next_wake = min(next_update_all, next_alert_check, next_storage_maint)
            sleep_duration = max(0.5, next_wake - now)

            if self._stop_event.wait(timeout=sleep_duration):
                break

            now = time.time()
            if now >= next_alert_check:
                self._check_log_alerts()
                next_alert_check = now + alert_check_interval

            if now >= next_update_all:
                self._update_all()
                next_update_all = now + check_interval

            if now >= next_storage_maint:
                self._run_scheduled_storage_maintenance()
                next_storage_maint = now + storage_maint_check_interval

    def _run_scheduled_storage_maintenance(self):
        """Perform autonomous periodic storage and database maintenance."""
        if self._flask_app is None:
            return
        try:
            with self._flask_app.app_context():
                from application.storage_health import StorageHealthApplicationService
                from models import Notification, User
                from shared.db import db

                service = StorageHealthApplicationService(self._flask_app.root_path)
                history = service.get_history(limit=1)

                now_ts = time.time()
                seven_days = 7 * 86400
                if history and (now_ts - history[0].get("timestamp", 0)) < seven_days:
                    from database.connection import checkpoint_sqlite_wal
                    checkpoint_sqlite_wal(truncate=True)
                    logger.debug("Otonom depolama bakımı henüz gerekli değil; periyodik WAL checkpoint yapıldı.")
                    return

                logger.info("Otonom arka plan depolama bakımı başlatılıyor...")
                result = service.execute_smart_tune_up(
                    purge_cache=True,
                    create_snapshot=True,
                    trigger_source="scheduled_background",
                    user_name="Sistem (Otonom)",
                )

                if result.get("success"):
                    freed_mb = result.get("total_bytes_freed", 0) / (1024 * 1024)
                    logger.info("Otonom depolama bakımı tamamlandı: %.2f MB kurtarıldı.", freed_mb)

                    # Admin kullanıcılarına sistem bildirimi gönder
                    admin_users = User.query.filter(User.role.in_(["admin", "yonetici"])).all()
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    for user in admin_users:
                        dedupe_key = f"maint_auto:{today_str}"
                        exists = Notification.query.filter_by(user_id=user.id, dedupe_key=dedupe_key).first()
                        if not exists:
                            notif = Notification(
                                user_id=user.id,
                                tenant_id=user.tenant_id,
                                category="system",
                                title="Otonom Sistem Bakımı Tamamlandı",
                                body=f"Haftalık otonom bakım başarıyla tamamlandı. Toplam {freed_mb:.1f} MB disk alanı geri kazanıldı ve veritabanı defragmente edildi.",
                                severity="info",
                                priority="low",
                                dedupe_key=dedupe_key,
                            )
                            db.session.add(notif)
                    db.session.commit()
        except Exception as exc:
            logger.warning("Otonom depolama bakımı sırasında istisna: %s", exc)

    def _check_log_alerts(self):
        """Optional log threshold monitoring — disabled unless LOG_ALERTS_ENABLED=true."""
        try:
            from utils.log_alert_monitor import get_log_alert_monitor

            get_log_alert_monitor().check()
        except Exception as exc:
            logger.debug('Log alert check skipped: %s', exc)

    def _market_cache_is_fresh(self, max_age_seconds: float = 3600.0) -> bool:
        """Diskteki piyasa verisi önbelleği tüm varlıkları içeriyor ve tazeyse True döner."""
        with self._lock:
            if not self._market_data or not all(k in self._market_data for k in MARKET_ASSETS):
                return False
        market_file = os.path.join(self._instance_dir, 'market_data_cache.json')
        if not os.path.exists(market_file) and os.path.exists(MARKET_CACHE_FILE):
            market_file = MARKET_CACHE_FILE
        try:
            return os.path.exists(market_file) and (time.time() - os.path.getmtime(market_file)) < max_age_seconds
        except OSError:
            return False

    def _update_all(self):
        """Tüm verileri güncelle ve kaydet"""
        try:
            logger.debug("Piyasa ve canlı veriler güncelleniyor...")
            self._update_live_data()
            try:
                from domain.analysis.services.gold_tracking_service import GoldTrackingService
                GoldTrackingService().get_snapshot(force_refresh=True)
            except Exception as gold_exc:
                logger.debug("Arka plan Harem Altın önbellek ısıtması atlandı: %s", gold_exc)
            if not self._market_cache_is_fresh():
                self._update_market_data()
            try:
                from infrastructure.market.market_data_service import get_macro_economic_data
                get_macro_economic_data(allow_network=True)
            except Exception as macro_exc:
                logger.debug("Arka plan makro veri yenilemesi atlandı: %s", macro_exc)
            self._save_cache()
            logger.debug("Tüm veriler başarıyla güncellendi ve diske kaydedildi.")
        except Exception as e:
            logger.error(f"Veri güncelleme döngüsünde kritik hata: {e}", exc_info=True)

    def _fetch_weather(self) -> str:
        """Bursa hava durumunu çeker. Open-Meteo birincil, wttr.in ikincil sağlayıcıdır."""
        # 1. Open-Meteo (Yüksek erişilebilirlik, datacenter IP engeli yok, ücretsiz JSON API)
        try:
            r = requests.get(
                "https://api.open-meteo.com/v1/forecast?latitude=40.1885&longitude=29.0610&current=temperature_2m",
                timeout=(2.0, 3.0),
                headers={"User-Agent": "E-Cuzdan/15 weather-resilience"}
            )
            if getattr(r, "status_code", 0) == 200:
                json_data = r.json() if callable(getattr(r, "json", None)) else {}
                if isinstance(json_data, dict):
                    temp = json_data.get("current", {}).get("temperature_2m")
                    if temp is not None:
                        sign = "+" if float(temp) > 0 else ""
                        return f"{sign}{round(float(temp))}°C"
        except Exception as exc:
            logger.debug("Open-Meteo hava durumu hatası: %s", exc)

        # 2. wttr.in fallback
        try:
            w = requests.get(
                "https://wttr.in/Bursa?format=%t",
                timeout=(1.5, 2.5),
                headers={"User-Agent": "curl/7.68.0"}
            )
            if getattr(w, "status_code", 0) == 200:
                raw_text = getattr(w, "text", "").strip().replace(" ", "")
                if raw_text and not raw_text.startswith("<") and len(raw_text) <= 12:
                    return raw_text if "°" in raw_text else f"{raw_text}°C"
        except Exception as exc:
            logger.debug("wttr.in hava durumu hatası: %s", exc)

        # 3. Önceki geçerli önbellek veya varsayılan
        prev = self._live_data.get("weather")
        if prev and prev not in ("--", "--°C", ""):
            return prev
        return DEFAULT_INDICATIVE_RATES["weather"]

    def _update_live_data(self):
        """Hava durumu ve döviz verilerini çeker"""
        d = {"weather": "--°C", "usd": "--", "eur": "--", "gold": "--", "last_updated": ""}

        # 1. Hava durumu (Open-Meteo primary, wttr.in secondary)
        d['weather'] = self._fetch_weather()

        # 2. Döviz ve altın için ordered provider chain.
        # Doviz.com remains first; official/public fallbacks are used per missing field.
        try:
            chain_enabled = os.getenv('FX_PROVIDER_CHAIN_ENABLED', 'true').lower() == 'true'
            live_quotes = fetch_resilient_live_quotes(chain_enabled=chain_enabled)
            d.update(live_quotes.values)
            self._live_provider_status = live_quotes.safe_status()
        except Exception as exc:
            # Provider boundary must never prevent the background worker from saving old cache.
            logger.warning("Çoklu döviz/altın provider zinciri beklenmedik şekilde başarısız: %s", type(exc).__name__)
            self._live_provider_status = {
                "provider_by_field": {},
                "fallback_used": False,
                "provider_error_count": 1,
                "missing_fields": list(FX_KEYS),
                "quality_status": "cache_only_after_provider_failure",
            }

        # Başarısız veya geçersiz alanlarda yalnızca geçerli eski cache’i veya varsayılanı koru.
        stale_fields = []
        for key in ['usd', 'eur', 'gold']:
            current_value = d[key]
            try:
                is_non_finite = not math.isfinite(float(str(current_value).replace(',', '')))
            except (TypeError, ValueError):
                is_non_finite = str(current_value).strip().lower() in {'nan', 'nat', 'none', ''}
            if current_value == '--' or not current_value or is_non_finite:
                stale_fields.append(key)
                previous_value = self._live_data.get(key, '--')
                try:
                    previous_non_finite = not math.isfinite(float(str(previous_value).replace(',', '')))
                except (TypeError, ValueError):
                    previous_non_finite = str(previous_value).strip().lower() in {'nan', 'nat', 'none', ''}
                d[key] = previous_value if previous_value and previous_value != '--' and not previous_non_finite else '--'

        # Eğer sağlayıcılar başarısız olduysa veya kritik alanlar eski önbellekten sunuluyorsa stale işaretle
        is_fallback_mode = (
            len(stale_fields) >= 2
            or self._live_provider_status.get("quality_status") == "cache_only_after_provider_failure"
        )

        if is_fallback_mode:
            d['is_stale'] = True
            # Kesinti durumunda gerçek son başarılı zamanı koru; boşsa şu anı kullan
            d['last_updated'] = self._live_data.get('last_updated') or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info("Piyasa verisi kesinti koruması devrede: Son geçerli önbellek sunuluyor (Eski alanlar: %s).", stale_fields)
        else:
            d['is_stale'] = False
            d['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._lock:
            self._live_data = d

    def _fetch_single_ticker(self, ticker: str, info: dict) -> tuple[str, dict | None]:
        """yfinance üzerinden tek bir varlığın tarihsel verisini zaman sınırlı çeker."""
        try:
            logger.debug("yfinance ile veri çekiliyor: %s", ticker)
            with self._yf_lock:
                data = _yf().download(ticker, period='10y', interval='1mo', progress=False, timeout=6.0)
            if data is not None and not data.empty:
                close_prices = data[['Close']].copy()
                close_prices.columns = ['price']
                serialized = {
                    'index': close_prices.index.strftime('%Y-%m-%d').tolist(),
                    'prices': [float(x) for x in close_prices['price'].tolist()]
                }
                return ticker, {
                    'data': serialized,
                    'name': info['name'],
                    'currency': info['currency']
                }
        except Exception as e:
            logger.warning("yfinance veri çekim hatası (%s): %s", ticker, e)
        return ticker, None

    def _update_market_data(self):
        """yfinance üzerinden piyasa geçmiş verilerini eşzamanlı ve zaman sınırlı çeker"""
        with self._lock:
            temp_market_data = dict(self._market_data)

        if getattr(self, '_stop_event', None) and self._stop_event.is_set():
            return
        import sys
        if getattr(sys, 'is_finalizing', lambda: False)():
            return

        workers = min(3, len(MARKET_ASSETS))
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers, thread_name_prefix="YFWorker") as executor:
                futures = {
                    executor.submit(self._fetch_single_ticker, ticker, info): ticker
                    for ticker, info in MARKET_ASSETS.items()
                }
                # Total wall-clock bound of 12 seconds for all tickers combined
                for future in concurrent.futures.as_completed(futures, timeout=12.0):
                    ticker = futures[future]
                    try:
                        t_id, payload = future.result()
                        if payload is not None:
                            temp_market_data[t_id] = payload
                    except Exception as exc:
                        logger.warning("Ticker %s işleme hatası: %s", ticker, exc)
        except TimeoutError:
            logger.warning("Piyasa verileri indirme genel zaman aşımına (12s) uğradı; mevcut önbellek korundu.")
        except RuntimeError as exc:
            if "cannot schedule new futures" in str(exc) or "interpreter shutdown" in str(exc):
                logger.debug("Tercüman kapanırken piyasa verileri görevi sonlandırıldı: %s", exc)
            else:
                logger.warning("Piyasa verileri havuzunda çalışma zamanı hatası: %s", exc)
        except Exception as exc:
            logger.warning("Piyasa verileri havuzunda istisna: %s", exc)

        with self._lock:
            self._market_data = temp_market_data


    def _save_cache(self):
        """Önbelleği JSON dosyalarına kaydeder"""
        with self._lock:
            try:
                live_file = os.path.join(self._instance_dir, 'live_data_cache.json')
                market_file = os.path.join(self._instance_dir, 'market_data_cache.json')
                with open(live_file, 'w', encoding='utf-8') as f:
                    json.dump(self._live_data, f, ensure_ascii=False, indent=2)
                with open(market_file, 'w', encoding='utf-8') as f:
                    json.dump(self._market_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Önbellek diske yazılırken hata oluştu: {e}")

    def _load_cache(self):
        """Önbellek dosyalarını okur"""
        with self._lock:
            live_file = os.path.join(self._instance_dir, 'live_data_cache.json')
            market_file = os.path.join(self._instance_dir, 'market_data_cache.json')
            if not os.path.exists(live_file) and os.path.exists(LIVE_CACHE_FILE):
                live_file = LIVE_CACHE_FILE
            if not os.path.exists(market_file) and os.path.exists(MARKET_CACHE_FILE):
                market_file = MARKET_CACHE_FILE

            if os.path.exists(live_file):
                try:
                    with open(live_file, 'r', encoding='utf-8') as f:
                        self._live_data = json.load(f)
                    logger.debug("Canlı veri önbelleği diskten yüklendi.")
                except Exception as e:
                    logger.error(f"Canlı veri önbelleği okuma hatası: {e}")

            if os.path.exists(market_file):
                try:
                    with open(market_file, 'r', encoding='utf-8') as f:
                        self._market_data = json.load(f)
                    logger.debug("Piyasa verileri önbelleği diskten yüklendi.")
                except Exception as e:
                    logger.error(f"Piyasa verileri önbelleği okuma hatası: {e}")

    def get_live_data(self):
        """Canlı verileri döner (24 saatten eskiyse veya kesinti koruması devredeyse is_stale=True içerir)."""
        with self._lock:
            data = dict(self._live_data)
            is_stale = bool(data.get('is_stale', False))
            last_updated_str = data.get('last_updated')
            if last_updated_str:
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                    try:
                        dt = datetime.strptime(last_updated_str, fmt)
                        if (datetime.now() - dt).total_seconds() > 86400:
                            is_stale = True
                        break
                    except ValueError:
                        continue

            # Eğer değerler henüz çekilmemişse veya kesinti sebebiyle '--' ise,
            # UI'ın bozuk '-- ₺' göstermemesi için gösterge niteliğindeki referans değerleri doldur
            has_missing = any(
                data.get(k) in (None, '', '--', '--°C')
                or str(data.get(k)).strip().lower() in {'nan', 'nat', 'none'}
                for k in ('usd', 'eur', 'gold', 'weather')
            )
            if has_missing:
                is_stale = True
                for k in ('usd', 'eur', 'gold', 'weather'):
                    if data.get(k) in (None, '', '--', '--°C') or str(data.get(k)).strip().lower() in {'nan', 'nat', 'none'}:
                        data[k] = DEFAULT_INDICATIVE_RATES.get(k, '--')
                if not data.get('last_updated'):
                    data['last_updated'] = DEFAULT_INDICATIVE_RATES['last_updated']

            data['is_stale'] = is_stale
            return data

    def get_live_provider_status(self):
        """Return safe provider metadata without quote values."""
        with self._lock:
            return dict(self._live_provider_status)

    def get_market_data(self, ticker):
        """Seçili ticker için DataFrame döner"""
        with self._lock:
            asset = self._market_data.get(ticker)
            if not asset:
                return None

            serialized = asset['data']
            cached = self._market_df_cache.get(ticker)
            if cached is not None and cached[0] == id(serialized):
                return cached[1].copy()

            # Tekrar DataFrame'e dönüştür ve önbelleğe al
            pd = _pd()
            df = pd.DataFrame(
                serialized['prices'],
                index=pd.to_datetime(serialized['index']),
                columns=['price']
            )
            self._market_df_cache[ticker] = (id(serialized), df)
            return df.copy()

    def get_all_market_data(self):
        """Tüm piyasa verilerini DataFrame formatında döner"""
        with self._lock:
            result = {}
            pd = _pd() if self._market_data else None
            for ticker, info in self._market_data.items():
                serialized = info['data']
                cached = self._market_df_cache.get(ticker)
                if cached is not None and cached[0] == id(serialized):
                    df = cached[1].copy()
                else:
                    df = pd.DataFrame(
                        serialized['prices'],
                        index=pd.to_datetime(serialized['index']),
                        columns=['price']
                    )
                    self._market_df_cache[ticker] = (id(serialized), df)
                    df = df.copy()
                result[ticker] = {
                    'data': df,
                    'name': info['name'],
                    'currency': info['currency']
                }
            return result

_background_service_instance: BackgroundService | None = None

def get_background_service(flask_app=None) -> BackgroundService:
    global _background_service_instance
    if _background_service_instance is None:
        _background_service_instance = BackgroundService(flask_app=flask_app)
    elif flask_app is not None:
        _background_service_instance._flask_app = flask_app
    return _background_service_instance


def get_background_service_instance() -> BackgroundService | None:
    return _background_service_instance
