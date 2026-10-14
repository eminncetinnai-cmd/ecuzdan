/**
 * Central Bank Reserves & Global Gold Holdings — Interactive Terminal Engine
 * Features: Multi-series Chart.js, Client-side Sorting, Multi-criteria Filtering, Theme Observer
 */

(function () {
    'use strict';

    let tcmbChartInstance = null;
    let fullTcmbData = null;

    /**
     * Resolve hex colors for Chart.js 2D Canvas from CSS theme tokens
     */
    function getThemeTokens() {
        const isDark = document.documentElement.classList.contains('dark') ||
            document.documentElement.getAttribute('data-theme') === 'dark';

        return {
            isDark: isDark,
            primary: isDark ? '#818cf8' : '#4f46e5',
            sky: isDark ? '#38bdf8' : '#0284c7',
            gold: isDark ? '#fbbf24' : '#d97706',
            goldLight: isDark ? 'rgba(251, 191, 36, 0.75)' : 'rgba(217, 119, 6, 0.75)',
            emerald: isDark ? '#34d399' : '#059669',
            emeraldSoft: isDark ? 'rgba(52, 211, 153, 0.15)' : 'rgba(5, 150, 105, 0.12)',
            rose: isDark ? '#f87171' : '#dc2626',
            textColor: isDark ? '#94a3b8' : '#64748b',
            textStrong: isDark ? '#f8fbff' : '#0f172a',
            gridColor: isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.05)',
            tooltipBg: isDark ? '#142238' : '#ffffff',
            tooltipTitleColor: isDark ? '#f8fbff' : '#0f172a',
            tooltipBodyColor: isDark ? '#dce7f5' : '#334155',
            tooltipBorder: isDark ? '#27374f' : '#e2e8f0'
        };
    }

    /**
     * Subtle Vertical Crosshair Line on Chart Hover (Terminal-grade visualization)
     */
    const verticalHoverLinePlugin = {
        id: 'verticalHoverLine',
        afterDraw: function (chart) {
            if (chart.tooltip && chart.tooltip._active && chart.tooltip._active.length) {
                const activePoint = chart.tooltip._active[0];
                const ctx = chart.ctx;
                const x = activePoint.element.x;
                const topY = chart.scales.y ? chart.scales.y.top : chart.chartArea.top;
                const bottomY = chart.scales.y ? chart.scales.y.bottom : chart.chartArea.bottom;

                ctx.save();
                ctx.beginPath();
                ctx.moveTo(x, topY);
                ctx.lineTo(x, bottomY);
                ctx.lineWidth = 1;
                const isDark = document.documentElement.classList.contains('dark') ||
                    document.documentElement.getAttribute('data-theme') === 'dark';
                ctx.strokeStyle = isDark ? 'rgba(255, 255, 255, 0.15)' : 'rgba(15, 23, 42, 0.12)';
                ctx.setLineDash([3, 3]);
                ctx.stroke();
                ctx.restore();
            }
        }
    };

    /**
     * Initialize TCMB Historical Reserves Multi-Series Chart
     */
    function initTcmbChart(chartData) {
        const ctx = document.getElementById('tcmbReservesChart');
        if (!ctx) return;

        if (tcmbChartInstance) {
            tcmbChartInstance.destroy();
        }

        const theme = getThemeTokens();
        fullTcmbData = chartData;

        const labels = chartData.labels || [];
        const fxData = chartData.gross_fx || [];
        const goldData = chartData.gold_usd || [];
        const netExSwapData = chartData.net_ex_swap || [];

        tcmbChartInstance = new Chart(ctx, {
            type: 'bar',
            plugins: [verticalHoverLinePlugin],
            data: {
                labels: labels,
                datasets: [
                    {
                        type: 'line',
                        label: 'Swap Hariç Net Rezerv ($ Mr)',
                        data: netExSwapData,
                        borderColor: theme.emerald,
                        backgroundColor: theme.emeraldSoft,
                        borderWidth: 2.5,
                        pointRadius: 0,
                        pointHoverRadius: 5,
                        pointBackgroundColor: theme.emerald,
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        fill: true,
                        tension: 0.35,
                        yAxisID: 'y'
                    },
                    {
                        type: 'bar',
                        label: 'Brüt Döviz Rezervi ($ Mr)',
                        data: fxData,
                        backgroundColor: theme.sky,
                        borderRadius: 4,
                        stack: 'reserves',
                        yAxisID: 'y'
                    },
                    {
                        type: 'bar',
                        label: 'Altın Rezervi ($ Mr)',
                        data: goldData,
                        backgroundColor: theme.goldLight,
                        borderRadius: 4,
                        stack: 'reserves',
                        yAxisID: 'y'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: false // Handled via interactive series buttons
                    },
                    tooltip: {
                        backgroundColor: theme.tooltipBg,
                        titleColor: theme.tooltipTitleColor,
                        bodyColor: theme.tooltipBodyColor,
                        borderColor: theme.tooltipBorder,
                        borderWidth: 1,
                        titleFont: { family: "'Outfit', sans-serif", size: 12, weight: 'bold' },
                        bodyFont: { family: "'Outfit', sans-serif", size: 11, weight: '600' },
                        padding: 12,
                        cornerRadius: 10,
                        boxPadding: 4,
                        callbacks: {
                            label: function (context) {
                                let label = context.dataset.label || '';
                                if (label) label += ': ';
                                if (context.parsed.y !== null) {
                                    label += context.parsed.y.toFixed(1) + ' Mr $';
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        border: { display: false },
                        ticks: {
                            font: { family: "'Outfit', sans-serif", size: 10, weight: '600' },
                            color: theme.textColor,
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 12
                        }
                    },
                    y: {
                        grid: {
                            color: theme.gridColor,
                            drawTicks: false
                        },
                        border: { display: false, dash: [4, 4] },
                        ticks: {
                            font: { family: "'Outfit', sans-serif", size: 10, weight: '600' },
                            color: theme.textColor,
                            callback: function (val) {
                                return val + ' Mr $';
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Set up Series Visibility Toggles (Döviz, Altın, Net Rezerv)
     */
    function setupSeriesToggles() {
        const toggleButtons = document.querySelectorAll('.series-toggle-btn');
        toggleButtons.forEach(btn => {
            btn.addEventListener('click', function () {
                const datasetIndex = parseInt(this.getAttribute('data-dataset-index'), 10);
                if (!tcmbChartInstance) return;

                const isVisible = tcmbChartInstance.isDatasetVisible(datasetIndex);
                tcmbChartInstance.setDatasetVisibility(datasetIndex, !isVisible);
                tcmbChartInstance.update();

                if (!isVisible) {
                    this.classList.add('active');
                    this.setAttribute('aria-pressed', 'true');
                } else {
                    this.classList.remove('active');
                    this.setAttribute('aria-pressed', 'false');
                }
            });
        });
    }

    /**
     * Set up Timeframe Range Filtering (6m, 1y, 2y, all)
     */
    function setupTimeframeSelector() {
        const timeframeButtons = document.querySelectorAll('.timeframe-pill-btn');
        timeframeButtons.forEach(btn => {
            btn.addEventListener('click', function () {
                timeframeButtons.forEach(b => b.classList.remove('active'));
                this.classList.add('active');

                const range = this.getAttribute('data-range');
                applyChartRange(range);
            });
        });
    }

    /**
     * Slice chart series by selected timeframe
     */
    function applyChartRange(range) {
        if (!fullTcmbData || !tcmbChartInstance) return;

        let sliceCount = 0;
        if (range === '6m') sliceCount = 6;
        else if (range === '1y') sliceCount = 12;
        else if (range === '2y') sliceCount = 24;

        const allLabels = fullTcmbData.labels || [];
        const allFx = fullTcmbData.gross_fx || [];
        const allGold = fullTcmbData.gold_usd || [];
        const allNet = fullTcmbData.net_ex_swap || [];

        if (sliceCount > 0 && sliceCount < allLabels.length) {
            tcmbChartInstance.data.labels = allLabels.slice(-sliceCount);
            tcmbChartInstance.data.datasets[0].data = allNet.slice(-sliceCount);
            tcmbChartInstance.data.datasets[1].data = allFx.slice(-sliceCount);
            tcmbChartInstance.data.datasets[2].data = allGold.slice(-sliceCount);
        } else {
            tcmbChartInstance.data.labels = allLabels;
            tcmbChartInstance.data.datasets[0].data = allNet;
            tcmbChartInstance.data.datasets[1].data = allFx;
            tcmbChartInstance.data.datasets[2].data = allGold;
        }

        tcmbChartInstance.update();
    }

    /**
     * Generic Client-Side Table Sorting Engine
     * Supports numeric values and Turkish string collation
     */
    function setupTableSorting(tableId) {
        const table = document.getElementById(tableId);
        if (!table) return;

        const headers = table.querySelectorAll('th.sortable');
        const tbody = table.querySelector('tbody');
        const collator = new Intl.Collator('tr', { numeric: true, sensitivity: 'base' });

        headers.forEach(header => {
            header.addEventListener('click', function () {
                const sortKey = this.getAttribute('data-sort');
                const currentSort = this.getAttribute('aria-sort');
                const isAsc = currentSort !== 'ascending';

                // Reset all headers
                headers.forEach(h => {
                    h.removeAttribute('aria-sort');
                    const icon = h.querySelector('.sort-icon');
                    if (icon) icon.textContent = '↕';
                });

                // Set active header
                this.setAttribute('aria-sort', isAsc ? 'ascending' : 'descending');
                const activeIcon = this.querySelector('.sort-icon');
                if (activeIcon) activeIcon.textContent = isAsc ? '▲' : '▼';

                const rows = Array.from(tbody.querySelectorAll('tr'));

                rows.sort((rowA, rowB) => {
                    const valA = rowA.getAttribute('data-' + sortKey) || '';
                    const valB = rowB.getAttribute('data-' + sortKey) || '';

                    const numA = parseFloat(valA);
                    const numB = parseFloat(valB);

                    let result = 0;
                    if (!isNaN(numA) && !isNaN(numB)) {
                        result = numA - numB;
                    } else {
                        result = collator.compare(valA, valB);
                    }

                    return isAsc ? result : -result;
                });

                // Re-append in sorted order
                rows.forEach(r => tbody.appendChild(r));
            });
        });
    }

    /**
     * Filter Global Central Banks Matrix Table
     */
    function setupGlobalTableFilter() {
        const searchInput = document.getElementById('globalTableSearch');
        const filterChips = document.querySelectorAll('.table-filter-bar .filter-chip-btn');
        const rows = document.querySelectorAll('#globalTableBody tr');
        const countDisplay = document.getElementById('matrixFilterCount');

        let activeFilter = 'all';
        let searchQuery = '';

        const G7_CODES = ['US', 'DE', 'IT', 'FR', 'JP', 'GB'];
        const EM_CODES = ['TR', 'CN', 'IN', 'RU', 'BR', 'KZ', 'SA', 'PL'];

        function applyFilters() {
            let visibleCount = 0;

            rows.forEach(row => {
                const country = row.getAttribute('data-country') || '';
                const bank = row.getAttribute('data-bank') || '';
                const code = row.getAttribute('data-code') || '';
                const rank = parseInt(row.getAttribute('data-rank') || '999', 10);
                const share = parseFloat(row.getAttribute('data-share') || '0');
                const change = parseFloat(row.getAttribute('data-change') || '0');

                // Search match
                const matchesSearch = !searchQuery ||
                    country.includes(searchQuery) ||
                    bank.includes(searchQuery) ||
                    code.toLowerCase().includes(searchQuery);

                // Category filter match
                let matchesCategory = true;
                if (activeFilter === 'top5') {
                    matchesCategory = rank <= 5;
                } else if (activeFilter === 'top10') {
                    matchesCategory = rank <= 10;
                } else if (activeFilter === 'g7') {
                    matchesCategory = G7_CODES.includes(code);
                } else if (activeFilter === 'em') {
                    matchesCategory = EM_CODES.includes(code);
                } else if (activeFilter === 'high_gold') {
                    matchesCategory = share >= 50;
                } else if (activeFilter === 'buyers') {
                    matchesCategory = change > 0;
                }

                if (matchesSearch && matchesCategory) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            if (countDisplay) {
                countDisplay.textContent = visibleCount + ' Ülke Listelendi';
            }
        }

        if (searchInput) {
            searchInput.addEventListener('input', function () {
                searchQuery = this.value.trim().toLowerCase();
                applyFilters();
            });
        }

        filterChips.forEach(chip => {
            chip.addEventListener('click', function () {
                filterChips.forEach(c => c.classList.remove('active'));
                this.classList.add('active');
                activeFilter = this.getAttribute('data-filter') || 'all';
                applyFilters();
            });
        });
    }

    /**
     * TCMB Historical Time Series Collapse & Year Filter
     */
    function setupHistoricalTable() {
        const toggleBtn = document.getElementById('btnToggleHistoricalTcmb');
        const wrap = document.getElementById('tcmbHistoricalTableWrap');
        const yearChips = document.querySelectorAll('[data-year-filter]');
        const rows = document.querySelectorAll('#tcmbMonthlyTableBody tr');

        if (toggleBtn && wrap) {
            toggleBtn.addEventListener('click', function () {
                const isHidden = wrap.style.display === 'none';
                wrap.style.display = isHidden ? '' : 'none';
                this.textContent = isHidden ? 'Gizle' : 'Göster';
                this.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
            });
        }

        yearChips.forEach(chip => {
            chip.addEventListener('click', function () {
                yearChips.forEach(c => c.classList.remove('active'));
                this.classList.add('active');

                const selectedYear = this.getAttribute('data-year-filter');
                rows.forEach(row => {
                    const rowYear = row.getAttribute('data-year');
                    if (selectedYear === 'all' || rowYear === selectedYear) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            });
        });
    }

    /**
     * Theme Observer for dynamic dark/light mode chart refreshes
     */
    function setupThemeObserver() {
        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                if (mutation.attributeName === 'class' || mutation.attributeName === 'data-theme') {
                    if (fullTcmbData) {
                        initTcmbChart(fullTcmbData);
                    }
                }
            });
        });

        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['class', 'data-theme']
        });
    }

    /**
     * Reserve Briefing Modal & Print Actions
     */
    function setupReserveBriefingModal() {
        const modal = document.getElementById('reserveBriefingModal');
        const openBtn = document.getElementById('btnOpenReserveBriefing');
        const closeBtn = document.getElementById('btnCloseReserveBriefing');
        const printBtn = document.getElementById('btnPrintReserveBriefing');
        const copyBtn = document.getElementById('btnCopyReserveBriefing');

        if (!modal) return;

        function openModal() {
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
            if (closeBtn) closeBtn.focus();
        }

        function closeModal() {
            modal.classList.add('hidden');
            document.body.style.overflow = '';
            if (openBtn) openBtn.focus();
        }

        if (openBtn) openBtn.addEventListener('click', openModal);
        if (closeBtn) closeBtn.addEventListener('click', closeModal);

        modal.addEventListener('click', function (e) {
            if (e.target === modal) closeModal();
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                closeModal();
            }
        });

        if (printBtn) {
            printBtn.addEventListener('click', function () {
                window.print();
            });
        }

        if (copyBtn) {
            copyBtn.addEventListener('click', function () {
                const textEl = document.getElementById('reserveBriefingPrintArea');
                if (!textEl) return;

                const textToCopy = textEl.innerText;
                navigator.clipboard.writeText(textToCopy).then(() => {
                    const orig = copyBtn.innerHTML;
                    copyBtn.innerHTML = '✅ Kopyalandı!';
                    setTimeout(() => { copyBtn.innerHTML = orig; }, 1500);
                }).catch(err => {
                    console.error('Clipboard copy failed:', err);
                });
            });
        }
    }

    /**
     * DOMContentLoaded Initialization
     */
    document.addEventListener('DOMContentLoaded', function () {
        const initialData = window.__RESERVES_INITIAL_DATA__;

        if (initialData && initialData.charts && initialData.charts.tcmb) {
            initTcmbChart(initialData.charts.tcmb);
        }

        setupSeriesToggles();
        setupTimeframeSelector();
        setupTableSorting('globalReservesTable');
        setupTableSorting('tcmbMonthlyTable');
        setupGlobalTableFilter();
        setupHistoricalTable();
        setupReserveBriefingModal();
        setupThemeObserver();
    });

})();
