"""
Advanced Asset Allocation Service
=================================
Multi-dimensional asset allocation analysis (sector, country, currency, liquidity, risk, tax)
Phase 9: Advanced asset allocation
"""

import logging
from collections import defaultdict
from typing import Dict, List

from models import Asset, AssetSector, db

logger = logging.getLogger(__name__)


class AdvancedAllocationAnalyzer:
    """Multi-dimensional asset allocation analysis"""

    @staticmethod
    def get_allocation_by_sector(tenant_id: str = None) -> Dict:
        """
        Analyze asset allocation by sector

        Args:
            tenant_id: Filter by tenant

        Returns:
            Dict with sector allocation breakdown
        """
        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        assets = query.all()

        if not assets:
            return {'total_assets': 0, 'by_sector': {}, 'concentration_risk': 'N/A'}

        total_value = sum(a.value for a in assets)
        sector_allocation = defaultdict(lambda: {'count': 0, 'value': 0, 'assets': []})

        for asset in assets:
            sector_id = asset.sector_id
            sector = db.session.get(AssetSector, sector_id) if sector_id else None
            sector_name = sector.name if sector else 'Bilinmeyen'

            sector_allocation[sector_name]['count'] += 1
            sector_allocation[sector_name]['value'] += asset.value
            sector_allocation[sector_name]['assets'].append({
                'id': asset.id,
                'name': asset.name,
                'value': asset.value
            })

        # Calculate percentages
        for sector_name, data in sector_allocation.items():
            data['percentage'] = (data['value'] / total_value * 100) if total_value > 0 else 0

        # Assess concentration risk
        max_sector_pct = max(data['percentage'] for data in sector_allocation.values()) if sector_allocation else 0
        concentration_risk = 'Düşük' if max_sector_pct < 30 else 'Orta' if max_sector_pct < 50 else 'Yüksek'

        return {
            'total_assets': len(assets),
            'total_value': total_value,
            'by_sector': dict(sector_allocation),
            'concentration_risk': concentration_risk,
            'max_sector_exposure': max_sector_pct
        }

    @staticmethod
    def get_allocation_by_currency(tenant_id: str = None) -> Dict:
        """
        Analyze asset allocation by currency

        Args:
            tenant_id: Filter by tenant

        Returns:
            Dict with currency allocation breakdown
        """
        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        assets = query.all()

        if not assets:
            return {'total_assets': 0, 'by_currency': {}, 'currency_risk': 'N/A'}

        total_value = sum(a.value for a in assets)
        currency_allocation = defaultdict(lambda: {'count': 0, 'value': 0, 'assets': []})

        for asset in assets:
            currency = asset.currency or 'TRY'

            currency_allocation[currency]['count'] += 1
            currency_allocation[currency]['value'] += asset.value
            currency_allocation[currency]['assets'].append({
                'id': asset.id,
                'name': asset.name,
                'value': asset.value
            })

        # Calculate percentages
        for currency, data in currency_allocation.items():
            data['percentage'] = (data['value'] / total_value * 100) if total_value > 0 else 0

        # Assess currency risk
        max_currency_pct = max(data['percentage'] for data in currency_allocation.values()) if currency_allocation else 0
        currency_risk = 'Düşük' if max_currency_pct < 50 else 'Orta' if max_currency_pct < 70 else 'Yüksek'

        return {
            'total_assets': len(assets),
            'total_value': total_value,
            'by_currency': dict(currency_allocation),
            'currency_risk': currency_risk,
            'max_currency_exposure': max_currency_pct
        }

    @staticmethod
    def get_allocation_by_liquidity(tenant_id: str = None) -> Dict:
        """
        Analyze asset allocation by liquidity

        Args:
            tenant_id: Filter by tenant

        Returns:
            Dict with liquidity allocation breakdown
        """
        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        assets = query.all()

        if not assets:
            return {'total_assets': 0, 'by_liquidity': {}, 'liquidity_score': 0}

        total_value = sum(a.value for a in assets)
        liquidity_allocation = defaultdict(lambda: {'count': 0, 'value': 0, 'assets': []})

        for asset in assets:
            liquidity = asset.liquidity or 'Bilinmeyen'

            liquidity_allocation[liquidity]['count'] += 1
            liquidity_allocation[liquidity]['value'] += asset.value
            liquidity_allocation[liquidity]['assets'].append({
                'id': asset.id,
                'name': asset.name,
                'value': asset.value
            })

        # Calculate percentages
        for liquidity, data in liquidity_allocation.items():
            data['percentage'] = (data['value'] / total_value * 100) if total_value > 0 else 0

        # Calculate liquidity score (0-100)
        liquidity_weights = {
            'Likit': 100,
            'Orta Likit': 60,
            'Az Likit': 30,
            'Likitsiz': 0,
            'Bilinmeyen': 50
        }

        liquidity_score = 0
        for liquidity, data in liquidity_allocation.items():
            weight = liquidity_weights.get(liquidity, 50)
            liquidity_score += (data['percentage'] / 100) * weight

        return {
            'total_assets': len(assets),
            'total_value': total_value,
            'by_liquidity': dict(liquidity_allocation),
            'liquidity_score': liquidity_score,
            'liquidity_rating': AdvancedAllocationAnalyzer._get_liquidity_rating(liquidity_score)
        }

    @staticmethod
    def _get_liquidity_rating(score: float) -> str:
        """Get liquidity rating"""
        if score >= 80:
            return 'Çok Yüksek'
        elif score >= 60:
            return 'Yüksek'
        elif score >= 40:
            return 'Orta'
        elif score >= 20:
            return 'Düşük'
        else:
            return 'Çok Düşük'

    @staticmethod
    def get_allocation_by_risk(tenant_id: str = None) -> Dict:
        """
        Analyze asset allocation by risk level

        Args:
            tenant_id: Filter by tenant

        Returns:
            Dict with risk allocation breakdown
        """
        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        assets = query.all()

        if not assets:
            return {'total_assets': 0, 'by_risk': {}, 'average_risk': 'N/A'}

        total_value = sum(a.value for a in assets)
        risk_allocation = defaultdict(lambda: {'count': 0, 'value': 0, 'assets': []})

        for asset in assets:
            risk = asset.risk_level or 'Bilinmeyen'

            risk_allocation[risk]['count'] += 1
            risk_allocation[risk]['value'] += asset.value
            risk_allocation[risk]['assets'].append({
                'id': asset.id,
                'name': asset.name,
                'value': asset.value
            })

        # Calculate percentages
        for risk, data in risk_allocation.items():
            data['percentage'] = (data['value'] / total_value * 100) if total_value > 0 else 0

        # Calculate average risk level
        risk_weights = {
            'Çok Düşük': 1,
            'Düşük': 2,
            'Orta': 3,
            'Yüksek': 4,
            'Çok Yüksek': 5,
            'Bilinmeyen': 3
        }

        weighted_risk = 0
        for risk, data in risk_allocation.items():
            weight = risk_weights.get(risk, 3)
            weighted_risk += (data['percentage'] / 100) * weight

        average_risk = 'Düşük' if weighted_risk < 2.5 else 'Orta' if weighted_risk < 3.5 else 'Yüksek'

        return {
            'total_assets': len(assets),
            'total_value': total_value,
            'by_risk': dict(risk_allocation),
            'average_risk': average_risk,
            'weighted_risk_score': weighted_risk
        }

    @staticmethod
    def get_allocation_by_type(tenant_id: str = None) -> Dict:
        """
        Analyze asset allocation by asset type

        Args:
            tenant_id: Filter by tenant

        Returns:
            Dict with type allocation breakdown
        """
        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        assets = query.all()

        if not assets:
            return {'total_assets': 0, 'by_type': {}, 'diversification_score': 0}

        total_value = sum(a.value for a in assets)
        type_allocation = defaultdict(lambda: {'count': 0, 'value': 0, 'assets': []})

        for asset in assets:
            asset_type = asset.type or 'Bilinmeyen'

            type_allocation[asset_type]['count'] += 1
            type_allocation[asset_type]['value'] += asset.value
            type_allocation[asset_type]['assets'].append({
                'id': asset.id,
                'name': asset.name,
                'value': asset.value
            })

        # Calculate percentages
        for asset_type, data in type_allocation.items():
            data['percentage'] = (data['value'] / total_value * 100) if total_value > 0 else 0

        # Calculate diversification score (0-100)
        diversification_score = min(100, len(type_allocation) * 20)

        return {
            'total_assets': len(assets),
            'total_value': total_value,
            'by_type': dict(type_allocation),
            'diversification_score': diversification_score,
            'diversification_rating': AdvancedAllocationAnalyzer._get_diversification_rating(diversification_score)
        }

    @staticmethod
    def _get_diversification_rating(score: float) -> str:
        """Get diversification rating"""
        if score >= 80:
            return 'Çok İyi'
        elif score >= 60:
            return 'İyi'
        elif score >= 40:
            return 'Orta'
        elif score >= 20:
            return 'Zayıf'
        else:
            return 'Çok Zayıf'

    @staticmethod
    def get_comprehensive_allocation(tenant_id: str = None) -> Dict:
        """
        Get comprehensive multi-dimensional allocation analysis

        Args:
            tenant_id: Filter by tenant

        Returns:
            Dict with all allocation dimensions
        """
        sector_alloc = AdvancedAllocationAnalyzer.get_allocation_by_sector(tenant_id)
        currency_alloc = AdvancedAllocationAnalyzer.get_allocation_by_currency(tenant_id)
        liquidity_alloc = AdvancedAllocationAnalyzer.get_allocation_by_liquidity(tenant_id)
        risk_alloc = AdvancedAllocationAnalyzer.get_allocation_by_risk(tenant_id)
        type_alloc = AdvancedAllocationAnalyzer.get_allocation_by_type(tenant_id)

        # Calculate overall allocation score (0-100)
        sector_score = 100 - sector_alloc['max_sector_exposure'] if 'max_sector_exposure' in sector_alloc else 50
        currency_score = 100 - currency_alloc['max_currency_exposure'] if 'max_currency_exposure' in currency_alloc else 50
        liquidity_score = liquidity_alloc['liquidity_score']
        diversification_score = type_alloc['diversification_score']

        overall_score = (sector_score + currency_score + liquidity_score + diversification_score) / 4

        return {
            'sector': sector_alloc,
            'currency': currency_alloc,
            'liquidity': liquidity_alloc,
            'risk': risk_alloc,
            'type': type_alloc,
            'overall_score': overall_score,
            'overall_rating': AdvancedAllocationAnalyzer._get_diversification_rating(overall_score),
            'recommendations': AdvancedAllocationAnalyzer._generate_allocation_recommendations(
                sector_alloc, currency_alloc, liquidity_alloc, type_alloc
            )
        }

    @staticmethod
    def _generate_allocation_recommendations(sector_alloc: Dict, currency_alloc: Dict, liquidity_alloc: Dict, type_alloc: Dict) -> List[str]:
        """Generate allocation optimization recommendations"""
        recommendations = []

        # Sector concentration
        if sector_alloc.get('max_sector_exposure', 0) > 40:
            recommendations.append(f"Sektör konsantrasyonu yüksek ({sector_alloc['max_sector_exposure']:.1f}%). Farklı sektörlere yayılın.")

        # Currency concentration
        if currency_alloc.get('max_currency_exposure', 0) > 60:
            recommendations.append(f"Döviz konsantrasyonu yüksek ({currency_alloc['max_currency_exposure']:.1f}%). Çoklu döviz kullanın.")

        # Liquidity
        if liquidity_alloc.get('liquidity_score', 0) < 40:
            recommendations.append(f"Likidite skoru düşük ({liquidity_alloc['liquidity_score']:.1f}). Daha likit varlıklar ekleyin.")

        # Diversification
        if type_alloc.get('diversification_score', 0) < 40:
            recommendations.append(f"Çeşitlendirme skoru düşük ({type_alloc['diversification_score']:.1f}). Farklı varlık tipleri ekleyin.")

        if not recommendations:
            recommendations.append("Portföy çeşitlendirmesi iyi durumda.")

        return recommendations
