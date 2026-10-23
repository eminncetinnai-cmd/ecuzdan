/**
 * E-Cüzdan Smart Quick Input Suite
 * 1. Bank SMS & Clipboard Auto-Parser
 * 2. Turkish Speech-to-Expense Voice Dictation
 */

(function () {
    'use strict';

    // Turkish number words dictionary
    const TURKISH_NUMBERS = {
        'bir': 1, 'iki': 2, 'üç': 3, 'uc': 3, 'dört': 4, 'dort': 4, 'beş': 5, 'bes': 5,
        'altı': 6, 'alti': 6, 'yedi': 7, 'sekiz': 8, 'dokuz': 9, 'on': 10,
        'yirmi': 20, 'otuz': 30, 'kırk': 40, 'kirk': 40, 'elli': 50,
        'altmış': 60, 'altmis': 60, 'yetmiş': 70, 'yetmis': 70, 'seksen': 80, 'doksan': 90,
        'yüz': 100, 'yuz': 100, 'bin': 1000, 'milyon': 1000000
    };

    const CATEGORY_KEYWORDS = {
        'Market': ['migros', 'carrefour', 'bim', 'a101', 'şok', 'sok', 'tarım kredi', 'tarim kredi', 'hakmar', 'file', 'macrocenter', 'market', 'bakkal', 'manav', 'kasap'],
        'Yemek': ['yemeksepeti', 'getir', 'trendyol yemek', 'burger', 'mcdonald', 'kfc', 'pizza', 'kafe', 'cafe', 'starbucks', 'espresso', 'restoran', 'restaurant', 'lokanta', 'kebap', 'döner', 'doner', 'kahve', 'yemek', 'öğle yemeği', 'ogle yemegi', 'akşam yemeği', 'aksam yemegi', 'kahvaltı', 'kahvalti'],
        'Ulaşım': ['shell', 'opet', 'bp', 'petrol ofisi', 'total', 'aygaz', 'uber', 'taksi', 'itaksi', 'martı', 'marti', 'binbin', 'tcdd', 'thy', 'pegasus', 'bilet', 'otobüs', 'otobus', 'metro', 'akaryakıt', 'akaryakit', 'benzin', 'mazot', 'dizel', 'lpg', 'otopark'],
        'Fatura': ['turkcell', 'vodafone', 'türk telekom', 'turk telekom', 'enerjisa', 'iski', 'igdaş', 'igdas', 'ck boğaziçi', 'netflix', 'spotify', 'youtube', 'd-smart', 'digiturk', 'fatura', 'elektrik', 'su faturası', 'doğalgaz', 'dogalgaz', 'internet', 'aidat'],
        'Sağlık': ['eczane', 'hastane', 'medikal', 'sağlık', 'saglik', 'klinik', 'optik', 'diş', 'ilac', 'ilaç'],
        'Giyim': ['zara', 'boyner', 'lcw', 'waikiki', 'mango', 'h&m', 'koton', 'mavi', 'defacto', 'beymen', 'network', 'ayakkabı', 'ayakkabi', 'flo', 'giyim', 'kıyafet', 'elbise'],
        'Maaş': ['maaş', 'maas', 'avans', 'hakediş', 'hakedis', 'prim', 'ücret', 'ucret', 'aylık', 'aylik']
    };

    /**
     * Parse Turkish bank transaction SMS text
     * Examples:
     * "0123 nolu kartınız ile MIGROS magazisinda 485,50 TL harcama yapilmistir."
     * "Hesabınızdan SHELL istasyonunda 1.250,00 TL harcama gerçekleşti."
     */
    function parseBankSMS(text) {
        if (!text || typeof text !== 'string') return null;

        let amount = null;
        let merchant = '';
        let detectedCategory = 'Diğer';
        let detectedType = 'Gider';

        // 1. Amount Extraction (supports 1.250,50 TL / 450.00 TL / 350 TL)
        const amountRegex = /(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?|\d+(?:[.,]\d{1,2})?)\s*(?:TL|₺|TRY|EUR|USD)/i;
        const amountFallbackRegex = /(?:tutar[ıi]?|harcama|ödenen|ödeme)\s*:?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?|\d+(?:[.,]\d{1,2})?)/i;

        let amountMatch = text.match(amountRegex) || text.match(amountFallbackRegex);
        if (amountMatch) {
            let rawNum = amountMatch[1];
            // Normalize Turkish dot/comma formatting
            if (rawNum.includes('.') && rawNum.includes(',')) {
                rawNum = rawNum.replace(/\./g, '').replace(',', '.');
            } else if (rawNum.includes(',')) {
                rawNum = rawNum.replace(',', '.');
            }
            amount = parseFloat(rawNum);
        }

        // 2. Merchant / Description Extraction
        const merchantRegex = /(?:kartınızla|kartinizla|kartı ile|karti ile|ile|hesabınızdan|hesabinizdan)\s+([A-Za-z0-9ÇĞİÖŞÜçğıöşü\s\.\*\-\_]+?)\s+(?:işyerinde|isyerinde|mağazasında|magazasinda|mağazası|üzerinden|tarafından|firmasında|şubesinde|harcama|yapılmıştır|yapilmistir)/i;
        let merchantMatch = text.match(merchantRegex);
        if (merchantMatch && merchantMatch[1]) {
            merchant = merchantMatch[1].trim()
                .replace(/^[*0-9\s]+/, '')
                .replace(/\s+/g, ' ');
        } else {
            // Fallback: search for keywords
            merchant = text.substring(0, 40).trim();
        }

        // Clean common noise
        merchant = merchant.replace(/(?:nolu|kart|hesap|banka)\s*/gi, '').trim();
        if (merchant.length > 30) {
            merchant = merchant.substring(0, 30);
        }

        // 3. Category Determination
        const lowerText = text.toLowerCase();
        for (const [cat, words] of Object.entries(CATEGORY_KEYWORDS)) {
            if (words.some(w => lowerText.includes(w))) {
                detectedCategory = cat;
                if (cat === 'Maaş') {
                    detectedType = 'Gelir';
                }
                break;
            }
        }

        return {
            amount: amount,
            merchant: merchant || 'Banka Harcaması',
            category: detectedCategory,
            type: detectedType
        };
    }

    /**
     * Convert Turkish number phrase into numeric value (e.g. "üç yüz elli" -> 350)
     */
    function parseTurkishSpokenNumber(text) {
        // Direct digits match
        const digitMatch = text.match(/\b\d+(?:[.,]\d+)?\b/);
        if (digitMatch) {
            return parseFloat(digitMatch[0].replace(',', '.'));
        }

        // Spoken words parser
        const words = text.toLowerCase().split(/\s+/);
        let total = 0;
        let current = 0;

        for (const word of words) {
            const val = TURKISH_NUMBERS[word];
            if (val !== undefined) {
                if (val === 1000) {
                    current = (current === 0 ? 1 : current) * 1000;
                    total += current;
                    current = 0;
                } else if (val === 100) {
                    current = (current === 0 ? 1 : current) * 100;
                } else {
                    current += val;
                }
            }
        }
        total += current;
        return total > 0 ? total : null;
    }

    // --- Global Exposed Action 1: Panodan Yapıştır (Banka SMS) ---
    window.pasteAndParseBankSMS = async function () {
        let text = '';
        if (navigator.clipboard && navigator.clipboard.readText) {
            try {
                text = await navigator.clipboard.readText();
            } catch (e) {
                console.warn('[SmartInput] Clipboard permission denied, prompting user');
            }
        }

        if (!text || text.trim().length === 0) {
            text = prompt('Lütfen kopyaladığınız banka harcama SMS veya bildirim metnini buraya yapıştırın:');
        }

        if (!text || text.trim().length === 0) return;

        const parsed = parseBankSMS(text);
        if (!parsed || !parsed.amount) {
            if (window.showToast) {
                window.showToast('Metin içinde geçerli bir tutar bulunamadı.', 'warning');
            }
            return;
        }

        // Populate Quick Tx Modal fields
        const amountInput = document.getElementById('globalQuickTxAmount');
        const descInput = document.getElementById('globalQuickTxDesc') || document.querySelector('#globalQuickTxForm input[name="description"]');
        const flowSelect = document.getElementById('globalQuickTxFlowType');
        const catSelect = document.getElementById('globalQuickTxCategory');

        if (amountInput) amountInput.value = parsed.amount.toFixed(2);
        if (descInput) descInput.value = parsed.merchant;
        if (flowSelect) {
            flowSelect.value = parsed.type;
            if (typeof updateGlobalQuickTxCategory === 'function') {
                updateGlobalQuickTxCategory();
            }
        }
        if (catSelect) {
            // Select category if available in options, or fallback
            for (let opt of catSelect.options) {
                if (opt.value.toLowerCase() === parsed.category.toLowerCase()) {
                    catSelect.value = opt.value;
                    break;
                }
            }
        }

        if (window.ECuzdanHaptics) window.ECuzdanHaptics.success();
        if (window.showToast) {
            window.showToast(
                `Banka SMS'i dolduruldu: ${parsed.merchant} · ${parsed.amount.toFixed(2)} ₺ (${parsed.category})`,
                'success'
            );
        }
    };

    // --- Global Exposed Action 2: Sesle Söyle (Speech-to-Expense) ---
    let speechRecognition = null;
    let isListening = false;

    window.toggleVoiceTxInput = function () {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRec) {
            if (window.showToast) {
                window.showToast('Tarayıcınız sesle yazmayı desteklemiyor (iOS 14.5+ Safari veya Chrome kullanın).', 'warning');
            }
            return;
        }

        const micBtn = document.getElementById('btnVoiceTxMic');
        const micLabel = document.getElementById('voiceMicLabel');

        if (isListening && speechRecognition) {
            speechRecognition.stop();
            return;
        }

        try {
            speechRecognition = new SpeechRec();
            speechRecognition.lang = 'tr-TR';
            speechRecognition.continuous = false;
            speechRecognition.interimResults = false;

            speechRecognition.onstart = function () {
                isListening = true;
                if (window.ECuzdanHaptics) window.ECuzdanHaptics.medium();
                if (micBtn) micBtn.classList.add('animate-pulse', 'text-rose-600', 'font-black');
                if (micLabel) micLabel.textContent = 'Dinliyor... 🔴';
            };

            speechRecognition.onresult = function (event) {
                const transcript = event.results[0][0].transcript;
                console.log('[VoiceInput] Transcript:', transcript);

                // Parse speech
                const lower = transcript.toLowerCase();
                const amount = parseTurkishSpokenNumber(lower);

                let detectedCategory = 'Diğer';
                let detectedType = 'Gider';
                for (const [cat, words] of Object.entries(CATEGORY_KEYWORDS)) {
                    if (words.some(w => lower.includes(w))) {
                        detectedCategory = cat;
                        if (cat === 'Maaş') detectedType = 'Gelir';
                        break;
                    }
                }

                // Clean description
                let cleanDesc = transcript
                    .replace(/\b\d+(?:[.,]\d+)?\b/g, '')
                    .replace(/\b(?:lira|tl|türk lirası|harcadım|harcama|verdim|yattı|aldım)\b/gi, '')
                    .trim();
                if (!cleanDesc) cleanDesc = detectedCategory + ' Harcaması';

                // Populate form
                const amountInput = document.getElementById('globalQuickTxAmount');
                const descInput = document.getElementById('globalQuickTxDesc') || document.querySelector('#globalQuickTxForm input[name="description"]');
                const flowSelect = document.getElementById('globalQuickTxFlowType');
                const catSelect = document.getElementById('globalQuickTxCategory');

                if (amount && amountInput) amountInput.value = amount.toFixed(2);
                if (descInput) descInput.value = cleanDesc;
                if (flowSelect) {
                    flowSelect.value = detectedType;
                    if (typeof updateGlobalQuickTxCategory === 'function') {
                        updateGlobalQuickTxCategory();
                    }
                }
                if (catSelect) {
                    for (let opt of catSelect.options) {
                        if (opt.value.toLowerCase() === detectedCategory.toLowerCase()) {
                            catSelect.value = opt.value;
                            break;
                        }
                    }
                }

                if (window.ECuzdanHaptics) window.ECuzdanHaptics.success();
                if (window.showToast) {
                    window.showToast(`Ses algılandı: "${transcript}"`, 'success');
                }
            };

            speechRecognition.onerror = function (e) {
                console.warn('[VoiceInput] Error:', e.error);
                if (window.ECuzdanHaptics) window.ECuzdanHaptics.error();
                if (window.showToast && e.error !== 'no-speech') {
                    window.showToast('Ses algılanamadı, lütfen tekrar deneyin.', 'info');
                }
            };

            speechRecognition.onend = function () {
                isListening = false;
                if (micBtn) micBtn.classList.remove('animate-pulse', 'text-rose-600', 'font-black');
                if (micLabel) micLabel.textContent = 'Sesle Söyle';
            };

            speechRecognition.start();
        } catch (err) {
            console.error('[VoiceInput] Speech error:', err);
        }
    };
})();
