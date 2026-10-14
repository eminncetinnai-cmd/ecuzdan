"""Unit tests for AutoCategorizationService (domain/transactions/services/auto_categorization_service.py).

Tests Turkish word extraction, stop-word filtering, keyword-based category prediction,
model training from historical transactions, user feedback learning, suggestions,
and batch categorization.
"""

import pytest
from domain.transactions.services.auto_categorization_service import AutoCategorizationService
from models import Category, Transaction, db


@pytest.fixture
def categorization_setup(app):
    with app.app_context():
        # Ensure standard categories exist in database
        cats = [
            ("Maaş", "Gelir"),
            ("Ek Gelir", "Gelir"),
            ("Kira Geliri", "Gelir"),
            ("Kira", "Gider"),
            ("Aylık Sabit Gider", "Gider"),
            ("Yatırıma Aktarılan", "Yatırım"),
        ]
        for name, c_type in cats:
            if not Category.query.filter_by(name=name).first():
                db.session.add(Category(name=name, type=c_type))
        db.session.commit()
        yield AutoCategorizationService()


def test_extract_words(categorization_setup):
    service = categorization_setup
    # None or empty
    assert service._extract_words("") == []
    assert service._extract_words(None) == []

    # Turkish text with stopwords and punctuation
    text = "Ahmet ve Mehmet için ev kirası ve elektrik aidat ödemesi yapıldı!"
    words = service._extract_words(text)
    assert "ahmet" in words
    assert "mehmet" in words
    assert "kirası" in words
    assert "elektrik" in words
    assert "aidat" in words
    # Stop words removed
    assert "ve" not in words
    assert "için" not in words


def test_predict_category_with_known_keyword(categorization_setup):
    service = categorization_setup
    tx = Transaction(description="Aylık maaş ödemesi hesaba geçti", type="Gelir")
    cat = service.predict_category(tx)
    assert cat is not None
    assert cat.name == "Maaş"


def test_predict_category_type_fallback(categorization_setup):
    service = categorization_setup
    # No matching keywords (unkeyed tokens), fallback based on type
    tx_income = Transaction(description="Tamamen alakasız birikim girdisi", type="Gelir")
    cat_inc = service.predict_category(tx_income)
    assert cat_inc is not None
    assert cat_inc.name == "Ek Gelir"

    tx_expense = Transaction(description="Tamamen alakasız cüzdan çıktısı", type="Gider")
    cat_exp = service.predict_category(tx_expense)
    assert cat_exp is not None
    assert cat_exp.name == "Aylık Sabit Gider"

    tx_invest = Transaction(description="Tamamen alakasız portföy hamlesi", type="Yatırım")
    cat_inv = service.predict_category(tx_invest)
    assert cat_inv is not None
    assert cat_inv.name == "Yatırıma Aktarılan"

    tx_other = Transaction(description="Tamamen alakasız transfer", type="Other")
    assert service.predict_category(tx_other) is None

    # Empty description
    tx_empty = Transaction(description="", type="Gelir")
    assert service.predict_category(tx_empty) is None



def test_train_model_from_historical_transactions(categorization_setup):
    service = categorization_setup
    tx1 = Transaction(description="Şirket yıllık başarı primi", category="Ek Gelir")
    tx2 = Transaction(description="Ofis kırtasiye malzemesi", category="Aylık Sabit Gider")

    service.train_model([tx1, tx2])
    # The new word "başarı" should now be mapped to "Ek Gelir"
    assert "başarı" in service.category_keywords
    assert service.category_keywords["başarı"]["Ek Gelir"] > 0


def test_learn_from_feedback(categorization_setup):
    service = categorization_setup
    correct_cat = Category.query.filter_by(name="Kira").first()
    tx = Transaction(id=101, description="Apt yönetim aidatı", type="Gider")

    service.learn_from_feedback(tx, correct_cat)
    assert "yönetim" in service.category_keywords
    assert service.category_keywords["yönetim"]["Kira"] >= 0.5


def test_get_category_suggestions(categorization_setup):
    service = categorization_setup
    # Empty description
    assert service.get_category_suggestions("") == []

    # Known keywords description
    suggestions = service.get_category_suggestions("kira ve elektrik aidatı", limit=3)
    assert len(suggestions) > 0
    first_suggestion = suggestions[0]
    assert "category" in first_suggestion
    assert "score" in first_suggestion
    assert 0 <= first_suggestion["confidence"] <= 1.0


def test_batch_categorize(categorization_setup):
    service = categorization_setup
    tx1 = Transaction(id=1, description="Aylık maaş bordrosu", type="Gelir")
    tx2 = Transaction(id=2, description="Ev kira ödemesi", type="Gider")

    batch_res = service.batch_categorize([tx1, tx2])
    assert 1 in batch_res
    assert 2 in batch_res
    assert batch_res[1].name == "Maaş"
    assert batch_res[2].name in ("Kira", "Kira Geliri")




def test_get_model_stats(categorization_setup):
    service = categorization_setup
    stats = service.get_model_stats()
    assert stats["model_type"] == "keyword_based"
    assert stats["total_keywords"] > 0
    assert stats["total_categories"] > 0
