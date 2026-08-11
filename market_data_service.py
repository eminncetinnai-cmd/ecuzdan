"""
Market Data Service - Finansal Strateji ve Analiz Motoru
yfinance kullanarak piyasa verilerini çeker, normalize eder ve önbelleğe alır.
"""

import logging
import time
from datetime import datetime

import requests
import yfinance as yf

logger = logging.getLogger(__name__)

# Piyasa varlıkları konfigürasyonu
MARKET_ASSETS = {
    'GC=F': {'name': 'Altın', 'currency': 'USD'},
    'SI=F': {'name': 'Gümüş', 'currency': 'USD'},
    'CL=F': {'name': 'Petrol', 'currency': 'USD'},
    'XU100.IS': {'name': 'BIST100', 'currency': 'TRY'},
    'BTC-USD': {'name': 'Bitcoin', 'currency': 'USD'},
    '^IXIC': {'name': 'Nasdaq', 'currency': 'USD'}
}

# Önbellekleme süresi (saniye)
CACHE_TTL = 3600  # 1 saat

class MarketDataService:
    """Piyasa verileri servisi"""

    def __init__(self):
        self._cache = {}
        self._cache_timestamps = {}

    def get_market_data(self, ticker, period='10y', interval='1mo'):
        """
        Piyasa verilerini arka plan servisinden çeker veya yedek olarak yfinance kullanır
        """
        try:
            from infrastructure.background.background_service import get_background_service
            df = get_background_service().get_market_data(ticker)
            if df is not None and not df.empty:
                return df
        except ImportError:
            logger.warning(f"Arka plan servisi modülü bulunamadı ({ticker}), yedek yöntem kullanılıyor")
        except AttributeError:
            logger.warning(f"Arka plan servisi başlatılmamış ({ticker}), yedek yöntem kullanılıyor")
        except Exception as e:
            logger.error(f"Arka plan servisinden piyasa verisi alınamadı ({ticker}): {e}")

        # Graceful fallback: Eğer cache boşsa ve acil lazımsa doğrudan yfinance ile çek
        try:
            logger.warning(f"Arka plan önbellek eksikliği ({ticker}), doğrudan yfinance yedek çekimi yapılıyor...")
            data = yf.download(ticker, period=period, interval=interval, progress=False)
            if not data.empty:
                close_prices = data[['Close']].copy()
                close_prices.columns = ['price']
                return close_prices
        except (requests.RequestException, ValueError) as fe:
            logger.error(f"Yedek yfinance çekimi başarısız ({ticker}): {fe}")
        except Exception as fe:
            logger.error(f"Yedek yfinance çekimi beklenmeyen hata ({ticker}): {fe}")
        return None

    def get_all_market_data(self, period='10y', interval='1mo'):
        """
        Tüm piyasa varlıklarının verilerini arka plan servisinden çeker
        """
        try:
            from infrastructure.background.background_service import get_background_service
            data = get_background_service().get_all_market_data()
            if data:
                return data
        except ImportError:
            logger.warning("Arka plan servisi modülü bulunamadı, yedek yöntem kullanılıyor")
        except AttributeError:
            logger.warning("Arka plan servisi başlatılmamış, yedek yöntem kullanılıyor")
        except Exception as e:
            logger.error(f"Arka plan servisinden toplu veri alınamadı: {e}")

        # Fallback
        all_data = {}
        for ticker, info in MARKET_ASSETS.items():
            data = self.get_market_data(ticker, period, interval)
            if data is not None:
                all_data[ticker] = {
                    'data': data,
                    'name': info['name'],
                    'currency': info['currency']
                }

        return all_data

    def normalize_to_base_100(self, data):
        """
        Verileri başlangıç değerine göre normalize et (Base-100)

        Args:
            data: DataFrame with 'price' column

        Returns:
            DataFrame: Normalize edilmiş fiyatlar
        """
        if data is None or data.empty:
            return None

        try:
            normalized = data.copy()
            base_value = normalized['price'].iloc[0]
            normalized['normalized'] = (normalized['price'] / base_value) * 100
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing data: {e}")
            return None

    def normalize_all_data(self, market_data):
        """
        Tüm piyasa verilerini normalize et

        Args:
            market_data: dict from get_all_market_data()

        Returns:
            dict: Normalize edilmiş veriler
        """
        normalized_data = {}

        for ticker, info in market_data.items():
            normalized = self.normalize_to_base_100(info['data'])
            if normalized is not None:
                normalized_data[ticker] = {
                    'data': normalized,
                    'name': info['name'],
                    'currency': info['currency']
                }

        return normalized_data

    def get_latest_prices(self):
        """
        Tüm varlıkların en son fiyatlarını getir

        Returns:
            dict: Ticker -> latest price
        """
        latest_prices = {}

        for ticker, info in MARKET_ASSETS.items():
            data = self.get_market_data(ticker, period='1mo', interval='1d')
            if data is not None and not data.empty:
                latest_prices[ticker] = {
                    'price': data['price'].iloc[-1],
                    'name': info['name'],
                    'currency': info['currency']
                }

        return latest_prices

    def clear_cache(self):
        """Önbelleği temizle"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Cache cleared")

# Singleton instance
market_data_service = MarketDataService()

# Makroekonomik veri önbelleği
MACRO_CACHE = {
    "data": None,
    "last_fetched": 0
}
MACRO_CACHE_TTL = 86400  # 24 saat (günlük güncelleme)

def _fetch_macro_from_investing():
    """
    investing.com TR sayfasından TCMB politika faizi ve TÜFE verisini çeker.
    Returns: (interest_rate, inflation_rate) veya (None, None)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        # Politika faizi
        interest_rate = None
        try:
            r = requests.get(
                'https://tr.investing.com/economic-calendar/turkish-central-bank-rate-decision-883',
                headers=headers, timeout=3.0
            )
            if r.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(r.text, 'html.parser')
                # Sayfadaki son açıklanan değeri bul
                actual_el = soup.find('td', {'class': 'bold'})
                if actual_el:
                    val_text = actual_el.text.strip().replace('%', '').replace(',', '.').strip()
                    if val_text:
                        try:
                            interest_rate = float(val_text)
                        except ValueError as parse_error:
                            logger.warning(f"investing.com politika faizi parsing hatası: {parse_error}")
        except requests.exceptions.Timeout:
            logger.error("investing.com timeout (3s) - politika faizi çekilemedi")
        except requests.exceptions.RequestException as req_error:
            logger.error(f"investing.com request hatası (politika faizi): {req_error}")

        # Enflasyon (TÜFE)
        inflation_rate = None
        try:
            r2 = requests.get(
                'https://tr.investing.com/economic-calendar/turkish-cpi-90',
                headers=headers, timeout=3.0
            )
            if r2.status_code == 200:
                from bs4 import BeautifulSoup
                soup2 = BeautifulSoup(r2.text, 'html.parser')
                actual_el2 = soup2.find('td', {'class': 'bold'})
                if actual_el2:
                    val_text2 = actual_el2.text.strip().replace('%', '').replace(',', '.').strip()
                    if val_text2:
                        try:
                            inflation_rate = float(val_text2)
                        except ValueError as parse_error:
                            logger.warning(f"investing.com TÜFE parsing hatası: {parse_error}")
        except requests.exceptions.Timeout:
            logger.error("investing.com timeout (3s) - TÜFE çekilemedi")
        except requests.exceptions.RequestException as req_error:
            logger.error(f"investing.com request hatası (TÜFE): {req_error}")

        return interest_rate, inflation_rate
    except Exception as e:
        logger.error(f"investing.com scraping beklenmeyen hata: {e}")
        return None, None


def _fetch_macro_from_evds():
    """
    TCMB EVDS (Elektronik Veri Dağıtım Sistemi) API'sinden politika faizi ve TÜFE verisini çeker.
    API anahtarı gerektirir. EVDS API kullanımı için:
    1. https://evds3.tcmb.gov.tr/ adresine gidin
    2. Kayıt olun ve giriş yapın
    3. Profil bölümünden API anahtarınızı alın
    4. API anahtarını sistem ortam değişkeni EVDS_API_KEY olarak ayarlayın

    Returns: (interest_rate, inflation_rate) veya (None, None)
    """
    try:
        import os
        api_key = os.environ.get('EVDS_API_KEY')
        if not api_key:
            logger.warning("EVDS_API_KEY ortam değişkeni bulunamadı. EVDS API kullanılamıyor.")
            return None, None

        from urllib.parse import urlencode
        headers = {'key': api_key}

        interest_rate = None
        inflation_rate = None

        # Politika faizi için seri kodu (TP.DK.USD.A.YTL - Dolar kuru bazlı)
        # Alternatif: TP.FG.J0 - Faiz oranları (Politika faizi için uygun seri kodu bulunmalı)
        # TCMB PPK faiz oranı için: TP.FG.G2210 (Bir hafta vadeli repo faiz oranı)
        series_code_interest = 'TP.FG.G2210'

        # TÜFE için seri kodu (TP.FG.J0 - Tüketici Fiyat Endeksi)
        series_code_inflation = 'TP.FG.J0'

        # Politika faizi çek
        params_interest = {
            'series': series_code_interest,
            'startDate': '01-01-2024',
            'endDate': datetime.now().strftime('%d-%m-%Y'),
            'frequency': '1',  # Günlük
            'type': 'json'
        }
        url_interest = f'https://evds2.tcmb.gov.tr/service/evds/{urlencode(params_interest)}'

        try:
            r_interest = requests.get(url=url_interest, headers=headers, timeout=3.0)
            if r_interest.status_code == 200:
                data_interest = r_interest.json()
                if data_interest.get('items'):
                    # En son değeri al
                    latest_item = data_interest['items'][-1]
                    # Değer sütununu bul (genellikle ikinci sütun)
                    values = list(latest_item.values())
                    if len(values) >= 2:
                        try:
                            val = float(str(values[1]).replace(',', '.').replace('NaN', '0'))
                            if 5.0 <= val <= 70.0:  # Makul faiz aralığı
                                interest_rate = val
                                logger.info(f"EVDS'ten politika faizi alındı: {interest_rate}%")
                        except (ValueError, IndexError) as parse_error:
                            logger.warning(f"EVDS politika faizi parsing hatası: {parse_error}")
        except requests.exceptions.Timeout:
            logger.error("EVDS API timeout (3s) - politika faizi çekilemedi")
        except requests.exceptions.RequestException as req_error:
            logger.error(f"EVDS API request hatası (politika faizi): {req_error}")
        except (ValueError, KeyError) as data_error:
            logger.error(f"EVDS API veri yapısı hatası (politika faizi): {data_error}")

        # TÜFE çek
        params_inflation = {
            'series': series_code_inflation,
            'startDate': '01-01-2024',
            'endDate': datetime.now().strftime('%d-%m-%Y'),
            'frequency': '1',  # Günlük
            'type': 'json'
        }
        url_inflation = f'https://evds2.tcmb.gov.tr/service/evds/{urlencode(params_inflation)}'

        try:
            r_inflation = requests.get(url=url_inflation, headers=headers, timeout=3.0)
            if r_inflation.status_code == 200:
                data_inflation = r_inflation.json()
                if data_inflation.get('items'):
                    # En son değeri al
                    latest_item = data_inflation['items'][-1]
                    # Değer sütununu bul
                    values = list(latest_item.values())
                    if len(values) >= 2:
                        try:
                            val = float(str(values[1]).replace(',', '.').replace('NaN', '0'))
                            if 20.0 <= val <= 100.0:  # Makul TÜFE aralığı
                                inflation_rate = val
                                logger.info(f"EVDS'ten TÜFE alındı: {inflation_rate}%")
                        except (ValueError, IndexError) as parse_error:
                            logger.warning(f"EVDS TÜFE parsing hatası: {parse_error}")
        except requests.exceptions.Timeout:
            logger.error("EVDS API timeout (3s) - TÜFE çekilemedi")
        except requests.exceptions.RequestException as req_error:
            logger.error(f"EVDS API request hatası (TÜFE): {req_error}")
        except (ValueError, KeyError) as data_error:
            logger.error(f"EVDS API veri yapısı hatası (TÜFE): {data_error}")

        return interest_rate, inflation_rate

    except Exception as e:
        logger.error(f"EVDS API beklenmeyen hata: {e}")
        return None, None


def _fetch_macro_from_tcmb():
    """
    TCMB'nin genel istatistik sayfasından politika faizini çeker.
    Returns: (interest_rate, inflation_rate) veya (None, None)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        }
        interest_rate = None
        inflation_rate = None

        # TCMB PPK kararları sayfasından politika faizini çek
        try:
            r = requests.get(
                'https://www.tcmb.gov.tr/wps/wcm/connect/EN/TCMB+EN/Main+Menu/Monetary+Policy/Monetary+Policy+Committee+Decisions/',
                headers=headers, timeout=3.0
            )
            if r.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(r.text, 'html.parser')
                # Tablodaki ilk satırdan (en güncel karar) oran bul
                rows = soup.find_all('tr')
                for row in rows[:5]:
                    cols = row.find_all('td')
                    for col in cols:
                        txt = col.text.strip().replace('%', '').replace(',', '.').strip()
                        try:
                            val = float(txt)
                            if 5.0 <= val <= 70.0:  # Makul faiz aralığı
                                interest_rate = val
                                break
                        except ValueError:
                            continue
                    if interest_rate:
                        break
        except requests.exceptions.Timeout:
            logger.error("TCMB scraping timeout (3s) - politika faizi çekilemedi")
        except requests.exceptions.RequestException as req_error:
            logger.error(f"TCMB scraping request hatası (politika faizi): {req_error}")

        # TÜİK TÜFE sayfasından enflasyon çek
        try:
            r2 = requests.get(
                'https://data.tuik.gov.tr/Bulten/Index?p=Tuketici-Fiyat-Endeksi-Aralik-2024-53752',
                headers=headers, timeout=3.0
            )
            if r2.status_code == 200:
                from bs4 import BeautifulSoup
                soup2 = BeautifulSoup(r2.text, 'html.parser')
                # Sayfadaki ilk büyük sayısal değeri bul (yıllık değişim)
                for el in soup2.find_all(['td', 'span', 'div'], limit=200):
                    txt = el.text.strip().replace('%', '').replace(',', '.').strip()
                    try:
                        val = float(txt)
                        if 20.0 <= val <= 100.0:  # Makul TÜFE aralığı
                            inflation_rate = val
                            break
                    except ValueError:
                        continue
        except requests.exceptions.Timeout:
            logger.error("TÜİK scraping timeout (3s) - TÜFE çekilemedi")
        except requests.exceptions.RequestException as req_error:
            logger.error(f"TÜİK scraping request hatası (TÜFE): {req_error}")

        return interest_rate, inflation_rate
    except Exception as e:
        logger.error(f"TCMB/TÜİK scraping beklenmeyen hata: {e}")
        return None, None


def get_macro_economic_data():
    """
    Türkiye makroekonomik verilerini dinamik olarak çeker.
    Kaynak önceliği:
      1. TCMB EVDS API (resmi API - API anahtarı gerekli)
      2. investing.com (TR) scraping
      3. TCMB / TÜİK açık sayfaları
      4. Son geçerli önbellek
      5. Sabit yedek değerler (fallback)

    EVDS API kullanımı için:
      1. https://evds3.tcmb.gov.tr/ adresine gidin
      2. Kayıt olun ve giriş yapın
      3. Profil bölümünden API anahtarınızı alın
      4. API anahtarını sistem ortam değişkeni EVDS_API_KEY olarak ayarlayın

    Returns:
        dict: {
            'inflation_rate': yıllık TÜFE (%),
            'interest_rate': TCMB politika faizi (%),
            'real_return_rate': reel getiri oranı (%),
            'last_updated': timestamp,
            'source': kaynak etiketi
        }
    """
    global MACRO_CACHE
    now = time.time()

    # Önbellek geçerliyse doğrudan dön
    if MACRO_CACHE["data"] and (now - MACRO_CACHE["last_fetched"]) < MACRO_CACHE_TTL:
        logger.info("Önbellekteki makro veri kullanılıyor")
        return MACRO_CACHE["data"]

    # Son geçerli önbellek değerlerini yedek olarak sakla
    cached_interest = MACRO_CACHE["data"].get('interest_rate', 37.0) if MACRO_CACHE["data"] else 37.0
    cached_inflation = MACRO_CACHE["data"].get('inflation_rate', 47.5) if MACRO_CACHE["data"] else 47.5

    interest_rate = None
    inflation_rate = None
    source = 'default'
    cache_this_data = False  # Only cache successful external fetches

    # --- Kaynak 1: TCMB EVDS API (resmi API) ---
    interest_rate, inflation_rate = _fetch_macro_from_evds()
    if interest_rate and inflation_rate:
        source = 'evds_api'
        cache_this_data = True  # Successful external fetch - cache this
        logger.info(f"Makroekonomik veri EVDS API'den alındı: faiz={interest_rate}, tüfe={inflation_rate}")

    # --- Kaynak 2: investing.com ---
    if not interest_rate or not inflation_rate:
        ir2, inf2 = _fetch_macro_from_investing()
        if ir2:
            interest_rate = ir2
            source = 'investing.com'
        if inf2:
            inflation_rate = inf2
            if source == 'investing.com':
                source = 'investing.com'
        if interest_rate and inflation_rate:
            cache_this_data = True  # Successful external fetch - cache this
            logger.info(f"Makroekonomik veri investing.com'dan alındı: faiz={interest_rate}, tüfe={inflation_rate}")

    # --- Kaynak 3: TCMB / TÜİK ---
    if not interest_rate or not inflation_rate:
        ir3, inf3 = _fetch_macro_from_tcmb()
        if ir3:
            interest_rate = ir3
            source = 'tcmb.gov.tr'
        if inf3:
            inflation_rate = inf3
            if source == 'tcmb.gov.tr':
                source = 'tcmb+tuik'
        if interest_rate and inflation_rate:
            cache_this_data = True  # Successful external fetch - cache this
            logger.info(f"Makroekonomik veri TCMB/TÜİK'ten alındı: faiz={interest_rate}, tüfe={inflation_rate}")

    # --- Kaynak 4: Önbellekte kalan son geçerli değer ---
    if not interest_rate:
        interest_rate = cached_interest
        source = 'cache_fallback'
        logger.warning("Politika faizi çekilemedi, önbellekteki son değer kullanılıyor.")
    if not inflation_rate:
        inflation_rate = cached_inflation
        source = 'cache_fallback'
        logger.warning("TÜFE çekilemedi, önbellekteki son değer kullanılıyor.")

    real_return = round(max(0.0, interest_rate - inflation_rate), 1)

    macro_data = {
        'inflation_rate': round(inflation_rate, 1),
        'interest_rate': round(interest_rate, 1),
        'real_return_rate': real_return,
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source': source
    }

    # Cache integrity fix: Only cache successful external fetches to prevent
    # repeated API calls on success. On cache_fallback, do NOT update last_fetched
    # so that the next request will still attempt external sources.
    MACRO_CACHE["data"] = macro_data
    if cache_this_data:
        MACRO_CACHE["last_fetched"] = now
    logger.info(f"Makro veri önbelleğe kaydedildi: {macro_data}")

    return macro_data


def get_market_data_summary():
    """
    Piyasa verilerinin özetini döner (dashboard için)

    Returns:
        dict: Normalize edilmiş veriler ve özet istatistikler
    """
    try:
        # Tüm verileri çek
        market_data = market_data_service.get_all_market_data()

        if not market_data:
            logger.warning("No market data available")
            return None

        # Normalize et
        normalized_data = market_data_service.normalize_all_data(market_data)

        # Özet istatistikler
        summary = {
            'assets': {},
            'data_available': True,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        for ticker, info in normalized_data.items():
            data = info['data']
            summary['assets'][ticker] = {
                'name': info['name'],
                'currency': info['currency'],
                'current_price': data['price'].iloc[-1],
                'current_normalized': data['normalized'].iloc[-1],
                'ytd_return': ((data['normalized'].iloc[-1] - data['normalized'].iloc[0]) / data['normalized'].iloc[0]) * 100,
                'data_points': len(data)
            }

        return summary

    except Exception as e:
        logger.error(f"Error getting market data summary: {e}")
        return {
            'assets': {},
            'data_available': False,
            'error': str(e),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
