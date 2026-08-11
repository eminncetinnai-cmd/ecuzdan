"""
Taxonomy Service - Kategori, Varlık Tipi ve Sektör Yönetimi
Phase 16: Hierarchical taxonomy management
"""

import logging
from typing import Dict, List, Optional

from models import AssetSector, AssetType, Category, CategoryAssetTypeMapping, db

logger = logging.getLogger(__name__)


class TaxonomyService:
    """Kategori, varlık tipi ve sektör yönetimi servisi"""

    @staticmethod
    def get_category_tree(tenant_id: Optional[str] = None, max_level: Optional[int] = None) -> List[Dict]:
        """
        Kategori ağacını hiyerarşik olarak döndürür

        Args:
            tenant_id: Tenant ID (None ise tüm kategoriler)
            max_level: Maksimum hiyerarşi seviyesi

        Returns:
            Hiyerarşik kategori listesi
        """
        query = Category.query.filter(Category.is_active)

        if tenant_id:
            query = query.filter((Category.tenant_id == tenant_id) | (Category.tenant_id.is_(None)))

        categories = query.order_by(Category.type, Category.name).all()

        def build_tree(parent_id: Optional[int] = None, level: int = 0) -> List[Dict]:
            if max_level is not None and level > max_level:
                return []

            tree = []
            for cat in categories:
                if cat.parent_id == parent_id:
                    node = {
                        'id': cat.id,
                        'name': cat.name,
                        'type': cat.type,
                        'level': cat.level,
                        'icon': cat.icon,
                        'color': cat.color,
                        'budget_limit': cat.budget_limit,
                        'children': build_tree(cat.id, level + 1)
                    }
                    tree.append(node)
            return tree

        return build_tree()

    @staticmethod
    def get_asset_type_tree(max_level: Optional[int] = None) -> List[Dict]:
        """
        Varlık tipi ağacını hiyerarşik olarak döndürür

        Args:
            max_level: Maksimum hiyerarşi seviyesi

        Returns:
            Hiyerarşik varlık tipi listesi
        """
        asset_types = AssetType.query.order_by(AssetType.name).all()

        def build_tree(parent_id: Optional[int] = None, level: int = 0) -> List[Dict]:
            if max_level is not None and level > max_level:
                return []

            tree = []
            for at in asset_types:
                if at.parent_id == parent_id:
                    node = {
                        'id': at.id,
                        'name': at.name,
                        'level': at.level,
                        'risk_profile': at.risk_profile,
                        'tax_treatment': at.tax_treatment,
                        'min_holding_period': at.min_holding_period,
                        'default_currency': at.default_currency,
                        'liquidity_profile': at.liquidity_profile,
                        'volatility_range': at.volatility_range,
                        'children': build_tree(at.id, level + 1)
                    }
                    tree.append(node)
            return tree

        return build_tree()

    @staticmethod
    def get_sector_tree(max_level: Optional[int] = None) -> List[Dict]:
        """
        Sektör ağacını hiyerarşik olarak döndürür (gelecekteki kullanım için)

        Args:
            max_level: Maksimum hiyerarşi seviyesi

        Returns:
            Hiyerarşik sektör listesi
        """
        # Phase 16'da henüz hiyerarşi yok, düz liste döndür
        sectors = AssetSector.query.order_by(AssetSector.name).all()
        return [{'id': s.id, 'name': s.name} for s in sectors]

    @staticmethod
    def suggest_category(transaction_data: Dict) -> Optional[Category]:
        """
        İşlem için kategori önerisi

        Args:
            transaction_data: İşlem verileri (amount, type, description vb.)

        Returns:
            Önerilen kategori veya None
        """
        # Basit öneri mantığı - gelecekte ML ile geliştirilebilir
        tx_type = transaction_data.get('type')
        description = transaction_data.get('description', '').lower()

        # İşlem tipine göre varsayılan kategori
        if tx_type == 'Gelir':
            # Gelir işlemleri için öneri
            if 'maaş' in description or 'prim' in description:
                return Category.query.filter_by(name='Maaş').first()
            elif 'kira' in description:
                return Category.query.filter_by(name='Kira Geliri').first()
            elif 'temettü' in description:
                return Category.query.filter_by(name='Temettü').first()
            elif 'faiz' in description:
                return Category.query.filter_by(name='Faiz').first()
            else:
                return Category.query.filter_by(name='Ek Gelir').first()

        elif tx_type == 'Gider':
            # Gider işlemleri için öneri
            if 'kredi' in description:
                return Category.query.filter_by(name='Kredi').first()
            elif 'kredi kartı' in description or 'kk' in description:
                return Category.query.filter_by(name='Kredi Kartı').first()
            elif 'kira' in description:
                return Category.query.filter_by(name='Kira').first()
            else:
                return Category.query.filter_by(name='Aylık Sabit Gider').first()

        elif tx_type == 'Yatırım':
            # Yatırım işlemleri için öneri
            return Category.query.filter_by(name='Yatırıma Aktarılan').first()

        return None

    @staticmethod
    def validate_mapping(category_id: int, asset_type_id: int) -> bool:
        """
        Kategori-AssetType uyumluluğunu kontrol eder

        Args:
            category_id: Kategori ID
            asset_type_id: Varlık tipi ID

        Returns:
            True uyumlu, False uyumsuz
        """
        # Mevcut mapping'i kontrol et
        existing = CategoryAssetTypeMapping.query.filter_by(
            category_id=category_id,
            asset_type_id=asset_type_id
        ).first()

        return existing is not None

    @staticmethod
    def create_mapping(category_id: int, asset_type_id: int,
                     is_default: bool = False, weight: float = 1.0,
                     tenant_id: Optional[str] = None) -> CategoryAssetTypeMapping:
        """
        Kategori-AssetType mapping oluşturur

        Args:
            category_id: Kategori ID
            asset_type_id: Varlık tipi ID
            is_default: Varsayılan eşleşme mi
            weight: Ağırlık katsayısı
            tenant_id: Tenant ID

        Returns:
            Oluşturulan mapping
        """
        # Eğer varsayılan ise, diğer varsayılanları kaldır
        if is_default:
            CategoryAssetTypeMapping.query.filter_by(
                category_id=category_id,
                is_default=True
            ).update({'is_default': False})

        mapping = CategoryAssetTypeMapping(
            category_id=category_id,
            asset_type_id=asset_type_id,
            is_default=is_default,
            weight=weight,
            tenant_id=tenant_id
        )

        db.session.add(mapping)
        db.session.commit()

        logger.info(f"Category-AssetType mapping oluşturuldu: Category {category_id} -> AssetType {asset_type_id}")
        return mapping

    @staticmethod
    def get_sector_exposure(portfolio_id: Optional[int] = None) -> Dict[str, float]:
        """
        Portföyün sektör bazlı dağılımını hesaplar

        Args:
            portfolio_id: Portföy ID (gelecekte kullanılacak)

        Returns:
            Sektör bazlı dağılım dict
        """
        from models import Asset

        # Tüm varlıkların sektör dağılımı
        assets = Asset.query.all()

        sector_distribution = {}
        total_value = 0.0

        for asset in assets:
            if asset.sector:
                sector_name = asset.sector.name
                sector_distribution[sector_name] = sector_distribution.get(sector_name, 0.0) + asset.value
                total_value += asset.value

        # Yüzdeleri hesapla
        if total_value > 0:
            for sector in sector_distribution:
                sector_distribution[sector] = (sector_distribution[sector] / total_value) * 100

        return sector_distribution

    @staticmethod
    def get_category_summary(tenant_id: Optional[str] = None) -> Dict[str, Dict]:
        """
        Kategori özetini döndürür (tip bazlı kategori sayısı)

        Args:
            tenant_id: Tenant ID

        Returns:
            Kategori özeti
        """
        query = Category.query.filter(Category.is_active)

        if tenant_id:
            query = query.filter((Category.tenant_id == tenant_id) | (Category.tenant_id.is_(None)))

        categories = query.all()

        summary = {}
        for cat in categories:
            if cat.type not in summary:
                summary[cat.type] = {'count': 0, 'categories': []}
            summary[cat.type]['count'] += 1
            summary[cat.type]['categories'].append({
                'id': cat.id,
                'name': cat.name,
                'level': cat.level
            })

        return summary

    @staticmethod
    def update_category_path(category: Category):
        """
        Kategori hiyerarşi yolunu günceller

        Args:
            category: Kategori nesnesi
        """
        if category.parent_id:
            parent = db.session.get(Category, category.parent_id)
            if parent:
                category.path = f"{parent.path}{category.id}/"
                category.level = parent.level + 1
            else:
                category.path = f"/{category.id}/"
                category.level = 0
        else:
            category.path = f"/{category.id}/"
            category.level = 0

        db.session.commit()

        # Çocukları da güncelle
        for child in category.children:
            TaxonomyService.update_category_path(child)
