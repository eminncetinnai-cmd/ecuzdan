"""Seed profile questions into the database."""

import json
import sys

# Add parent directory to path
sys.path.insert(0, '.')

import app
from models import ProfileQuestion
from shared.db import db


def get_default_questions():
    """Default question bank from profile scoring engine."""
    questions = []

    # Finansal Okuryazarlık (10 soru)
    literacy_questions = [
        {
            'id': 'LIT001',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'Bileşik faiz nedir?',
            'options': [
                {'value': 0, 'text': 'Ana paranın sadece faiz kazanması'},
                {'value': 1, 'text': 'Faizin de faiz kazanması'},
                {'value': 0, 'text': 'Bankanın kâr payı'},
                {'value': 0, 'text': 'Enflasyon oranı'}
            ],
            'correct_answer': 1,
            'explanation': 'Bileşik faiz, kazanılan faizin de faiz kazanmasıdır.',
            'difficulty': 'easy'
        },
        {
            'id': 'LIT002',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'Diversifikasyon (çeşitlendirme) ne anlama gelir?',
            'options': [
                {'value': 0, 'text': 'Tek bir varlığa tüm parayı yatırmak'},
                {'value': 1, 'text': 'Farklı varlık sınıflarına yatırım yapmak'},
                {'value': 0, 'text': 'Sadece hisse senedi almak'},
                {'value': 0, 'text': 'Yüksek riskli yatırımlardan kaçınmak'}
            ],
            'correct_answer': 1,
            'explanation': 'Çeşitlendirme, riski azaltmak için farklı varlıklara yatırım yapmaktır.',
            'difficulty': 'easy'
        },
        {
            'id': 'LIT003',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'P/E (Price-to-Earnings) oranı neyi gösterir?',
            'options': [
                {'value': 0, 'text': 'Şirketin borç miktarı'},
                {'value': 1, 'text': 'Hisse fiyatının kâra oranı'},
                {'value': 0, 'text': 'Şirketin piyasa değeri'},
                {'value': 0, 'text': 'Temettü ödeme oranı'}
            ],
            'correct_answer': 1,
            'explanation': 'P/E oranı, hissenin kârlılık göstergesidir.',
            'difficulty': 'medium'
        },
        {
            'id': 'LIT004',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'Enflasyon yatırım portföyünü nasıl etkiler?',
            'options': [
                {'value': 0, 'text': 'Etkilemez'},
                {'value': 1, 'text': 'Satın alma gücünü azaltır'},
                {'value': 0, 'text': 'Her zaman yatırım getirilerini artırır'},
                {'value': 0, 'text': 'Sadece nakit varlıkları etkiler'}
            ],
            'correct_answer': 1,
            'explanation': 'Enflasyon, paranın satın alma gücünü azaltır.',
            'difficulty': 'easy'
        },
        {
            'id': 'LIT005',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'Temettü nedir?',
            'options': [
                {'value': 0, 'text': 'Hisse senedi fiyat artışı'},
                {'value': 1, 'text': 'Şirketin kârından hissedarlara ödenen pay'},
                {'value': 0, 'text': 'Banka faiz oranı'},
                {'value': 0, 'text': 'Vergi indirimi'}
            ],
            'correct_answer': 1,
            'explanation': 'Temettü, şirketin kârından hissedarlara dağıtılan paydır.',
            'difficulty': 'easy'
        },
        {
            'id': 'LIT006',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'Risk primi nedir?',
            'options': [
                {'value': 0, 'text': 'Risk almadan kazanılan getiri'},
                {'value': 1, 'text': 'Risksiz faiz üzerindeki ek getiri beklentisi'},
                {'value': 0, 'text': 'Yatırımın maliyeti'},
                {'value': 0, 'text': 'Enflasyon oranı'}
            ],
            'correct_answer': 1,
            'explanation': 'Risk primi, riskli yatırımların risksiz faiz üzerindeki ek getirisidir.',
            'difficulty': 'medium'
        },
        {
            'id': 'LIT007',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'Likit varlık nedir?',
            'options': [
                {'value': 1, 'text': 'Kolayca nakde çevrilebilen varlık'},
                {'value': 0, 'text': 'Uzun vadeli yatırım'},
                {'value': 0, 'text': 'Gayrimenkul'},
                {'value': 0, 'text': 'Borçlanma aracı'}
            ],
            'correct_answer': 1,
            'explanation': 'Likit varlıklar hızlıca nakde çevrilebilir.',
            'difficulty': 'easy'
        },
        {
            'id': 'LIT008',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'Volatilite neyi ifade eder?',
            'options': [
                {'value': 1, 'text': 'Fiyat dalgalanması'},
                {'value': 0, 'text': 'Yatırım getirisi'},
                {'value': 0, 'text': 'Şirket büyümesi'},
                {'value': 0, 'text': 'Piyasa hacmi'}
            ],
            'correct_answer': 1,
            'explanation': 'Volatilite, fiyatların dalgalanma derecesidir.',
            'difficulty': 'medium'
        },
        {
            'id': 'LIT009',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'Beta katsayısı neyi ölçer?',
            'options': [
                {'value': 0, 'text': 'Şirketin büyüme hızı'},
                {'value': 1, 'text': 'Piyasa ile korelasyon ve risk'},
                {'value': 0, 'text': 'Temettü oranı'},
                {'value': 0, 'text': 'Borç seviyesi'}
            ],
            'correct_answer': 1,
            'explanation': 'Beta, hissenin piyasa hareketlerine duyarlılığını ölçer.',
            'difficulty': 'medium'
        },
        {
            'id': 'LIT010',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'Stop-loss emri nedir?',
            'options': [
                {'value': 0, 'text': 'Kar alma emri'},
                {'value': 1, 'text': 'Zararı sınırlama emri'},
                {'value': 0, 'text': 'Alış emri'},
                {'value': 0, 'text': 'Piyasa izleme emri'}
            ],
            'correct_answer': 1,
            'explanation': 'Stop-loss, zararı sınırlamak için otomatik satış emridir.',
            'difficulty': 'medium'
        }
    ]
    questions.extend(literacy_questions)

    # Risk Kapasitesi (8 soru)
    capacity_questions = [
        {
            'id': 'CAP001',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Aylık gelirinizin ne kadarını yatırım yapabilirsiniz?',
            'options': [
                {'value': 0, 'text': '%0-5'},
                {'value': 1, 'text': '%5-10'},
                {'value': 2, 'text': '%10-20'},
                {'value': 3, 'text': '%20+'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Yatırım kapasitesi, gelirin yatırım oranına göre değerlendirilir.',
            'difficulty': 'medium'
        },
        {
            'id': 'CAP002',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Acil durum fonunuz ne kadar süre idare eder?',
            'options': [
                {'value': 0, 'text': 'Yok'},
                {'value': 1, 'text': '1-3 ay'},
                {'value': 2, 'text': '3-6 ay'},
                {'value': 3, 'text': '6 ay+'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Acil durum fonu, finansal güvenlik göstergesidir.',
            'difficulty': 'easy'
        },
        {
            'id': 'CAP003',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Toplam varlıklarınızın ne kadarı likit (nakit/eşdeğer)?',
            'options': [
                {'value': 0, 'text': '%0-10'},
                {'value': 1, 'text': '%10-30'},
                {'value': 2, 'text': '%30-50'},
                {'value': 3, 'text': '%50+'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Likit varlık oranı, finansal esneklik gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'CAP004',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Aylık sabit giderleriniz gelirinizin ne kadarını oluşturuyor?',
            'options': [
                {'value': 3, 'text': '%0-30'},
                {'value': 2, 'text': '%30-50'},
                {'value': 1, 'text': '%50-70'},
                {'value': 0, 'text': '%70+'}
            ],
            'scoring_weights': {'3': 100, '2': 67, '1': 33, '0': 0},
            'explanation': 'Düşük sabit gider oranı, yüksek risk kapasitesi gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'CAP005',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Borç/gelir oranınız nedir?',
            'options': [
                {'value': 3, 'text': '%0-20'},
                {'value': 2, 'text': '%20-40'},
                {'value': 1, 'text': '%40-60'},
                {'value': 0, 'text': '%60+'}
            ],
            'scoring_weights': {'3': 100, '2': 67, '1': 33, '0': 0},
            'explanation': 'Düşük borç oranı, yüksek risk kapasitesi sağlar.',
            'difficulty': 'medium'
        },
        {
            'id': 'CAP006',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Yatırım deneyiminiz kaç yıl?',
            'options': [
                {'value': 0, 'text': '0-1 yıl'},
                {'value': 1, 'text': '1-3 yıl'},
                {'value': 2, 'text': '3-5 yıl'},
                {'value': 3, 'text': '5 yıl+'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Uzun deneyim, yüksek risk kapasitesi gösterir.',
            'difficulty': 'easy'
        },
        {
            'id': 'CAP007',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Yatırım hedefiniz için zaman ufku nedir?',
            'options': [
                {'value': 0, 'text': '1 yıl altı'},
                {'value': 1, 'text': '1-3 yıl'},
                {'value': 2, 'text': '3-5 yıl'},
                {'value': 3, 'text': '5 yıl+'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Uzun vadeli hedefler, yüksek risk kapasitesine izin verir.',
            'difficulty': 'easy'
        },
        {
            'id': 'CAP008',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Gelir istikrarınız nasıl?',
            'options': [
                {'value': 0, 'text': 'Çok değişken'},
                {'value': 1, 'text': 'Bazen değişken'},
                {'value': 2, 'text': 'Genellikle istikrarlı'},
                {'value': 3, 'text': 'Çok istikrarlı'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'İstikrarlı gelir, yüksek risk kapasitesi sağlar.',
            'difficulty': 'easy'
        }
    ]
    questions.extend(capacity_questions)

    # Risk Toleransı (8 soru)
    tolerance_questions = [
        {
            'id': 'TOL001',
            'dimension': 'tolerance',
            'type': 'scale',
            'question': 'Portföyünüz %20 değer kaybederse ne yaparsınız?',
            'options': [
                {'value': 0, 'text': 'Hemen satarsınız'},
                {'value': 1, 'text': 'Beklersiniz'},
                {'value': 2, 'text': 'Daha fazla alırsınız'},
                {'value': 3, 'text': 'Fırsat olarak görürsünüz'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Düşüşte fırsat görmek, yüksek risk toleransı gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'TOL002',
            'dimension': 'tolerance',
            'type': 'scale',
            'question': 'Hangi getiri/volatilite kombinasyonunu tercih edersiniz?',
            'options': [
                {'value': 0, 'text': '%5 getiri, %5 volatilite'},
                {'value': 1, 'text': '%10 iade, %15 volatilite'},
                {'value': 2, 'text': '%15 iade, %25 volatilite'},
                {'value': 3, 'text': '%20+ iade, %35+ volatilite'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Yüksek getiri/volatilite tercihi, yüksek risk toleransı gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'TOL003',
            'dimension': 'tolerance',
            'type': 'scale',
            'question': 'Yatırım kararlarında ne kadar stres yaşarsınız?',
            'options': [
                {'value': 0, 'text': 'Çok yüksek stres'},
                {'value': 1, 'text': 'Orta stres'},
                {'value': 2, 'text': 'Düşük stres'},
                {'value': 3, 'text': 'Neredeyse hiç stres'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Düşük stres toleransı, yüksek risk toleransı gösterir.',
            'difficulty': 'easy'
        },
        {
            'id': 'TOL004',
            'dimension': 'tolerance',
            'type': 'scale',
            'question': 'Piyasa düşüşlerinde uyku kaliteniz nasıl etkilenir?',
            'options': [
                {'value': 0, 'text': 'Çok kötü etkilenir'},
                {'value': 1, 'text': 'Biraz etkilenir'},
                {'value': 2, 'text': 'Az etkilenir'},
                {'value': 3, 'text': 'Etkilenmez'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Piyasa dalgalanmalarına duyarsızlık, yüksek risk toleransı gösterir.',
            'difficulty': 'easy'
        },
        {
            'id': 'TOL005',
            'dimension': 'tolerance',
            'type': 'scale',
            'question': 'Arkadaşlarınız yatırım tavsiyesi verdiğinde ne yaparsınız?',
            'options': [
                {'value': 0, 'text': 'Hemen uygularsınız'},
                {'value': 1, 'text': 'Araştırırsınız'},
                {'value': 2, 'text': 'Kendi analiziniz yaparsınız'},
                {'value': 3, 'text': 'Kendi stratejinize sadık kalırsınız'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Kendi stratejiye sadakat, yüksek risk toleransı gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'TOL006',
            'dimension': 'tolerance',
            'type': 'scale',
            'question': 'Hangi yatırım tarzını tercih edersiniz?',
            'options': [
                {'value': 0, 'text': 'Çok muhafazakar'},
                {'value': 1, 'text': 'Muhafazakar'},
                {'value': 2, 'text': 'Dengeli'},
                {'value': 3, 'text': 'Agresif'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Agresif tarz, yüksek risk toleransı gösterir.',
            'difficulty': 'easy'
        },
        {
            'id': 'TOL007',
            'dimension': 'tolerance',
            'type': 'scale',
            'question': 'Bilinmeyen yatırımlara ne kadar açıksınız?',
            'options': [
                {'value': 0, 'text': 'Hiç açık değilim'},
                {'value': 1, 'text': 'Biraz açığım'},
                {'value': 2, 'text': 'Oldukça açığım'},
                {'value': 3, 'text': 'Çok açığım'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Bilinmeyene açıklık, yüksek risk toleransı gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'TOL008',
            'dimension': 'tolerance',
            'type': 'scale',
            'question': 'Kötü yatırım kararlarından sonra kendinizi nasıl hissedersiniz?',
            'options': [
                {'value': 0, 'text': 'Çok kötü, uzun süre etkilenirim'},
                {'value': 1, 'text': 'Kötü, bir süre etkilenirim'},
                {'value': 2, 'text': 'Kötü ama hızla geçer'},
                {'value': 3, 'text': 'Normal, ders çıkarırım'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Hızlı toparlanma, yüksek risk toleransı gösterir.',
            'difficulty': 'medium'
        }
    ]
    questions.extend(tolerance_questions)

    # Davranışsal Finans (7 soru)
    behavioral_questions = [
        {
            'id': 'BEH001',
            'dimension': 'behavioral',
            'type': 'scale',
            'question': 'Kazanç elde ettiğinizde ne yaparsınız?',
            'options': [
                {'value': 0, 'text': 'Hemen realize ederim'},
                {'value': 1, 'text': 'Kısa sürede realize ederim'},
                {'value': 2, 'text': 'Beklerim'},
                {'value': 3, 'text': 'Uzun süre tutarım'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Uzun vadeli tutma, disiplinli davranış gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'BEH002',
            'dimension': 'behavioral',
            'type': 'scale',
            'question': 'Kayıp yaşadığınızda ne yaparsınız?',
            'options': [
                {'value': 0, 'text': 'Hemen satıp zararı keserim'},
                {'value': 1, 'text': 'Kısa sürede satıp zararı keserim'},
                {'value': 2, 'text': 'Beklerim'},
                {'value': 3, 'text': 'Daha fazla alırım'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Düşüşte alım, disiplinli davranış gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'BEH003',
            'dimension': 'behavioral',
            'type': 'scale',
            'question': 'Piyasa haberlerine ne kadar tepki verirsiniz?',
            'options': [
                {'value': 0, 'text': 'Hemen tepki veririm'},
                {'value': 1, 'text': 'Kısa sürede tepki veririm'},
                {'value': 2, 'text': 'Araştırıp karar veririm'},
                {'value': 3, 'text': 'Stratejime sadık kalırım'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Stratejiye sadakat, disiplinli davranış gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'BEH004',
            'dimension': 'behavioral',
            'type': 'scale',
            'question': 'Duygusal karar verme sıklığınız nedir?',
            'options': [
                {'value': 0, 'text': 'Çok sık'},
                {'value': 1, 'text': 'Sık'},
                {'value': 2, 'text': 'Az'},
                {'value': 3, 'text': 'Hiç'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Düşük duygusal karar, disiplinli davranış gösterir.',
            'difficulty': 'easy'
        },
        {
            'id': 'BEH005',
            'dimension': 'behavioral',
            'type': 'scale',
            'question': 'Yatırım planınızı ne sıklıkla değiştirirsiniz?',
            'options': [
                {'value': 0, 'text': 'Çok sık'},
                {'value': 1, 'text': 'Sık'},
                {'value': 2, 'text': 'Az'},
                {'value': 3, 'text': 'Hiç'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Plan sadakati, disiplinli davranış gösterir.',
            'difficulty': 'easy'
        },
        {
            'id': 'BEH006',
            'dimension': 'behavioral',
            'type': 'scale',
            'question': 'FOMO (fırsatı kaçırma korkusu) yaşar mısınız?',
            'options': [
                {'value': 0, 'text': 'Çok sık'},
                {'value': 1, 'text': 'Sık'},
                {'value': 2, 'text': 'Az'},
                {'value': 3, 'text': 'Hiç'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Düşük FOMO, disiplinli davranış gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'BEH007',
            'dimension': 'behavioral',
            'type': 'scale',
            'question': 'Kendi kendinize ne kadar güvenirsiniz?',
            'options': [
                {'value': 0, 'text': 'Çok az'},
                {'value': 1, 'text': 'Az'},
                {'value': 2, 'text': 'Oldukça'},
                {'value': 3, 'text': 'Çok fazla'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Yüksek özgüven, disiplinli davranış gösterir.',
            'difficulty': 'easy'
        }
    ]
    questions.extend(behavioral_questions)

    # Yatırım Deneyimi (7 soru)
    experience_questions = [
        {
            'id': 'EXP001',
            'dimension': 'experience',
            'type': 'scale',
            'question': 'Kaç farklı varlık sınıfına yatırım yaptınız?',
            'options': [
                {'value': 0, 'text': '0-1'},
                {'value': 1, 'text': '2-3'},
                {'value': 2, 'text': '4-5'},
                {'value': 3, 'text': '5+'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Çeşitli varlık sınıfları, deneyim gösterir.',
            'difficulty': 'easy'
        },
        {
            'id': 'EXP002',
            'dimension': 'experience',
            'type': 'scale',
            'question': 'Kaç farklı yatırım ürünü kullandınız?',
            'options': [
                {'value': 0, 'text': '0-2'},
                {'value': 1, 'text': '3-5'},
                {'value': 2, 'text': '6-10'},
                {'value': 3, 'text': '10+'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Çeşitli ürünler, deneyim gösterir.',
            'difficulty': 'easy'
        },
        {
            'id': 'EXP003',
            'dimension': 'experience',
            'type': 'scale',
            'question': 'Finansal okuma/yazma seviyeniz nedir?',
            'options': [
                {'value': 0, 'text': 'Başlangıç'},
                {'value': 1, 'text': 'Temel'},
                {'value': 2, 'text': 'İleri'},
                {'value': 3, 'text': 'Uzman'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Yüksek finansal okuryazarlık, deneyim gösterir.',
            'difficulty': 'easy'
        },
        {
            'id': 'EXP004',
            'dimension': 'experience',
            'type': 'scale',
            'question': 'Finansal haberleri takip ediyor musunuz?',
            'options': [
                {'value': 0, 'text': 'Hiç'},
                {'value': 1, 'text': 'Bazen'},
                {'value': 2, 'text': 'Sık'},
                {'value': 3, 'text': 'Her gün'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Haber takibi, deneyim gösterir.',
            'difficulty': 'easy'
        },
        {
            'id': 'EXP005',
            'dimension': 'experience',
            'type': 'scale',
            'question': 'Finansal eğitim aldınız mı?',
            'options': [
                {'value': 0, 'text': 'Hiç'},
                {'value': 1, 'text': 'Biraz'},
                {'value': 2, 'text': 'Oldukça'},
                {'value': 3, 'text': 'Çok fazla'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Finansal eğitim, deneyim gösterir.',
            'difficulty': 'easy'
        },
        {
            'id': 'EXP006',
            'dimension': 'experience',
            'type': 'scale',
            'question': 'Profesyonel danışman kullandınız mı?',
            'options': [
                {'value': 0, 'text': 'Hiç'},
                {'value': 1, 'text': 'Biraz'},
                {'value': 2, 'text': 'Sık'},
                {'value': 3, 'text': 'Sürekli'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Profesyonel danışmanlık, deneyim gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'EXP007',
            'dimension': 'experience',
            'type': 'scale',
            'question': 'Kendi yatırım stratejiniz var mı?',
            'options': [
                {'value': 0, 'text': 'Yok'},
                {'value': 1, 'text': 'Temel'},
                {'value': 2, 'text': 'Gelişmiş'},
                {'value': 3, 'text': 'Çok gelişmiş'}
            ],
            'scoring_weights': {'0': 0, '1': 33, '2': 67, '3': 100},
            'explanation': 'Gelişmiş strateji, deneyim gösterir.',
            'difficulty': 'medium'
        }
    ]
    questions.extend(experience_questions)

    return questions


def seed_questions():
    """Seed profile questions into the database."""

    with app.app.app_context():
        # Clear existing questions
        ProfileQuestion.query.delete()
        db.session.commit()

        # Get default questions
        questions = get_default_questions()

        # Add questions to database
        for q in questions:
            question = ProfileQuestion(
                id=q['id'],
                dimension=q['dimension'],
                question_text=q['question'],
                question_type=q['type'],
                options=json.dumps(q['options']),
                correct_order=json.dumps(q.get('correct_order'), ensure_ascii=False) if q.get('correct_order') else None,
                correct_answer=q.get('correct_answer'),
                scoring_weights=json.dumps(q.get('scoring_weights', {})),
                explanation=q.get('explanation'),
                difficulty=q.get('difficulty', 'medium'),
                is_active=True,
                version='1.0'
            )
            db.session.add(question)

        db.session.commit()
        print(f"✓ {len(questions)} profile questions seeded successfully")


if __name__ == '__main__':
    seed_questions()
