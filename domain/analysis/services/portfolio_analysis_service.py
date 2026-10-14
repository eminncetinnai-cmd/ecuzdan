"""Portfolio and Asset Analysis Service.

Computes portfolio diversification, risk score, liquidity score, and asset returns.
"""
from domain.analysis.services.helpers import _apply_tenant, _as_decimal, _safe_percentage
from models import Asset, AssetSector
from shared.decimal_precision import to_decimal


def calculate_asset_analysis(tenant_id: str | None = None) -> dict:
    """Profesyonel varlık analizi hesaplamaları.

    Portföy performansı, diversification, risk analizi gibi metrikleri döner.
    """
    assets = _apply_tenant(Asset.query, Asset, tenant_id).all()
    if not assets:
        return {
            'total_value': 0,
            'total_cost': 0,
            'total_gain_loss': 0,
            'overall_roi': 0,
            'asset_count': 0,
            'by_type': {},
            'by_risk': {},
            'by_liquidity': {},
            'by_sector': {},
            'top_performers': [],
            'worst_performers': [],
            'portfolio_concentration': {},
            'risk_score': 0,
            'liquidity_score': 0,
        }

    base_currency = 'TRY'
    try:
        from domain.analysis.services.multi_currency import CurrencyManager
        base_currency = CurrencyManager.get_base_currency(tenant_id)
    except Exception:
        pass

    def _to_base(amount, curr):
        if not curr or curr == base_currency:
            return _as_decimal(amount)
        try:
            from domain.analysis.services.multi_currency import CurrencyManager
            converted = CurrencyManager.convert_currency(float(amount or 0), curr, base_currency)
            return _as_decimal(converted)
        except Exception:
            return _as_decimal(amount)

    total_value = sum((_to_base(a.value, getattr(a, 'currency', base_currency)) for a in assets), to_decimal(0))
    total_cost = sum((_to_base(a.purchase_cost, getattr(a, 'currency', base_currency)) for a in assets if a.purchase_cost), to_decimal(0))
    total_gain_loss = total_value - total_cost
    overall_roi = _safe_percentage(total_gain_loss, total_cost)

    # Varlık tipine göre gruplama
    by_type = {}
    for a in assets:
        val_in_base = _to_base(a.value, getattr(a, 'currency', base_currency))
        if a.type not in by_type:
            by_type[a.type] = {'count': 0, 'value': 0, 'weight': 0}
        by_type[a.type]['count'] += 1
        by_type[a.type]['value'] += val_in_base

    for t in by_type:
        by_type[t]['weight'] = _safe_percentage(by_type[t]['value'], total_value)

    # Risk seviyesine göre gruplama
    by_risk = {
        'Düşük': {'count': 0, 'value': 0, 'weight': 0},
        'Orta': {'count': 0, 'value': 0, 'weight': 0},
        'Yüksek': {'count': 0, 'value': 0, 'weight': 0},
    }
    for a in assets:
        val_in_base = _to_base(a.value, getattr(a, 'currency', base_currency))
        risk = a.risk_level or 'Orta'
        if risk in by_risk:
            by_risk[risk]['count'] += 1
            by_risk[risk]['value'] += val_in_base

    for r in by_risk:
        by_risk[r]['weight'] = _safe_percentage(by_risk[r]['value'], total_value)

    # Likiditeye göre gruplama
    by_liquidity = {
        'Likit': {'count': 0, 'value': 0, 'weight': 0},
        'Yarı-Likit': {'count': 0, 'value': 0, 'weight': 0},
        'İ-Likit': {'count': 0, 'value': 0, 'weight': 0},
    }
    for a in assets:
        val_in_base = _to_base(a.value, getattr(a, 'currency', base_currency))
        liq = a.liquidity or 'Likit'
        if liq in by_liquidity:
            by_liquidity[liq]['count'] += 1
            by_liquidity[liq]['value'] += val_in_base

    for liquidity in by_liquidity:
        by_liquidity[liquidity]['weight'] = _safe_percentage(by_liquidity[liquidity]['value'], total_value)

    # Sektöre göre gruplama — toplu sektör sözlüğü ile N+1 sorgu engellenir
    sectors_by_id = {s.id: s.name for s in AssetSector.query.all()}
    by_sector = {}
    for a in assets:
        val_in_base = _to_base(a.value, getattr(a, 'currency', base_currency))
        sector = sectors_by_id.get(a.sector_id, 'Diğer') if a.sector_id else 'Diğer'
        if sector not in by_sector:
            by_sector[sector] = {'count': 0, 'value': 0, 'weight': 0}
        by_sector[sector]['count'] += 1
        by_sector[sector]['value'] += val_in_base

    for s in by_sector:
        by_sector[s]['weight'] = _safe_percentage(by_sector[s]['value'], total_value)

    # En iyi ve en kötü performans gösteren varlıklar (total_gain_loss'a göre sırala)
    assets_with_gain = [(a, a.total_gain_loss) for a in assets if a.value and a.value > 0]
    assets_with_gain.sort(key=lambda x: x[1], reverse=True)

    # En iyi performanslar: Sadece pozitif gain_loss olan varlıklar
    top_performers = [
        {'name': a.name, 'type': a.type, 'roi': a.roi, 'gain_loss': gain, 'value': a.value}
        for a, gain in assets_with_gain if gain > 0
    ][:5]

    # En kötü performanslar: Sadece negatif gain_loss olan varlıklar (en düşükten başla)
    worst_performers = [
        {'name': a.name, 'type': a.type, 'roi': a.roi, 'gain_loss': gain, 'value': a.value}
        for a, gain in assets_with_gain if gain < 0
    ][-5:][::-1]

    # Portföy konsantrasyonu (Herhangi bir varlığın %20'den fazla olması riskli)
    high_concentration = []
    has_concentration_risk = False
    for a in assets:
        # Precomputed total_value üzerinden ağırlık hesapla (N+1 query ve çoklu çağrı engellenir)
        weight = _safe_percentage(_to_base(a.value, getattr(a, 'currency', base_currency)), total_value)
        if weight > 20:
            has_concentration_risk = True
            high_concentration.append({'name': a.name, 'weight': weight})

    portfolio_concentration = {
        'high_concentration_assets': high_concentration,
        'concentration_risk': has_concentration_risk,
    }

    # Risk skoru hesaplama (0-100)
    risk_score = 0
    if by_risk['Yüksek']['weight'] > 30:
        risk_score += 30
    elif by_risk['Yüksek']['weight'] > 10:
        risk_score += 15
    if by_risk['Orta']['weight'] > 50:
        risk_score += 20
    if portfolio_concentration['concentration_risk']:
        risk_score += 25
    if by_liquidity['İ-Likit']['weight'] > 30:
        risk_score += 15
    risk_score = min(100, risk_score)

    # Likidite skoru hesaplama (0-100)
    liquidity_score = by_liquidity['Likit']['weight']
    liquidity_score += by_liquidity['Yarı-Likit']['weight'] * to_decimal(0.5, scale=1)
    liquidity_score = min(100, liquidity_score)

    return {
        'total_value': total_value,
        'total_cost': total_cost,
        'total_gain_loss': total_gain_loss,
        'overall_roi': overall_roi,
        'asset_count': len(assets),
        'by_type': by_type,
        'by_risk': by_risk,
        'by_liquidity': by_liquidity,
        'by_sector': by_sector,
        'top_performers': top_performers,
        'worst_performers': worst_performers,
        'portfolio_concentration': portfolio_concentration,
        'risk_score': round(risk_score, 1),
        'liquidity_score': round(liquidity_score, 1),
        'base_currency': base_currency,
    }
