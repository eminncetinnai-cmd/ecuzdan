"""
Auto Categorization Service - ML tabanlı otomatik kategorizasyon
Phase 16: Machine learning based automatic categorization
"""

import logging
import re
from collections import defaultdict
from typing import Dict, List, Optional

from models import Category, Transaction

logger = logging.getLogger(__name__)


class AutoCategorizationService:
    """ML tabanlı otomatik kategorizasyon servisi"""

    def __init__(self):
        # Basit kelime tabanlı model - gelecekte gerçek ML ile değiştirilebilir
        self.category_keywords = self._build_keyword_model()
        self.transaction_history = defaultdict(list)

    def _build_keyword_model(self) -> Dict[str, Dict[str, float]]:
        """
        Kategori bazlı kelime ağırlıkları modeli oluştur
        Geçmiş işlemlerden öğrenerek kategori-kel ilişkisi kurar
        """
        model = defaultdict(lambda: defaultdict(float))

        # Varsayılan keyword mapping
        default_keywords = {
            'Maaş': ['maaş', 'prim', 'ücret', 'maaş'],
            'Kira Geliri': ['kira', 'ev kirası', 'daire kirası'],
            'Ek Gelir': ['ek gelir', 'bonus', 'hediye', 'ikramiye'],
            'Kira': ['kira', 'ev kirası', 'daire kirası', 'konut'],
            'Kredi': ['kredi', 'borç', 'taksit', 'faiz'],
            'Kredi Kartı': ['kredi kartı', 'kk', 'kart', 'pos'],
            'Aylık Sabit Gider': ['aidat', 'elektrik', 'su', 'doğalgaz', 'internet'],
            'Temettü': ['temettü', 'kar payı', 'dividend'],
            'Faiz': ['faiz', 'getiri', 'kazanç'],
            'Yatırıma Aktarılan': ['yatırım', 'hisse', 'fon', 'altın', 'döviz'],
        }

        for category, keywords in default_keywords.items():
            for keyword in keywords:
                model[keyword][category] = 1.0

        return dict(model)

    def train_model(self, historical_transactions: List[Transaction]):
        """
        Geçmiş işlemlerle model eğitir

        Args:
            historical_transactions: Geçmiş işlem listesi
        """
        logger.info(f"Model eğitiliyor... {len(historical_transactions)} işlem ile")

        for tx in historical_transactions:
            if tx.category:
                description = tx.description or ''
                words = self._extract_words(description)

                for word in words:
                    weights = self.category_keywords.setdefault(word, {})
                    weights[tx.category] = weights.get(tx.category, 0.0) + 0.1

        logger.info("Model eğitimi tamamlandı")

    def _extract_words(self, text: str) -> List[str]:
        """
        Metinden kelimeleri çıkarır (Türkçe destekli)
        """
        if not text:
            return []

        # Küçük harfe çevir ve özel karakterleri kaldır
        text = text.lower()
        text = re.sub(r'[^\w\sğüşıöç]', ' ', text)

        # Kelimeleri ayır
        words = text.split()

        # Stop words kaldır (Türkçe)
        stop_words = {'ve', 'veya', 'ile', 'için', 'bu', 'şu', 'o', 'bir', 've', 'de', 'da'}
        words = [w for w in words if w not in stop_words and len(w) > 2]

        return words

    def predict_category(self, transaction: Transaction) -> Optional[Category]:
        """
        İşlem için kategori tahmin eder

        Args:
            transaction: İşlem nesnesi

        Returns:
            Tahmin edilen kategori veya None
        """
        description = transaction.description or ''
        words = self._extract_words(description)

        if not words:
            return None

        # Her kelime için kategori skorları
        category_scores = defaultdict(float)

        for word in words:
            if word in self.category_keywords:
                for category, score in self.category_keywords[word].items():
                    category_scores[category] += score

        # En yüksek skoru olan kategoriyi seç
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            category = Category.query.filter_by(name=best_category[0]).first()
            return category

        # İşlem tipine göre varsayılan kategori
        if transaction.type == 'Gelir':
            return Category.query.filter_by(name='Ek Gelir').first()
        elif transaction.type == 'Gider':
            return Category.query.filter_by(name='Aylık Sabit Gider').first()
        elif transaction.type == 'Yatırım':
            return Category.query.filter_by(name='Yatırıma Aktarılan').first()

        return None

    def learn_from_feedback(self, transaction: Transaction, correct_category: Category):
        """
        Kullanıcı geri bildiriminden öğrenir

        Args:
            transaction: İşlem nesnesi
            correct_category: Doğru kategori
        """
        description = transaction.description or ''
        words = self._extract_words(description)

        for word in words:
            # Doğru kategori için skoru artır
            weights = self.category_keywords.setdefault(word, {})
            weights[correct_category.name] = weights.get(correct_category.name, 0.0) + 0.5

        logger.info(f"Model güncellendi: {transaction.id} için {correct_category.name}")

    def get_category_suggestions(self, description: str, limit: int = 5) -> List[Dict]:
        """
        Açıklama için kategori önerileri döndürür

        Args:
            description: İşlem açıklaması
            limit: Maksimum öneri sayısı

        Returns:
            Kategori önerileri listesi
        """
        words = self._extract_words(description)

        if not words:
            return []

        category_scores = defaultdict(float)

        for word in words:
            if word in self.category_keywords:
                for category, score in self.category_keywords[word].items():
                    category_scores[category] += score

        # Skorlara göre sırala
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)

        suggestions = []
        for category_name, score in sorted_categories[:limit]:
            category = Category.query.filter_by(name=category_name).first()
            if category:
                suggestions.append({
                    'category': category,
                    'score': score,
                    'confidence': min(score / (score + 1.0), 1.0)  # Basit confidence hesabı
                })

        return suggestions

    def batch_categorize(self, transactions: List[Transaction]) -> Dict[int, Optional[Category]]:
        """
        Toplu kategorizasyon

        Args:
            transactions: İşlem listesi

        Returns:
            İşlem ID -> Kategori mapping
        """
        results = {}

        for tx in transactions:
            predicted_category = self.predict_category(tx)
            results[tx.id] = predicted_category

        return results

    def get_model_stats(self) -> Dict:
        """
        Model istatistiklerini döndürür
        """
        total_keywords = len(self.category_keywords)
        total_categories = len(set(cat for words in self.category_keywords.values() for cat in words.keys()))

        return {
            'total_keywords': total_keywords,
            'total_categories': total_categories,
            'model_type': 'keyword_based'
        }
