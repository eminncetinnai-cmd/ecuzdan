/**
 * Financial Strategy Client Logic
 * EAFGS Compliant - Monte Carlo Simulation Chart & Strategy Settings Modal
 */

(function() {
    let mcChart = null;
    let mcScenarios = {};
    let mcSuccessRates = {};
    let baseSuccessRate = 0;
    let years = 30;

    const currCode = window.BASE_CURRENCY_CODE || 'TRY';
    const currSym = window.BASE_CURRENCY_SYMBOL || '₺';
    const fmt = v => new Intl.NumberFormat('tr-TR', {
        style: 'currency',
        currency: currCode,
        maximumFractionDigits: 0
    }).format(v);

    function initPage() {
        const pageEl = document.getElementById('strategy-page');
        if (!pageEl) return;

        try {
            mcScenarios = JSON.parse(pageEl.getAttribute('data-mc-scenarios') || '{}');
            mcSuccessRates = JSON.parse(pageEl.getAttribute('data-mc-success-rates') || '{}');
            years = parseInt(pageEl.getAttribute('data-mc-years') || '30', 10);
            baseSuccessRate = parseFloat(pageEl.getAttribute('data-mc-success-rate') || '0');
        } catch (e) {
            console.error('Error parsing Monte Carlo data:', e);
        }

        buildChart('balanced');
        setupForm();

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                const modal = document.getElementById('strategySettingsModal');
                if (modal && !modal.classList.contains('hidden')) {
                    closeStrategySettings();
                }
            }
        });
    }

    function buildChart(scenarioKey) {
        const chartEl = document.getElementById('mcChart');
        if (!chartEl) return;

        if (typeof Chart === 'undefined') {
            let retryCount = 0;
            const retryInterval = setInterval(() => {
                retryCount++;
                if (typeof Chart !== 'undefined') {
                    clearInterval(retryInterval);
                    buildChart(scenarioKey);
                } else if (retryCount >= 50) {
                    clearInterval(retryInterval);
                    console.warn('[Strategy] Chart.js is not loaded');
                }
            }, 100);
            return;
        }

        const d = mcScenarios[scenarioKey] || mcScenarios[Object.keys(mcScenarios)[0]];
        if (!d) return;

        const currentYear = new Date().getFullYear();
        const labels = Array.from({ length: years + 1 }, (_, i) => i + currentYear);

        const isDark = document.documentElement.classList.contains('dark') ||
                       document.documentElement.getAttribute('data-user-theme') === 'dark' ||
                       document.documentElement.getAttribute('data-theme') === 'dark';
        const textColor = isDark ? '#94a3b8' : '#64748b';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.04)';

        const ctx = chartEl.getContext('2d');
        if (mcChart) {
            mcChart.destroy();
        }

        mcChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Medyan (En Olası)',
                        data: d.p50,
                        borderColor: '#f59e0b', // EAFGS Amber-500
                        borderWidth: 3,
                        pointRadius: 0,
                        fill: false,
                        tension: 0.35
                    },
                    {
                        label: 'Kötümser (%10)',
                        data: d.p10,
                        borderColor: 'rgba(239, 68, 68, 0.45)', // Rose-500
                        borderWidth: 1.5,
                        pointRadius: 0,
                        fill: '+1',
                        backgroundColor: 'rgba(245, 158, 11, 0.08)',
                        tension: 0.35
                    },
                    {
                        label: 'İyimser (%90)',
                        data: d.p90,
                        borderColor: 'rgba(16, 185, 129, 0.45)', // Emerald-500
                        borderWidth: 1.5,
                        pointRadius: 0,
                        fill: false,
                        tension: 0.35
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 16,
                            color: textColor,
                            font: { weight: 'bold', size: 11 }
                        }
                    },
                    tooltip: {
                        backgroundColor: isDark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(15, 23, 42, 0.90)',
                        titleFont: { size: 12, weight: 'bold' },
                        bodyFont: { size: 12 },
                        padding: 12,
                        callbacks: {
                            label: ctx => (ctx.dataset.label || '') + ': ' + fmt(ctx.parsed.y)
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: gridColor },
                        ticks: {
                            color: textColor,
                            callback: v => v >= 1e6 ? (v / 1e6).toFixed(1) + 'M ' + currSym : fmt(v),
                            font: { size: 10, weight: 'bold' }
                        }
                    },
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: textColor,
                            font: { size: 10, weight: 'bold' }
                        }
                    }
                }
            }
        });

        // İstatistik kartları
        const p10El = document.getElementById('p10-final');
        if (p10El && d.p10 && d.p10.length > 0) {
            p10El.textContent = fmt(d.p10[d.p10.length - 1]);
        }
        const p90El = document.getElementById('p90-final');
        if (p90El && d.p90 && d.p90.length > 0) {
            p90El.textContent = fmt(d.p90[d.p90.length - 1]);
        }

        // Başarı oranı rozeti
        const rate = mcSuccessRates[scenarioKey] ?? baseSuccessRate;
        const badgeEl = document.getElementById('mc-success-rate-badge');
        if (badgeEl) {
            badgeEl.textContent = '✓ %' + rate + ' Başarı Olasılığı';
        }
    }

    function switchScenario(key, btn) {
        document.querySelectorAll('.scenario-btn').forEach(b => b.classList.remove('active'));
        if (btn) btn.classList.add('active');
        buildChart(key);
    }

    function openStrategySettings() {
        const modal = document.getElementById('strategySettingsModal');
        if (!modal) return;
        modal.classList.remove('hidden');
        setTimeout(() => document.getElementById('mc_scenario')?.focus(), 100);

        const settingsUrl = (window.ECuzdanEndpoints && window.ECuzdanEndpoints.strategy && window.ECuzdanEndpoints.strategy.settings) 
            ? window.ECuzdanEndpoints.strategy.settings 
            : '/strategy/settings';

        fetch(settingsUrl)
            .then(r => r.json())
            .then(d => {
                const expEl = document.getElementById('mc_expected_return');
                if (expEl && d.mc_expected_return != null) expEl.value = (d.mc_expected_return * 100).toFixed(1);

                const volEl = document.getElementById('mc_volatility');
                if (volEl && d.mc_volatility != null) volEl.value = (d.mc_volatility * 100).toFixed(1);

                const yrEl = document.getElementById('mc_years');
                if (yrEl && d.mc_years != null) yrEl.value = d.mc_years;

                const scEl = document.getElementById('mc_scenario');
                if (scEl && d.mc_scenario) scEl.value = d.mc_scenario;

                const infEl = document.getElementById('annual_inflation');
                if (infEl && d.annual_inflation != null) infEl.value = (d.annual_inflation * 100).toFixed(1);

                const anomEl = document.getElementById('anomaly_sigma_threshold');
                if (anomEl && d.anomaly_sigma_threshold != null) anomEl.value = d.anomaly_sigma_threshold;
            })
            .catch(err => console.error('Error fetching strategy settings:', err));
    }

    function closeStrategySettings() {
        const modal = document.getElementById('strategySettingsModal');
        if (modal) modal.classList.add('hidden');
    }

    function setupForm() {
        const form = document.getElementById('strategySettingsForm');
        if (!form) return;

        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const fd = new FormData(this);
            fd.set('mc_expected_return', parseFloat(document.getElementById('mc_expected_return').value) / 100);
            fd.set('mc_volatility', parseFloat(document.getElementById('mc_volatility').value) / 100);
            fd.set('annual_inflation', parseFloat(document.getElementById('annual_inflation').value) / 100);

            const settingsUrl = (window.ECuzdanEndpoints && window.ECuzdanEndpoints.strategy && window.ECuzdanEndpoints.strategy.settings) 
                ? window.ECuzdanEndpoints.strategy.settings 
                : '/strategy/settings';

            fetch(settingsUrl, { method: 'POST', body: fd })
                .then(r => r.json())
                .then(d => {
                    if (d.status === 'success') {
                        closeStrategySettings();
                        location.reload();
                    }
                })
                .catch(err => console.error('Error saving strategy settings:', err));
        });
    }

    // Global erişim için window üzerine expose et
    window.switchScenario = switchScenario;
    window.openStrategySettings = openStrategySettings;
    window.closeStrategySettings = closeStrategySettings;
    window.addEventListener('ecuzdan:theme-changed', function() {
        if (mcChart) {
            renderMCChart();
        }
    });

    document.addEventListener('DOMContentLoaded', initPage);
})();
