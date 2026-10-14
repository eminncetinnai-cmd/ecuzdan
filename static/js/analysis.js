/**
 * E-Cüzdan — Analysis & Financial Health JavaScript
 * Pure Vanilla JS, No jQuery, Chart.js Integration with EAFGS Hex Standard Colors
 */

(function () {
    'use strict';

    let benchmarkChartInstance = null;
    let chartInitialized = false;

    // Standard Hex Chart Colors (EAFGS Specification - No CSS var in canvas)
    const BENCHMARK_COLORS = {
        portfolio: '#6366f1',  // Indigo-500 — Kullanıcı Portföyü
        tufe:      '#ef4444',  // Rose-500   — TÜFE Enflasyonu
        gold:      '#f59e0b',  // Amber-500  — Gram Altın
        bist:      '#0ea5e9',  // Sky-500    — BIST 100
        usd:       '#10b981'   // Emerald-500 — Dolar/TL
    };

    /**
     * Switch Tabs with URL Hash Syncing
     */
    window.switchAnalysisTab = function (tabId, updateUrl = true) {
        if (!['health', 'inflation', 'strategy'].includes(tabId)) {
            tabId = 'health';
        }

        document.querySelectorAll('.analysis-tab-btn').forEach(btn => {
            const isActive = btn.getAttribute('data-tab') === tabId;
            btn.classList.toggle('active', isActive);
            btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
        });

        document.querySelectorAll('.analysis-tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabId}-content`);
        });

        if (updateUrl && window.history && window.history.replaceState) {
            window.history.replaceState(null, '', `#${tabId}`);
        }

        if (tabId === 'inflation' && !chartInitialized) {
            initBenchmarkChart();
        }
    };

    /**
     * Animate Metric Bars
     */
    function initMetricBars() {
        const fills = document.querySelectorAll('.metric-bar-fill');
        fills.forEach(fill => {
            const targetWidth = fill.dataset.width || 0;
            setTimeout(() => {
                fill.style.width = targetWidth + '%';
            }, 150);
        });
    }

    /**
     * Animate Health Score Counter
     */
    function initScoreCounter() {
        const scoreEl = document.getElementById('scoreCounter');
        if (!scoreEl) return;

        const target = parseInt(scoreEl.textContent, 10);
        if (isNaN(target)) return;

        let current = 0;
        const increment = Math.max(1, Math.ceil(target / 30));
        const timer = setInterval(() => {
            current = Math.min(current + increment, target);
            scoreEl.textContent = current;
            if (current >= target) {
                clearInterval(timer);
            }
        }, 25);
    }

    /**
     * Initialize Inflation & Real Return Benchmark Chart
     */
    async function initBenchmarkChart() {
        const canvas = document.getElementById('inflationBenchmarkChart');
        if (!canvas || typeof Chart === 'undefined') return;

        chartInitialized = true;
        const loadingIndicator = document.getElementById('benchmarkLoading');
        if (loadingIndicator) loadingIndicator.classList.remove('hidden');

        let benchmarksData = null;
        try {
            const res = await fetch('/analysis/api/inflation_benchmarks?nominal_return=45.0');
            if (res.ok) {
                const json = await res.json();
                if (json.success && json.data) {
                    benchmarksData = json.data;
                }
            }
        } catch (e) {
            console.warn('[Analysis] Failed to fetch live benchmarks, using fallback:', e);
        } finally {
            if (loadingIndicator) loadingIndicator.classList.add('hidden');
        }

        // Default or fetched benchmarks
        const labels = ['Portföyünüz', 'TÜFE (Enflasyon)', 'Gram Altın', 'BIST 100', 'USD/TRY'];
        const values = [
            benchmarksData ? Number(benchmarksData.nominal_return || 45) : 45.0,
            benchmarksData && benchmarksData.benchmarks ? Number(benchmarksData.benchmarks.official_cpi || 58.5) : 58.5,
            benchmarksData && benchmarksData.benchmarks ? Number(benchmarksData.benchmarks.gold_return || 65.2) : 65.2,
            benchmarksData && benchmarksData.benchmarks ? Number(benchmarksData.benchmarks.stock_index_return || 52.0) : 52.0,
            benchmarksData && benchmarksData.benchmarks ? Number(benchmarksData.benchmarks.usd_return || 40.8) : 40.8
        ];

        const colors = [
            BENCHMARK_COLORS.portfolio,
            BENCHMARK_COLORS.tufe,
            BENCHMARK_COLORS.gold,
            BENCHMARK_COLORS.bist,
            BENCHMARK_COLORS.usd
        ];

        if (benchmarkChartInstance) {
            benchmarkChartInstance.destroy();
        }

        const isDark = document.documentElement.classList.contains('dark') ||
                       document.documentElement.getAttribute('data-user-theme') === 'dark' ||
                       document.documentElement.getAttribute('data-theme') === 'dark';
        const ctx = canvas.getContext('2d');

        benchmarkChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Yıllık Getiri / Enflasyon Oranı (%)',
                    data: values,
                    backgroundColor: colors,
                    borderRadius: 8,
                    borderWidth: 0,
                    barThickness: 36
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#0f172a',
                        titleColor: '#f8fafc',
                        bodyColor: '#e2e8f0',
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            label: function (ctx) {
                                return ` Oran: %${ctx.parsed.y.toFixed(1)}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: isDark ? '#334155' : '#f1f5f9'
                        },
                        ticks: {
                            color: isDark ? '#94a3b8' : '#64748b',
                            callback: function (val) {
                                return '%' + val;
                            },
                            font: {
                                size: 11,
                                weight: '600'
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: isDark ? '#cbd5e1' : '#475569',
                            font: {
                                size: 11,
                                weight: '700'
                            }
                        }
                    }
                }
            }
        });
    }

    // Initialize on DOM load
    document.addEventListener('DOMContentLoaded', function () {
        initMetricBars();
        initScoreCounter();

        // Restore tab from hash if present
        const hash = window.location.hash.replace('#', '');
        if (hash && ['health', 'inflation', 'strategy'].includes(hash)) {
            window.switchAnalysisTab(hash, false);
        }

        window.addEventListener('hashchange', function () {
            const h = window.location.hash.replace('#', '');
            if (h && ['health', 'inflation', 'strategy'].includes(h)) {
                window.switchAnalysisTab(h, false);
            }
        });

        // Re-render chart on theme change
        window.addEventListener('ecuzdan:theme-changed', function () {
            if (benchmarkChartInstance) {
                initBenchmarkChart();
            }
        });

        // Safe cleanup on page leave
        window.addEventListener('beforeunload', function () {
            if (benchmarkChartInstance) {
                benchmarkChartInstance.destroy();
                benchmarkChartInstance = null;
            }
        });
    });
})();
