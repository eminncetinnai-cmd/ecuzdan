"""Default question bank for investor profile scoring."""

def get_default_question_bank():
    """Varsayılan 40 soruluk banka oluştur"""
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
            'question': 'Reel getiri nedir?',
            'options': [
                {'value': 0, 'text': 'Nominal faiz oranı'},
                {'value': 1, 'text': 'Enflasyon düşüldükten sonra kalan getiri'},
                {'value': 0, 'text': 'Vergi öncesi getiri'},
                {'value': 0, 'text': 'Banka faizi'}
            ],
            'correct_answer': 1,
            'explanation': 'Reel getiri = Nominal getiri - Enflasyon.',
            'difficulty': 'medium'
        },
        {
            'id': 'LIT003',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'Diversifikasyon nedir?',
            'options': [
                {'value': 0, 'text': 'Tek varlığa yatırım yapmak'},
                {'value': 1, 'text': 'Farklı varlıklara yayılmak'},
                {'value': 0, 'text': 'Sadece hisse senedi almak'},
                {'value': 0, 'text': 'Yüksek risk almak'}
            ],
            'correct_answer': 1,
            'explanation': 'Diversifikasyon riski azaltmak için farklı varlıklara yayılmaktır.',
            'difficulty': 'easy'
        },
        {
            'id': 'LIT004',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'Volatilite neyi ifade eder?',
            'options': [
                {'value': 0, 'text': 'Yüksek getiri'},
                {'value': 1, 'text': 'Fiyat dalgalanması'},
                {'value': 0, 'text': 'Düşük risk'},
                {'value': 0, 'text': 'Sabit getiri'}
            ],
            'correct_answer': 1,
            'explanation': 'Volatilite, fiyatların dalgalanma derecesidir.',
            'difficulty': 'medium'
        },
        {
            'id': 'LIT005',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'Yatırım fonu nedir?',
            'options': [
                {'value': 0, 'text': 'Tek bir hisse senedi'},
                {'value': 1, 'text': 'Birden fazla varlığın toplu yatırımı'},
                {'value': 0, 'text': 'Banka mevduatı'},
                {'value': 0, 'text': 'Devlet tahvili'}
            ],
            'correct_answer': 1,
            'explanation': 'Yatırım fonu, profesyonel yönetilen varlık sepetidir.',
            'difficulty': 'easy'
        },
        {
            'id': 'LIT006',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'Enflasyonun etkisi nedir?',
            'options': [
                {'value': 0, 'text': 'Satın alma gücünü artırır'},
                {'value': 1, 'text': 'Satın alma gücünü azaltır'},
                {'value': 0, 'text': 'Faiz oranlarını düşürür'},
                {'value': 0, 'text': 'Yatırım getirilerini artırır'}
            ],
            'correct_answer': 1,
            'explanation': 'Enflasyon paranın satın alma gücünü azaltır.',
            'difficulty': 'easy'
        },
        {
            'id': 'LIT007',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'Tahvil nedir?',
            'options': [
                {'value': 0, 'text': 'Hisse senedi'},
                {'value': 1, 'text': 'Borçlanma aracı'},
                {'value': 0, 'text': 'Yatırım fonu'},
                {'value': 0, 'text': 'Emtia'}
            ],
            'correct_answer': 1,
            'explanation': 'Tahvil, devlet veya şirketlerin borçlanma aracıdır.',
            'difficulty': 'medium'
        },
        {
            'id': 'LIT008',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'Uzun vadeli yatırımın avantajı nedir?',
            'options': [
                {'value': 0, 'text': 'Hızlı getiri'},
                {'value': 1, 'text': 'Bileşik faiz etkisi'},
                {'value': 0, 'text': 'Düşük risk'},
                {'value': 0, 'text': 'Kolay likidite'}
            ],
            'correct_answer': 1,
            'explanation': 'Uzun vadeli yatırım bileşik faiz avantajı sunar.',
            'difficulty': 'medium'
        },
        {
            'id': 'LIT009',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'Risk-getiri ilişkisi nedir?',
            'options': [
                {'value': 0, 'text': 'Yüksek risk = düşük getiri'},
                {'value': 1, 'text': 'Yüksek risk = yüksek getiri beklentisi'},
                {'value': 0, 'text': 'Risk yoktur'},
                {'value': 0, 'text': 'Getiri sabittir'}
            ],
            'correct_answer': 1,
            'explanation': 'Genellikle yüksek risk, yüksek getiri beklentisi ile ilişkilidir.',
            'difficulty': 'easy'
        },
        {
            'id': 'LIT010',
            'dimension': 'literacy',
            'type': 'multiple_choice',
            'question': 'Likidite nedir?',
            'options': [
                {'value': 0, 'text': 'Yüksek risk'},
                {'value': 1, 'text': 'Nakit dönüş hızı'},
                {'value': 0, 'text': 'Düşük getiri'},
                {'value': 0, 'text': 'Uzun vadeli yatırım'}
            ],
            'correct_answer': 1,
            'explanation': 'Likidite, varlığın nakite dönüş hızını ifade eder.',
            'difficulty': 'medium'
        }
    ]

    # Risk Kapasitesi (10 soru)
    capacity_questions = [
        {
            'id': 'CAP001',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Aylık gelirinizin ne kadarını acil durum fonuna ayırabilirsiniz?',
            'options': [
                {'value': 0, 'text': 'Hiçbir zaman'},
                {'value': 2, 'text': '%1-5'},
                {'value': 4, 'text': '%5-10'},
                {'value': 6, 'text': '%10-20'},
                {'value': 10, 'text': '%20+'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Acil durum fonu finansal güvenliğin temelidir.',
            'difficulty': 'easy'
        },
        {
            'id': 'CAP002',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Yaşınız nedir?',
            'options': [
                {'value': 10, 'text': '18-25'},
                {'value': 8, 'text': '26-35'},
                {'value': 6, 'text': '36-45'},
                {'value': 4, 'text': '46-55'},
                {'value': 2, 'text': '56+'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Genç yaşlar daha yüksek risk kapasitesi sunar.',
            'difficulty': 'easy'
        },
        {
            'id': 'CAP003',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Aylık gelir durmunuz?',
            'options': [
                {'value': 2, 'text': 'Yetersiz'},
                {'value': 4, 'text': 'Sınırlı'},
                {'value': 6, 'text': 'Orta'},
                {'value': 8, 'text': 'İyi'},
                {'value': 10, 'text': 'Yüksek'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Gelir düzeyi risk kapasitesini belirler.',
            'difficulty': 'easy'
        },
        {
            'id': 'CAP004',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Gelir istikrarınız?',
            'options': [
                {'value': 2, 'text': 'Çok değişken'},
                {'value': 4, 'text': 'Bazen değişken'},
                {'value': 6, 'text': 'Genellikle stabil'},
                {'value': 8, 'text': 'Stabil'},
                {'value': 10, 'text': 'Çok stabil'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Gelir istikrarı risk kapasitesini artırır.',
            'difficulty': 'medium'
        },
        {
            'id': 'CAP005',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Borç durumunuz?',
            'options': [
                {'value': 2, 'text': 'Çok yüksek borç'},
                {'value': 4, 'text': 'Yüksek borç'},
                {'value': 6, 'text': 'Orta borç'},
                {'value': 8, 'text': 'Düşük borç'},
                {'value': 10, 'text': 'Borç yok'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Düşük borç daha yüksek risk kapasitesi sağlar.',
            'difficulty': 'easy'
        },
        {
            'id': 'CAP006',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Kaç kişinin geçiminden sorumlusunuz?',
            'options': [
                {'value': 2, 'text': '4+ kişi'},
                {'value': 4, 'text': '3 kişi'},
                {'value': 6, 'text': '2 kişi'},
                {'value': 8, 'text': '1 kişi'},
                {'value': 10, 'text': 'Kendim'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Daha az bağımlı kişi daha yüksek risk kapasitesi sağlar.',
            'difficulty': 'easy'
        },
        {
            'id': 'CAP007',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Yatırım süreniz ne kadar?',
            'options': [
                {'value': 2, 'text': '< 1 yıl'},
                {'value': 4, 'text': '1-3 yıl'},
                {'value': 6, 'text': '3-5 yıl'},
                {'value': 8, 'text': '5-10 yıl'},
                {'value': 10, 'text': '10+ yıl'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Uzun yatırım süresi daha yüksek risk kapasitesi sağlar.',
            'difficulty': 'easy'
        },
        {
            'id': 'CAP008',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Likidite ihtiyacınız?',
            'options': [
                {'value': 2, 'text': 'Çok yüksek'},
                {'value': 4, 'text': 'Yüksek'},
                {'value': 6, 'text': 'Orta'},
                {'value': 8, 'text': 'Düşük'},
                {'value': 10, 'text': 'Çok düşük'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Düşük likidite ihtiyacı daha yüksek risk kapasitesi sağlar.',
            'difficulty': 'medium'
        },
        {
            'id': 'CAP009',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Acil durum fonunuz var mı?',
            'options': [
                {'value': 0, 'text': 'Yok'},
                {'value': 3, 'text': '1 aylık gider'},
                {'value': 6, 'text': '3 aylık gider'},
                {'value': 8, 'text': '6 aylık gider'},
                {'value': 10, 'text': '12+ aylık gider'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Acil durum fonu risk kapasitesini artırır.',
            'difficulty': 'easy'
        },
        {
            'id': 'CAP010',
            'dimension': 'capacity',
            'type': 'scale',
            'question': 'Maaş dışı geliriniz var mı?',
            'options': [
                {'value': 0, 'text': 'Yok'},
                {'value': 3, 'text': 'Az'},
                {'value': 6, 'text': 'Orta'},
                {'value': 8, 'text': 'İyi'},
                {'value': 10, 'text': 'Çok iyi'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Ek gelir kaynakları risk kapasitesini artırır.',
            'difficulty': 'medium'
        }
    ]

    # Risk Toleransı (10 soru)
    tolerance_questions = [
        {
            'id': 'TOL001',
            'dimension': 'tolerance',
            'type': 'scale',
            'question': 'Yatırımınızın %10 değer kaybederse ne yaparsınız?',
            'options': [
                {'value': 0, 'text': 'Hemen satıyorum'},
                {'value': 2, 'text': 'Birkaç gün bekliyorum'},
                {'value': 4, 'text': '1-3 ay bekliyorum'},
                {'value': 6, 'text': '6-12 ay bekliyorum'},
                {'value': 10, 'text': '3+ yıl bekliyorum'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Risk toleransı kayıp durumunda davranışı gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'TOL002',
            'dimension': 'tolerance',
            'type': 'scale',
            'question': 'Yatırımınızın %20 değer kaybederse?',
            'options': [
                {'value': 0, 'text': 'Hemen satıyorum'},
                {'value': 2, 'text': 'Birkaç gün bekliyorum'},
                {'value': 4, 'text': '1-3 ay bekliyorum'},
                {'value': 6, 'text': '6-12 ay bekliyorum'},
                {'value': 10, 'text': '3+ yıl bekliyorum'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Büyük kayıplara tolerans risk seviyesini gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'TOL003',
            'dimension': 'tolerance',
            'type': 'scale',
            'question': 'Yatırımınızın %40 değer kaybederse?',
            'options': [
                {'value': 0, 'text': 'Hemen satıyorum'},
                {'value': 2, 'text': 'Birkaç gün bekliyorum'},
                {'value': 4, 'text': '1-3 ay bekliyorum'},
                {'value': 6, 'text': '6-12 ay bekliyorum'},
                {'value': 10, 'text': '3+ yıl bekliyorum'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Ekstrem kayıplara tolerans en yüksek riski gösterir.',
            'difficulty': 'hard'
        },
        {
            'id': 'TOL004',
            'dimension': 'tolerance',
            'type': 'yes_no',
            'question': 'Piyasa düşerken alım yapma eğiliminde misiniz?',
            'options': [
                {'value': 0, 'text': 'Hayır'},
                {'value': 10, 'text': 'Evet'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Düşüşte alım yüksek risk toleransı gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'TOL005',
            'dimension': 'tolerance',
            'type': 'scale',
            'question': 'Piyasa haberlerini ne sıklıkla takip edersiniz?',
            'options': [
                {'value': 0, 'text': 'Hiçbir zaman'},
                {'value': 2, 'text': 'Ayda bir'},
                {'value': 4, 'text': 'Haftada bir'},
                {'value': 6, 'text': 'Günde bir'},
                {'value': 10, 'text': 'Sürekli'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Sürekli takip yüksek risk toleransı gösterebilir.',
            'difficulty': 'easy'
        },
        {
            'id': 'TOL006',
            'dimension': 'tolerance',
            'type': 'scale',
            'question': 'Yatırım kararlarını ne sıklıkla değiştirirsiniz?',
            'options': [
                {'value': 10, 'text': 'Hiçbir zaman'},
                {'value': 8, 'text': 'Yılda bir'},
                {'value': 6, 'text': 'Ayda bir'},
                {'value': 4, 'text': 'Haftada bir'},
                {'value': 0, 'text': 'Günlük'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Sık değişiklik düşük risk toleransı gösterebilir.',
            'difficulty': 'medium'
        },
        {
            'id': 'TOL007',
            'dimension': 'tolerance',
            'type': 'yes_no',
            'question': 'Kısa vadeli kazançlar peşinde misiniz?',
            'options': [
                {'value': 2, 'text': 'Evet'},
                {'value': 8, 'text': 'Hayır'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Kısa vadeli kazanç arayışı risk toleransını etkiler.',
            'difficulty': 'medium'
        },
        {
            'id': 'TOL008',
            'dimension': 'tolerance',
            'type': 'scale',
            'question': 'Uzun vadeli hedefleriniz var mı?',
            'options': [
                {'value': 0, 'text': 'Yok'},
                {'value': 3, 'text': '1-3 yıl'},
                {'value': 6, 'text': '3-5 yıl'},
                {'value': 8, 'text': '5-10 yıl'},
                {'value': 10, 'text': '10+ yıl'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Uzun vadeli hedefler yüksek risk toleransı ile ilişkilidir.',
            'difficulty': 'easy'
        },
        {
            'id': 'TOL009',
            'dimension': 'tolerance',
            'type': 'scale',
            'question': 'Riskli yatırımlara ilginiz var mı?',
            'options': [
                {'value': 0, 'text': 'Hiçbir zaman'},
                {'value': 2, 'text': 'Az'},
                {'value': 4, 'text': 'Orta'},
                {'value': 6, 'text': 'İyi'},
                {'value': 10, 'text': 'Çok iyi'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Riskli yatırımlara ilgi risk toleransını gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'TOL010',
            'dimension': 'tolerance',
            'type': 'scale',
            'question': 'Yatırım stres seviyeniz?',
            'options': [
                {'value': 10, 'text': 'Çok düşük'},
                {'value': 8, 'text': 'Düşük'},
                {'value': 6, 'text': 'Orta'},
                {'value': 4, 'text': 'Yüksek'},
                {'value': 0, 'text': 'Çok yüksek'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Düşük stres seviyesi yüksek risk toleransı gösterir.',
            'difficulty': 'medium'
        }
    ]

    # Davranışsal Finans (5 soru)
    behavioral_questions = [
        {
            'id': 'BEH001',
            'dimension': 'behavioral',
            'type': 'yes_no',
            'question': 'Piyasa yükselirken daha fazla alım yapma eğiliminde misiniz?',
            'options': [
                {'value': 0, 'text': 'Hayır'},
                {'value': 10, 'text': 'Evet'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Bu, sürü psikolojisi (herding behavior) göstergesidir.',
            'difficulty': 'medium'
        },
        {
            'id': 'BEH002',
            'dimension': 'behavioral',
            'type': 'yes_no',
            'question': 'Kayıplardan kaçınma eğiliminiz var mı?',
            'options': [
                {'value': 0, 'text': 'Evet'},
                {'value': 10, 'text': 'Hayır'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Kayıptan kaçınma (loss aversion) davranışsal risktir.',
            'difficulty': 'medium'
        },
        {
            'id': 'BEH003',
            'dimension': 'behavioral',
            'type': 'yes_no',
            'question': 'FOMO (Fırsatı Kaçırma Korkusu) yaşıyor musunuz?',
            'options': [
                {'value': 0, 'text': 'Evet'},
                {'value': 10, 'text': 'Hayır'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'FOMO davranışsal risk göstergesidir.',
            'difficulty': 'medium'
        },
        {
            'id': 'BEH004',
            'dimension': 'behavioral',
            'type': 'yes_no',
            'question': 'Kendi analizlerinize aşırı güveniyor musunuz?',
            'options': [
                {'value': 0, 'text': 'Evet'},
                {'value': 10, 'text': 'Hayır'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Aşırı özgüven (overconfidence) davranışsal risktir.',
            'difficulty': 'medium'
        },
        {
            'id': 'BEH005',
            'dimension': 'behavioral',
            'type': 'yes_no',
            'question': 'Sadece kendi görüşlerinizi doğrulayan bilgileri mi arıyorsunuz?',
            'options': [
                {'value': 0, 'text': 'Evet'},
                {'value': 10, 'text': 'Hayır'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Doğrulama yanlılığı (confirmation bias) davranışsal risktir.',
            'difficulty': 'medium'
        }
    ]

    # Yatırım Deneyimi (5 soru)
    experience_questions = [
        {
            'id': 'EXP001',
            'dimension': 'experience',
            'type': 'multiple_choice',
            'question': 'Hangi yatırım araçlarını kullandınız?',
            'options': [
                {'value': 0, 'text': 'Hiçbiri'},
                {'value': 2, 'text': 'Sadece mevduat'},
                {'value': 4, 'text': 'Hisse senedi/fon'},
                {'value': 6, 'text': 'Tahvil/altın'},
                {'value': 10, 'text': 'Türev/kripto'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Yatırım deneyimi kullanılan araç çeşitliliğini gösterir.',
            'difficulty': 'easy'
        },
        {
            'id': 'EXP002',
            'dimension': 'experience',
            'type': 'scale',
            'question': 'Yatırım süreniz ne kadar?',
            'options': [
                {'value': 0, 'text': 'Yatırım yapmadım'},
                {'value': 2, 'text': '< 1 yıl'},
                {'value': 4, 'text': '1-3 yıl'},
                {'value': 6, 'text': '3-5 yıl'},
                {'value': 10, 'text': '5+ yıl'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Yatırım süresi deneyimi gösterir.',
            'difficulty': 'easy'
        },
        {
            'id': 'EXP003',
            'dimension': 'experience',
            'type': 'scale',
            'question': 'Portföy büyüklüğünüz?',
            'options': [
                {'value': 0, 'text': 'Yatırım yok'},
                {'value': 2, 'text': '< 10.000 TL'},
                {'value': 4, 'text': '10.000-50.000 TL'},
                {'value': 6, 'text': '50.000-200.000 TL'},
                {'value': 10, 'text': '200.000+ TL'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Portföy büyüklüğü deneyimi gösterir.',
            'difficulty': 'easy'
        },
        {
            'id': 'EXP004',
            'dimension': 'experience',
            'type': 'scale',
            'question': 'Yatırım işlem sıklığınız?',
            'options': [
                {'value': 0, 'text': 'Yatırım yapmıyorum'},
                {'value': 2, 'text': 'Yılda birkaç kez'},
                {'value': 4, 'text': 'Ayda bir'},
                {'value': 6, 'text': 'Haftada bir'},
                {'value': 10, 'text': 'Günlük'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'İşlem sıklığı deneyimi gösterir.',
            'difficulty': 'easy'
        },
        {
            'id': 'EXP005',
            'dimension': 'experience',
            'type': 'yes_no',
            'question': 'Yatırım eğitimi aldınız mı?',
            'options': [
                {'value': 0, 'text': 'Hayır'},
                {'value': 10, 'text': 'Evet'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Yatırım eğitimi deneyimi artırır.',
            'difficulty': 'easy'
        }
    ]

    # Senaryo Bazlı Sorular (5 yeni soru - yeni soru türü)
    scenario_questions = [
        {
            'id': 'SCN001',
            'dimension': 'tolerance',
            'type': 'scenario',
            'question': 'Senaryo: Piyasa %30 düşerse, 100.000 TL\'lik yatırımınız 70.000 TL\'ye düşer. Ne yaparsınız?',
            'options': [
                {'value': 0, 'text': 'Hemen satıp nakite çevirim'},
                {'value': 3, 'text': 'Kısa vadede beklerim'},
                {'value': 6, 'text': 'Uzun vadede beklerim'},
                {'value': 10, 'text': 'Düşüşte alım yaparım'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Senaryo bazlı sorular gerçek piyasa davranışını tahmin eder.',
            'difficulty': 'hard'
        },
        {
            'id': 'SCN002',
            'dimension': 'capacity',
            'type': 'scenario',
            'question': 'Senaryo: İşinizi kaybedersiniz ve 6 ay iş bulamazsınız. Ne kadar tasarrufunuz var?',
            'options': [
                {'value': 0, 'text': '1 hafta yetecek'},
                {'value': 3, 'text': '1 ay yetecek'},
                {'value': 6, 'text': '3 ay yetecek'},
                {'value': 10, 'text': '6+ ay yetecek'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Acil durum senaryosu risk kapasitesini gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'SCN003',
            'dimension': 'behavioral',
            'type': 'scenario',
            'question': 'Senaryo: Arkadaşınız kripto para ile %100 kazandığını söylüyor. Ne yaparsınız?',
            'options': [
                {'value': 0, 'text': 'Hemen yatırım yaparım'},
                {'value': 3, 'text': 'Araştırıp yatırım yaparım'},
                {'value': 6, 'text': 'Küçük miktar denerim'},
                {'value': 10, 'text': 'Risk almadan beklerim'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Sosyal etki ve FOMO davranışını ölçer.',
            'difficulty': 'medium'
        },
        {
            'id': 'SCN004',
            'dimension': 'literacy',
            'type': 'scenario',
            'question': 'Senaryo: Banka %20 faiz sunuyor, enflasyon %40. Bu yatırım size ne kazandırır?',
            'options': [
                {'value': 0, 'text': '%20 kazandırır'},
                {'value': 5, 'text': 'Kayıp veririm'},
                {'value': 10, 'text': '%20 reel kayıp veririm'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Reel getiri kavramını senaryo ile test eder.',
            'difficulty': 'medium'
        },
        {
            'id': 'SCN005',
            'dimension': 'experience',
            'type': 'scenario',
            'question': 'Senaryo: Hisse senediniz %10 düşükken şirket iyi haberler açıkladı. Ne yaparsınız?',
            'options': [
                {'value': 0, 'text': 'Hemen satıyorum'},
                {'value': 3, 'text': 'Bekliyorum'},
                {'value': 6, 'text': 'Düşüşte alım yaparım'},
                {'value': 10, 'text': 'Analiz edip karar veririm'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Piyasa analizi ve karar verme deneyimini gösterir.',
            'difficulty': 'hard'
        }
    ]

    # Sıralama Soruları (3 yeni soru - yeni soru türü)
    ranking_questions = [
        {
            'id': 'RNK001',
            'dimension': 'literacy',
            'type': 'ranking',
            'question': 'Aşağıdaki yatırım araçlarını risk seviyesine göre sıralayın (Düşük riskten Yüksek riske):',
            'options': [
                {'value': 0, 'text': 'Hisse senedi'},
                {'value': 1, 'text': 'Devlet tahvili'},
                {'value': 2, 'text': 'Kripto para'},
                {'value': 3, 'text': 'Mevduat'}
            ],
            'correct_order': ['Mevduat', 'Devlet tahvili', 'Hisse senedi', 'Kripto para'],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Risk sıralaması finansal okuryazarlığı gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'RNK002',
            'dimension': 'tolerance',
            'type': 'ranking',
            'question': 'Aşağıdaki hedefleri önem sırasına göre sıralayın:',
            'options': [
                {'value': 0, 'text': 'Yüksek getiri'},
                {'value': 1, 'text': 'Sermayeyi koruma'},
                {'value': 2, 'text': 'Düzenli gelir'},
                {'value': 3, 'text': 'Likidite'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Hedef sıralaması risk toleransını gösterir.',
            'difficulty': 'medium'
        },
        {
            'id': 'RNK003',
            'dimension': 'behavioral',
            'type': 'ranking',
            'question': 'Piyasa haberlerini takip önceliğinizi sıralayın:',
            'options': [
                {'value': 0, 'text': 'Kısa vadeli haberler'},
                {'value': 1, 'text': 'Uzun vadeli trendler'},
                {'value': 2, 'text': 'Şirket haberleri'},
                {'value': 3, 'text': 'Global ekonomi'}
            ],
            'scoring_weights': {'min': 0, 'max': 10},
            'explanation': 'Haber takip davranışını gösterir.',
            'difficulty': 'easy'
        }
    ]

    # Tüm soruları birleştir
    questions = literacy_questions + capacity_questions + tolerance_questions + behavioral_questions + experience_questions + scenario_questions + ranking_questions

    # Dictionary formatına çevir
    question_dict = {}
    for q in questions:
        question_dict[q['id']] = q

    return question_dict

