"""
Background Update Service for E-Cüzdan v15
Asenkron veri çekme, önbellekleme ve hata toleransı yönetimi.
"""

import json
import logging
import os
import threading
import time
from datetime import datetime

import pandas as pd
import requests
import yfinance as yf
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Önbellek dosyaları
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
LIVE_CACHE_FILE = os.path.join(INSTANCE_DIR, 'live_data_cache.json')
MARKET_CACHE_FILE = os.path.join(INSTANCE_DIR, 'market_data_cache.json')

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
    def __init__(self):
        self._lock = threading.Lock()
        self._live_data = {"weather": "--°C", "usd": "--", "eur": "--", "gold": "--", "last_updated": ""}
        self._market_data = {}
        self._stop_event = threading.Event()
        self._thread = None

        # instance klasörünü oluştur
        os.makedirs(INSTANCE_DIR, exist_ok=True)

        # Önbellekten yükle
        self._load_cache()

    def start(self):
        """Servisi başlat"""
        if self._thread is not None and self._thread.is_alive():
            logger.info("BackgroundService zaten çalışıyor.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="ECuzdanBackgroundWorker")
        self._thread.start()
        logger.info("BackgroundService daemon thread olarak başlatıldı.")

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
        logger.info("BackgroundService ilk güncellemeyi başlatıyor...")
        self._update_all()

        # Döngü - Her saat başı güncelle (veya stop_event tetiklenirse çık)
        # Saniyeler halinde uyuyarak stop_event kontrolünü sıklaştırıyoruz
        check_interval = 3600  # 1 saat (3600 saniye)
        elapsed = 0

        while not self._stop_event.is_set():
            time.sleep(1)
            elapsed += 1
            if elapsed >= check_interval:
                self._update_all()
                elapsed = 0

    def _update_all(self):
        """Tüm verileri güncelle ve kaydet"""
        try:
            logger.info("Piyasa ve canlı veriler güncelleniyor...")
            self._update_live_data()
            self._update_market_data()
            self._save_cache()
            logger.info("Tüm veriler başarıyla güncellendi ve diske kaydedildi.")
        except Exception as e:
            logger.error(f"Veri güncelleme döngüsünde kritik hata: {e}", exc_info=True)

    def _update_live_data(self):
        """Hava durumu ve döviz verilerini çeker"""
        d = {"weather": "--°C", "usd": "--", "eur": "--", "gold": "--", "last_updated": ""}

        def _to_2dp(raw: str) -> str:
            """Ham string değeri (virgül/nokta karışık) 2 ondalık haneli ₺ formatına çevirir."""
            try:
                normalized = raw.replace('.', '').replace(',', '.').strip()
                return f"{float(normalized):,.2f}"
            except Exception:
                # Sadece virgülle dene
                try:
                    return f"{float(raw.replace(',', '.').strip()):,.2f}"
                except Exception:
                    return raw  # parse edilemezse orijinal bırak

        # 1. Hava durumu
        try:
            w = requests.get("https://wttr.in/Bursa?format=%t", timeout=10)
            if w.status_code == 200:
                d['weather'] = w.text.strip()
        except Exception as e:
            logger.warning(f"Hava durumu verisi çekilemedi: {e}")
            d['weather'] = self._live_data.get('weather', '--°C')

        # 2. Döviz ve Altın (doviz.com scraping)
        try:
            res = requests.get("https://www.doviz.com", timeout=10)
            if res.status_code == 200:
                s = BeautifulSoup(res.text, 'html.parser')
                usd_el  = s.find("span", {"data-socket-key": "USD"})
                eur_el  = s.find("span", {"data-socket-key": "EUR"})
                gold_el = s.find("span", {"data-socket-key": "XAU"})
                if usd_el:
                    d['usd'] = _to_2dp(usd_el.text.strip())
                if eur_el:
                    d['eur'] = _to_2dp(eur_el.text.strip())
                if gold_el:
                    d['gold'] = _to_2dp(gold_el.text.strip())
        except Exception as e:
            logger.warning(f"Döviz scraping başarısız oldu: {e}")

        # Eğer scraping başarısız olursa yfinance ile yedek döviz çekimi
        if d['usd'] == '--' or d['eur'] == '--' or d['gold'] == '--':
            try:
                logger.info("Döviz/altın scraping başarısız oldu, yfinance ile yedek çekiliyor...")
                tickers = ['USDTRY=X', 'EURTRY=X', 'GC=F']
                data = yf.download(tickers, period='1d', progress=False)
                if not data.empty:
                    if 'Close' in data:
                        if 'USDTRY=X' in data['Close'].columns:
                            usd_val = data['Close']['USDTRY=X'].iloc[-1]
                            d['usd'] = f"{usd_val:,.2f}"
                        if 'EURTRY=X' in data['Close'].columns:
                            eur_val = data['Close']['EURTRY=X'].iloc[-1]
                            d['eur'] = f"{eur_val:,.2f}"
                        if 'GC=F' in data['Close'].columns:
                            gold_usd = data['Close']['GC=F'].iloc[-1]
                            # USD altın fiyatını TRY'ye çevirmek için USDTRY kullan
                            if d['usd'] != '--':
                                usd_rate = float(d['usd'].replace(',', ''))
                                gold_try = gold_usd * usd_rate
                                # Troy ons (31.1035 gram) yerine gram altın fiyatı
                                gold_gram_try = gold_try / 31.1035
                                d['gold'] = f"{gold_gram_try:,.2f}"
                            else:
                                # Troy ons (31.1035 gram) yerine gram altın fiyatı
                                gold_gram_usd = gold_usd / 31.1035
                                d['gold'] = f"{gold_gram_usd:,.2f}"
            except Exception as yfe:
                logger.warning(f"Yedek yfinance çekimi de başarısız: {yfe}")

        # Başarısız olan alanlarda eski önbellek değerlerini koru
        for key in ['usd', 'eur', 'gold']:
            if d[key] == '--' or not d[key]:
                d[key] = self._live_data.get(key, '--')

        d['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._lock:
            self._live_data = d


    def _update_market_data(self):
        """yfinance üzerinden piyasa geçmiş verilerini çeker"""
        temp_market_data = {}
        for ticker, info in MARKET_ASSETS.items():
            try:
                logger.info(f"yfinance ile veri çekiliyor: {ticker}")
                data = yf.download(ticker, period='10y', interval='1mo', progress=False)
                if not data.empty:
                    # Sadece Close sütununu al ve formatla
                    close_prices = data[['Close']].copy()
                    close_prices.columns = ['price']

                    # DataFrame'i JSON'a serileştirilebilir formata çevir
                    serialized = {
                        'index': close_prices.index.strftime('%Y-%m-%d').tolist(),
                        'prices': [float(x) for x in close_prices['price'].tolist()]
                    }
                    temp_market_data[ticker] = {
                        'data': serialized,
                        'name': info['name'],
                        'currency': info['currency']
                    }
            except Exception as e:
                logger.error(f"yfinance veri çekim hatası ({ticker}): {e}")
                # Hata durumunda eski önbelleği koru
                if ticker in self._market_data:
                    temp_market_data[ticker] = self._market_data[ticker]

        with self._lock:
            self._market_data = temp_market_data

    def _save_cache(self):
        """Önbelleği JSON dosyalarına kaydeder"""
        with self._lock:
            try:
                with open(LIVE_CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self._live_data, f, ensure_ascii=False, indent=2)
                with open(MARKET_CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self._market_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Önbellek diske yazılırken hata oluştu: {e}")

    def _load_cache(self):
        """Önbellek dosyalarını okur"""
        with self._lock:
            if os.path.exists(LIVE_CACHE_FILE):
                try:
                    with open(LIVE_CACHE_FILE, 'r', encoding='utf-8') as f:
                        self._live_data = json.load(f)
                    logger.info("Canlı veri önbelleği diskten yüklendi.")
                except Exception as e:
                    logger.error(f"Canlı veri önbelleği okuma hatası: {e}")

            if os.path.exists(MARKET_CACHE_FILE):
                try:
                    with open(MARKET_CACHE_FILE, 'r', encoding='utf-8') as f:
                        self._market_data = json.load(f)
                    logger.info("Piyasa verileri önbelleği diskten yüklendi.")
                except Exception as e:
                    logger.error(f"Piyasa verileri önbelleği okuma hatası: {e}")

    def get_live_data(self):
        """Canlı verileri döner"""
        with self._lock:
            return self._live_data

    def get_market_data(self, ticker):
        """Seçili ticker için DataFrame döner"""
        with self._lock:
            asset = self._market_data.get(ticker)
            if not asset:
                return None

            serialized = asset['data']
            # Tekrar DataFrame'e dönüştür
            df = pd.DataFrame(
                serialized['prices'],
                index=pd.to_datetime(serialized['index']),
                columns=['price']
            )
            return df

    def get_all_market_data(self):
        """Tüm piyasa verilerini DataFrame formatında döner"""
        with self._lock:
            result = {}
            for ticker, info in self._market_data.items():
                serialized = info['data']
                df = pd.DataFrame(
                    serialized['prices'],
                    index=pd.to_datetime(serialized['index']),
                    columns=['price']
                )
                result[ticker] = {
                    'data': df,
                    'name': info['name'],
                    'currency': info['currency']
                }
            return result

_background_service_instance: BackgroundService | None = None

def get_background_service() -> BackgroundService:
    global _background_service_instance
    if _background_service_instance is None:
        _background_service_instance = BackgroundService()
    return _background_service_instance


def get_background_service_instance() -> BackgroundService | None:
    return _background_service_instance
