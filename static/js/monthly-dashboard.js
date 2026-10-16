/**
 * E-Cüzdan — Monthly Consolidated Dashboard JS
 */

const MONTHLY_INTL_LOCALES = {
    tr: 'tr-TR',
    en: 'en-US',
    de: 'de-DE',
    it: 'it-IT'
};

function getMonthlyLocale() {
    const lang = (window.monthlyChartData && window.monthlyChartData.lang) || 'tr';
    return MONTHLY_INTL_LOCALES[lang] || 'tr-TR';
}

function getMonthlyUiCopy() {
    return (window.monthlyChartData && window.monthlyChartData.uiCopy) || {
        income: 'Gelir',
        expense: 'Gider',
        investment: 'Yatırım',
        incomeAmount: 'Gelir Tutarı',
        expenseAmount: 'Gider Tutarı',
        investmentAmount: 'Yatırım Tutarı'
    };
}

function formatMonthlyMoney(value) {
    let val = value;
    if (typeof value === 'string') {
        val = parseFloat(value);
        if (isNaN(val)) val = 0;
    }
    const curr = window.BASE_CURRENCY_CODE || 'TRY';
    return new Intl.NumberFormat(getMonthlyLocale(), {
        style: 'currency',
        currency: curr
    }).format(val);
}

function changeYear(year) {
    window.location.href = '/monthly_dashboard?year=' + encodeURIComponent(year);
}

function resolveColor(varName, fallbackHex) {
    try {
        const val = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
        if (val && val.startsWith('#')) return val;
    } catch (e) {}
    return fallbackHex;
}

function initMonthlyCharts() {
    if (typeof Chart === 'undefined') {
        let retryCount = 0;
        const retryInterval = setInterval(() => {
            retryCount++;
            if (typeof Chart !== 'undefined') {
                clearInterval(retryInterval);
                initMonthlyCharts();
            } else if (retryCount >= 50) {
                clearInterval(retryInterval);
                console.error('Chart.js is not loaded');
            }
        }, 100);
        return;
    }

    const data = window.monthlyChartData || {};
    const monthlyUiCopy = getMonthlyUiCopy();

    const CHART_COLORS = {
        green: resolveColor('--color-emerald-500', '#10b981'),
        red: resolveColor('--color-rose-500', '#ef4444'),
        blue: resolveColor('--color-blue-500', '#0ea5e9'),
        indigo: resolveColor('--color-indigo-500', '#6366f1'),
        amber: resolveColor('--color-amber-500', '#f59e0b')
    };

    // Main Investment Trend Chart
    const ctxInvest = document.getElementById('topInvestChart');
    if (ctxInvest && Array.isArray(data.monthsTr) && Array.isArray(data.invData)) {
        new Chart(ctxInvest.getContext('2d'), {
            type: 'bar',
            data: {
                labels: data.monthsTr,
                datasets: [{
                    label: monthlyUiCopy.investmentAmount,
                    data: data.invData.map(v => Number(v) || 0),
                    backgroundColor: CHART_COLORS.blue,
                    borderRadius: 8,
                    borderSkipped: false,
                    hoverBackgroundColor: CHART_COLORS.indigo
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.92)',
                        titleFont: { size: 12, weight: 'bold' },
                        bodyFont: { size: 13 },
                        padding: 14,
                        callbacks: {
                            label: function(ctx) {
                                return monthlyUiCopy.investment + ': ' + formatMonthlyMoney(ctx.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 10, weight: '600' }, color: resolveColor('--color-slate-500', '#64748b') }
                    },
                    y: {
                        grid: { color: resolveColor('--color-slate-200', '#e2e8f0'), drawBorder: false },
                        ticks: {
                            font: { size: 10, weight: '600' },
                            color: resolveColor('--color-slate-500', '#64748b'),
                            callback: function(value) { return formatMonthlyMoney(value); }
                        }
                    }
                }
            }
        });
    }

    // Monthly Breakdown Mini Charts
    if (Array.isArray(data.monthsData)) {
        data.monthsData.forEach((m, idx) => {
            const chartIndex = idx + 1;
            const canvas = document.getElementById('chart-' + chartIndex);
            if (canvas) {
                new Chart(canvas.getContext('2d'), {
                    type: 'bar',
                    data: {
                        labels: [monthlyUiCopy.income, monthlyUiCopy.expense, monthlyUiCopy.investment],
                        datasets: [{
                            data: [Number(m.inc) || 0, Number(m.exp) || 0, Number(m.inv) || 0],
                            backgroundColor: [CHART_COLORS.green, CHART_COLORS.red, CHART_COLORS.blue],
                            borderRadius: 6,
                            borderSkipped: false
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                backgroundColor: 'rgba(15, 23, 42, 0.92)',
                                titleFont: { size: 11, weight: 'bold' },
                                bodyFont: { size: 12 },
                                padding: 12,
                                callbacks: {
                                    label: function(ctx) {
                                        const labels = [monthlyUiCopy.income, monthlyUiCopy.expense, monthlyUiCopy.investment];
                                        return labels[ctx.dataIndex] + ': ' + formatMonthlyMoney(ctx.parsed.y);
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                grid: { display: false },
                                ticks: { font: { size: 11, weight: '700' }, color: resolveColor('--color-slate-500', '#64748b') }
                            },
                            y: { display: false }
                        }
                    }
                });
            }
        });
    }

    // Income Trend Chart
    const ctxIncome = document.getElementById('incomeChart');
    if (ctxIncome && Array.isArray(data.monthsTr) && Array.isArray(data.incData)) {
        new Chart(ctxIncome.getContext('2d'), {
            type: 'bar',
            data: {
                labels: data.monthsTr,
                datasets: [{
                    label: monthlyUiCopy.incomeAmount,
                    data: data.incData.map(v => Number(v) || 0),
                    backgroundColor: CHART_COLORS.green,
                    borderRadius: 8,
                    borderSkipped: false,
                    hoverBackgroundColor: CHART_COLORS.indigo
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.92)',
                        titleFont: { size: 12, weight: 'bold' },
                        bodyFont: { size: 13 },
                        padding: 14,
                        callbacks: {
                            label: function(ctx) {
                                return monthlyUiCopy.income + ': ' + formatMonthlyMoney(ctx.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 10, weight: '600' }, color: resolveColor('--color-slate-500', '#64748b') }
                    },
                    y: {
                        grid: { color: resolveColor('--color-slate-200', '#e2e8f0'), drawBorder: false },
                        ticks: {
                            font: { size: 10, weight: '600' },
                            color: resolveColor('--color-slate-500', '#64748b'),
                            callback: function(value) { return formatMonthlyMoney(value); }
                        }
                    }
                }
            }
        });
    }

    // Expense Trend Chart
    const ctxExpense = document.getElementById('expenseChart');
    if (ctxExpense && Array.isArray(data.monthsTr) && Array.isArray(data.expData)) {
        new Chart(ctxExpense.getContext('2d'), {
            type: 'bar',
            data: {
                labels: data.monthsTr,
                datasets: [{
                    label: monthlyUiCopy.expenseAmount,
                    data: data.expData.map(v => Number(v) || 0),
                    backgroundColor: CHART_COLORS.red,
                    borderRadius: 8,
                    borderSkipped: false,
                    hoverBackgroundColor: CHART_COLORS.indigo
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.92)',
                        titleFont: { size: 12, weight: 'bold' },
                        bodyFont: { size: 13 },
                        padding: 14,
                        callbacks: {
                            label: function(ctx) {
                                return monthlyUiCopy.expense + ': ' + formatMonthlyMoney(ctx.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 10, weight: '600' }, color: resolveColor('--color-slate-500', '#64748b') }
                    },
                    y: {
                        grid: { color: resolveColor('--color-slate-200', '#e2e8f0'), drawBorder: false },
                        ticks: {
                            font: { size: 10, weight: '600' },
                            color: resolveColor('--color-slate-500', '#64748b'),
                            callback: function(value) { return formatMonthlyMoney(value); }
                        }
                    }
                }
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', initMonthlyCharts);

// Global showToast fallback
function showToast(message, type) {
    if (typeof window.showToast === 'function') {
        window.showToast(message, type || 'info');
        return;
    }
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    const bgColor = type === 'success' ? 'bg-emerald-500' : type === 'error' ? 'bg-rose-500' : 'bg-amber-500';
    const textColor = 'text-white';
    toast.className = `px-4 py-2 rounded shadow ${bgColor} ${textColor} animate-fade-in`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => { toast.remove(); }, 4000);
}
