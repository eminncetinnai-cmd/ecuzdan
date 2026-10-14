/**
 * Investment Performance Client Logic
 * EAFGS Compliant - Chart.js & Dynamic Currency Handling
 */
function renderPerformanceCharts() {
    const pageData = document.getElementById('investment-performance-page');
    if (!pageData) return;

    if (typeof Chart === 'undefined') {
        let retryCount = 0;
        const retryInterval = setInterval(() => {
            retryCount++;
            if (typeof Chart !== 'undefined') {
                clearInterval(retryInterval);
                renderPerformanceCharts();
            } else if (retryCount >= 50) {
                clearInterval(retryInterval);
                console.warn('[InvestmentPerformance] Chart.js is not loaded');
            }
        }, 100);
        return;
    }

    try {
        const yearlyDataRaw = JSON.parse(pageData.getAttribute('data-yearly-data') || '{}');
        const inflationAdjRaw = JSON.parse(pageData.getAttribute('data-inflation-adjusted') || '{}');

        if (!yearlyDataRaw || Object.keys(yearlyDataRaw).length === 0) return;

        // Yılları sıralı liste olarak al
        const years = Object.keys(yearlyDataRaw).map(Number).sort((a, b) => a - b);

        // Nominal ve gerçek getiri dizileri
        const nominalReturns = years.map(y => {
            const d = yearlyDataRaw[y];
            return d ? Math.round((d.roi || 0) * 100) / 100 : 0;
        });
        const realReturns = years.map(y => {
            const d = inflationAdjRaw[y];
            return d ? Math.round((d.real_roi || 0) * 100) / 100 : 0;
        });
        const portfolioValues = years.map(y => {
            const d = yearlyDataRaw[y];
            return d ? (d.total_value || 0) : 0;
        });

        const sym = window.BASE_CURRENCY_SYMBOL || '₺';

        // Dark theme check for chart text/grid colors
        const isDark = document.documentElement.classList.contains('dark') ||
                       document.documentElement.getAttribute('data-user-theme') === 'dark' ||
                       document.documentElement.getAttribute('data-theme') === 'dark';
        const textColor = isDark ? '#94a3b8' : '#64748b';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)';

        // ── Grafik 1: Yıllık Nominal vs Gerçek Getiri ────────────────────────────
        const perfCanvas = document.getElementById('performanceChart');
        if (perfCanvas) {
            if (typeof Chart.getChart === 'function' && Chart.getChart(perfCanvas)) {
                Chart.getChart(perfCanvas).destroy();
            }
            new Chart(perfCanvas, {
                type: 'bar',
                data: {
                    labels: years,
                    datasets: [
                        {
                            label: 'Nominal Getiri %',
                            data: nominalReturns,
                            backgroundColor: 'rgba(14, 165, 233, 0.75)', // Sky-500
                            borderColor: '#0ea5e9',
                            borderWidth: 2,
                            borderRadius: 6
                        },
                        {
                            label: 'Gerçek Getiri %',
                            data: realReturns,
                            backgroundColor: 'rgba(99, 102, 241, 0.75)', // Indigo-500
                            borderColor: '#6366f1',
                            borderWidth: 2,
                            borderRadius: 6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                color: textColor,
                                font: { size: 11, weight: 'bold' }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: ctx => ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(2) + '%'
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            ticks: {
                                color: textColor,
                                font: { size: 10, weight: '600' },
                                callback: v => v + '%'
                            },
                            grid: { color: gridColor }
                        },
                        x: {
                            ticks: {
                                color: textColor,
                                font: { size: 10, weight: '600' }
                            },
                            grid: { display: false }
                        }
                    }
                }
            });
        }

        // ── Grafik 2: Portföy Değeri Gelişimi ────────────────────────────────────
        const valCanvas = document.getElementById('valueChart');
        if (valCanvas) {
            if (typeof Chart.getChart === 'function' && Chart.getChart(valCanvas)) {
                Chart.getChart(valCanvas).destroy();
            }
            new Chart(valCanvas, {
                type: 'line',
                data: {
                    labels: years,
                    datasets: [{
                        label: 'Portföy Değeri (' + sym + ')',
                        data: portfolioValues,
                        borderColor: '#10b981', // Emerald-500
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#10b981',
                        pointBorderColor: '#ffffff',
                        pointHoverRadius: 7,
                        pointRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                color: textColor,
                                font: { size: 11, weight: 'bold' }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: ctx => 'Değer: ' + new Intl.NumberFormat('tr-TR').format(ctx.parsed.y) + ' ' + sym
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                color: textColor,
                                font: { size: 10, weight: '600' },
                                callback: v => new Intl.NumberFormat('tr-TR', { notation: 'compact' }).format(v) + ' ' + sym
                            },
                            grid: { color: gridColor }
                        },
                        x: {
                            ticks: {
                                color: textColor,
                                font: { size: 10, weight: '600' }
                            },
                            grid: { display: false }
                        }
                    }
                }
            });
        }
    } catch (e) {
        console.error('Error parsing investment performance data:', e);
    }
}

// ── Table Sorting & CSV Export Logic ─────────────────────────────────────────
let perfSortCol = -1;
let perfSortAsc = true;
const PERF_COL_KEYS = ['year', 'value', 'cost', 'gain', 'roi', 'inflation', 'realRoi'];

function sortPerfTable(colIdx) {
    const tbody = document.getElementById('yearlyPerfTbody');
    if (!tbody) return;

    if (perfSortCol === colIdx) {
        perfSortAsc = !perfSortAsc;
    } else {
        perfSortCol = colIdx;
        perfSortAsc = true;
    }

    const key = PERF_COL_KEYS[colIdx];
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.sort((a, b) => {
        const valA = parseFloat(a.dataset[key]) || 0;
        const valB = parseFloat(b.dataset[key]) || 0;
        return perfSortAsc ? valA - valB : valB - valA;
    });

    rows.forEach(r => tbody.appendChild(r));

    // Update sort header icons
    const icons = document.querySelectorAll('.sort-icon-perf');
    icons.forEach((icon, idx) => {
        if (idx === colIdx) {
            icon.textContent = perfSortAsc ? '▲' : '▼';
            icon.classList.remove('opacity-40');
            icon.classList.add('opacity-100', 'text-indigo-600', 'dark:text-indigo-400');
        } else {
            icon.textContent = '↕';
            icon.classList.add('opacity-40');
            icon.classList.remove('opacity-100', 'text-indigo-600', 'dark:text-indigo-400');
        }
    });
}

function exportPerformanceCsv() {
    const table = document.getElementById('yearlyPerfTable');
    if (!table) return;

    const rows = Array.from(table.querySelectorAll('tr'));
    if (!rows.length) return;

    const csvLines = [];
    rows.forEach(row => {
        const cells = Array.from(row.querySelectorAll('th, td'));
        const rowData = cells.map(cell => {
            let text = cell.innerText.replace(/[▲▼↕]/g, '').trim();
            return '"' + text.replace(/"/g, '""') + '"';
        });
        csvLines.push(rowData.join(';'));
    });

    const csvContent = '\uFEFF' + csvLines.join('\r\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const today = new Date().toISOString().slice(0, 10);
    link.setAttribute('href', url);
    link.setAttribute('download', `yatirim_performansi_${today}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

document.addEventListener('DOMContentLoaded', renderPerformanceCharts);
window.addEventListener('ecuzdan:theme-changed', renderPerformanceCharts);

