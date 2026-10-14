import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from models import QuizQuestion
from shared.db import db

logger = logging.getLogger("QuizQuestionsSeed")


QUIZ_QUESTIONS = [
    # Beginner Questions
    {
        "question": "Bütçe yaparken öncelikle hangi harcamaları dikkate almalısınız?",
        "options": {"A": "Lüks harcamalar", "B": "Sabit giderler", "C": "Tatil harcamaları", "D": "Hobi harcamaları"},
        "correct_answer": "B",
        "explanation": "Sabit giderler (kira, faturalar, sigorta) öncelikli olarak ödenmelidir çünkü bunlar zorunlu harcamalardır.",
        "difficulty": "beginner",
        "topic": "income_expenses"
    },
    {
        "question": "Acil durum fonu ne kadar olmalıdır?",
        "options": {"A": "1 aylık harcama", "B": "3-6 aylık harcama", "C": "12 aylık harcama", "D": "Yarım aylık harcama"},
        "correct_answer": "B",
        "explanation": "Genel olarak 3-6 aylık harcama tutarında acil durum fonu önerilir.",
        "difficulty": "beginner",
        "topic": "emergency_fund"
    },
    {
        "question": "Faiz bileşik etkisi nedir?",
        "options": {"A": "Sadece anaparaya uygulanan faiz", "B": "Anapara ve biriken faize uygulanan faiz", "C": "Sadece faize uygulanan faiz", "D": "Sabit faiz oranı"},
        "correct_answer": "B",
        "explanation": "Bileşik faiz, anapara ve biriken faizin tamamına uygulanan faizdir, bu da zamanla büyümenin hızlanmasını sağlar.",
        "difficulty": "beginner",
        "topic": "compound_interest"
    },
    {
        "question": "Kredi kartı borcunun ödenmesinde en iyi yöntem nedir?",
        "options": {"A": "Minimum ödeme yapmak", "B": "Tamamen ödemek", "C": "Borcu transfer etmek", "D": "Yeni kredi kartı almak"},
        "correct_answer": "B",
        "explanation": "Kredi kartı borcunu tamamen ödemek, faiz maliyetlerini en aza indirir ve finansal sağlığı korur.",
        "difficulty": "beginner",
        "topic": "debt_management"
    },
    {
        "question": "Yatırım yaparken risk ve getiri arasındaki ilişki nedir?",
        "options": {"A": "Risk arttıkça getiri azalır", "B": "Risk arttıkça getiri artabilir", "C": "Risk ve getiri ilişkisi yoktur", "D": "Risk her zaman düşüktür"},
        "correct_answer": "B",
        "explanation": "Genellikle yüksek riskli yatırımlar daha yüksek potansiyel getiri sunar, ancak kayıp riski de daha yüksektir.",
        "difficulty": "beginner",
        "topic": "risk_return"
    },
    # Intermediate Questions
    {
        "question": "Diversifikasyon (çeşitlendirme) nedir?",
        "options": {"A": "Tek bir yatırıma tüm parayı yatırmak", "B": "Farklı varlık türlerine yatırım yapmak", "C": "Sadece hisse senedi almak", "D": "Yatırım yapmamak"},
        "correct_answer": "B",
        "explanation": "Diversifikasyon, riski dağıtmak için farklı varlık türlerine (hisse, tahvil, emtia vb.) yatırım yapmaktır.",
        "difficulty": "intermediate",
        "topic": "diversification"
    },
    {
        "question": "P/E (Price-to-Earnings) oranı neyi gösterir?",
        "options": {"A": "Şirketin borç miktarını", "B": "Hisse başına kazanç ile fiyat ilişkisi", "C": "Şirketin piyasa değeri", "D": "Temettü ödeme oranı"},
        "correct_answer": "B",
        "explanation": "P/E oranı, bir hissenin fiyatının şirketin hisse başına kazancına oranını gösterir ve değerleme için kullanılır.",
        "difficulty": "intermediate",
        "topic": "stock_analysis"
    },
    {
        "question": "Enflasyonun tasarruflar üzerindeki etkisi nedir?",
        "options": {"A": "Tasarrufların değerini artırır", "B": "Tasarrufların satın alma gücünü azaltır", "C": "Etkisi yoktur", "D": "Sadece nakit para için geçerlidir"},
        "correct_answer": "B",
        "explanation": "Enflasyon, paranın satın alma gücünü azaltır, bu da tasarrufların gerçek değerini zamanla düşürür.",
        "difficulty": "intermediate",
        "topic": "inflation"
    },
    {
        "question": "Tax-loss harvesting nedir?",
        "options": {"A": "Vergi kaçırma yöntemi", "B": "Zararlı yatırımları satıp vergi avantajı elde etme", "C": "Yatırım yapmama", "D": "Sadece kazançlı yatırımları satma"},
        "correct_answer": "B",
        "explanation": "Tax-loss harvesting, zararlı yatırımları satarak sermaye kazançlarını dengelemek ve vergi yükünü azaltmak için kullanılan bir stratejidir.",
        "difficulty": "intermediate",
        "topic": "tax_optimization"
    },
    {
        "question": "Dolar-cost averaging (DCA) nedir?",
        "options": {"A": "Tek seferde büyük yatırım", "B": "Düzenli aralıklarla sabit tutarlı yatırım", "C": "Sadece düşük fiyattan alma", "D": "Yatırım yapmama"},
        "correct_answer": "B",
        "explanation": "DCA, zamanlama riskini azaltmak için düzenli aralıklarla sabit tutarlarla yatırım yapma stratejisidir.",
        "difficulty": "intermediate",
        "topic": "investment_strategy"
    },
    # Advanced Questions
    {
        "question": "Beta katsayısı neyi ölçer?",
        "options": {"A": "Şirketin büyüme potansiyelini", "B": "Hissenin piyasa volatilitesine duyarlılığını", "C": "Temettü ödeme kapasitesini", "D": "Şirketin borç oranını"},
        "correct_answer": "B",
        "explanation": "Beta katsayısı, bir hissenin piyasa hareketlerine ne kadar duyarlı olduğunu gösterir. Beta > 1 ise piyasa daha volatildir.",
        "difficulty": "advanced",
        "topic": "risk_metrics"
    },
    {
        "question": "Sharpe oranı neyi gösterir?",
        "options": {"A": "Yatırımın toplam getirisini", "B": "Risk ayarlı getiri performansını", "C": "Volatiliteyi", "D": "Maksimum düşüşü"},
        "correct_answer": "B",
        "explanation": "Sharpe oranı, bir yatırımın risk ayarlı getiri performansını ölçer. Yüksek Sharpe oranı, birim risk başına daha yüksek getiri anlamına gelir.",
        "difficulty": "advanced",
        "topic": "performance_metrics"
    },
    {
        "question": "Rebalancing nedir?",
        "options": {"A": "Portföyü tamamen değiştirmek", "B": "Hedef ağırlıkları korumak için portföyü yeniden dengelemek", "C": "Sadece kazançlı varlıkları satmak", "D": "Portföyü büyütmek"},
        "correct_answer": "B",
        "explanation": "Rebalancing, portföyün hedef varlık ağırlıklarını korumak için zamanla değişen ağılıkları yeniden ayarlama işlemidir.",
        "difficulty": "advanced",
        "topic": "portfolio_management"
    },
    {
        "question": "Alpha nedir?",
        "options": {"A": "Piyasa getirisinden fazla getiri", "B": "Piyasa getirisinden düşük getiri", "C": "Volatilite ölçüsü", "D": "Risk oranı"},
        "correct_answer": "A",
        "explanation": "Alpha, bir yatırımın piyasa getirisinden (benchmark) fazla veya eksik performansını gösterir. Pozitif alpha, piyasa üzerinde performans anlamına gelir.",
        "difficulty": "advanced",
        "topic": "performance_metrics"
    },
    {
        "question": "Derivatives (türev araçlar) nedir?",
        "options": {"A": "Sadece hisse senetleri", "B": "Değeri başka bir varlıktan türetilen finansal araçlar", "C": "Sadece tahviller", "D": "Nakit para"},
        "correct_answer": "B",
        "explanation": "Türev araçlar, değeri başka bir varlıktan (hisse, emtia, döviz vb.) türetilen finansal sözleşmelerdir (opsiyon, futures vb.).",
        "difficulty": "advanced",
        "topic": "derivatives"
    },
]


def seed_quiz_questions():
    """Quiz sorularını database'e ekler"""
    logger.debug("Quiz soruları seed işlemi başlatılıyor...")

    for q_data in QUIZ_QUESTIONS:
        # Check if question already exists
        existing = QuizQuestion.query.filter_by(
            question=q_data["question"],
            difficulty=q_data["difficulty"],
            topic=q_data["topic"]
        ).first()

        if not existing:
            question = QuizQuestion(
                question=q_data["question"],
                options=q_data["options"],
                correct_answer=q_data["correct_answer"],
                explanation=q_data.get("explanation"),
                difficulty=q_data["difficulty"],
                topic=q_data["topic"],
                tenant_id=None,  # Global questions
                is_active=True
            )
            db.session.add(question)
            logger.debug(f"Soru eklendi: {q_data['question'][:50]}...")
        else:
            logger.debug(f"Soru zaten var: {q_data['question'][:50]}...")

    db.session.commit()
    logger.debug(f"Quiz soruları seed işlemi tamamlandı. Toplam soru: {len(QUIZ_QUESTIONS)}")


if __name__ == "__main__":
    from app import app
    with app.app_context():
        seed_quiz_questions()
