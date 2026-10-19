// Financial Dashboard JavaScript

// ─── Piyasa Stres Gauge ────────────────────────────────────────────────────
function initStressGauge(stressIndex) {
    const ctx = document.getElementById('stressGauge');
    if (!ctx) return;
    const val = stressIndex;
    new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [val, 100 - val],
                backgroundColor: [
                    val > 70 ? '#ef4444' : val > 40 ? '#f59e0b' : '#10b981',
                    'rgba(148,163,184,0.2)'  /* dark bg uyumlu boş segment */
                ],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '78%',
            circumference: 180,
            rotation: -90,
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            responsive: true,
            maintainAspectRatio: true
        }
    });
}

// ─── Normalize Piyasa Grafiği ─────────────────────────────────────────────
function initMainChart(assets) {
    const ctx = document.getElementById('mainChart');
    if (!ctx) return;

    const COLORS = {
        'GC=F':    'rgba(251,191,36,1)',
        'SI=F':    'rgba(156,163,175,1)',
        'CL=F':    'rgba(239,68,68,1)',
        'XU100.IS':'rgba(59,130,246,1)',
        'BTC-USD': 'rgba(249,115,22,1)',
        '^IXIC':   'rgba(16,185,129,1)'
    };

    const tickers = Object.keys(assets);

    // YTD getiri verilerinden basit çubuk grafik için normalize değerleri oluştur
    const labels = tickers.map(t => assets[t].name);
    const ytdReturns = tickers.map(t => parseFloat((assets[t].ytd_return || 0).toFixed(2)));
    const bgColors = tickers.map(t => {
        const r = assets[t].ytd_return || 0;
        return r >= 0 ? 'rgba(16,185,129,0.7)' : 'rgba(239,68,68,0.7)';
    });
    const borderColors = tickers.map(t => COLORS[t] || 'rgba(100,100,100,1)');

    new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'YTD Getiri (%)',
                data: ytdReturns,
                backgroundColor: bgColors,
                borderColor: borderColors,
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => `${ctx.parsed.y >= 0 ? '+' : ''}${ctx.parsed.y.toFixed(2)}%`
                    }
                }
            },
            scales: {
                y: {
                    grid: { color: '#e2e8f0' },  /* beyaz bg üzeri hafif gri grid */
                    ticks: {
                        font: { size: 10 },
                        color: '#334155',  /* #334155 / white → 10.1:1 ✅ */
                        callback: v => `${v >= 0 ? '+' : ''}${v}%`
                    },
                    title: {
                        display: true,
                        text: 'Toplam Getiri (%)',
                        font: { size: 10 },
                        color: '#64748b'  /* #64748b / white → 5.44:1 ✅ */
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 11, weight: '700' }, color: '#334155'  /* 10.1:1 ✅ */ }
                }
            }
        }
    });
}

// ─── Sharpe Ratio Karşılaştırma Grafiği ──────────────────────────────────
function initSharpeChart(sharpeData) {
    const ctx = document.getElementById('sharpeChart');
    if (!ctx) return;
    const data = sharpeData;
    const labels = Object.values(data).map(d => d.name);
    const values = Object.values(data).map(d => d.sharpe_ratio);
    const colors = values.map(v =>
        v > 2 ? 'rgba(16,185,129,0.8)' :
        v > 1 ? 'rgba(99,102,241,0.8)' :
        v > 0 ? 'rgba(245,158,11,0.8)' :
                'rgba(239,68,68,0.8)'
    );
    new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Sharpe Ratio',
                data: values,
                backgroundColor: colors,
                borderRadius: 6,
                borderWidth: 0
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: c => `SR: ${c.parsed.x.toFixed(2)}` } }
            },
            scales: {
                x: {
                    grid: { color: '#e2e8f0' },  /* beyaz bg üzeri hafif gri */
                    ticks: { font: { size: 10 }, color: '#334155'  /* 10.1:1 ✅ */ },
                    title: { display: true, text: 'Sharpe Ratio', font: { size: 10 }, color: '#64748b' }
                },
                y: { grid: { display: false }, ticks: { font: { size: 10, weight: '700' }, color: '#334155'  /* 10.1:1 ✅ */ } }
            }
        }
    });
}

// ─── Korelasyon Matrisi Sekme Geçişi ─────────────────────────────────────
function showCorrelation(period) {
    document.querySelectorAll('.corr-matrix-panel').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('[id^="corr-btn-"]').forEach(el => el.classList.remove('active'));
    const panel = document.getElementById('corr-matrix-' + period);
    const btn   = document.getElementById('corr-btn-' + period);
    if (panel) panel.classList.remove('hidden');
    if (btn)   btn.classList.add('active');
}

// ─── Sözlük Sekme Geçişi ──────────────────────────────────────────────────
function showGlossaryTab(tab) {
    document.querySelectorAll('.glossary-panel').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('[id^="gtab-"]').forEach(el => {
        if (!el.id.includes('panel')) el.classList.remove('active');
    });
    const panel = document.getElementById('gtab-panel-' + tab);
    const btn   = document.getElementById('gtab-' + tab);
    if (panel) panel.classList.remove('hidden');
    if (btn)   btn.classList.add('active');
}

// ─── Sözlük Arama Filtresi ────────────────────────────────────────────────
function filterGlossary(query) {
    const q = (query || '').toLowerCase().trim();
    document.querySelectorAll('.glossary-item').forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = (!q || text.includes(q)) ? '' : 'none';
    });
}

// ─── Hesap Makinası ───────────────────────────────────────────────────────
function runCalculator(type) {
    const get = id => parseFloat(document.getElementById(id)?.value) || 0;
    let result = '';
    if (type === 'sharpe') {
        const rp = get('calc-rp'), rf = get('calc-rf'), sigma = get('calc-sigma');
        if (sigma === 0) { result = 'Hata: Volatilite 0 olamaz'; }
        else {
            const sr = (rp - rf) / sigma;
            const grade = sr > 2 ? 'Üstün' : sr > 1 ? 'Kabul Edilebilir' : sr > 0 ? 'Zayıf' : 'Negatif';
            result = `Sharpe Ratio = (${rp}% − ${rf}%) / ${sigma}% = <strong>${sr.toFixed(3)}</strong> <span class="text-slate-500">(${grade})</span>`;
        }
    } else if (type === 'zscore') {
        const p = get('calc-p'), mu = get('calc-mu'), sigma = get('calc-sigma2');
        if (sigma === 0) { result = 'Hata: Standart sapma 0 olamaz'; }
        else {
            const z = (p - mu) / sigma;
            const sig = z > 2 ? '❌ SAT Sinyali' : z < -2 ? '✅ AL Sinyali' : '⏸️ TUT (Nötr)';
            result = `Z-Score = (${p} − ${mu}) / ${sigma} = <strong>${z.toFixed(3)}</strong> → ${sig}`;
        }
    } else if (type === 'real') {
        const nom = get('calc-nom'), inf = get('calc-inf');
        const real = ((1 + nom/100) / (1 + inf/100) - 1) * 100;
        const icon = real >= 0 ? '✅' : '❌';
        result = `Reel Getiri = ((1+${nom}%) / (1+${inf}%)) − 1 = <strong>${real.toFixed(2)}%</strong> ${icon}`;
    }
    const out = document.getElementById('calc-result-' + type);
    if (out) { out.innerHTML = result; out.classList.remove('hidden'); }
}

// ─── Sözlük Panel Aç/Kapat ───────────────────────────────────────────────
function toggleGlossary() {
    const panel = document.getElementById('glossary-panel');
    const icon  = document.getElementById('glossary-toggle-icon');
    if (!panel) return;
    const isHidden = panel.classList.contains('hidden');
    panel.classList.toggle('hidden', !isHidden);
    if (icon) icon.style.transform = isHidden ? 'rotate(180deg)' : '';
}

// ─── Grafik Başlatıcılar (isimli sarıcılar) ───────────────────────────────
function initMainChartWrapper()   { /* IIFE ile başlatıldı */ }
function initSharpeChartWrapper() { /* IIFE ile başlatıldı */ }
function initStressGaugeWrapper() { /* IIFE ile başlatıldı */ }

(function() {
    const pageData = document.getElementById('financial-dashboard-page');
    if (!pageData) return;
    try {
        const marketStress = parseFloat(pageData.getAttribute('data-market-stress') || '0');
        const marketAssets = JSON.parse(pageData.getAttribute('data-market-assets') || '[]');
        const sharpeRatios = JSON.parse(pageData.getAttribute('data-sharpe-ratios') || '{}');

        if (marketStress && typeof initStressGauge === 'function') {
            initStressGauge(marketStress);
        }
        if (marketAssets && (Array.isArray(marketAssets) ? marketAssets.length > 0 : Object.keys(marketAssets).length > 0) && typeof initMainChart === 'function') {
            initMainChart(marketAssets);
        }
        if (sharpeRatios && Object.keys(sharpeRatios).length > 0 && typeof initSharpeChart === 'function') {
            initSharpeChart(sharpeRatios);
        }
    } catch (e) {
        console.error('Error parsing financial dashboard data:', e);
    }
})();
