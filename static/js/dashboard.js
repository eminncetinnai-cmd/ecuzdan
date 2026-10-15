/**
 * Dashboard & Cash Flow Client Logic
 * EAFGS Compliant - Chart.js, Modal Handlers & Dynamic Currency
 */

(function() {
    const dashboardCharts = window.__ecuzdanDashboardCharts = window.__ecuzdanDashboardCharts || [];

    function resolveColor(varName, fallbackHex) {
        try {
            const val = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
            if (val && (val.startsWith('#') || val.startsWith('rgb'))) return val;
        } catch (e) {}
        return fallbackHex;
    }

    const CHART_GREEN = '#10b981'; // Emerald-500
    const CHART_RED = '#ef4444';   // Rose-500

    function getDashboardChartTheme() {
        const isDark = document.documentElement.classList.contains('dark') ||
                       document.documentElement.getAttribute('data-user-theme') === 'dark' ||
                       document.documentElement.getAttribute('data-theme') === 'dark';
        return {
            surface: isDark ? '#0f172a' : '#ffffff',
            grid: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)',
            text: isDark ? '#94a3b8' : '#64748b',
            textStrong: isDark ? '#f8fafc' : '#1e293b',
            border: isDark ? '#334155' : '#e2e8f0',
            tooltipBg: isDark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(255, 255, 255, 0.97)',
            tooltipText: isDark ? '#f8fafc' : '#1e293b'
        };
    }

    function formatCompactMoney(value) {
        let val = value;
        if (typeof value === 'string') {
            val = parseFloat(value);
            if (isNaN(val)) val = 0;
        }
        const currSym = window.BASE_CURRENCY_SYMBOL || '₺';
        const absVal = Math.abs(val);
        const sign = val < 0 ? '-' : '';
        if (absVal >= 1000000) {
            return sign + (absVal / 1000000).toFixed(1).replace('.', ',') + 'M ' + currSym;
        }
        if (absVal >= 10000) {
            return sign + Math.round(absVal / 1000) + 'K ' + currSym;
        }
        if (absVal >= 1000) {
            return sign + (absVal / 1000).toFixed(1).replace('.', ',') + 'K ' + currSym;
        }
        if (Number.isInteger(val)) {
            return sign + absVal + ' ' + currSym;
        }
        return sign + absVal.toFixed(2).replace('.', ',') + ' ' + currSym;
    }

    function formatDashboardMoney(value) {
        let val = value;
        if (typeof value === 'string') {
            val = parseFloat(value);
            if (isNaN(val)) val = 0;
        }
        const currCode = window.BASE_CURRENCY_CODE || 'TRY';
        const currSym = window.BASE_CURRENCY_SYMBOL || '₺';
        try {
            return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: currCode }).format(val);
        } catch (e) {
            return new Intl.NumberFormat('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val) + ' ' + currSym;
        }
    }

    function segmentColor(y) {
        return y < 0 ? CHART_RED : CHART_GREEN;
    }

    function applyDashboardChartTheme() {
        const theme = getDashboardChartTheme();
        window.__ecuzdanDashboardCharts = dashboardCharts.filter(chart => {
            try {
                return chart && chart.ctx && document.body.contains(chart.canvas);
            } catch (e) {
                return false;
            }
        });
        window.__ecuzdanDashboardCharts.forEach(chart => {
            chart.options.plugins = chart.options.plugins || {};
            chart.options.plugins.legend = chart.options.plugins.legend || {};
            chart.options.plugins.legend.labels = chart.options.plugins.legend.labels || {};
            chart.options.plugins.legend.labels.color = theme.textStrong;
            chart.options.plugins.tooltip = chart.options.plugins.tooltip || {};
            chart.options.plugins.tooltip.backgroundColor = theme.tooltipBg;
            chart.options.plugins.tooltip.titleColor = theme.tooltipText;
            chart.options.plugins.tooltip.bodyColor = theme.text;
            chart.options.plugins.tooltip.borderColor = theme.border;
            if (chart.options.scales && chart.options.scales.x) {
                chart.options.scales.x.ticks = chart.options.scales.x.ticks || {};
                chart.options.scales.x.ticks.color = theme.text;
                chart.options.scales.x.grid = chart.options.scales.x.grid || {};
                chart.options.scales.x.grid.color = theme.grid;
            }
            if (chart.options.scales && chart.options.scales.y) {
                chart.options.scales.y.ticks = chart.options.scales.y.ticks || {};
                chart.options.scales.y.ticks.color = theme.text;
                chart.options.scales.y.grid = chart.options.scales.y.grid || {};
                chart.options.scales.y.grid.color = theme.grid;
            }
            if (chart.config.type === 'doughnut') {
                chart.data.datasets.forEach(ds => {
                    ds.borderColor = theme.surface;
                });
            } else if (chart.config.type === 'line') {
                chart.data.datasets.forEach(ds => {
                    ds.pointBorderColor = theme.surface;
                });
            }
            chart.update('none');
        });
    }

    function createChart(id, labels, data) {
        const canvas = document.getElementById(id);
        if (!canvas || typeof Chart === 'undefined') return null;
        if (Chart.getChart(canvas)) {
            Chart.getChart(canvas).destroy();
        }
        const ctx = canvas.getContext('2d');
        const theme = getDashboardChartTheme();
        const defaultColor = (data && data.length > 0 && data[data.length - 1] < 0) ? CHART_RED : CHART_GREEN;

        let bgGradient = 'rgba(16, 185, 129, 0.12)';
        try {
            const grad = ctx.createLinearGradient(0, 0, 0, 240);
            if (defaultColor === CHART_RED) {
                grad.addColorStop(0, 'rgba(239, 68, 68, 0.22)');
                grad.addColorStop(1, 'rgba(239, 68, 68, 0.01)');
            } else {
                grad.addColorStop(0, 'rgba(16, 185, 129, 0.22)');
                grad.addColorStop(1, 'rgba(16, 185, 129, 0.01)');
            }
            bgGradient = grad;
        } catch (e) {}

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    fill: true,
                    tension: 0.38,
                    borderWidth: 2.5,
                    borderColor: defaultColor,
                    backgroundColor: bgGradient,
                    pointRadius: 3.5,
                    pointHoverRadius: 6,
                    pointBackgroundColor: function(c) {
                        const val = c.raw !== undefined ? c.raw : (c.parsed ? c.parsed.y : 0);
                        return val < 0 ? CHART_RED : CHART_GREEN;
                    },
                    pointBorderColor: theme.surface,
                    pointBorderWidth: 2,
                    segment: {
                        borderColor: c => segmentColor(c.p1.parsed.y),
                        backgroundColor: c => c.p1.parsed.y < 0 ? 'rgba(239, 68, 68, 0.08)' : 'rgba(16, 185, 129, 0.08)'
                    }
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
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: theme.tooltipBg,
                        titleColor: theme.tooltipText,
                        bodyColor: theme.text,
                        borderColor: theme.border,
                        borderWidth: 1,
                        padding: 10,
                        cornerRadius: 8,
                        caretSize: 6,
                        callbacks: {
                            label: function(context) {
                                return ' ' + formatDashboardMoney(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false, color: theme.grid },
                        ticks: {
                            font: { size: 10, weight: '600' },
                            color: theme.text,
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 7
                        }
                    },
                    y: {
                        grid: { color: theme.grid },
                        ticks: {
                            callback: v => formatCompactMoney(v),
                            font: { size: 10, weight: '500' },
                            color: theme.text,
                            maxTicksLimit: 6
                        }
                    }
                }
            }
        });
        dashboardCharts.push(chart);
        return chart;
    }

    function initAssetDistChart(labels, values) {
        if (typeof Chart === 'undefined') return;
        const canvas = document.getElementById('assetDistChart');
        if (!canvas) return;
        if (Chart.getChart(canvas)) {
            Chart.getChart(canvas).destroy();
        }
        if (!values || values.length === 0) return;

        const PALETTE = [
            '#6366f1', // Indigo-500
            '#3b82f6', // Blue-500
            '#10b981', // Emerald-500
            '#f59e0b', // Amber-500
            '#ef4444', // Rose-500
            '#8b5cf6', // Violet-500
            '#06b6d4', // Cyan-500
            '#84cc16', // Lime-500
            '#f97316', // Orange-500
            '#ec4899'  // Pink-500
        ];
        const theme = getDashboardChartTheme();
        const distChart = new Chart(canvas.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: labels.map((_, i) => PALETTE[i % PALETTE.length]),
                    borderColor: theme.surface,
                    borderWidth: 3,
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '68%',
                animation: { animateRotate: true, duration: 800 },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: theme.textStrong,
                            font: { size: 11, weight: '700' },
                            padding: 12,
                            boxWidth: 12,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: theme.tooltipBg,
                        titleColor: theme.tooltipText,
                        bodyColor: theme.text,
                        borderColor: theme.border,
                        borderWidth: 1,
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(ctx) {
                                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = total > 0 ? ((ctx.raw / total) * 100).toFixed(1) : 0;
                                return ` ${ctx.label}: ${formatDashboardMoney(ctx.raw)} (%${pct})`;
                            }
                        }
                    }
                }
            }
        });
        dashboardCharts.push(distChart);
    }

    function initDashboardCharts() {
        let weekLabels = [], weekData = [], monthLabels = [], monthData = [];
        let assetLabels = [], assetValues = [];

        // 1. Try reading from dedicated application/json script tag
        const jsonEl = document.getElementById('dashboard-chart-data');
        if (jsonEl && jsonEl.textContent) {
            try {
                const parsed = JSON.parse(jsonEl.textContent.trim());
                weekLabels = Array.isArray(parsed.weekLabels) ? parsed.weekLabels : [];
                weekData = Array.isArray(parsed.weekData) ? parsed.weekData : [];
                monthLabels = Array.isArray(parsed.monthLabels) ? parsed.monthLabels : [];
                monthData = Array.isArray(parsed.monthData) ? parsed.monthData : [];
                assetLabels = Array.isArray(parsed.assetLabels) ? parsed.assetLabels : [];
                assetValues = Array.isArray(parsed.assetValues) ? parsed.assetValues : [];
            } catch (e) {
                console.error('Error parsing dashboard JSON script data:', e);
            }
        }

        // 2. Fallback to data attributes if not populated
        const pageData = document.getElementById('dashboard-page-data');
        if (pageData && !weekLabels.length && !weekData.length && !monthLabels.length && !monthData.length) {
            try {
                const rawWeekLabels = pageData.getAttribute('data-week-labels');
                if (rawWeekLabels) weekLabels = JSON.parse(rawWeekLabels);

                const rawWeekData = pageData.getAttribute('data-week-data');
                if (rawWeekData) weekData = JSON.parse(rawWeekData);

                const rawMonthLabels = pageData.getAttribute('data-month-labels');
                if (rawMonthLabels) monthLabels = JSON.parse(rawMonthLabels);

                const rawMonthData = pageData.getAttribute('data-month-data');
                if (rawMonthData) monthData = JSON.parse(rawMonthData);

                const rawAssetLabels = pageData.getAttribute('data-asset-labels');
                if (rawAssetLabels) assetLabels = JSON.parse(rawAssetLabels);

                const rawAssetValues = pageData.getAttribute('data-asset-values');
                if (rawAssetValues) assetValues = JSON.parse(rawAssetValues);
            } catch (e) {
                console.error('Error parsing dashboard chart data attributes:', e);
            }
        }

        if (!pageData && !jsonEl) return;

        function renderAllCharts() {
            createChart('weekChart', weekLabels, weekData);
            createChart('monthChart', monthLabels, monthData);

            if (assetValues && assetValues.length > 0) {
                initAssetDistChart(assetLabels, assetValues);
            }
        }

        if (typeof Chart === 'undefined') {
            let retryCount = 0;
            const retryInterval = setInterval(() => {
                retryCount++;
                if (typeof Chart !== 'undefined') {
                    clearInterval(retryInterval);
                    renderAllCharts();
                } else if (retryCount >= 50) {
                    clearInterval(retryInterval);
                    console.error('Chart.js was not loaded within timeout.');
                }
            }, 100);
        } else {
            renderAllCharts();
        }
    }

    // Modal & Transaction Handlers
    function openEditModal(btn) {
        if (!btn || !btn.dataset) return;
        const d = btn.dataset;
        const setVal = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.value = val;
        };

        setVal('modalTransactionId', d.id || '');
        setVal('modalDate', d.date || '');
        setVal('modalCategory', d.category || '');
        setVal('modalAmount', d.amount || '');
        setVal('modalDescription', d.description || '');
        setVal('modalNote', d.note || '');
        setVal('modalStatus', d.status || 'Bekliyor');

        if (typeof window.openModal === 'function') {
            window.openModal('editTransactionModal');
        } else {
            const m = document.getElementById('editTransactionModal');
            if (m) {
                m.classList.remove('hidden');
                m.classList.add('active');
                m.style.display = 'flex';
            }
        }
    }

    function closeModal() {
        if (typeof window.closeModal === 'function') {
            window.closeModal('editTransactionModal');
        } else {
            const m = document.getElementById('editTransactionModal');
            if (m) {
                m.classList.add('hidden');
                m.classList.remove('active');
                m.style.display = 'none';
            }
        }
    }

    function deleteTransaction(transactionId) {
        if (typeof window.showGlobalConfirm === 'function') {
            window.showGlobalConfirm('İşlemi Sil', 'Bu işlemi silmek istediğinize emin misiniz?', () => {
                performDelete(transactionId);
            }, true);
        } else if (confirm('Bu işlemi silmek istediğinize emin misiniz?')) {
            performDelete(transactionId);
        }
    }

    function performDelete(transactionId) {
        const deleteUrl = (window.ECuzdanEndpoints && window.ECuzdanEndpoints.transactions && window.ECuzdanEndpoints.transactions.delete)
            ? window.ECuzdanEndpoints.transactions.delete(transactionId)
            : `/delete_t/${transactionId}`;

        const csrfToken = document.querySelector('input[name="csrf_token"]')?.value || '';

        fetch(deleteUrl, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (typeof window.showToast === 'function') {
                    window.showToast(data.message || 'İşlem başarıyla silindi', 'success');
                }
                setTimeout(() => window.location.reload(), 1200);
            } else {
                if (typeof window.showToast === 'function') {
                    window.showToast(data.message || 'Hata oluştu', 'error');
                }
            }
        })
        .catch(error => {
            console.error('Error deleting transaction:', error);
            if (typeof window.showToast === 'function') {
                window.showToast('İşlem silinirken bir hata oluştu', 'error');
            }
        });
    }

    function setupEditForm() {
        const form = document.getElementById('editModalForm');
        if (!form) return;

        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const transactionId = document.getElementById('modalTransactionId')?.value;
            if (!transactionId) return;

            const editUrl = (window.ECuzdanEndpoints && window.ECuzdanEndpoints.transactions && window.ECuzdanEndpoints.transactions.edit)
                ? window.ECuzdanEndpoints.transactions.edit(transactionId)
                : `/edit_t/${transactionId}`;

            const formData = new FormData(this);

            fetch(editUrl, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    if (typeof window.showToast === 'function') {
                        window.showToast(data.message || 'İşlem güncellendi', 'success');
                    }
                    closeModal();
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    if (typeof window.showToast === 'function') {
                        window.showToast(data.message || 'Güncelleme başarısız', 'error');
                    }
                }
            })
            .catch(err => console.error('Error editing transaction:', err));
        });
    }

    // ── Quick Transaction & Transfer Handlers ──────────────────────────────────
    let dashboardMeta = {
        incomeCats: ['Maaş', 'Ek Gelir', 'Kira Geliri', 'Yatırım Getirisi', 'Diğer'],
        expenseCats: ['Kira', 'Market', 'Fatura', 'Ulaşım', 'Sağlık', 'Eğlence', 'Diğer'],
        investmentCats: ['Hisse Senedi', 'Altın/Emtia', 'Döviz', 'Kripto Para', 'BES', 'Fon', 'Diğer'],
        openAssets: []
    };

    function loadDashboardMetaData() {
        const metaEl = document.getElementById('dashboard-meta-data');
        if (metaEl && metaEl.textContent) {
            try {
                const parsed = JSON.parse(metaEl.textContent.trim());
                if (parsed.incomeCats && parsed.incomeCats.length) dashboardMeta.incomeCats = parsed.incomeCats;
                if (parsed.expenseCats && parsed.expenseCats.length) dashboardMeta.expenseCats = parsed.expenseCats;
                if (parsed.investmentCats && parsed.investmentCats.length) dashboardMeta.investmentCats = parsed.investmentCats;
                if (parsed.openAssets && Array.isArray(parsed.openAssets)) dashboardMeta.openAssets = parsed.openAssets;
            } catch (e) {
                console.warn('Dashboard meta data parsing fallback:', e);
            }
        }
    }

    function openQuickTransactionModal(type) {
        const targetType = type || 'Gelir';
        const modal = document.getElementById('quickTransactionModal');
        if (!modal) return;
        const form = document.getElementById('quickTransactionForm');
        if (form) form.reset();

        const dateInput = document.getElementById('quickTxDate');
        if (dateInput) {
            const today = new Date();
            const yyyy = today.getFullYear();
            const mm = String(today.getMonth() + 1).padStart(2, '0');
            const dd = String(today.getDate()).padStart(2, '0');
            dateInput.value = `${yyyy}-${mm}-${dd}`;
        }

        switchQuickTxType(targetType);

        modal.classList.remove('hidden');
        modal.classList.add('active');
        const amtInput = document.getElementById('quickTxAmount');
        if (amtInput) setTimeout(() => amtInput.focus(), 100);
    }

    function switchQuickTxType(type) {
        const typeInput = document.getElementById('quickTxType');
        if (typeInput) typeInput.value = type;

        const titleEl = document.getElementById('quickModalTitle');
        const iconBox = document.getElementById('quickModalTypeIcon');
        const iconTxt = document.getElementById('quickModalIconText');
        const submitBtn = document.getElementById('btnQuickTxSubmit');

        const tabGelir = document.getElementById('tabQuickGelir');
        const tabGider = document.getElementById('tabQuickGider');
        const tabYatirim = document.getElementById('tabQuickYatirim');

        const baseTabCls = 'py-2 text-xs font-black rounded-lg transition text-slate-600 dark:text-slate-400 hover:text-indigo-500';
        [tabGelir, tabGider, tabYatirim].forEach(tab => {
            if (tab) tab.className = baseTabCls;
        });

        const catSelect = document.getElementById('quickTxCategory');
        if (catSelect) {
            catSelect.innerHTML = '';
            let catList = dashboardMeta.expenseCats;
            if (type === 'Gelir') catList = dashboardMeta.incomeCats;
            else if (type === 'Yatırım') catList = dashboardMeta.investmentCats;

            catList.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c;
                opt.textContent = c;
                catSelect.appendChild(opt);
            });
        }

        if (type === 'Gelir') {
            if (titleEl) titleEl.textContent = 'Hızlı Gelir Ekle';
            if (iconTxt) iconTxt.textContent = '↑';
            if (iconBox) iconBox.className = 'w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center border border-emerald-500/20';
            if (tabGelir) tabGelir.className = 'py-2 text-xs font-black rounded-lg transition bg-white dark:bg-slate-700 text-emerald-600 dark:text-emerald-400 shadow-sm';
            if (submitBtn) {
                submitBtn.className = 'flex-1 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-black rounded-xl text-xs uppercase tracking-wider transition shadow-md flex items-center justify-center gap-2';
            }
        } else if (type === 'Yatırım') {
            if (titleEl) titleEl.textContent = 'Hızlı Yatırım Ekle';
            if (iconTxt) iconTxt.textContent = '◆';
            if (iconBox) iconBox.className = 'w-10 h-10 rounded-xl bg-sky-500/10 text-sky-600 dark:text-sky-400 flex items-center justify-center border border-sky-500/20';
            if (tabYatirim) tabYatirim.className = 'py-2 text-xs font-black rounded-lg transition bg-white dark:bg-slate-700 text-sky-600 dark:text-sky-400 shadow-sm';
            if (submitBtn) {
                submitBtn.className = 'flex-1 py-3 bg-sky-600 hover:bg-sky-700 text-white font-black rounded-xl text-xs uppercase tracking-wider transition shadow-md flex items-center justify-center gap-2';
            }
        } else {
            if (titleEl) titleEl.textContent = 'Hızlı Gider Ekle';
            if (iconTxt) iconTxt.textContent = '↓';
            if (iconBox) iconBox.className = 'w-10 h-10 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400 flex items-center justify-center border border-rose-500/20';
            if (tabGider) tabGider.className = 'py-2 text-xs font-black rounded-lg transition bg-white dark:bg-slate-700 text-rose-600 dark:text-rose-400 shadow-sm';
            if (submitBtn) {
                submitBtn.className = 'flex-1 py-3 bg-rose-600 hover:bg-rose-700 text-white font-black rounded-xl text-xs uppercase tracking-wider transition shadow-md flex items-center justify-center gap-2';
            }
        }
    }

    function openQuickTransferModal() {
        const modal = document.getElementById('quickTransferModal');
        if (!modal) return;
        const form = document.getElementById('quickTransferForm');
        if (form) form.reset();

        const dateInput = document.getElementById('quickTransferDate');
        if (dateInput) {
            const today = new Date();
            const yyyy = today.getFullYear();
            const mm = String(today.getMonth() + 1).padStart(2, '0');
            const dd = String(today.getDate()).padStart(2, '0');
            dateInput.value = `${yyyy}-${mm}-${dd}`;
        }

        const preview = document.getElementById('transferQtyPreview');
        if (preview) preview.classList.add('hidden');

        modal.classList.remove('hidden');
        modal.classList.add('active');
        const selectEl = document.getElementById('quickTransferAssetSelect');
        if (selectEl) setTimeout(() => selectEl.focus(), 100);
    }

    function calcTransferQty() {
        const select = document.getElementById('quickTransferAssetSelect');
        const amtInput = document.getElementById('quickTransferAmount');
        const preview = document.getElementById('transferQtyPreview');
        const qtyVal = document.getElementById('transferQtyVal');
        if (!select || !amtInput || !preview || !qtyVal) return;

        const opt = select.options[select.selectedIndex];
        const unitPrice = opt ? parseFloat(opt.getAttribute('data-unit-price') || '0') : 0;
        const amount = parseFloat(amtInput.value || '0');

        if (unitPrice > 0 && amount > 0) {
            const qty = amount / unitPrice;
            qtyVal.textContent = qty >= 1 ? qty.toLocaleString('tr-TR', { maximumFractionDigits: 4 }) : qty.toFixed(6);
            preview.classList.remove('hidden');
        } else {
            preview.classList.add('hidden');
        }
    }

    function updateTransferAssetInfo() {
        calcTransferQty();
    }

    function closeQuickModal(modalId) {
        const m = document.getElementById(modalId);
        if (m) {
            m.classList.add('hidden');
            m.classList.remove('active');
        }
    }

    function quickPayTransaction(transactionId, btn) {
        if (!transactionId) return;
        if (btn) btn.disabled = true;

        const csrfToken = document.querySelector('input[name="csrf_token"]')?.value || '';
        fetch(`/transactions/${transactionId}/quick-pay`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ csrf_token: csrfToken })
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                if (typeof window.showToast === 'function') {
                    window.showToast(data.message || 'İşlem ödendi olarak işaretlendi', 'success');
                }
                setTimeout(() => window.location.reload(), 700);
            } else {
                if (typeof window.showToast === 'function') {
                    window.showToast(data.message || 'İşlem güncellenemedi', 'error');
                }
                if (btn) btn.disabled = false;
            }
        })
        .catch(err => {
            console.error('Quick pay error:', err);
            if (typeof window.showToast === 'function') {
                window.showToast('Ödeme kaydedilirken bir hata oluştu', 'error');
            }
            if (btn) btn.disabled = false;
        });
    }

    function setupQuickForms() {
        const txForm = document.getElementById('quickTransactionForm');
        if (txForm) {
            txForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const submitBtn = document.getElementById('btnQuickTxSubmit');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.classList.add('opacity-75');
                }

                const formData = new FormData(this);
                fetch('/new_transaction', {
                    method: 'POST',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' },
                    body: formData
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        if (typeof window.showToast === 'function') {
                            window.showToast(data.message || 'İşlem başarıyla kaydedildi', 'success');
                        }
                        closeQuickModal('quickTransactionModal');
                        setTimeout(() => window.location.reload(), 700);
                    } else {
                        if (typeof window.showToast === 'function') {
                            window.showToast(data.message || 'Kayıt başarısız', 'error');
                        }
                        if (submitBtn) {
                            submitBtn.disabled = false;
                            submitBtn.classList.remove('opacity-75');
                        }
                    }
                })
                .catch(err => {
                    console.error('Quick tx error:', err);
                    if (typeof window.showToast === 'function') {
                        window.showToast('İşlem kaydedilirken bir hata oluştu', 'error');
                    }
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.classList.remove('opacity-75');
                    }
                });
            });
        }

        const transferForm = document.getElementById('quickTransferForm');
        if (transferForm) {
            transferForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const submitBtn = document.getElementById('btnQuickTransferSubmit');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.classList.add('opacity-75');
                }

                const formData = new FormData(this);
                fetch('/quick_transfer', {
                    method: 'POST',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' },
                    body: formData
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        if (typeof window.showToast === 'function') {
                            window.showToast(data.message || 'Yatırım transferi tamamlandı', 'success');
                        }
                        closeQuickModal('quickTransferModal');
                        setTimeout(() => window.location.reload(), 700);
                    } else {
                        if (typeof window.showToast === 'function') {
                            window.showToast(data.message || 'Transfer başarısız', 'error');
                        }
                        if (submitBtn) {
                            submitBtn.disabled = false;
                            submitBtn.classList.remove('opacity-75');
                        }
                    }
                })
                .catch(err => {
                    console.error('Quick transfer error:', err);
                    if (typeof window.showToast === 'function') {
                        window.showToast('Transfer sırasında bir hata oluştu', 'error');
                    }
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.classList.remove('opacity-75');
                    }
                });
            });
        }
    }

    // Global exposes
    window.openEditModal = openEditModal;
    window.closeModal = closeModal;
    window.deleteTransaction = deleteTransaction;
    window.openQuickTransactionModal = openQuickTransactionModal;
    window.switchQuickTxType = switchQuickTxType;
    window.openQuickTransferModal = openQuickTransferModal;
    window.closeQuickModal = closeQuickModal;
    window.calcTransferQty = calcTransferQty;
    window.updateTransferAssetInfo = updateTransferAssetInfo;
    window.quickPayTransaction = quickPayTransaction;

    // Theme changes listener
    window.addEventListener('ecuzdan:theme-changed', applyDashboardChartTheme);

    function onReady() {
        loadDashboardMetaData();
        initDashboardCharts();
        setupEditForm();
        setupQuickForms();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', onReady);
    } else {
        onReady();
    }
})();
