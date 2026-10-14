/**
 * Global Macro Ratios Terminal — Interactive Engine
 * Features: 20 Sparklines with Corridor Bounds, Category Heatmap Filters, Table Sorting, Live Sync
 */

(function () {
    'use strict';

    const ratioChartInstances = {};
    let globalRatiosData = [];
    let currentRange = 'all';

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
            emerald: isDark ? '#34d399' : '#059669',
            emeraldSoft: isDark ? 'rgba(52, 211, 153, 0.12)' : 'rgba(5, 150, 105, 0.08)',
            rose: isDark ? '#f87171' : '#dc2626',
            amber: isDark ? '#fbbf24' : '#d97706',
            corridorBg: isDark ? 'rgba(52, 211, 153, 0.1)' : 'rgba(5, 150, 105, 0.07)',
            textColor: isDark ? '#94a3b8' : '#64748b',
            textStrong: isDark ? '#f8fbff' : '#0f172a',
            gridColor: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.04)',
            tooltipBg: isDark ? '#142238' : '#ffffff',
            tooltipTitleColor: isDark ? '#f8fbff' : '#0f172a',
            tooltipBodyColor: isDark ? '#dce7f5' : '#334155',
            tooltipBorder: isDark ? '#27374f' : '#e2e8f0'
        };
    }

    /**
     * Initialize a single Ratio Sparkline Chart with corridor fill
     */
    function initRatioChart(ratio, theme) {
        const canvasId = 'ratioChart_' + ratio.code;
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (ratioChartInstances[ratio.code]) {
            ratioChartInstances[ratio.code].destroy();
        }

        const cdata = ratio.chart_data || {};
        let labels = cdata.labels || [];
        let values = cdata.values || [];
        let minLine = cdata.normal_min_line || [];
        let maxLine = cdata.normal_max_line || [];

        // Apply slice if range filter is active
        let sliceCount = 0;
        if (currentRange === '6m') sliceCount = 6;
        else if (currentRange === '1y') sliceCount = 12;
        else if (currentRange === '2y') sliceCount = 24;

        if (sliceCount > 0 && sliceCount < labels.length) {
            labels = labels.slice(-sliceCount);
            values = values.slice(-sliceCount);
            minLine = minLine.slice(-sliceCount);
            maxLine = maxLine.slice(-sliceCount);
        }

        // Determine line color based on signal
        let strokeColor = theme.primary;
        if (ratio.signal_status === 'HEALTHY') strokeColor = theme.emerald;
        else if (ratio.signal_status === 'ELEVATED') strokeColor = theme.rose;
        else if (ratio.signal_status === 'NEUTRAL') strokeColor = theme.amber;

        ratioChartInstances[ratio.code] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Normal Alt Eşik',
                        data: minLine,
                        borderColor: 'transparent',
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        label: 'Normal Üst Eşik',
                        data: maxLine,
                        borderColor: 'transparent',
                        pointRadius: 0,
                        backgroundColor: theme.corridorBg,
                        fill: '-1' // Fill between minLine and maxLine
                    },
                    {
                        label: ratio.name,
                        data: values,
                        borderColor: strokeColor,
                        borderWidth: 2,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        pointBackgroundColor: strokeColor,
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        fill: false,
                        tension: 0.35
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 0 },
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: theme.tooltipBg,
                        titleColor: theme.tooltipTitleColor,
                        bodyColor: theme.tooltipBodyColor,
                        borderColor: theme.tooltipBorder,
                        borderWidth: 1,
                        padding: 8,
                        cornerRadius: 8,
                        titleFont: { family: "'Outfit', sans-serif", size: 10, weight: 'bold' },
                        bodyFont: { family: "'Outfit', sans-serif", size: 10, weight: '600' },
                        callbacks: {
                            label: function (ctx) {
                                if (ctx.datasetIndex !== 2) return null;
                                return ratio.name + ': ' + ctx.parsed.y + ' ' + ratio.unit;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        display: true,
                        border: { display: false },
                        grid: { color: theme.gridColor, drawTicks: false },
                        ticks: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    let chartObserver = null;
    const PINNED_STORAGE_KEY = 'ecuzdan_pinned_ratios';

    function getPinnedCodes() {
        try {
            const raw = localStorage.getItem(PINNED_STORAGE_KEY);
            return raw ? JSON.parse(raw) : [];
        } catch (e) {
            return [];
        }
    }

    function savePinnedCodes(codes) {
        try {
            localStorage.setItem(PINNED_STORAGE_KEY, JSON.stringify(codes));
        } catch (e) {
            console.error('Failed to save pinned ratios:', e);
        }
    }

    /**
     * Initialize ratio charts with IntersectionObserver for lazy offscreen rendering
     */
    function initAllRatioCharts(ratios) {
        const theme = getThemeTokens();
        globalRatiosData = ratios;

        if ('IntersectionObserver' in window) {
            if (chartObserver) chartObserver.disconnect();

            chartObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const card = entry.target;
                        const code = card.getAttribute('data-code');
                        const ratio = globalRatiosData.find(r => r.code === code);
                        if (ratio && !ratioChartInstances[code]) {
                            initRatioChart(ratio, theme);
                        }
                        observer.unobserve(card);
                    }
                });
            }, { rootMargin: '120px 0px' });

            document.querySelectorAll('#ratiosGrid .ratio-terminal-card').forEach(card => {
                chartObserver.observe(card);
            });
        } else {
            ratios.forEach(r => {
                initRatioChart(r, theme);
            });
        }
    }

    /**
     * Category & Pinned Ratios Filtering
     */
    function setupCategoryFiltering() {
        const filterChips = document.querySelectorAll('[data-category-filter]');
        const heatmapBlocks = document.querySelectorAll('.heatmap-block');
        const cards = document.querySelectorAll('#ratiosGrid .ratio-terminal-card');
        const tableRows = document.querySelectorAll('#ratiosMatrixTableBody tr');

        function setCategory(selectedCategory) {
            filterChips.forEach(chip => {
                if (chip.getAttribute('data-category-filter') === selectedCategory) {
                    chip.classList.add('active');
                } else {
                    chip.classList.remove('active');
                }
            });

            if (selectedCategory === 'pinned') {
                const pinned = getPinnedCodes();
                let visibleCards = 0;
                cards.forEach(card => {
                    const code = card.getAttribute('data-code');
                    const isPinned = pinned.includes(code);
                    card.style.display = isPinned ? '' : 'none';
                    if (isPinned) visibleCards++;
                });

                let visibleRows = 0;
                tableRows.forEach(row => {
                    const code = row.querySelector('.font-mono')?.textContent.trim();
                    const isPinned = code && pinned.includes(code);
                    row.style.display = isPinned ? '' : 'none';
                    if (isPinned) visibleRows++;
                });

                const countDisplay = document.getElementById('tableRowCountDisplay');
                if (countDisplay) {
                    countDisplay.textContent = visibleRows + ' Sabitlenmiş Rasyo';
                }
                return;
            }

            cards.forEach(card => {
                const cardCat = card.getAttribute('data-category');
                if (selectedCategory === 'all' || cardCat === selectedCategory) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });

            let visibleCount = 0;
            tableRows.forEach(row => {
                const rowCat = row.getAttribute('data-category');
                if (selectedCategory === 'all' || rowCat === selectedCategory) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            const countDisplay = document.getElementById('tableRowCountDisplay');
            if (countDisplay) {
                countDisplay.textContent = visibleCount + ' Rasyo Listelendi';
            }
        }

        filterChips.forEach(chip => {
            chip.addEventListener('click', function () {
                const cat = this.getAttribute('data-category-filter');
                setCategory(cat);
            });
        });

        heatmapBlocks.forEach(block => {
            block.addEventListener('click', function () {
                const cat = this.getAttribute('data-category');
                setCategory(cat);

                const workspace = document.querySelector('.ratios-workspace-surface');
                if (workspace) {
                    workspace.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    }

    /**
     * Setup Interactive Pinned Ratios
     */
    function setupPinnedRatios() {
        const pinButtons = document.querySelectorAll('.btn-pin-ratio');
        const countDisplay = document.getElementById('pinnedCountDisplay');

        function updatePinnedUI() {
            const pinned = getPinnedCodes();
            if (countDisplay) {
                countDisplay.textContent = pinned.length;
            }

            pinButtons.forEach(btn => {
                const code = btn.getAttribute('data-ratio-code');
                const isPinned = pinned.includes(code);
                const card = btn.closest('.ratio-terminal-card');

                if (isPinned) {
                    btn.classList.add('pinned');
                    btn.setAttribute('title', 'Panodan Kaldır');
                    if (card) card.classList.add('is-pinned');
                } else {
                    btn.classList.remove('pinned');
                    btn.setAttribute('title', 'Göstergeyi Panoya Sabitle');
                    if (card) card.classList.remove('is-pinned');
                }
            });
        }

        pinButtons.forEach(btn => {
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                const code = this.getAttribute('data-ratio-code');
                let pinned = getPinnedCodes();

                if (pinned.includes(code)) {
                    pinned = pinned.filter(c => c !== code);
                } else {
                    pinned.push(code);
                }

                savePinnedCodes(pinned);
                updatePinnedUI();

                // If currently viewing pinned filter, refresh filter view
                const activeFilterChip = document.querySelector('.filter-chip-btn.active');
                if (activeFilterChip && activeFilterChip.getAttribute('data-category-filter') === 'pinned') {
                    activeFilterChip.click();
                }
            });
        });

        updatePinnedUI();
    }

    /**
     * Instant Live Search Filter across cards and table rows
     */
    function setupLiveSearch() {
        const searchInput = document.getElementById('ratiosLiveSearch');
        const cards = document.querySelectorAll('#ratiosGrid .ratio-terminal-card');
        const tableRows = document.querySelectorAll('#ratiosMatrixTableBody tr');
        const countDisplay = document.getElementById('tableRowCountDisplay');

        if (!searchInput) return;

        searchInput.addEventListener('input', function () {
            const q = this.value.trim().toLowerCase();
            let visibleCount = 0;

            cards.forEach(card => {
                const name = card.getAttribute('data-name') || '';
                const code = card.getAttribute('data-code') || '';
                const matches = !q || name.includes(q) || code.includes(q);
                card.style.display = matches ? '' : 'none';
            });

            tableRows.forEach(row => {
                const name = row.getAttribute('data-name') || '';
                const matches = !q || name.includes(q);
                if (matches) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            if (countDisplay) {
                countDisplay.textContent = visibleCount + ' Rasyo Listelendi';
            }
        });
    }

    /**
     * Timeframe Range Slicing
     */
    function setupRangeSelector() {
        const rangeButtons = document.querySelectorAll('.workspace-actions .timeframe-pill-btn');

        rangeButtons.forEach(btn => {
            btn.addEventListener('click', function () {
                rangeButtons.forEach(b => b.classList.remove('active'));
                this.classList.add('active');

                currentRange = this.getAttribute('data-range') || 'all';
                const theme = getThemeTokens();

                globalRatiosData.forEach(r => {
                    initRatioChart(r, theme);
                });
            });
        });
    }

    /**
     * Client-side Table Sorting Engine
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

                rows.forEach(r => tbody.appendChild(r));
            });
        });
    }

    /**
     * Live Market Sync Trigger via AJAX
     */
    function setupLiveSyncButton() {
        const syncBtn = document.getElementById('btnSyncLiveRatios');
        if (!syncBtn) return;

        syncBtn.addEventListener('click', async function () {
            const originalHtml = this.innerHTML;
            this.disabled = true;
            this.innerHTML = '<span class="mr-1.5 animate-spin">⏳</span> Güncelleniyor...';

            try {
                const csrfToken = window.CSRF_TOKEN ||
                    document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';

                const response = await fetch('/global-ratios/api/sync', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    }
                });

                const data = await response.json();
                if (data.success) {
                    this.innerHTML = '<span class="mr-1.5">✅</span> Güncellendi!';
                    setTimeout(() => {
                        window.location.reload();
                    }, 800);
                } else {
                    alert('Canlı veri senkronizasyonu başarısız: ' + (data.error || 'Bilinmeyen hata'));
                    this.innerHTML = originalHtml;
                    this.disabled = false;
                }
            } catch (err) {
                console.error('Sync error:', err);
                alert('Piyasa verileri güncellenirken ağ hatası oluştu.');
                this.innerHTML = originalHtml;
                this.disabled = false;
            }
        });
    }

    /**
     * Theme Observer for dark/light mode switches
     */
    function setupThemeObserver() {
        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                if (mutation.attributeName === 'class' || mutation.attributeName === 'data-theme') {
                    const theme = getThemeTokens();
                    globalRatiosData.forEach(r => {
                        initRatioChart(r, theme);
                    });
                }
            });
        });

        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['class', 'data-theme']
        });
    }

    /**
     * Cross-Asset Correlation Matrix Interactions
     */
    function setupCorrelationMatrix() {
        const toggleBtn = document.getElementById('btnToggleCorrelation');
        const section = document.getElementById('macroCorrelationSection');
        const cells = document.querySelectorAll('.corr-td-cell');
        const insightText = document.getElementById('corrInsightText');

        if (toggleBtn && section) {
            toggleBtn.addEventListener('click', function () {
                section.classList.toggle('is-collapsed');
                const isCollapsed = section.classList.contains('is-collapsed');
                toggleBtn.classList.toggle('active', !isCollapsed);
                if (!isCollapsed) {
                    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        }

        cells.forEach(cell => {
            function showInsight() {
                const pair = cell.getAttribute('data-pair') || '';
                const r = cell.getAttribute('data-r') || '';
                const desc = cell.getAttribute('data-desc') || '';
                if (insightText) {
                    insightText.innerHTML = '<strong>' + pair + '</strong> (r = <code>' + r + '</code>): ' + desc;
                }
            }

            cell.addEventListener('mouseenter', showInsight);
            cell.addEventListener('click', showInsight);
            cell.addEventListener('focus', showInsight);
        });
    }

    /**
     * Executive Briefing Modal & Actions
     */
    function setupExecutiveBriefingModal() {
        const modal = document.getElementById('executiveBriefingModal');
        const openBtn = document.getElementById('btnOpenBriefing');
        const closeBtn = document.getElementById('btnCloseBriefing');
        const printBtn = document.getElementById('btnPrintBriefing');
        const copyBtn = document.getElementById('btnCopyBriefing');

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
                const textEl = document.getElementById('briefingPrintArea');
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
     * Macro Alerts Center Modal & Persistence
     */
    function setupMacroAlertsModal() {
        const modal = document.getElementById('macroAlertModal');
        const openBtn = document.getElementById('btnOpenAlerts');
        const closeBtn = document.getElementById('btnCloseAlerts');
        const saveBtn = document.getElementById('btnSaveAlerts');
        const inAppCheck = document.getElementById('chkInAppAlerts');

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

        const bannerOpenBtn = document.getElementById('btnBannerOpenAlerts');
        const bannerCloseBtn = document.getElementById('btnBannerCloseAlerts');
        const banner = document.getElementById('macroElevatedBanner');

        if (openBtn) openBtn.addEventListener('click', openModal);
        if (bannerOpenBtn) bannerOpenBtn.addEventListener('click', openModal);
        if (closeBtn) closeBtn.addEventListener('click', closeModal);
        if (bannerCloseBtn && banner) {
            bannerCloseBtn.addEventListener('click', function () {
                banner.remove();
            });
        }

        modal.addEventListener('click', function (e) {
            if (e.target === modal) closeModal();
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                closeModal();
            }
        });

        if (saveBtn) {
            saveBtn.addEventListener('click', async function () {
                const csrfToken = document.querySelector('input[name="csrf_token"]')?.value ||
                    document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';

                try {
                    const res = await fetch('/global-ratios/api/alerts/config', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken
                        },
                        body: JSON.stringify({
                            enabled: true,
                            sensitivity: 'BALANCED',
                            channels: inAppCheck && inAppCheck.checked ? ['IN_APP'] : []
                        })
                    });
                    const data = await res.json();
                    if (data.success) {
                        saveBtn.innerHTML = '✅ Tercihler Kaydedildi!';
                        setTimeout(() => {
                            closeModal();
                            saveBtn.innerHTML = 'Tercihleri Kaydet';
                        }, 800);
                    }
                } catch (e) {
                    console.error('Alerts config save error:', e);
                }
            });
        }
    }

    /**
     * DOMContentLoaded Initialization
     */
    document.addEventListener('DOMContentLoaded', function () {
        const initialData = window.__GLOBAL_RATIOS_INITIAL_DATA__;

        if (initialData && initialData.ratios) {
            initAllRatioCharts(initialData.ratios);
        }

        setupCategoryFiltering();
        setupPinnedRatios();
        setupLiveSearch();
        setupRangeSelector();
        setupTableSorting('ratiosMatrixTable');
        setupLiveSyncButton();
        setupCorrelationMatrix();
        setupExecutiveBriefingModal();
        setupMacroAlertsModal();
        setupThemeObserver();
    });

})();
