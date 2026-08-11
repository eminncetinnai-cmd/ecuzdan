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
    };

    const popover = document.getElementById('cal-popover');
    const gridEl = document.getElementById('cal-grid');
    const titleEl = document.getElementById('cal-month-title');
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
            html += '<div><h4 class="text-[9px] font-black uppercase text-emerald-600 mb-1 flex justify-between"><span>Gelirler</span><span>' + formatMoney(data.income_total) + '</span></h4><ul class="text-[11px]">' + renderTxList(data.income, 'text-emerald-600') + '</ul></div>';
            html += '<div><h4 class="text-[9px] font-black uppercase text-rose-600 mb-1 flex justify-between"><span>Giderler</span><span>' + formatMoney(data.expense_total) + '</span></h4><ul class="text-[11px]">' + renderTxList(data.expense, 'text-rose-600') + '</ul></div>';
            if (data.investment && data.investment.length) {
                html += '<div><h4 class="text-[9px] font-black uppercase text-blue-600 mb-1 flex justify-between"><span>Yatırım</span><span>' + formatMoney(data.investment_total) + '</span></h4><ul class="text-[11px]">' + renderTxList(data.investment, 'text-blue-600') + '</ul></div>';
            }
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
            const hasIncome = data && data.income.length > 0;
            const hasExpense = data && data.expense.length > 0;
            const hasInv = data && data.investment && data.investment.length > 0;
            let cls = 'cal-day';
            if (isToday) cls += ' cal-day--today';
            if (data) cls += ' cal-day--has-data';

            let badges = '';
            if (hasIncome) badges += '<span class="cal-dot cal-dot--income" title="Gelir"></span>';
            if (hasExpense) badges += '<span class="cal-dot cal-dot--expense" title="Gider"></span>';
            if (hasInv) badges += '<span class="cal-dot cal-dot--inv" title="Yatırım"></span>';

            let mini = '';
            if (data && (hasIncome || hasExpense)) {
                mini = '<div class="cal-mini">';
                if (hasIncome) mini += '<span class="text-emerald-600">+' + formatMoney(data.income_total) + '</span>';
                if (hasExpense) mini += '<span class="text-rose-600">-' + formatMoney(data.expense_total) + '</span>';
                mini += '</div>';
            }

            html += '<div class="' + cls + '" data-date="' + iso + '" tabindex="0">' +
                '<span class="cal-day-num">' + d + '</span>' +
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
        const loading = document.getElementById('cal-loading');
        if (loading) loading.classList.remove('hidden');
        return fetch('/payment_calendar/month_data?year=' + year + '&month=' + month)
            .then(function (r) { 
                if (!r.ok) {
                    console.error('API error:', r.status, r.statusText);
                    throw new Error('API request failed');
                }
                return r.json(); 
            })
            .then(function (data) {
                console.log('Calendar data received:', data);
                if (data.error) throw new Error(data.error);
                state.year = data.year;
                state.month = data.month;
                state.today = data.today;
                state.days = data.days || {};
                updateTitle();
                buildGrid();
            })
            .catch(function (error) {
                console.error('Error loading calendar data:', error);
                if (loading) loading.classList.add('hidden');
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

    function initTabs() {
        document.querySelectorAll('.pay-tab-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const tab = btn.dataset.tab;
                console.log('Tab clicked:', tab);
                document.querySelectorAll('.pay-tab-btn').forEach(function (b) {
                    b.classList.toggle('active', b.dataset.tab === tab);
                });
                document.querySelectorAll('.pay-tab-panel').forEach(function (p) {
                    p.classList.toggle('active', p.id === 'pay-tab-' + tab);
                });
                if (tab === 'calendar' && gridEl && !gridEl.dataset.loaded) {
                    console.log('Loading calendar for month:', state.year, state.month);
                    gridEl.dataset.loaded = '1';
                    loadMonth(state.year, state.month);
                }
                if (tab === 'balance') {
                    initBalanceTab();
                }
            });
        });
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

        return fetch('/payment_calendar/daily_balance?year=' + year + '&month=' + month)
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
    });
})();
