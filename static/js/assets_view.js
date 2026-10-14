/**
 * E-Cüzdan — Assets View Page JavaScript (static/js/assets_view.js)
 * Isolated client logic: Delete modal, Edit modal, Sell modal, and Chart.js Doughnut visualizations.
 * Follows EAFGS Hex Standard (Prevents Solid Black Bug on canvas).
 */

(function () {
    'use strict';

    // Standard Hex Chart Colors (EAFGS Specification - No CSS var in canvas)
    const CHART_PALETTE = [
        '#0ea5e9', // Sky-500 (Hisse / Menkul)
        '#f59e0b', // Amber-500 (Altın / Kıymetli Maden)
        '#10b981', // Emerald-500 (Nakit / Döviz)
        '#6366f1', // Indigo-500 (Fon)
        '#8b5cf6', // Violet-500 (Kripto)
        '#ec4899', // Pink-500 (Gayrimenkul)
        '#14b8a6', // Teal-500 (Mevduat)
        '#64748b'  // Slate-500 (Diğer)
    ];

    const RISK_COLORS = {
        'Düşük': '#10b981',
        'Orta': '#f59e0b',
        'Yüksek': '#ef4444'
    };

    let currentDeleteAssetId = null;
    let currentSellAssetId = null;
    let currentSellMaxQty = 0;
    let currentSellCostPrice = 0;
    let currentSellCurrency = '₺';

    function formatMoneyTr(val) {
        const n = Number(val) || 0;
        const symbol = window.BASE_CURRENCY_SYMBOL || '₺';
        return n.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' ' + symbol;
    }

    function getEndpoint(action, id) {
        if (window.ECuzdanEndpoints && window.ECuzdanEndpoints.assets && typeof window.ECuzdanEndpoints.assets[action] === 'function') {
            return window.ECuzdanEndpoints.assets[action](id);
        }
        if (action === 'delete') return '/delete_asset/' + id;
        if (action === 'edit') return '/edit_asset/' + id;
        if (action === 'sell') return '/sell_asset/' + id;
        return '/assets_view';
    }

    // ─── Silme Modal İşlemleri ─────────────────────────────────────────────
    window.confirmDeleteAsset = function (assetId, assetName) {
        const nameEl = document.getElementById('deleteAssetName');
        if (nameEl) nameEl.textContent = assetName || '—';
        currentDeleteAssetId = assetId;
        if (window.openModal) window.openModal('deleteAssetModal');
        else {
            const m = document.getElementById('deleteAssetModal');
            if (m) m.classList.remove('hidden');
        }
        return false;
    };

    window.closeDeleteModal = function () {
        if (window.closeModal) window.closeModal('deleteAssetModal');
        else {
            const m = document.getElementById('deleteAssetModal');
            if (m) m.classList.add('hidden');
        }
        currentDeleteAssetId = null;
    };

    // ─── Düzenleme Modal İşlemleri ─────────────────────────────────────────
    window.openEditAssetModal = function (btn) {
        const ds = btn.dataset;
        const setVal = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.value = val !== undefined ? val : '';
        };

        setVal('modalAssetId', ds.id);
        setVal('modalType', ds.type);
        setVal('modalName', ds.name);
        setVal('modalSymbol', ds.symbol);
        setVal('modalCurrency', ds.currency);
        setVal('modalDescription', ds.description);
        setVal('modalQuantity', ds.quantity);
        setVal('modalUnitPrice', ds.unitPrice);
        setVal('modalValue', ds.value);
        setVal('modalPurchaseDate', ds.purchaseDate);
        setVal('modalPurchaseCost', ds.purchaseCost);
        setVal('modalRiskLevel', ds.riskLevel);
        setVal('modalLiquidity', ds.liquidity);
        setVal('modalSectorId', ds.sectorId);
        setVal('modalNotes', ds.notes);

        const errorDiv = document.getElementById('modalAssetError');
        if (errorDiv) errorDiv.classList.remove('active');

        if (window.openModal) window.openModal('editAssetModal');
        else {
            const m = document.getElementById('editAssetModal');
            if (m) m.classList.add('active');
        }
    };

    window.closeAssetModal = function () {
        if (window.closeModal) window.closeModal('editAssetModal');
        else {
            const m = document.getElementById('editAssetModal');
            if (m) m.classList.remove('active');
        }
        const form = document.getElementById('editAssetModalForm');
        if (form) form.reset();
        const errorDiv = document.getElementById('modalAssetError');
        if (errorDiv) errorDiv.classList.remove('active');
    };

    window.calculateModalValue = function () {
        const qtyEl = document.getElementById('modalQuantity');
        const priceEl = document.getElementById('modalUnitPrice');
        const valEl = document.getElementById('modalValue');
        if (!qtyEl || !priceEl || !valEl) return;

        const q = parseFloat(qtyEl.value) || 0;
        const p = parseFloat(priceEl.value) || 0;
        valEl.value = (q * p).toFixed(2);
    };

    // ─── Satış Modal İşlemleri ─────────────────────────────────────────────
    window.openSellAssetModal = function (btn) {
        currentSellAssetId = btn.dataset.id;
        const name = btn.dataset.name;
        currentSellMaxQty = parseFloat(btn.dataset.quantity) || 0;
        const unitPrice = parseFloat(btn.dataset.unitPrice) || 0;
        currentSellCostPrice = parseFloat(btn.dataset.costPrice) || 0;
        currentSellCurrency = btn.dataset.currency || window.BASE_CURRENCY_SYMBOL || '₺';

        const nameEl = document.getElementById('sellAssetName');
        if (nameEl) nameEl.textContent = name || '';

        const qtyLabel = document.getElementById('sellCurrentQtyLabel');
        if (qtyLabel) qtyLabel.textContent = currentSellMaxQty.toString();

        const qtyInput = document.getElementById('sellQuantity');
        if (qtyInput) {
            qtyInput.value = currentSellMaxQty;
            qtyInput.max = currentSellMaxQty;
        }

        const unitInput = document.getElementById('sellUnitPrice');
        if (unitInput) unitInput.value = unitPrice.toFixed(2);

        window.updateSellPreview();

        const errDiv = document.getElementById('sellError');
        if (errDiv) errDiv.classList.add('hidden');

        const modal = document.getElementById('sellAssetModal');
        if (modal) modal.classList.remove('hidden');
    };

    window.closeSellModal = function () {
        const modal = document.getElementById('sellAssetModal');
        if (modal) modal.classList.add('hidden');
        const form = document.getElementById('sellAssetForm');
        if (form) form.reset();
        currentSellAssetId = null;
        currentSellCostPrice = 0;
    };

    window.setMaxSellQty = function () {
        const qtyInput = document.getElementById('sellQuantity');
        if (qtyInput) qtyInput.value = currentSellMaxQty;
        window.updateSellPreview();
    };

    window.updateSellPreview = function () {
        const qtyEl = document.getElementById('sellQuantity');
        const priceEl = document.getElementById('sellUnitPrice');
        const previewEl = document.getElementById('sellTotalPreview');
        const costPreviewEl = document.getElementById('sellCostPreview');
        const remainingPreviewEl = document.getElementById('sellRemainingQtyPreview');
        const pnlBadgeEl = document.getElementById('sellPnlBadge');
        if (!qtyEl || !priceEl || !previewEl) return;

        const qty = parseFloat(qtyEl.value) || 0;
        const p = parseFloat(priceEl.value) || 0;
        const total = qty * p;
        const cost = qty * (currentSellCostPrice || 0);
        const pnl = total - cost;
        const remainingQty = Math.max(0, currentSellMaxQty - qty);
        const sym = currentSellCurrency || window.BASE_CURRENCY_SYMBOL || '₺';
        const formatMoney = (val) => Number(val).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

        previewEl.textContent = `${formatMoney(total)} ${sym}`;
        if (costPreviewEl) {
            costPreviewEl.textContent = `${formatMoney(cost)} ${sym}`;
        }
        if (remainingPreviewEl) {
            remainingPreviewEl.textContent = remainingQty <= 0.0001
                ? 'Tamamen Kapatılacak (0 Adet)'
                : `${remainingQty.toLocaleString('tr-TR', { maximumFractionDigits: 4 })} Adet`;
        }
        if (pnlBadgeEl) {
            const pct = cost > 0 ? ((pnl / cost) * 100).toFixed(1) : '0.0';

            if (pnl > 0.005) {
                pnlBadgeEl.className = 'inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-black bg-emerald-100 text-emerald-800 dark:bg-emerald-950/70 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800';
                pnlBadgeEl.textContent = `+${formatMoney(pnl)} ${sym} (%+${pct}) Kâr`;
            } else if (pnl < -0.005) {
                pnlBadgeEl.className = 'inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-black bg-rose-100 text-rose-800 dark:bg-rose-950/70 dark:text-rose-300 border border-rose-200 dark:border-rose-800';
                pnlBadgeEl.textContent = `${formatMoney(pnl)} ${sym} (%${pct}) Zarar`;
            } else {
                pnlBadgeEl.className = 'inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-black bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-600';
                pnlBadgeEl.textContent = `0,00 ${sym} (Başa baş)`;
            }
        }
    };

    window.submitSellAsset = function (e) {
        e.preventDefault();
        const form = document.getElementById('sellAssetForm');
        if (!form) return;
        const formData = new FormData(form);
        const errorDiv = document.getElementById('sellError');
        const btn = document.getElementById('sellConfirmBtn');

        if (errorDiv) errorDiv.classList.add('hidden');
        if (btn) {
            btn.disabled = true;
            btn.style.opacity = '0.7';
        }

        fetch(getEndpoint('sell', currentSellAssetId), {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.closeSellModal();
                    if (window.showToast) window.showToast(data.message || 'Satış tamamlandı', 'success');
                    setTimeout(() => window.location.reload(), 800);
                } else {
                    if (errorDiv) {
                        errorDiv.textContent = data.message || 'Satış başarısız.';
                        errorDiv.classList.remove('hidden');
                    }
                    if (btn) {
                        btn.disabled = false;
                        btn.style.opacity = '1';
                    }
                }
            })
            .catch(err => {
                console.error('[AssetsView] Sell error:', err);
                if (errorDiv) {
                    errorDiv.textContent = 'Bağlantı hatası, lütfen tekrar deneyin.';
                    errorDiv.classList.remove('hidden');
                }
                if (btn) {
                    btn.disabled = false;
                    btn.style.opacity = '1';
                }
            });
    };

    // ─── Grafiklerin Başlatılması ──────────────────────────────────────────
    function initAssetsViewCharts() {
        const pageData = document.getElementById('assets-view-page');
        if (!pageData) return;

        if (typeof Chart === 'undefined') {
            let retryCount = 0;
            const retryInterval = setInterval(() => {
                retryCount++;
                if (typeof Chart !== 'undefined') {
                    clearInterval(retryInterval);
                    initAssetsViewCharts();
                } else if (retryCount >= 50) {
                    clearInterval(retryInterval);
                    console.warn('[AssetsView] Chart.js is not loaded');
                }
            }, 100);
            return;
        }

        const isDark = document.documentElement.classList.contains('dark') ||
                       document.documentElement.getAttribute('data-user-theme') === 'dark' ||
                       document.documentElement.getAttribute('data-theme') === 'dark';
        const borderColor = isDark ? '#1e293b' : '#ffffff';
        const textColor = isDark ? '#cbd5e1' : '#475569';

        try {
            // Varlık Tipi Dağılımı
            const typeLabels = JSON.parse(pageData.getAttribute('data-type-labels') || '[]');
            const typeValues = JSON.parse(pageData.getAttribute('data-type-values') || '[]');
            const typeCanvas = document.getElementById('typePieChart');

            if (typeCanvas && typeLabels.length > 0) {
                if (typeof Chart.getChart === 'function' && Chart.getChart(typeCanvas)) {
                    Chart.getChart(typeCanvas).destroy();
                }
                const bgColors = typeLabels.map((_, i) => CHART_PALETTE[i % CHART_PALETTE.length]);
                new Chart(typeCanvas, {
                    type: 'doughnut',
                    data: {
                        labels: typeLabels,
                        datasets: [{
                            data: typeValues.map(v => Number(v) || 0),
                            backgroundColor: bgColors,
                            borderWidth: 2,
                            borderColor: borderColor
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '70%',
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    boxWidth: 12,
                                    font: { size: 10, weight: 'bold' },
                                    padding: 15,
                                    color: textColor
                                }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(15, 23, 42, 0.92)',
                                titleFont: { size: 11, weight: 'bold' },
                                bodyFont: { size: 12 },
                                padding: 12,
                                callbacks: {
                                    label: function (ctx) {
                                        const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                        const pct = total > 0 ? ((ctx.parsed / total) * 100).toFixed(1) : '0.0';
                                        return ctx.label + ': ' + formatMoneyTr(ctx.parsed) + ' (' + pct + '%)';
                                    }
                                }
                            }
                        }
                    }
                });
            }

            // Risk Seviyesi Dağılımı
            const riskDataRaw = JSON.parse(pageData.getAttribute('data-risk-analysis') || '{}');
            const riskLabels = Object.keys(riskDataRaw);
            const riskValues = riskLabels.map(k => (riskDataRaw[k] && riskDataRaw[k].value) || 0);
            const riskBgColors = riskLabels.map(k => RISK_COLORS[k] || '#64748b');
            const riskCanvas = document.getElementById('riskPieChart');

            if (riskCanvas && riskValues.some(v => v > 0)) {
                if (typeof Chart.getChart === 'function' && Chart.getChart(riskCanvas)) {
                    Chart.getChart(riskCanvas).destroy();
                }
                new Chart(riskCanvas, {
                    type: 'doughnut',
                    data: {
                        labels: riskLabels,
                        datasets: [{
                            data: riskValues,
                            backgroundColor: riskBgColors,
                            borderWidth: 2,
                            borderColor: borderColor
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '70%',
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    boxWidth: 12,
                                    font: { size: 10, weight: 'bold' },
                                    padding: 15,
                                    color: textColor
                                }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(15, 23, 42, 0.92)',
                                titleFont: { size: 11, weight: 'bold' },
                                bodyFont: { size: 12 },
                                padding: 12,
                                callbacks: {
                                    label: function (ctx) {
                                        const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                        const pct = total > 0 ? ((ctx.parsed / total) * 100).toFixed(1) : '0.0';
                                        return ctx.label + ': ' + formatMoneyTr(ctx.parsed) + ' (' + pct + '%)';
                                    }
                                }
                            }
                        }
                    }
                });
            }
        } catch (e) {
            console.error('[AssetsView] Error initializing charts:', e);
        }
    }

    // Event listeners
    window.addEventListener('ecuzdan:theme-changed', function () {
        initAssetsViewCharts();
    });

    document.addEventListener('DOMContentLoaded', function () {
        initAssetsViewCharts();

        // Delete confirm
        const deleteConfirmBtn = document.getElementById('deleteAssetConfirmBtn');
        if (deleteConfirmBtn) {
            deleteConfirmBtn.addEventListener('click', function (e) {
                e.preventDefault();
                if (!currentDeleteAssetId) return;

                const formData = new FormData();
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content
                    || document.querySelector('input[name="csrf_token"]')?.value;
                if (csrfToken) formData.append('csrf_token', csrfToken);

                fetch(getEndpoint('delete', currentDeleteAssetId), {
                    method: 'POST',
                    headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },
                    body: formData
                })
                    .then(async response => {
                        const data = await response.json().catch(() => null);
                        if (!data) throw new Error('Sunucu yanıtı okunamadı');
                        return data;
                    })
                    .then(data => {
                        if (data.success) {
                            window.location.reload();
                        } else {
                            if (window.showToast) window.showToast('Silme başarısız: ' + (data.message || 'Bilinmeyen hata'), 'error');
                            window.closeDeleteModal();
                        }
                    })
                    .catch(error => {
                        console.error('[AssetsView] Delete error:', error);
                        if (window.showToast) window.showToast('Silme sırasında bir hata oluştu.', 'error');
                        window.closeDeleteModal();
                    });
            });
        }

        // Edit form submit
        const editForm = document.getElementById('editAssetModalForm');
        if (editForm) {
            editForm.addEventListener('submit', function (e) {
                e.preventDefault();
                const assetId = document.getElementById('modalAssetId')?.value;
                const errorDiv = document.getElementById('modalAssetError');
                const formData = new FormData(this);

                fetch(getEndpoint('edit', assetId), {
                    method: 'POST',
                    headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },
                    body: formData
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            window.closeAssetModal();
                            window.location.reload();
                        } else {
                            if (errorDiv) {
                                errorDiv.textContent = data.message || 'Bir hata oluştu';
                                errorDiv.classList.add('active');
                            }
                        }
                    })
                    .catch(error => {
                        console.error('[AssetsView] Update error:', error);
                        if (errorDiv) {
                            errorDiv.textContent = 'Güncelleme sırasında bir hata oluştu.';
                            errorDiv.classList.add('active');
                        }
                    });
            });
        }

        // Sell form input listeners
        const sellQty = document.getElementById('sellQuantity');
        const sellPrice = document.getElementById('sellUnitPrice');
        if (sellQty) sellQty.addEventListener('input', window.updateSellPreview);
        if (sellPrice) sellPrice.addEventListener('input', window.updateSellPreview);

        const sellForm = document.getElementById('sellAssetForm');
        if (sellForm) sellForm.addEventListener('submit', window.submitSellAsset);
    });
})();
