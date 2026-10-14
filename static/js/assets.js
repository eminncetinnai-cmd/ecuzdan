/**
 * E-Cüzdan — Unified Assets Hub JavaScript
 * Pure Vanilla JS, No jQuery, Chart.js Integration with EAFGS Hex Standard Colors
 */

(function () {
    'use strict';

    let allocationChartInstance = null;
    let activeTypeFilter = '';

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

    /**
     * Initialize Allocation Donut Chart
     */
    function initAllocationChart() {
        const canvas = document.getElementById('assetAllocationChart');
        if (!canvas) return;

        let rawData = {};
        try {
            const dataAttr = canvas.getAttribute('data-chart-data');
            if (dataAttr) {
                rawData = JSON.parse(dataAttr);
            }
        } catch (e) {
            console.error('[Assets] Failed to parse chart data:', e);
        }

        const labels = Object.keys(rawData);
        const values = labels.map(key => {
            const item = rawData[key];
            return typeof item === 'object' && item !== null ? (item.value || 0) : Number(item || 0);
        });

        if (labels.length === 0 || values.every(v => v === 0)) {
            const placeholder = document.getElementById('chartEmptyPlaceholder');
            if (placeholder) placeholder.classList.remove('hidden');
            canvas.classList.add('hidden');
            return;
        }

        const backgroundColors = labels.map((_, idx) => CHART_PALETTE[idx % CHART_PALETTE.length]);
        const symbol = window.BASE_CURRENCY_SYMBOL || '₺';

        if (allocationChartInstance) {
            allocationChartInstance.destroy();
        }

        if (typeof Chart === 'undefined') {
            let retryCount = 0;
            const retryInterval = setInterval(() => {
                retryCount++;
                if (typeof Chart !== 'undefined') {
                    clearInterval(retryInterval);
                    initAllocationChart();
                } else if (retryCount >= 50) {
                    clearInterval(retryInterval);
                    console.warn('[Assets] Chart.js is not loaded');
                }
            }, 100);
            return;
        }

        const isDark = document.documentElement.classList.contains('dark') ||
                       document.documentElement.getAttribute('data-user-theme') === 'dark' ||
                       document.documentElement.getAttribute('data-theme') === 'dark';
        const ctx = canvas.getContext('2d');
        allocationChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: backgroundColors,
                    borderWidth: 2,
                    borderColor: isDark ? '#1e293b' : '#ffffff',
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '72%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            boxHeight: 12,
                            usePointStyle: true,
                            pointStyle: 'circle',
                            font: {
                                size: 11,
                                weight: '600',
                                family: 'inherit'
                            },
                            color: isDark ? '#cbd5e1' : '#475569',
                            padding: 12
                        }
                    },
                    tooltip: {
                        backgroundColor: '#0f172a',
                        titleColor: '#f8fafc',
                        bodyColor: '#e2e8f0',
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            label: function (context) {
                                const val = Number(context.parsed || 0);
                                const total = context.dataset.data.reduce((a, b) => a + Number(b), 0);
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                const formattedVal = val.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                                return ` ${context.label}: ${formattedVal} ${symbol} (%${pct})`;
                            }
                        }
                    }
                }
            }
        });
    }

    window.addEventListener('ecuzdan:theme-changed', function() {
        if (allocationChartInstance) {
            initAllocationChart();
        }
    });

    /**
     * Filter Table Rows & Live Recalculate Hero KPIs
     */
    function filterTable() {
        const searchInput = document.getElementById('assetSearch');
        const riskSelect = document.getElementById('assetFilterRisk');
        const liquiditySelect = document.getElementById('assetFilterLiquidity');
        const currencySelect = document.getElementById('assetFilterCurrency');

        const query = searchInput ? searchInput.value.trim().toLowerCase() : '';
        const risk = riskSelect ? riskSelect.value : '';
        const liquidity = liquiditySelect ? liquiditySelect.value : '';
        const currency = currencySelect ? currencySelect.value : '';

        const rows = document.querySelectorAll('.asset-row');
        let visibleCount = 0;
        let filteredValue = 0;
        let filteredCost = 0;
        const totalRowsCount = rows.length;

        rows.forEach(row => {
            const rowSearch = (row.dataset.search || '').toLowerCase();
            const rowType = row.dataset.type || '';
            const rowRisk = row.dataset.risk || '';
            const rowLiquidity = row.dataset.liquidity || '';
            const rowCurrency = (row.dataset.currency || 'TRY').toUpperCase();

            const matchesQuery = !query || rowSearch.includes(query);
            const matchesType = !activeTypeFilter || rowType.toLowerCase() === activeTypeFilter.toLowerCase();
            const matchesRisk = !risk || rowRisk === risk;
            const matchesLiquidity = !liquidity || rowLiquidity === liquidity;
            const matchesCurrency = !currency || rowCurrency === currency.toUpperCase();

            if (matchesQuery && matchesType && matchesRisk && matchesLiquidity && matchesCurrency) {
                row.style.display = '';
                visibleCount++;
                try {
                    const assetData = row.dataset.asset ? JSON.parse(row.dataset.asset) : null;
                    if (assetData) {
                        filteredValue += parseFloat(assetData.value) || 0;
                        filteredCost += parseFloat(assetData.purchase_cost) || 0;
                    }
                } catch (e) {
                    console.warn('[Assets] Error reading row data:', e);
                }
            } else {
                row.style.display = 'none';
            }
        });

        const counter = document.getElementById('assetVisibleCount');
        if (counter) counter.textContent = visibleCount;

        const emptyState = document.getElementById('assetTableEmptyState');
        if (emptyState) {
            emptyState.style.display = visibleCount === 0 ? '' : 'none';
        }

        // Live Hero KPI Update
        const isFiltered = (visibleCount < totalRowsCount) || Boolean(query) || Boolean(activeTypeFilter) || Boolean(risk) || Boolean(liquidity) || Boolean(currency);
        const sym = window.BASE_CURRENCY_SYMBOL || '₺';
        const formatMoney = (n) => (n || 0).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

        const heroValueEl = document.getElementById('heroTotalValue');
        const heroCostEl = document.getElementById('heroTotalCost');
        const heroGainEl = document.getElementById('heroTotalGain');
        const heroGainBadge = document.getElementById('heroGainBadge');
        const heroRoiEl = document.getElementById('heroTotalRoi');
        const heroFilterBadge = document.getElementById('heroFilterBadge');

        if (heroValueEl && isFiltered) {
            const gain = filteredValue - filteredCost;
            const roi = filteredCost > 0 ? ((gain / filteredCost) * 100) : 0;

            heroValueEl.innerHTML = `${formatMoney(filteredValue)} <span class="text-sm font-bold text-slate-400">${sym}</span>`;
            if (heroCostEl) heroCostEl.innerHTML = `${formatMoney(filteredCost)} <span class="text-sm font-bold text-slate-400">${sym}</span>`;
            if (heroGainEl) {
                heroGainEl.className = `text-2xl md:text-3xl font-black ${gain >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'} tracking-tight`;
                heroGainEl.innerHTML = `${formatMoney(gain)} <span class="text-sm font-bold opacity-75">${sym}</span>`;
            }
            if (heroGainBadge) {
                heroGainBadge.textContent = gain >= 0 ? '+Kâr' : '-Zarar';
                heroGainBadge.className = `px-2 py-0.5 rounded text-[10px] font-black uppercase ${gain >= 0 ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300' : 'bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300'}`;
            }
            if (heroRoiEl) {
                heroRoiEl.className = `text-2xl md:text-3xl font-black ${roi >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'} tracking-tight`;
                heroRoiEl.textContent = `%${roi.toFixed(2)}`;
            }
            if (heroFilterBadge) {
                heroFilterBadge.classList.remove('hidden');
                heroFilterBadge.textContent = `${visibleCount} / ${totalRowsCount} Filtrelendi`;
            }
        } else if (heroFilterBadge && !isFiltered) {
            heroFilterBadge.classList.add('hidden');
        }
    }

    function resetAssetFilters() {
        const searchInput = document.getElementById('assetSearch');
        const riskSelect = document.getElementById('assetFilterRisk');
        const liquiditySelect = document.getElementById('assetFilterLiquidity');
        const currencySelect = document.getElementById('assetFilterCurrency');
        if (searchInput) searchInput.value = '';
        if (riskSelect) riskSelect.value = '';
        if (liquiditySelect) liquiditySelect.value = '';
        if (currencySelect) currencySelect.value = '';
        activeTypeFilter = '';
        const chips = document.querySelectorAll('.asset-chip');
        chips.forEach(c => c.classList.remove('active'));
        const allChip = document.querySelector('.asset-chip[data-type-filter=""]');
        if (allChip) allChip.classList.add('active');
        filterTable();
        if (typeof window.showToast === 'function') {
            window.showToast('Varlık filtreleri sıfırlandı.', 'info');
        }
    }

    function exportAssetsToCsv() {
        const rows = document.querySelectorAll('.asset-row');
        const visibleRows = Array.from(rows).filter(r => r.style.display !== 'none');
        if (visibleRows.length === 0) {
            if (typeof window.showToast === 'function') {
                window.showToast('Dışa aktarılacak varlık bulunamadı.', 'warning');
            }
            return;
        }

        const headers = ['Tür', 'Varlık Adı', 'Sembol', 'Para Birimi', 'Adet', 'Birim Fiyat', 'Piyasa Değeri', 'Maliyet', 'Kâr/Zarar', 'ROI (%)', 'Risk Seviyesi', 'Likidite'];
        const csvRows = [headers.join(';')];

        visibleRows.forEach(row => {
            let data = null;
            try {
                data = row.dataset.asset ? JSON.parse(row.dataset.asset) : null;
            } catch (e) {}

            if (!data) return;

            const val = parseFloat(data.value) || 0;
            const cost = parseFloat(data.purchase_cost) || 0;
            const gain = val - cost;
            const roi = cost > 0 ? ((gain / cost) * 100).toFixed(2) : '0.00';

            const clean = (s) => `"${String(s || '').replace(/"/g, '""')}"`;
            csvRows.push([
                clean(data.type),
                clean(data.name),
                clean(data.symbol || ''),
                clean(data.currency || 'TRY'),
                clean(data.quantity),
                clean(data.unit_price),
                clean(val.toFixed(2)),
                clean(cost.toFixed(2)),
                clean(gain.toFixed(2)),
                clean(roi),
                clean(data.risk_level || 'Orta'),
                clean(data.liquidity || 'Likit')
            ].join(';'));
        });

        const csvContent = '\uFEFF' + csvRows.join('\r\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        const today = new Date().toISOString().slice(0, 10);
        link.setAttribute('href', url);
        link.setAttribute('download', `e_cuzdan_portfoy_${today}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        if (typeof window.showToast === 'function') {
            window.showToast(`${visibleRows.length} varlık CSV olarak indirildi.`, 'success');
        }
    }

    /**
     * Filter Chips Event Listeners
     */
    function initFilterChips() {
        const chips = document.querySelectorAll('.asset-chip');
        chips.forEach(chip => {
            chip.addEventListener('click', function () {
                chips.forEach(c => c.classList.remove('active'));
                this.classList.add('active');
                activeTypeFilter = this.getAttribute('data-type-filter') || '';
                filterTable();
            });
        });

        const searchInput = document.getElementById('assetSearch');
        if (searchInput) {
            searchInput.addEventListener('input', filterTable);
        }

        const riskSelect = document.getElementById('assetFilterRisk');
        if (riskSelect) {
            riskSelect.addEventListener('change', filterTable);
        }

        const liquiditySelect = document.getElementById('assetFilterLiquidity');
        if (liquiditySelect) {
            liquiditySelect.addEventListener('change', filterTable);
        }

        const currencySelect = document.getElementById('assetFilterCurrency');
        if (currencySelect) {
            currencySelect.addEventListener('change', filterTable);
        }
    }

    /**
     * Interactive Table Sorting
     */
    let sortCol = null;
    let sortAsc = true;

    window.sortAssetsTable = function (col) {
        if (sortCol === col) {
            sortAsc = !sortAsc;
        } else {
            sortCol = col;
            sortAsc = true;
        }

        document.querySelectorAll('.sort-indicator').forEach(ind => {
            const c = ind.getAttribute('data-sort-col');
            if (c === col) {
                ind.textContent = sortAsc ? '▲' : '▼';
            } else {
                ind.textContent = '⇅';
            }
        });

        const tbody = document.querySelector('#assetsOverviewTable tbody');
        if (!tbody) return;
        const rows = Array.from(tbody.querySelectorAll('.asset-row'));

        rows.sort((a, b) => {
            let valA, valB;
            if (col === 'type' || col === 'name') {
                valA = (a.dataset[col] || '').toLowerCase();
                valB = (b.dataset[col] || '').toLowerCase();
                return sortAsc ? valA.localeCompare(valB, 'tr') : valB.localeCompare(valA, 'tr');
            } else {
                valA = parseFloat(a.dataset[col]) || 0;
                valB = parseFloat(b.dataset[col]) || 0;
                return sortAsc ? valA - valB : valB - valA;
            }
        });

        rows.forEach(r => tbody.appendChild(r));
    };

    /**
     * Live Market Price Suggestion & Autofill
     */
    let currentDetectedLivePrice = null;

    function getLiveTickerPrices() {
        const root = document.getElementById('assets-page-root');
        if (!root) return { usd: 0, eur: 0, gold: 0 };
        const parseNum = (v) => {
            if (!v) return 0;
            let str = String(v).replace(/[^0-9.,]/g, '').trim();
            if (str.includes(',') && str.includes('.')) {
                str = str.replace(/\./g, '').replace(',', '.');
            } else if (str.includes(',')) {
                str = str.replace(',', '.');
            }
            return parseFloat(str) || 0;
        };
        return {
            usd: parseNum(root.dataset.liveUsd),
            eur: parseNum(root.dataset.liveEur),
            gold: parseNum(root.dataset.liveGold)
        };
    }

    function checkAndSuggestLivePrice() {
        const typeEl = document.getElementById('modalType');
        const symbolEl = document.getElementById('modalSymbol');
        const currEl = document.getElementById('modalCurrency');
        const btnLive = document.getElementById('btnApplyLivePrice');
        const hintEl = document.getElementById('livePriceHintText');

        if (!typeEl || !btnLive || !hintEl) return;

        const livePrices = getLiveTickerPrices();
        const typeVal = (typeEl.value || '').toLowerCase();
        const symVal = (symbolEl ? symbolEl.value : '').toUpperCase();
        const currVal = (currEl ? currEl.value : 'TRY').toUpperCase();

        let detected = null;
        let detectedLabel = '';

        if (typeVal.includes('altın') || symVal.includes('ALTIN') || symVal.includes('GRAM') || symVal.includes('XAU') || symVal === 'GA') {
            if (livePrices.gold > 0) {
                detected = livePrices.gold;
                detectedLabel = `${detected.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺`;
            }
        } else if (currVal === 'USD' || symVal.includes('USD') || symVal.includes('DOLAR')) {
            if (livePrices.usd > 0) {
                detected = livePrices.usd;
                detectedLabel = `${detected.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺`;
            }
        } else if (currVal === 'EUR' || symVal.includes('EUR') || symVal.includes('AVRO')) {
            if (livePrices.eur > 0) {
                detected = livePrices.eur;
                detectedLabel = `${detected.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺`;
            }
        }

        if (detected && detected > 0) {
            currentDetectedLivePrice = detected;
            hintEl.textContent = detectedLabel;
            btnLive.classList.remove('hidden');
        } else {
            currentDetectedLivePrice = null;
            btnLive.classList.add('hidden');
        }
    }

    window.applyLiveAssetPrice = function () {
        if (!currentDetectedLivePrice) return;
        const priceEl = document.getElementById('modalUnitPrice');
        if (priceEl) {
            priceEl.value = currentDetectedLivePrice.toFixed(2);
            window.calculateModalValue();
            if (typeof window.showToast === 'function') {
                window.showToast(`Canlı fiyat (${currentDetectedLivePrice.toFixed(2)}) birim fiyata uygulandı.`, 'info');
            }
        }
    };

    /**
     * Modal Operations
     */
    window.openAddAssetModal = function () {
        const modal = document.getElementById('assetModal');
        const form = document.getElementById('assetModalForm');
        if (!modal || !form) return;

        form.reset();
        document.getElementById('modalTitle').textContent = 'Yeni Varlık Ekle';
        document.getElementById('modalSubmitBtn').textContent = 'Varlığı Kaydet';
        document.getElementById('modalAssetId').value = '';
        form.action = '/new_asset';

        const purchaseCost = document.getElementById('modalPurchaseCost');
        if (purchaseCost) purchaseCost.readOnly = false;

        checkAndSuggestLivePrice();
        modal.classList.add('active');
        setTimeout(() => {
            const nameEl = document.getElementById('modalName');
            if (nameEl) nameEl.focus();
        }, 100);
    };

    window.openEditAssetModal = function (assetId) {
        const modal = document.getElementById('assetModal');
        const form = document.getElementById('assetModalForm');
        if (!modal || !form) return;

        let assetData = null;
        const row = document.querySelector(`.asset-row[data-asset-id="${assetId}"]`);
        if (row && row.dataset.asset) {
            try {
                assetData = JSON.parse(row.dataset.asset);
            } catch (e) {
                console.error('[Assets] Error parsing asset JSON:', e);
            }
        }

        if (!assetData) {
            console.error('[Assets] Asset not found for ID:', assetId);
            return;
        }

        document.getElementById('modalTitle').textContent = 'Varlık Düzenle';
        document.getElementById('modalSubmitBtn').textContent = 'Değişiklikleri Güncelle';
        form.action = '/update_asset';
        document.getElementById('modalAssetId').value = assetId;

        const setVal = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.value = (val !== null && val !== undefined) ? val : '';
        };

        setVal('modalType', assetData.type);
        setVal('modalName', assetData.name);
        setVal('modalSymbol', assetData.symbol);
        setVal('modalCurrency', assetData.currency || 'TRY');
        setVal('modalQuantity', assetData.quantity);
        setVal('modalUnitPrice', assetData.unit_price);
        setVal('modalValue', assetData.value);
        setVal('modalPurchaseDate', assetData.purchase_date);
        setVal('modalPurchaseCost', assetData.purchase_cost);
        setVal('modalRiskLevel', assetData.risk_level || 'Orta');
        setVal('modalLiquidity', assetData.liquidity || 'Likit');
        setVal('modalSectorId', assetData.sector_id);
        setVal('modalMonthlyRent', assetData.monthly_rent);
        setVal('modalDescription', assetData.description);
        setVal('modalNotes', assetData.notes);

        const purchaseCost = document.getElementById('modalPurchaseCost');
        if (purchaseCost) purchaseCost.readOnly = true;

        checkAndSuggestLivePrice();
        modal.classList.add('active');
        setTimeout(() => {
            const priceEl = document.getElementById('modalUnitPrice');
            if (priceEl) priceEl.focus();
        }, 100);
    };

    window.closeAssetModal = function () {
        const modal = document.getElementById('assetModal');
        if (modal) modal.classList.remove('active');
    };

    window.calculateModalValue = function () {
        const qtyEl = document.getElementById('modalQuantity');
        const priceEl = document.getElementById('modalUnitPrice');
        const valEl = document.getElementById('modalValue');
        if (!qtyEl || !priceEl || !valEl) return;

        const q = parseFloat(qtyEl.value) || 0;
        const p = parseFloat(priceEl.value) || 0;
        const total = (q * p);
        valEl.value = total.toFixed(2);

        const indicator = document.getElementById('liveCostIndicator');
        if (indicator) {
            const sym = document.getElementById('modalCurrency')?.value || window.BASE_CURRENCY_SYMBOL || '₺';
            if (total > 0) {
                indicator.textContent = `Toplam Değer: ${total.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${sym}`;
                indicator.classList.remove('hidden');
            } else {
                indicator.classList.add('hidden');
            }
        }
    };

    /**
     * Sell Asset Modal Operations
     */
    window.openSellAssetModal = function (assetId) {
        const modal = document.getElementById('sellAssetModal');
        const form = document.getElementById('sellAssetModalForm');
        if (!modal || !form) return;

        let assetData = null;
        const row = document.querySelector(`.asset-row[data-asset-id="${assetId}"]`);
        if (row && row.dataset.asset) {
            try {
                assetData = JSON.parse(row.dataset.asset);
            } catch (e) {
                console.error('[Assets] Error parsing asset JSON:', e);
            }
        }

        if (!assetData) return;

        form.reset();
        form.action = `/sell_asset/${assetId}`;
        document.getElementById('sellAssetId').value = assetId;

        const sym = assetData.currency || 'TRY';
        document.getElementById('sellAssetInfo').value = `${assetData.name} (${assetData.symbol || '—'})`;
        document.getElementById('sellCurrentQuantity').value = assetData.quantity;
        document.getElementById('sellQuantity').value = assetData.quantity;
        document.getElementById('sellQuantity').max = assetData.quantity;
        document.getElementById('sellPrice').value = assetData.unit_price;

        const costPerUnit = (Number(assetData.purchase_cost || 0) / Number(assetData.quantity || 1)) || 0;
        modal.dataset.costPerUnit = costPerUnit;
        modal.dataset.currency = sym;

        // Today's date YYYY-MM-DD
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('sellDate').value = today;

        window.calculateSellTotal();
        modal.classList.add('active');
        setTimeout(() => {
            const qtyEl = document.getElementById('sellQuantity');
            if (qtyEl) {
                qtyEl.focus();
                qtyEl.select();
            }
        }, 100);
    };

    window.closeSellAssetModal = function () {
        const modal = document.getElementById('sellAssetModal');
        if (modal) modal.classList.remove('active');
    };

    window.calculateSellTotal = function () {
        const qtyEl = document.getElementById('sellQuantity');
        const priceEl = document.getElementById('sellPrice');
        const currentQtyEl = document.getElementById('sellCurrentQuantity');
        const totalEl = document.getElementById('sellTotal');
        const profitEl = document.getElementById('sellProfit');
        const costEl = document.getElementById('sellPurchaseCost');
        const modal = document.getElementById('sellAssetModal');
        if (!qtyEl || !priceEl || !modal) return;

        const q = parseFloat(qtyEl.value) || 0;
        const p = parseFloat(priceEl.value) || 0;
        const currentQty = parseFloat(currentQtyEl?.value) || 0;
        const costPerUnit = parseFloat(modal.dataset.costPerUnit) || 0;
        const sym = modal.dataset.currency || window.BASE_CURRENCY_SYMBOL || '₺';

        const totalSale = q * p;
        const totalCost = q * costPerUnit;
        const profit = totalSale - totalCost;
        const roi = totalCost > 0 ? (profit / totalCost) * 100 : 0;
        const remainingQty = Math.max(0, currentQty - q);

        if (totalEl) totalEl.value = totalSale.toFixed(2);
        if (costEl) costEl.value = totalCost.toFixed(2);
        if (profitEl) {
            profitEl.value = (profit >= 0 ? '+' : '') + profit.toFixed(2);
            profitEl.className = 'asset-modal-input font-bold ' + (profit >= 0 ? 'text-emerald-600' : 'text-rose-600');
        }

        const formatMoney = (val) => val.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

        const totalPreview = document.getElementById('sellTotalPreview');
        if (totalPreview) totalPreview.textContent = `${formatMoney(totalSale)} ${sym}`;

        const costPreview = document.getElementById('sellCostPreview');
        if (costPreview) costPreview.textContent = `${formatMoney(totalCost)} ${sym}`;

        const remainingPreview = document.getElementById('sellRemainingQtyPreview');
        if (remainingPreview) {
            remainingPreview.textContent = remainingQty <= 0.0001
                ? 'Tamamen Kapatılacak (0 Adet)'
                : `${remainingQty.toLocaleString('tr-TR', { maximumFractionDigits: 4 })} Adet`;
        }

        const pnlBadge = document.getElementById('sellPnlBadge');
        if (pnlBadge) {
            const pnlFormatted = `${profit >= 0 ? '+' : ''}${formatMoney(profit)} ${sym}`;
            const roiFormatted = `(%${roi >= 0 ? '+' : ''}${roi.toFixed(1)})`;
            if (profit > 0.005) {
                pnlBadge.className = 'inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-black bg-emerald-100 text-emerald-800 dark:bg-emerald-950/70 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800';
                pnlBadge.textContent = `${pnlFormatted} ${roiFormatted} Kâr`;
            } else if (profit < -0.005) {
                pnlBadge.className = 'inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-black bg-rose-100 text-rose-800 dark:bg-rose-950/70 dark:text-rose-300 border border-rose-200 dark:border-rose-800';
                pnlBadge.textContent = `${pnlFormatted} ${roiFormatted} Zarar`;
            } else {
                pnlBadge.className = 'inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-black bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-600';
                pnlBadge.textContent = `0,00 ${sym} (Başa baş)`;
            }
        }
    };

    /**
     * Quick Partial Sell by Percentage
     */
    window.applySellPercentage = function (ratio) {
        const currentQtyEl = document.getElementById('sellCurrentQuantity');
        const sellQtyEl = document.getElementById('sellQuantity');
        if (!currentQtyEl || !sellQtyEl) return;
        const currentQty = parseFloat(currentQtyEl.value) || 0;
        const targetQty = currentQty * ratio;
        sellQtyEl.value = parseFloat(targetQty.toFixed(4));
        window.calculateSellTotal();
    };

    /**
     * Delete Asset Confirmation
     */
    window.confirmDeleteAsset = function (assetId, assetName) {
        const executeDelete = () => {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/delete_asset/${assetId}`;

            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrf_token';
            const csrfMeta = document.querySelector('meta[name="csrf-token"]') || document.querySelector('input[name="csrf_token"]');
            csrfInput.value = csrfMeta ? (csrfMeta.content || csrfMeta.value) : '';
            form.appendChild(csrfInput);

            document.body.appendChild(form);
            form.submit();
        };

        if (typeof window.showGlobalConfirm === 'function') {
            window.showGlobalConfirm('Varlığı Sil', `"${assetName}" adlı varlığı portföyünüzden silmek istediğinize emin misiniz? Bu işlem geri alınamaz.`, executeDelete, true);
        } else if (confirm(`"${assetName}" adlı varlığı silmek istediğinize emin misiniz?`)) {
            executeDelete();
        }
    };

    window.resetAssetFilters = resetAssetFilters;
    window.exportAssetsToCsv = exportAssetsToCsv;

    // Close modals on Escape key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            window.closeAssetModal();
            window.closeSellAssetModal();
        }
    });

    // Initialize on DOM load
    document.addEventListener('DOMContentLoaded', function () {
        initAllocationChart();
        initFilterChips();
        filterTable();

        // Listen for live price triggers on modal inputs
        const modalType = document.getElementById('modalType');
        const modalSymbol = document.getElementById('modalSymbol');
        const modalCurrency = document.getElementById('modalCurrency');
        if (modalType) modalType.addEventListener('change', checkAndSuggestLivePrice);
        if (modalSymbol) modalSymbol.addEventListener('input', checkAndSuggestLivePrice);
        if (modalCurrency) modalCurrency.addEventListener('change', checkAndSuggestLivePrice);

        // Auto-open modal if URL has ?modal=new
        try {
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('modal') === 'new') {
                window.openAddAssetModal();
            }
        } catch (e) {
            console.warn('[Assets] URL parameter parse error:', e);
        }

        // Safe cleanup on page leave
        window.addEventListener('beforeunload', function () {
            if (allocationChartInstance) {
                allocationChartInstance.destroy();
                allocationChartInstance = null;
            }
        });
    });
})();
