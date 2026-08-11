"""
Investment Performance Analysis Service
Yıllık getiri analizi, enflasyon ayarlaması ve performans metrikleri
"""

import logging
from datetime import datetime

from flask import g, has_request_context

from models import Asset, AssetUpdate
from shared.decimal_precision import to_decimal
from decimal import Decimal

logger = logging.getLogger(__name__)

# Türkiye yıllık enflasyon verileri (TÜİK verileri)
TURKEY_INFLATION_DATA = {
    2020: 12.28,
    2021: 19.60,
    2022: 72.31,
    2023: 53.86,
    2024: 47.06,
    2025: 40.00,
}


def _resolve_tenant_id(tenant_id=None):
    if tenant_id:
        return tenant_id
    if has_request_context():
        return g.get('tenant_id')
    return None


def _get_current_macro_inflation_context():
    """Güncel makro servisten enflasyon oranını ve kaynağını getirir."""
    try:
        from market_data_service import get_macro_economic_data
        from shared.decimal_precision import to_decimal

        macro = get_macro_economic_data()
        rate = macro.get('inflation_rate') if macro else None
        if rate is not None:
            return to_decimal(rate), macro.get('source', 'macro_service')
    except Exception as e:
        logger.warning(f"Güncel enflasyon verisi alınamadı: {e}")
    return None, None


def _resolve_inflation_rate(year):
    """Yıl bazlı enflasyon oranını ve kaynağını çözer."""
    if year in TURKEY_INFLATION_DATA:
        return to_decimal(TURKEY_INFLATION_DATA[year]), 'historical_table'

    current_year = datetime.now().year
    current_rate, current_source = _get_current_macro_inflation_context()
    if current_rate is not None and year >= current_year:
        return current_rate, current_source or 'current_macro_proxy'

    latest_year = max(TURKEY_INFLATION_DATA)
    return to_decimal(TURKEY_INFLATION_DATA[latest_year]), f'fallback_latest_known_{latest_year}'


def _build_inflation_context(years):
    rates = {}
    sources = {}
    for year in years:
        rate, source = _resolve_inflation_rate(year)
        rates[year] = rate
        sources[year] = source
    return rates, sources


def get_yearly_performance(tenant_id=None):
    """
    Yıllık yatırım performans analizi

    Returns:
        dict: Yıllık getiri verileri, enflasyon ayarlı getiriler ve özet metrikler
    """
    try:
        tenant_id = _resolve_tenant_id(tenant_id)
        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        assets = query.all()
        if not assets:
            return _empty_performance_data()

        # Yıllık performans verilerini hesapla
        yearly_data = {}

        for asset in assets:
            asset_years = _get_asset_yearly_performance(asset)
        for year, data in asset_years.items():
            if year not in yearly_data:
                yearly_data[year] = {
                    'total_value': to_decimal(0),
                    'total_cost': to_decimal(0),
                    'gain_loss': to_decimal(0),
                    'roi': to_decimal(0),
                    'assets': []
                }

            yearly_data[year]['total_value'] += to_decimal(str(data['value']))
            yearly_data[year]['total_cost'] += to_decimal(str(data['cost']))
            yearly_data[year]['assets'].append({
                'name': asset.name,
                'type': asset.type,
                'roi': to_decimal(str(data['roi'])),
                'gain_loss': to_decimal(str(data['gain_loss']))
            })

        # Yıllık özetleri hesapla
        for year in yearly_data:
            data = yearly_data[year]
            if data['total_cost'] > to_decimal(0):
                data['gain_loss'] = data['total_value'] - data['total_cost']
                data['roi'] = (data['gain_loss'] / data['total_cost']) * to_decimal('100')

        # Enflasyon ayarlı getirileri hesapla
        inflation_rates, inflation_sources = _build_inflation_context(yearly_data.keys())
        inflation_adjusted = _calculate_inflation_adjusted_returns(yearly_data, inflation_rates, inflation_sources)

        # Portföy genel metrikleri
        summary = _calculate_portfolio_summary(yearly_data, inflation_adjusted)

        def _to_python_number(value):
            if isinstance(value, Decimal):
                return float(value)
            return value
 
        serial_yearly = {}
        for y, d in yearly_data.items():
            serial_assets = []
            for a in d['assets']:
                serial_assets.append({
                    'name': a['name'],
                    'type': a['type'],
                    'roi': _to_python_number(a['roi']),
                    'gain_loss': _to_python_number(a['gain_loss'])
                })
            serial_yearly[y] = {
                'total_value': _to_python_number(d['total_value']),
                'total_cost': _to_python_number(d['total_cost']),
                'gain_loss': _to_python_number(d['gain_loss']),
                'roi': _to_python_number(d['roi']),
                'assets': serial_assets
            }
 
        serial_inflation_adjusted = {}
        for y, ia in inflation_adjusted.items():
            serial_inflation_adjusted[y] = {
                'real_roi': _to_python_number(ia['real_roi']),
                'inflation_rate': _to_python_number(ia['inflation_rate']),
                'nominal_roi': _to_python_number(ia['nominal_roi']),
                'inflation_source': ia.get('inflation_source')
            }
 
        serial_summary = {}
        for k, v in summary.items():
            serial_summary[k] = _to_python_number(v)
 
        return {
            'yearly_data': serial_yearly,
            'inflation_adjusted': serial_inflation_adjusted,
            'summary': serial_summary,
            'inflation_rates': {y: _to_python_number(r) for y, r in inflation_rates.items()},
            'inflation_sources': inflation_sources,
        }

    except Exception as e:
        logger.error(f"Yearly performance calculation error: {e}")
        return _empty_performance_data()


def _get_asset_yearly_performance(asset):
    """
    Tek bir varlık için yıllık performans hesapla

    Args:
        asset: Asset model instance

    Returns:
        dict: {year: {'value': float, 'cost': float, 'roi': float, 'gain_loss': float}}
    """
    yearly_performance = {}

    # Satın alma yılı - farklı tarih formatlarını işle
    purchase_year = datetime.now().year
    if asset.purchase_date:
        try:
            # YYYY-MM-DD formatı
            if '-' in asset.purchase_date:
                purchase_year = int(asset.purchase_date[:4])
            # DD/MM/YYYY formatı
            elif '/' in asset.purchase_date:
                parts = asset.purchase_date.split('/')
                if len(parts) == 3:
                    purchase_year = int(parts[2])
        except (ValueError, IndexError):
            purchase_year = datetime.now().year

    # Güncelleme geçmişinden yıllık değerleri al
    updates = AssetUpdate.query.filter_by(asset_id=asset.id).order_by(AssetUpdate.updated_at).all()

    if not updates:
        # Güncelleme yoksa, sadece satın alma ve güncel değer
        yearly_performance[purchase_year] = {
            'value': to_decimal(asset.value or 0),
            'cost': to_decimal(asset.purchase_cost or 0),
            'roi': to_decimal(asset.roi or 0),
            'gain_loss': to_decimal(asset.total_gain_loss or 0)
        }
        return yearly_performance

    # Her güncelleme için yıllık performans hesapla
    for update in updates:
        update_year = update.updated_at.year

        if update_year not in yearly_performance:
            purchase_cost = to_decimal(asset.purchase_cost or 0)
            new_value = to_decimal(update.new_value or 0)
            yearly_performance[update_year] = {
                'value': new_value,
                'cost': purchase_cost,
                'roi': ((new_value - purchase_cost) / purchase_cost * to_decimal('100')) if purchase_cost > to_decimal(0) else to_decimal(0),
                'gain_loss': new_value - purchase_cost
            }
        else:
            # Aynı yılda birden fazla güncelleme varsa, sonuncuyu al
            purchase_cost = to_decimal(asset.purchase_cost or 0)
            new_value = to_decimal(update.new_value or 0)
            yearly_performance[update_year]['value'] = new_value
            yearly_performance[update_year]['roi'] = ((new_value - purchase_cost) / purchase_cost * to_decimal('100')) if purchase_cost > to_decimal(0) else to_decimal(0)
            yearly_performance[update_year]['gain_loss'] = new_value - purchase_cost

    # Güncel değeri de ekle (son güncelleme yoksa)
    current_year = datetime.now().year
    if current_year not in yearly_performance:
        yearly_performance[current_year] = {
            'value': to_decimal(asset.value or 0),
            'cost': to_decimal(asset.purchase_cost or 0),
            'roi': to_decimal(asset.roi or 0),
            'gain_loss': to_decimal(asset.total_gain_loss or 0)
        }

    return yearly_performance


def _calculate_inflation_adjusted_returns(yearly_data, inflation_rates=None, inflation_sources=None):
    """
    Enflasyon ayarlı gerçek getiri hesapla

    Args:
        yearly_data: Yıllık performans verileri

    Returns:
        dict: {year: {'real_roi': float, 'inflation_rate': float}}
    """
    inflation_adjusted = {}

    inflation_rates = inflation_rates or {}
    inflation_sources = inflation_sources or {}

    for year, data in yearly_data.items():
        inflation_rate = inflation_rates.get(year)
        inflation_source = inflation_sources.get(year)
        if inflation_rate is None:
            inflation_rate, inflation_source = _resolve_inflation_rate(year)

        # Gerçek getiri formülü: (1 + nominal_return) / (1 + inflation) - 1
        nominal_return = to_decimal(data['roi']) / to_decimal('100')  # Yüzdeyi ondalığa çevir
        inflation_rate_dec = to_decimal(inflation_rate) if inflation_rate is not None else to_decimal(0)
        real_return = ((to_decimal(1) + nominal_return) / (to_decimal(1) + inflation_rate_dec / to_decimal('100'))) - to_decimal(1)
        real_roi = real_return * to_decimal('100')  # Yüzdeye çevir

        inflation_adjusted[year] = {
            'real_roi': real_roi,
            'inflation_rate': inflation_rate_dec,
            'nominal_roi': to_decimal(data['roi']),
            'inflation_source': inflation_source,
        }

    return inflation_adjusted


def _calculate_portfolio_summary(yearly_data, inflation_adjusted):
    """
    Portföy genel özet metrikleri hesapla

    Args:
        yearly_data: Yıllık performans verileri
        inflation_adjusted: Enflasyon ayarlı veriler

    Returns:
        dict: Portföy özeti
    """
    if not yearly_data:
        return {
            'total_years': 0,
            'avg_nominal_roi': 0,
            'avg_real_roi': 0,
            'best_year': None,
            'worst_year': None,
            'total_inflation_impact': 0
        }

    years = sorted(yearly_data.keys())
    total_years = len(years)

    # Ortalama getiriler
    nominal_rois = [to_decimal(yearly_data[y]['roi']) for y in years]
    real_rois = [to_decimal(inflation_adjusted[y]['real_roi']) for y in years]

    avg_nominal_roi = (sum(nominal_rois) / to_decimal(total_years)) if total_years > 0 else to_decimal(0)
    avg_real_roi = (sum(real_rois) / to_decimal(total_years)) if total_years > 0 else to_decimal(0)

    # En iyi ve en kötü yıl
    best_year = max(years, key=lambda y: to_decimal(yearly_data[y]['roi'])) if years else None
    worst_year = min(years, key=lambda y: to_decimal(yearly_data[y]['roi'])) if years else None

    # Toplam enflasyon etkisi
    total_inflation_impact = sum(real_rois) - sum(nominal_rois)

    return {
        'total_years': total_years,
        'avg_nominal_roi': avg_nominal_roi,
        'avg_real_roi': avg_real_roi,
        'best_year': best_year,
        'worst_year': worst_year,
        'best_year_roi': yearly_data[best_year]['roi'] if best_year else to_decimal(0),
        'worst_year_roi': yearly_data[worst_year]['roi'] if worst_year else to_decimal(0),
        'total_inflation_impact': total_inflation_impact
    }


def _empty_performance_data():
    """
    Boş performans verisi döndür (veri yoksa)
    """
    return {
        'yearly_data': {},
        'inflation_adjusted': {},
        'summary': {
            'total_years': 0,
            'avg_nominal_roi': 0,
            'avg_real_roi': 0,
            'best_year': None,
            'worst_year': None,
            'total_inflation_impact': 0
        },
        'inflation_rates': {},
        'inflation_sources': {},
    }


def get_inflation_rate(year):
    """
    Belirli bir yıl için enflasyon oranı döndür

    Args:
        year: Yıl (int)

    Returns:
        Decimal: Enflasyon oranı (yüzde)
    """
    return to_decimal(_resolve_inflation_rate(year)[0])


def update_inflation_data(year, rate):
    """
    Enflasyon verisini güncelle (gelecekte API entegrasyonu için)

    Args:
        year: Yıl (int)
        rate: Enflasyon oranı (float or Decimal)
    """
    TURKEY_INFLATION_DATA[year] = rate if isinstance(rate, Decimal) else to_decimal(rate)
    logger.info(f"Inflation data updated for {year}: {rate}%")
