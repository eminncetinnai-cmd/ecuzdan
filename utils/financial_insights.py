import json
import os
from datetime import date
from typing import Dict, Optional

# JSON dosya yolu
INSIGHTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'financial_insights.json')

# Cache için global değişken
_insights_cache = None
_cache_date = None


def _load_insights() -> Dict:
    """
    JSON dosyasından finansal içgörüleri yükler.
    Performans için cache kullanır.
    """
    global _insights_cache, _cache_date

    today = date.today()

    # Cache varsa ve aynı gün ise cache'i kullan
    if _insights_cache is not None and _cache_date == today:
        return _insights_cache

    try:
        with open(INSIGHTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Cache'i güncelle
        _insights_cache = data
        _cache_date = today

        return data
    except FileNotFoundError:
        return {"insights": []}
    except json.JSONDecodeError:
        return {"insights": []}


def get_daily_insight() -> Optional[Dict]:
    """
    Güne göre deterministik bir içgörü döndürür.
    Aynı gün içinde her zaman aynı içgörüyü gösterir.

    Returns:
        Dict: İçgörü objesi (id, category, text, source) veya None
    """
    data = _load_insights()
    insights = data.get('insights', [])

    if not insights:
        return None

    # Günün tarihinden deterministik bir index hesapla
    # YYYYMMDD formatında bir sayı oluşturup
    # toplam insight sayısına göre mod alıyoruz
    today = date.today()
    date_number = today.year * 10000 + today.month * 100 + today.day
    insight_index = date_number % len(insights)

    return insights[insight_index]


def get_insight_by_date(target_date: date) -> Optional[Dict]:
    """
    Belirli bir tarih için içgörü döndürür (test için).

    Args:
        target_date: İçgörü alınacak tarih

    Returns:
        Dict: İçgörü objesi veya None
    """
    data = _load_insights()
    insights = data.get('insights', [])

    if not insights:
        return None

    date_number = target_date.year * 10000 + target_date.month * 100 + target_date.day
    insight_index = date_number % len(insights)

    return insights[insight_index]


def get_insight_count() -> int:
    """
    Toplam içgörü sayısını döndürür.

    Returns:
        int: İçgörü sayısı
    """
    data = _load_insights()
    return len(data.get('insights', []))


def get_categories() -> list:
    """
    Mevcut kategorileri döndürür.

    Returns:
        list: Kategori listesi
    """
    data = _load_insights()
    return data.get('categories', [])
