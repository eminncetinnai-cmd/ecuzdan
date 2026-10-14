/* E-Cüzdan v15 — Gizlilik Modu istemci katmanı

 *
  * Jinja `format_money` filtresi tutarları <span class="amount"> ile sarar,
 * ancak tutarların bir kısmı sunucu tarafında f-string içinde üretilip
 * hazır metin olarak geliyor (ör. engines/financial_engine.py'deki kriter
 * açıklamaları). Bu dosya o tutarları metin dönüşümü taramasıyla işaretler.

 */
(function () {
    'use strict';

    // 1.234,56 ₺ / ₺1.234,56 / 1.234,56 TL — en az bir ondalık ya da binlik ayraç ister.
    // Yıl (2026), yüzde (%45) ve sade tam sayılar kapsam dışı kalsın diye
    // para birimi işareti zorunlu tutulur.
    var MONEY = /(?:[₺$€£]\s?\d[\d.]*(?:,\d+)?)|(?:\d[\d.]*(?:,\d+)?\s?(?:₺|TL\b|USD\b|EUR\b|GBP\b))/g;

    var SKIP_TAGS = { SCRIPT: 1, STYLE: 1, TEXTAREA: 1, INPUT: 1, SELECT: 1, OPTION: 1 };

    function markTextNodes(root) {
        var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
            acceptNode: function (node) {
                var parent = node.parentElement;
                if (!parent || SKIP_TAGS[parent.tagName]) return NodeFilter.FILTER_REJECT;
                // Zaten işaretlenmişse tekrar sarma

                if (parent.classList && parent.classList.contains('amount')) return NodeFilter.FILTER_REJECT;
                if (!node.nodeValue || !MONEY.test(node.nodeValue)) return NodeFilter.FILTER_REJECT;
                MONEY.lastIndex = 0;
                return NodeFilter.FILTER_ACCEPT;
            }
        });

        var targets = [];
        var current;
        while ((current = walker.nextNode())) targets.push(current);

        targets.forEach(function (node) {
            var frag = document.createDocumentFragment();
            var text = node.nodeValue;
            var last = 0;
            var match;
            MONEY.lastIndex = 0;
            while ((match = MONEY.exec(text)) !== null) {
                if (match.index > last) frag.appendChild(document.createTextNode(text.slice(last, match.index)));
                // Not: tabindex verilmiyor — sayfa başına 25+ tutar olduğu için
                // her biri tab durağı olsaydı klavye gezinmesi kullanılamaz hale
                // gelirdi. Klavye kullanıcısı üst bardaki düğmeyle tümünü açar.

                var span = document.createElement('span');
                span.className = 'amount';
                span.textContent = match[0];
                frag.appendChild(span);
                last = match.index + match[0].length;
            }
            if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
            node.parentNode.replaceChild(frag, node);
        });

        return targets.length;
    }

    function apply() {
        markTextNodes(document.body);
    }

    window.privacyMode = {
        /** Sunucuya yazar ve <html> sınıfını günceller. */

        toggle: function () {
            // CSRF koruması token'ı yalnızca FORM alanından okuyor (routes/__init__.py),
            // header'dan değil; bu yüzden form-encoded gönderilir.

            var meta = document.querySelector('meta[name="csrf-token"]');
            var body = new URLSearchParams();
            body.append('csrf_token', meta ? meta.content : '');
            return fetch(ECuzdanEndpoints.settings.privacy, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: body
            })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data && data.success) {
                        document.documentElement.classList.toggle('privacy', data.privacy_mode);
                        // Persist privacy mode to localStorage
                        localStorage.setItem('privacyMode', data.privacy_mode);
                        if (data.privacy_mode) apply();
                    } else if (window.showToast) {
                        window.showToast((data && data.message) || 'Gizlilik modu değiştirilemedi.', 'error');
                    }
                    return data;
                })
                .catch(function () {
                    if (window.showToast) window.showToast('Gizlilik modu değiştirilemedi.', 'error');
                });
        },
        mark: apply
    };

    // Sayfa a├ğ─▒l─▒┼ş─▒nda localStorage'dan gizlilik modunu kontrol et
    var savedPrivacyMode = localStorage.getItem('privacyMode');
    if (savedPrivacyMode === 'true') {
        document.documentElement.classList.add('privacy');
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', apply);
        } else {
            apply();
        }
    } else if (document.documentElement.classList.contains('privacy')) {
        // Sunucu taraf─▒nda gizlilik modu a├ğ─▒ksa
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', apply);
        } else {
            apply();
        }
    }
})();
