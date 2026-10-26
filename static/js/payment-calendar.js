/**
 * Ödeme takvimi — aylık grid, gün hover detayı.
 */
(function () {
    const MONTH_NAMES = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
    const WEEKDAYS = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'];

    let state = {
        year: parseInt(document.getElementById('cal-root')?.dataset.year, 10),
        month: parseInt(document.getElementById('cal-root')?.dataset.month, 10),
        today: document.getElementById('cal-root')?.dataset.today || '',
        days: {},
        hideReminders: (function () {
            try { return localStorage.getItem('cal_hide_reminders') === '1'; } catch (e) { return false; }
        })(),
    };

    const popover = document.getElementById('cal-popover');
    const gridEl = document.getElementById('cal-grid');
    const titleEl = document.getElementById('cal-month-title');
    const monthCache = new Map();
    let hideTimer = null;

    function formatMoney(n) {
        var val = n;
        if (typeof n === 'string') {
            // Server returns precise stringified decimals for monetary values; parse safely
            val = parseFloat(n);
            if (isNaN(val)) val = 0;
        }
        return new Intl.NumberFormat('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val || 0);
    }

    function pad2(n) {
        return String(n).padStart(2, '0');
    }

    function dateKey(year, month, day) {
        return year + '-' + pad2(month) + '-' + pad2(day);
    }

    function escapeHtml(s) {
        const d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }

    function renderTxList(items, colorClass) {
        if (!items || !items.length) {
            return '<p class="text-[10px] text-slate-400 italic py-1">Kayıt yok</p>';
        }
        return items.map(function (t) {
            const status = t.status === 'Ödendi'
                ? '<span class="text-emerald-600">Ödendi</span>'
                : '<span class="text-amber-600">Bekliyor</span>';
            const note = t.note ? '<span class="text-slate-400"> · ' + escapeHtml(t.note) + '</span>' : '';
            return (
                '<li class="py-2 border-b border-slate-100 last:border-0">' +
                '<div class="flex justify-between gap-2">' +
                '<span class="font-bold text-slate-800">' + escapeHtml(t.description || t.category) + '</span>' +
                '<span class="font-black whitespace-nowrap ' + colorClass + '">' + escapeHtml(t.amount_fmt) + '</span>' +
                '</div>' +
                '<div class="text-[9px] text-slate-500 mt-0.5">' + escapeHtml(t.category) + ' · ' + status + ' · ' + escapeHtml(t.origin) + note + '</div>' +
                '</li>'
            );
        }).join('');
    }

    function renderReminderList(items) {
        if (!items || !items.length) return '';
        return items.map(function (r) {
            const amt = r.amount ? '<span class="font-bold text-slate-700 dark:text-slate-300 ml-1">' + formatMoney(r.amount) + ' ₺</span>' : '';
            const status = r.is_completed ? '<span class="text-emerald-600 font-bold ml-1">✓ Tamamlandı</span>' : '';
            const note = r.note ? '<div class="text-[9px] text-slate-500 italic mt-0.5">' + escapeHtml(r.note) + '</div>' : '';
            return (
                '<li class="py-1.5 border-b border-indigo-100/60 dark:border-slate-800 last:border-0">' +
                '<div class="flex items-center justify-between gap-1">' +
                '<div class="flex items-center gap-1.5 font-bold text-slate-800 dark:text-slate-200">' +
                '<span>' + (r.category_emoji || '🔔') + '</span>' +
                '<span>' + escapeHtml(r.title) + '</span>' +
                '</div>' +
                '<div class="text-[10px]">' + amt + status + '</div>' +
                '</div>' +
                '<div class="text-[9px] text-indigo-600 dark:text-indigo-400 font-semibold">' + escapeHtml(r.frequency) + ' · ' + escapeHtml(r.category) + '</div>' +
                note +
                '</li>'
            );
        }).join('');
    }

    function showPopover(cell, isoDate) {
        if (!popover) return;
        const data = state.days[isoDate];
        const parts = isoDate.split('-');
        const dayNum = parseInt(parts[2], 10);
        const monthName = MONTH_NAMES[parseInt(parts[1], 10) - 1];

        let html = '<div class="p-4 min-w-[280px] max-w-[340px]">';
        html += '<div class="flex justify-between items-start border-b border-slate-200 pb-3 mb-3">';
        html += '<div><p class="text-[10px] font-bold text-slate-400 uppercase">' + dayNum + ' ' + monthName + ' ' + parts[0] + '</p>';
        if (data) {
            const netClass = data.net >= 0 ? 'text-emerald-600' : 'text-rose-600';
            html += '<p class="text-xs font-black ' + netClass + ' mt-1">Net: ' + formatMoney(data.net) + '</p>';
        } else {
            html += '<p class="text-xs text-slate-400 mt-1">Bu günde kayıt yok</p>';
        }
        html += '</div><button type="button" class="cal-popover-close text-slate-400 hover:text-slate-700 text-lg leading-none" aria-label="Kapat">&times;</button></div>';

        if (data) {
            html += '<div class="space-y-3 max-h-[320px] overflow-y-auto pr-1">';
            if (data.has_cash_gap) {
                html += '<div class="p-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/50 flex items-start gap-2 mb-2">' +
                    '<span class="text-rose-600 dark:text-rose-400 text-sm">⚠️</span>' +
                    '<div class="text-[10px] leading-tight">' +
                    '<p class="font-black text-rose-700 dark:text-rose-300 uppercase tracking-tight">Nakit Boşluğu Riski</p>' +
                    '<p class="text-rose-600 dark:text-rose-400 mt-0.5">Ödemeler sonrası tahmini kasa açığı: <strong>-' + formatMoney(data.cash_gap_amount) + '</strong></p>' +
                    '</div>' +
                    '</div>';
            }
            html += '<div><h4 class="text-[9px] font-black uppercase text-emerald-600 mb-1 flex justify-between"><span>Gelirler</span><span>' + formatMoney(data.income_total) + '</span></h4><ul class="text-[11px]">' + renderTxList(data.income, 'text-emerald-600') + '</ul></div>';
            html += '<div><h4 class="text-[9px] font-black uppercase text-rose-600 mb-1 flex justify-between"><span>Giderler</span><span>' + formatMoney(data.expense_total) + '</span></h4><ul class="text-[11px]">' + renderTxList(data.expense, 'text-rose-600') + '</ul></div>';
            if (data.investment && data.investment.length) {
                html += '<div><h4 class="text-[9px] font-black uppercase text-blue-600 mb-1 flex justify-between"><span>Yatırım</span><span>' + formatMoney(data.investment_total) + '</span></h4><ul class="text-[11px]">' + renderTxList(data.investment, 'text-blue-600') + '</ul></div>';
            }
            if (data.reminders && data.reminders.length && !state.hideReminders) {
                html += '<div class="pt-2.5 mt-2 border-t border-indigo-100 dark:border-slate-800">' +
                    '<h4 class="text-[9px] font-black uppercase text-indigo-700 dark:text-indigo-400 mb-1 flex justify-between items-center">' +
                    '<span class="flex items-center gap-1"><span>🔔</span> <span>Özel Gün & Hatırlatıcılar</span></span>' +
                    '<span class="px-1.5 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 text-[8px] font-bold">' + data.reminders.length + '</span>' +
                    '</h4>' +
                    '<ul class="text-[11px] space-y-1">' + renderReminderList(data.reminders) + '</ul>' +
                    '</div>';
            }
            html += '<div class="pt-2 border-t border-slate-100 flex justify-end">';
            html += '<a href="/transactions?date=' + encodeURIComponent(isoDate) + '" class="text-[10px] font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"><span>Günün İşlemlerini Gör</span><span>→</span></a>';
            html += '</div>';
            html += '</div>';
        }
        html += '</div>';

        popover.innerHTML = html;
        popover.classList.remove('hidden');
        popover.querySelector('.cal-popover-close')?.addEventListener('click', hidePopover);

        const rect = cell.getBoundingClientRect();
        const popW = 320;
        let left = rect.left + rect.width / 2 - popW / 2;
        let top = rect.bottom + 8;
        if (left < 12) left = 12;
        if (left + popW > window.innerWidth - 12) left = window.innerWidth - popW - 12;
        if (top + 360 > window.innerHeight - 12) top = rect.top - 8 - 280;
        if (top < 12) top = 12;
        popover.style.left = left + 'px';
        popover.style.top = top + 'px';
    }

    function hidePopover() {
        if (popover) popover.classList.add('hidden');
    }

    function scheduleHide() {
        clearTimeout(hideTimer);
        hideTimer = setTimeout(hidePopover, 200);
    }

    function cancelHide() {
        clearTimeout(hideTimer);
    }

    function buildGrid() {
        if (!gridEl) return;
        const first = new Date(state.year, state.month - 1, 1);
        const lastDay = new Date(state.year, state.month, 0).getDate();
        let startWd = first.getDay() - 1;
        if (startWd < 0) startWd = 6;

        let html = '';
        WEEKDAYS.forEach(function (wd) {
            html += '<div class="cal-wd text-[9px] font-black text-slate-400 uppercase text-center py-2">' + wd + '</div>';
        });

        for (let i = 0; i < startWd; i++) {
            html += '<div class="cal-day cal-day--empty"></div>';
        }

        for (let d = 1; d <= lastDay; d++) {
            const iso = dateKey(state.year, state.month, d);
            const data = state.days[iso];
            const isToday = iso === state.today;
            const hasIncome = data && data.income && data.income.length > 0;
            const hasExpense = data && data.expense && data.expense.length > 0;
            const hasInv = data && data.investment && data.investment.length > 0;
            const hasReminders = data && data.reminders && data.reminders.length > 0;
            const hasCashGap = data && data.has_cash_gap;
            let cls = 'cal-day';
            if (isToday) cls += ' cal-day--today';
            if (data && (hasIncome || hasExpense || hasInv || hasReminders)) cls += ' cal-day--has-data';
            if (hasCashGap) cls += ' cal-day--cash-gap';

            let badges = '';
            if (hasIncome) badges += '<span class="cal-dot cal-dot--income" title="Gelir"></span>';
            if (hasExpense) badges += '<span class="cal-dot cal-dot--expense" title="Gider"></span>';
            if (hasInv) badges += '<span class="cal-dot cal-dot--inv" title="Yatırım"></span>';

            let reminderBadge = '';
            if (hasReminders) {
                const rem = data.reminders[0];
                const remCount = data.reminders.length > 1 ? ' <span class="text-[8px] font-bold">+' + (data.reminders.length - 1) + '</span>' : '';
                const hideCls = state.hideReminders ? 'hidden' : '';
                reminderBadge = '<span class="cal-reminder-badge ' + hideCls + '" title="' + escapeHtml(rem.title) + '">' + (rem.category_emoji || '🔔') + remCount + '</span>';
            }

            let mini = '';
            if (data && (hasIncome || hasExpense)) {
                mini = '<div class="cal-mini">';
                if (hasIncome) mini += '<span class="text-emerald-600">+' + formatMoney(data.income_total) + '</span>';
                if (hasExpense) mini += '<span class="text-rose-600">-' + formatMoney(data.expense_total) + '</span>';
                mini += '</div>';
            }

            html += '<div class="' + cls + '" data-date="' + iso + '" tabindex="0">' +
                '<div class="flex justify-between items-start">' +
                '<span class="cal-day-num">' + d + '</span>' +
                reminderBadge +
                '</div>' +
                '<div class="cal-dots">' + badges + '</div>' + mini + '</div>';
        }

        gridEl.innerHTML = html;

        gridEl.querySelectorAll('.cal-day[data-date]').forEach(function (cell) {
            cell.addEventListener('mouseenter', function () {
                cancelHide();
                showPopover(cell, cell.dataset.date);
            });
            cell.addEventListener('mouseleave', scheduleHide);
            cell.addEventListener('focus', function () {
                cancelHide();
                showPopover(cell, cell.dataset.date);
            });
            cell.addEventListener('blur', scheduleHide);
        });
    }

    function updateTitle() {
        if (titleEl) {
            titleEl.textContent = MONTH_NAMES[state.month - 1] + ' ' + state.year;
        }
    }

    function loadMonth(year, month) {
        const cacheKey = year + '-' + month;
        if (monthCache.has(cacheKey)) {
            const data = monthCache.get(cacheKey);
            state.year = data.year;
            state.month = data.month;
            state.today = data.today || state.today;
            state.days = data.days || {};
            updateTitle();
            buildGrid();
            return Promise.resolve(data);
        }

        const loading = document.getElementById('cal-loading');
        if (loading) loading.classList.remove('hidden');
        return fetch(ECuzdanEndpoints.plans.paymentCalendarMonthData + '?year=' + year + '&month=' + month)
            .then(function (r) { 
                if (!r.ok) {
                    console.error('API error:', r.status, r.statusText);
                    throw new Error('API request failed');
                }
                return r.json(); 
            })
            .then(function (data) {
                if (data.error) throw new Error(data.error);
                monthCache.set(cacheKey, data);
                state.year = data.year;
                state.month = data.month;
                state.today = data.today || state.today;
                state.days = data.days || {};
                updateTitle();
                buildGrid();
                return data;
            })
            .catch(function (error) {
                console.error('Error loading calendar data:', error);
            })
            .finally(function () {
                if (loading) loading.classList.add('hidden');
            });
    }

    function shiftMonth(delta) {
        let m = state.month + delta;
        let y = state.year;
        if (m > 12) { m = 1; y++; }
        if (m < 1) { m = 12; y--; }
        loadMonth(y, m);
    }

    function activateTab(tab, updateUrl = true) {
        if (!tab) return;
        document.querySelectorAll('.pay-tab-btn').forEach(function (b) {
            b.classList.toggle('active', b.dataset.tab === tab);
            b.setAttribute('aria-selected', String(b.dataset.tab === tab));
        });
        document.querySelectorAll('.pay-tab-panel').forEach(function (p) {
            p.classList.toggle('active', p.id === 'pay-tab-' + tab);
        });
        if (tab === 'calendar' && gridEl && !gridEl.dataset.loaded) {
            gridEl.dataset.loaded = '1';
            loadMonth(state.year, state.month);
        }
        if (tab === 'balance') {
            initBalanceTab();
        }
        if (updateUrl) {
            try {
                history.replaceState(null, '', '#' + tab);
            } catch (e) {}
        }
    }

    function initTabs() {
        document.querySelectorAll('.pay-tab-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                activateTab(btn.dataset.tab, true);
            });
        });

        // URL hash or query param support (?tab=calendar or #calendar)
        const urlParams = new URLSearchParams(window.location.search);
        const queryTab = urlParams.get('tab');
        const hashTab = (window.location.hash || '').replace('#', '');
        const targetTab = queryTab || hashTab;

        if (targetTab && ['list', 'calendar', 'balance'].includes(targetTab)) {
            activateTab(targetTab, false);
        }
    }

    // Balance Chart Functions
    let balanceChart = null;
    let balanceYear = new Date().getFullYear();
    let balanceMonth = new Date().getMonth() + 1;

    function initBalanceTab() {
        const periodEl = document.getElementById('balance-period');
        const prevBtn = document.getElementById('balance-prev');
        const nextBtn = document.getElementById('balance-next');
        
        if (!periodEl || !prevBtn || !nextBtn) return;

        // Set initial period to current month
        updatePeriodDisplay();
        loadBalanceData(balanceYear, balanceMonth);

        // Add navigation listeners
        prevBtn.addEventListener('click', function () {
            shiftBalanceMonth(-1);
        });
        nextBtn.addEventListener('click', function () {
            shiftBalanceMonth(1);
        });
    }

    function updatePeriodDisplay() {
        const periodEl = document.getElementById('balance-period');
        if (periodEl) {
            periodEl.textContent = MONTH_NAMES[balanceMonth - 1] + ' ' + balanceYear;
        }
    }

    function shiftBalanceMonth(delta) {
        let m = balanceMonth + delta;
        let y = balanceYear;
        if (m > 12) { m = 1; y++; }
        if (m < 1) { m = 12; y--; }
        
        // Check if going to past month
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1;
        
        if (y < currentYear || (y === currentYear && m < currentMonth)) {
            return; // Don't allow going to past months
        }
        
        balanceYear = y;
        balanceMonth = m;
        updatePeriodDisplay();
        loadBalanceData(balanceYear, balanceMonth);
    }

    function loadBalanceData(year, month) {
        const loading = document.getElementById('balance-loading');
        if (loading) loading.classList.remove('hidden');

        return fetch(ECuzdanEndpoints.plans.paymentCalendarDailyBalance + '?year=' + year + '&month=' + month)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.error) throw new Error(data.error);
                renderBalanceChart(data.labels, data.data);
            })
            .catch(function (err) {
                console.error('Balance data error:', err);
            })
            .finally(function () {
                if (loading) loading.classList.add('hidden');
            });
    }

    function renderBalanceChart(labels, data) {
        const ctx = document.getElementById('balanceChart');
        if (!ctx) return;

        if (typeof Chart === 'undefined') {
            let retryCount = 0;
            const retryInterval = setInterval(() => {
                retryCount++;
                if (typeof Chart !== 'undefined') {
                    clearInterval(retryInterval);
                    renderBalanceChart(labels, data);
                } else if (retryCount >= 50) {
                    clearInterval(retryInterval);
                    console.warn('[PaymentCalendar] Chart.js is not loaded');
                }
            }, 100);
            return;
        }

        // Destroy existing chart
        if (balanceChart) {
            balanceChart.destroy();
        }

        // Calculate colors based on values
        const colors = data.map(function (val) {
            return val >= 0 ? '#10b981' : '#f43f5e';
        });

        const hasPositive = data.some(function (v) { return v > 0; });
        const hasNegative = data.some(function (v) { return v < 0; });
        const maxVal = Math.max(...data);
        const minVal = Math.min(...data);

        balanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Kasa Bakiyesi',
                    data: data,
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointBackgroundColor: colors,
                    pointBorderColor: colors,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.92)',
                        titleFont: { size: 11, weight: 'bold' },
                        bodyFont: { size: 12 },
                        padding: 12,
                        callbacks: {
                            label: function (ctx) {
                                const v = ctx.parsed.y;
                                const tone = v < 0 ? ' (negatif)' : ' (pozitif)';
                                return 'Bakiye: ' + formatMoney(v) + tone;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            font: { size: 9, weight: '600' },
                            color: '#64748b',
                            maxRotation: 45,
                            autoSkip: true,
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        suggestedMin: hasNegative ? minVal * 1.08 : Math.min(0, minVal),
                        suggestedMax: hasPositive ? maxVal * 1.08 : Math.max(0, maxVal),
                        grid: {
                            color: function (ctx) {
                                if (ctx.tick.value === 0) return '#94a3b8';
                                return '#e2e8f0';
                            },
                            lineWidth: function (ctx) {
                                return ctx.tick.value === 0 ? 1.5 : 1;
                            }
                        },
                        ticks: {
                            font: { size: 9, weight: '600' },
                            color: '#64748b',
                            callback: function (value) { return formatMoney(value); }
                        }
                    }
                }
            }
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        const root = document.getElementById('cal-root');
        if (!root) return;

        // Pre-seed calendar from SSR initial data if available for zero-wait rendering
        const initScript = document.getElementById('cal-initial-data');
        if (initScript && initScript.textContent.trim()) {
            try {
                const initData = JSON.parse(initScript.textContent);
                if (initData && initData.year && initData.month && initData.days) {
                    const cacheKey = initData.year + '-' + initData.month;
                    monthCache.set(cacheKey, initData);
                    state.year = initData.year;
                    state.month = initData.month;
                    state.today = initData.today || state.today;
                    state.days = initData.days;
                    updateTitle();
                    buildGrid();
                    if (gridEl) gridEl.dataset.loaded = '1';
                }
            } catch (err) {
                console.warn('Could not parse pre-seeded calendar initial data:', err);
            }
        }

        initTabs();

        document.getElementById('cal-prev')?.addEventListener('click', function () { shiftMonth(-1); });
        document.getElementById('cal-next')?.addEventListener('click', function () { shiftMonth(1); });
        document.getElementById('cal-today')?.addEventListener('click', function () {
            const t = state.today.split('-');
            loadMonth(parseInt(t[0], 10), parseInt(t[1], 10));
        });

        if (popover) {
            popover.addEventListener('mouseenter', cancelHide);
            popover.addEventListener('mouseleave', hidePopover);
        }

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                hidePopover();
                return;
            }

            // Keyboard navigation when on calendar tab
            const activePanel = document.querySelector('.pay-tab-panel.active');
            if (activePanel && activePanel.id === 'pay-tab-calendar') {
                const isInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName);
                if (!isInput && !e.ctrlKey && !e.metaKey && !e.altKey) {
                    if (e.key === 'ArrowLeft' || e.key === '[') {
                        e.preventDefault();
                        shiftMonth(-1);
                    } else if (e.key === 'ArrowRight' || e.key === ']') {
                        e.preventDefault();
                        shiftMonth(1);
                    } else if (e.key.toLowerCase() === 't') {
                        e.preventDefault();
                        const t = state.today.split('-');
                        loadMonth(parseInt(t[0], 10), parseInt(t[1], 10));
                    }
                }
            }
        });
    });

    window.toggleCalendarReminders = function () {
        state.hideReminders = !state.hideReminders;
        try { localStorage.setItem('cal_hide_reminders', state.hideReminders ? '1' : '0'); } catch (e) { }
        const icon = document.getElementById('toggleReminderIcon');
        const text = document.getElementById('toggleReminderText');
        if (state.hideReminders) {
            if (icon) icon.textContent = '🙈';
            if (text) text.textContent = 'Hatırlatıcıları Göster';
            document.querySelectorAll('.cal-reminder-badge').forEach(function (el) {
                el.classList.add('hidden');
            });
        } else {
            if (icon) icon.textContent = '👁️';
            if (text) text.textContent = 'Hatırlatıcıları Gizle';
            document.querySelectorAll('.cal-reminder-badge').forEach(function (el) {
                el.classList.remove('hidden');
            });
        }
        if (window.ECuzdanHaptics) window.ECuzdanHaptics.light();
    };

    if (state.hideReminders) {
        const icon = document.getElementById('toggleReminderIcon');
        const text = document.getElementById('toggleReminderText');
        if (icon) icon.textContent = '🙈';
        if (text) text.textContent = 'Hatırlatıcıları Göster';
    }

    window.showCalendarSubscribeModal = function () {
        if (typeof window.openModal === 'function') {
            window.openModal('calendarSubscribeModal');
        } else {
            const m = document.getElementById('calendarSubscribeModal');
            if (m) {
                m.classList.remove('hidden');
                m.classList.add('active');
                m.style.display = 'flex';
            }
        }
        if (window.ECuzdanHaptics) window.ECuzdanHaptics.light();
    };

    window.hideCalendarSubscribeModal = function () {
        if (typeof window.closeModal === 'function') {
            window.closeModal('calendarSubscribeModal');
        } else {
            const m = document.getElementById('calendarSubscribeModal');
            if (m) {
                m.classList.add('hidden');
                m.classList.remove('active');
                m.style.display = 'none';
            }
        }
    };

    window.copyCalendarSubscribeUrl = function () {
        const inp = document.getElementById('calFeedUrlInput');
        if (!inp) return;
        const val = inp.value;
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(val).then(function () {
                if (typeof showToast === 'function') {
                    showToast('Takvim bağlantısı panoya kopyalandı!', 'success');
                } else {
                    alert('Takvim bağlantısı kopyalandı.');
                }
                if (window.ECuzdanHaptics) window.ECuzdanHaptics.success();
            }).catch(function () {
                inp.select();
                document.execCommand('copy');
            });
        } else {
            inp.select();
            document.execCommand('copy');
            if (typeof showToast === 'function') {
                showToast('Takvim bağlantısı panoya kopyalandı!', 'success');
            }
        }
    };

    window.quickPayFromCalendar = function (txId, buttonEl) {
        if (!txId) return;

        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
            || window.CSRF_TOKEN
            || (document.querySelector('input[name="csrf_token"]') ? document.querySelector('input[name="csrf_token"]').value : '');

        const originalHtml = buttonEl ? buttonEl.innerHTML : '';
        if (buttonEl) {
            buttonEl.disabled = true;
            buttonEl.innerHTML = '<span class="inline-block animate-spin" aria-hidden="true">⏳</span> <span>İşleniyor...</span>';
        }

        fetch(`/transactions/${txId}/quick-pay`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ id: txId })
        })
        .then(function (res) {
            if (!res.ok) {
                return res.json().then(function (data) {
                    throw new Error(data.message || 'Ödeme işlemi tamamlanamadı.');
                });
            }
            return res.json();
        })
        .then(function (data) {
            if (!data.success) {
                throw new Error(data.message || 'Ödeme işlemi başarısız.');
            }

            const paidAmount = parseFloat(buttonEl?.getAttribute('data-amount') || data.data?.amount || '0');

            // Find all matching rows in week_p and month_p
            const matchingRows = document.querySelectorAll(`tr[data-tx-id="${txId}"]`);
            matchingRows.forEach(function (row) {
                row.classList.add('cal-tx-row--paid');
                const btn = row.querySelector('.btn-cal-quick-pay');
                if (btn) {
                    btn.classList.add('is-paid');
                    btn.disabled = true;
                    btn.innerHTML = '<span class="text-emerald-500 font-black" aria-hidden="true">✓</span> <span class="text-emerald-600 dark:text-emerald-400 font-bold">Ödendi</span>';
                    btn.title = 'Ödeme yapıldı';
                }
            });

            // Adjust Live KPI values on client side
            const sym = window.BASE_CURRENCY_SYMBOL || '₺';

            // 1. Today cash: cash decreases by amount if expense
            const todayCashEl = document.getElementById('cal-kpi-today-cash');
            if (todayCashEl && !isNaN(paidAmount)) {
                const currentCash = parseFloat(todayCashEl.getAttribute('data-raw-val') || '0');
                const newCash = currentCash - paidAmount;
                todayCashEl.setAttribute('data-raw-val', newCash.toFixed(2));
                todayCashEl.textContent = formatMoney(newCash) + ' ' + sym;
                if (newCash < 0) {
                    todayCashEl.classList.remove('text-emerald-600', 'dark:text-emerald-400');
                    todayCashEl.classList.add('text-rose-600', 'dark:text-rose-400');
                }
            }

            // 2. Week total
            const weekTotalEl = document.getElementById('cal-kpi-week-total');
            if (weekTotalEl && !isNaN(paidAmount)) {
                const curWeek = parseFloat(weekTotalEl.getAttribute('data-raw-val') || '0');
                const newWeek = Math.max(0, curWeek - paidAmount);
                weekTotalEl.setAttribute('data-raw-val', newWeek.toFixed(2));
                weekTotalEl.textContent = formatMoney(newWeek) + ' ' + sym;
            }

            // 3. Month total
            const monthTotalEl = document.getElementById('cal-kpi-month-total');
            if (monthTotalEl && !isNaN(paidAmount)) {
                const curMonth = parseFloat(monthTotalEl.getAttribute('data-raw-val') || '0');
                const newMonth = Math.max(0, curMonth - paidAmount);
                monthTotalEl.setAttribute('data-raw-val', newMonth.toFixed(2));
                monthTotalEl.textContent = formatMoney(newMonth) + ' ' + sym;
            }

            // Invalidate calendar client cache and reload if calendar tab is currently open
            monthCache.clear();
            if (gridEl) gridEl.dataset.loaded = '';
            if (document.querySelector('.pay-tab-panel.active')?.id === 'pay-tab-calendar') {
                loadMonth(state.year, state.month);
            }

            if (window.ECuzdanHaptics) window.ECuzdanHaptics.success();
            if (typeof showToast === 'function') {
                showToast('İşlem başarıyla ödendi olarak işaretlendi.', 'success');
            }
        })
        .catch(function (err) {
            console.error('Quick pay calendar error:', err);
            if (buttonEl) {
                buttonEl.disabled = false;
                buttonEl.innerHTML = originalHtml;
            }
            if (window.ECuzdanHaptics) window.ECuzdanHaptics.error();
            if (typeof showToast === 'function') {
                showToast(err.message || 'Ödeme işlemi sırasında bir hata oluştu.', 'error');
            } else {
                alert(err.message || 'Ödeme işlemi sırasında bir hata oluştu.');
            }
        });
    };
})();
