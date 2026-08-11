/**
 * Tarih alanları: gg/aa/yyyy manuel giriş + takvim, geçersiz tarih reddi.
 */
(function () {
    const DATE_PATTERN = /^(\d{2})\/(\d{2})\/(\d{4})$/;

    function isValidDateParts(day, month, year) {
        if (year < 1990 || year > 2100) return false;
        if (month < 1 || month > 12) return false;
        if (day < 1 || day > 31) return false;
        const d = new Date(year, month - 1, day);
        return d.getFullYear() === year && d.getMonth() === month - 1 && d.getDate() === day;
    }

    window.validateDateTr = function (value) {
        if (!value || !String(value).trim()) return false;
        const m = String(value).trim().match(DATE_PATTERN);
        if (!m) return false;
        return isValidDateParts(parseInt(m[1], 10), parseInt(m[2], 10), parseInt(m[3], 10));
    };

    function setInvalid(input, invalid) {
        input.classList.toggle('ring-2', invalid);
        input.classList.toggle('ring-rose-500', invalid);
        input.classList.toggle('border-rose-500', invalid);
        input.setCustomValidity(invalid ? 'Geçerli bir tarih girin (gg/aa/yyyy).' : '');
    }

    function maskWhileTyping(el) {
        const digits = el.value.replace(/\D/g, '').slice(0, 8);
        if (digits.length <= 2) el.value = digits;
        else if (digits.length <= 4) el.value = digits.slice(0, 2) + '/' + digits.slice(2);
        else el.value = digits.slice(0, 2) + '/' + digits.slice(2, 4) + '/' + digits.slice(4);
    }

    function initDateField(input) {
        if (input.dataset.dateInited) return;
        input.dataset.dateInited = '1';

        input.addEventListener('input', function () {
            if (!input._flatpickr) maskWhileTyping(input);
            if (input.classList.contains('ring-rose-500')) setInvalid(input, false);
        });

        if (typeof flatpickr === 'undefined') {
            input.addEventListener('blur', function () {
                const v = input.value.trim();
                if (!v) { setInvalid(input, input.required); return; }
                setInvalid(input, !validateDateTr(v));
            });
            return;
        }

        flatpickr(input, {
            locale: flatpickr.l10ns.tr,
            dateFormat: 'd/m/Y',
            allowInput: true,
            disableMobile: false,
            clickOpens: true,
            monthSelectorType: 'dropdown',
            prevArrow: '‹',
            nextArrow: '›',
            onReady: function (_, __, inst) {
                const wrap = input.closest('.date-field-wrap');
                const btn = wrap && wrap.querySelector('.date-picker-btn');
                if (btn) {
                    btn.addEventListener('click', function (e) {
                        e.preventDefault();
                        inst.open();
                    });
                }
            },
            onChange: function () {
                setInvalid(input, false);
            },
            onClose: function (selectedDates, dateStr) {
                if (!dateStr.trim()) {
                    setInvalid(input, input.required);
                    return;
                }
                const ok = selectedDates.length > 0 || validateDateTr(dateStr);
                setInvalid(input, !ok);
                if (!ok && selectedDates.length === 0) {
                    input.value = dateStr;
                }
            }
        });

        input.addEventListener('blur', function () {
            const v = input.value.trim();
            if (!v) {
                setInvalid(input, input.required);
                return;
            }
            setInvalid(input, !validateDateTr(v));
        });
    }

    function initAll() {
        document.querySelectorAll('.date-tr').forEach(initDateField);
    }

    document.addEventListener('submit', function (e) {
        const form = e.target;
        if (!form || form.tagName !== 'FORM') return;
        let firstInvalid = null;
        form.querySelectorAll('.date-tr').forEach(function (input) {
            const v = input.value.trim();
            if (input.required && !v) {
                setInvalid(input, true);
                if (!firstInvalid) firstInvalid = input;
                return;
            }
            if (v && !validateDateTr(v)) {
                setInvalid(input, true);
                if (!firstInvalid) firstInvalid = input;
            }
        });
        if (firstInvalid) {
            e.preventDefault();
            e.stopImmediatePropagation();
            firstInvalid.reportValidity();
            firstInvalid.focus();
        }
    }, true);

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
    } else {
        initAll();
    }
})();
