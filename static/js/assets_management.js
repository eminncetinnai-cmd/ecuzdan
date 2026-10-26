/**
 * E-Cüzdan — Assets Management JavaScript (static/js/assets_management.js)
 * Isolated client logic for /assets_management page.
 */

(function () {
    'use strict';

    let currentEditingRow = null;
    let currentDeleteAssetId = null;

    function getEndpoint(name, id) {
        if (window.ECuzdanEndpoints && window.ECuzdanEndpoints.assets && typeof window.ECuzdanEndpoints.assets[name] === 'function') {
            return window.ECuzdanEndpoints.assets[name](id);
        }
        if (name === 'delete') return '/delete_asset/' + id;
        if (name === 'edit') return '/edit_asset/' + id;
        if (name === 'sell') return '/sell_asset/' + id;
        if (name === 'create') return '/new_asset';
        return '/assets';
    }

    function calculateValue() {
        const qEl = document.getElementById('quantity');
        const pEl = document.getElementById('unit_price');
        const vEl = document.getElementById('value');
        if (!qEl || !pEl || !vEl) return;

        const q = parseFloat(qEl.value) || 0;
        const p = parseFloat(pEl.value) || 0;
        const v = q * p;
        vEl.value = v.toFixed(2);

        const costInput = document.getElementById('purchase_cost');
        const form = document.getElementById('asset_form');
        if (form && !form.classList.contains('edit-mode') && costInput && !costInput.dataset.userEdited) {
            costInput.value = v > 0 ? v.toFixed(2) : '';
        }
    }

    function calculateModalValue() {
        const qEl = document.getElementById('modalQuantity');
        const pEl = document.getElementById('modalUnitPrice');
        const vEl = document.getElementById('modalValue');
        if (!qEl || !pEl || !vEl) return;

        const q = parseFloat(qEl.value) || 0;
        const p = parseFloat(pEl.value) || 0;
        vEl.value = (q * p).toFixed(2);
    }

    function calculateSellTotal() {
        const qEl = document.getElementById('sellQuantity');
        const pEl = document.getElementById('sellPrice');
        const currentQtyEl = document.getElementById('sellCurrentQuantity');
        const costEl = document.getElementById('sellPurchaseCost');
        const totalEl = document.getElementById('sellTotal');
        const profitEl = document.getElementById('sellProfit');
        const modal = document.getElementById('sellAssetModal');
        if (!qEl || !pEl || !modal) return;

        const quantity = parseFloat(qEl.value) || 0;
        const price = parseFloat(pEl.value) || 0;
        const currentQty = parseFloat(currentQtyEl?.value) || 0;
        const costPerUnit = parseFloat(modal.dataset.costPerUnit) || 0;
        const sym = modal.dataset.currency || window.BASE_CURRENCY_SYMBOL || '₺';

        const totalSale = quantity * price;
        const totalCost = quantity * costPerUnit;
        const profit = totalSale - totalCost;
        const roi = totalCost > 0 ? (profit / totalCost) * 100 : 0;
        const remainingQty = Math.max(0, currentQty - quantity);

        if (totalEl) totalEl.value = totalSale.toFixed(2);
        if (costEl) costEl.value = totalCost.toFixed(2);
        if (profitEl) profitEl.value = (profit >= 0 ? '+' : '') + profit.toFixed(2);

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
    }

    window.applySellPercentage = function (ratio) {
        const currentQtyEl = document.getElementById('sellCurrentQuantity');
        const sellQtyEl = document.getElementById('sellQuantity');
        if (!currentQtyEl || !sellQtyEl) return;
        const currentQty = parseFloat(currentQtyEl.value) || 0;
        const targetQty = currentQty * ratio;
        sellQtyEl.value = parseFloat(targetQty.toFixed(4));
        calculateSellTotal();
    };

    // Modal Helpers
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
        setVal('modalMonthlyRent', ds.monthlyRent);
        setVal('modalNotes', ds.notes);

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
        const f = document.getElementById('editAssetModalForm');
        if (f) f.reset();
    };

    window.openSellAssetModal = function (btn) {
        const ds = btn.dataset;
        const setVal = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.value = val !== undefined ? val : '';
        };

        const modal = document.getElementById('sellAssetModal');
        if (modal) {
            const totalCost = Number(ds.purchaseCost || 0);
            const totalQty = Number(ds.quantity || 1) || 1;
            modal.dataset.costPerUnit = totalQty > 0 ? (totalCost / totalQty) : 0;
            modal.dataset.currency = ds.currency || 'TRY';
        }

        setVal('sellAssetId', ds.id);
        setVal('sellAssetInfo', `${ds.type || ''} - ${ds.name || ''} (${ds.symbol || ''})`);
        setVal('sellCurrentQuantity', ds.quantity);
        setVal('sellQuantity', ds.quantity);
        setVal('sellPrice', ds.unitPrice);
        setVal('sellPurchaseCost', ds.purchaseCost);

        calculateSellTotal();
        if (window.openModal) window.openModal('sellAssetModal');
        else {
            const m = document.getElementById('sellAssetModal');
            if (m) m.classList.add('active');
        }
    };

    window.closeSellAssetModal = function () {
        if (window.closeModal) window.closeModal('sellAssetModal');
        else {
            const m = document.getElementById('sellAssetModal');
            if (m) m.classList.remove('active');
        }
        const f = document.getElementById('sellAssetModalForm');
        if (f) f.reset();
    };

    window.confirmDeleteAsset = function (assetId, assetName) {
        currentDeleteAssetId = assetId;
        const nameEl = document.getElementById('deleteAssetName');
        if (nameEl) nameEl.textContent = assetName || '—';
        if (window.openModal) window.openModal('deleteAssetModal');
        else {
            const m = document.getElementById('deleteAssetModal');
            if (m) m.classList.add('active');
        }
    };

    window.closeDeleteAssetModal = function () {
        if (window.closeModal) window.closeModal('deleteAssetModal');
        else {
            const m = document.getElementById('deleteAssetModal');
            if (m) m.classList.remove('active');
        }
        currentDeleteAssetId = null;
    };

    window.editAsset = function (btn) {
        if (currentEditingRow) {
            currentEditingRow.classList.remove('bg-emerald-100', 'dark:bg-emerald-950/40');
            currentEditingRow.classList.add('hover:bg-slate-50/30');
        }
        const row = btn.closest('tr');
        if (!row) return;
        row.classList.remove('hover:bg-slate-50/30');
        row.classList.add('bg-emerald-100', 'dark:bg-emerald-950/40');
        currentEditingRow = row;

        try {
            const data = JSON.parse(row.dataset.asset || '{}');
            fillEditFormDirect(data);
        } catch (e) {
            console.error('[AssetsManagement] Error parsing asset data:', e);
        }
    };

    function fillEditFormDirect(data) {
        const form = document.getElementById('asset_form');
        if (!form) return;

        const setField = (selector, val) => {
            const f = form.querySelector(selector);
            if (f) f.value = val !== undefined ? val : '';
        };

        setField('[name="type"]', data.type);
        setField('[name="name"]', data.name);
        setField('[name="symbol"]', data.symbol);
        setField('[name="currency"]', data.currency || 'TRY');
        setField('[name="description"]', data.description);
        setField('[name="quantity"]', data.quantity);
        setField('[name="unit_price"]', data.unit_price);
        setField('[name="value"]', data.value);
        setField('[name="risk_level"]', data.risk_level || 'Orta');
        setField('[name="liquidity"]', data.liquidity || 'Likit');
        setField('[name="sector_id"]', data.sector_id);
        setField('[name="monthly_rent"]', data.monthly_rent);
        setField('[name="notes"]', data.notes);

        const dateInput = form.querySelector('[name="purchase_date"]');
        if (dateInput) {
            dateInput.value = data.purchase_date || '';
            if (dateInput._flatpickr) {
                dateInput._flatpickr.setDate(data.purchase_date, false, 'd/m/Y');
            }
        }

        const costInput = document.getElementById('purchase_cost');
        if (costInput) {
            costInput.value = data.purchase_cost || 0;
            costInput.readOnly = true;
            costInput.classList.add('readonly-field');
            costInput.dataset.userEdited = '1';
        }

        form.action = getEndpoint('edit', data.id);
        form.classList.add('edit-mode');

        const submitBtn = document.getElementById('asset_submit_btn');
        const hint = document.getElementById('edit_hint');

        if (data.is_closed) {
            const titleEl = document.getElementById('form_title');
            const subEl = document.getElementById('form_subtitle');
            if (titleEl) titleEl.textContent = 'Varlık Kapatılmış (Salt Okunur)';
            if (subEl) subEl.textContent = 'Satılmış varlıklar düzenlenemez';
            if (hint) {
                hint.textContent = 'Bu varlık tamamen satılmış/kapatılmış. Düzenleme yapılamaz.';
                hint.className = 'text-[9px] font-bold text-rose-600 uppercase tracking-wide bg-rose-50 dark:bg-rose-950/50 p-2 rounded-lg border border-rose-100 dark:border-rose-900 md:col-span-2 lg:col-span-3';
                hint.classList.remove('hidden');
            }
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(inp => inp.disabled = true);
            if (submitBtn) submitBtn.style.display = 'none';
        } else {
            const titleEl = document.getElementById('form_title');
            const subEl = document.getElementById('form_subtitle');
            if (titleEl) titleEl.textContent = 'Varlığı Düzenle';
            if (subEl) subEl.textContent = 'Değerleme güncellemesi';
            if (hint) {
                hint.textContent = 'Düzenleme modu: alış maliyeti korunur, değer değişikliği deftere işlenir.';
                hint.className = 'text-[9px] font-bold text-amber-600 uppercase tracking-wide bg-amber-50 dark:bg-amber-950/50 p-2 rounded-lg border border-amber-100 dark:border-amber-900 md:col-span-2 lg:col-span-3';
                hint.classList.remove('hidden');
            }
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(inp => { if (inp.id !== 'value' && inp.id !== 'purchase_cost') inp.disabled = false; });
            if (submitBtn) {
                submitBtn.textContent = 'VARLIĞI GÜNCELLE';
                submitBtn.classList.add('ring-4', 'ring-emerald-300');
                submitBtn.style.display = 'block';
            }
        }

        const cancelBtn = document.getElementById('asset_cancel_btn');
        if (cancelBtn) cancelBtn.classList.remove('hidden');

        const card = form.closest('.asset-card');
        if (card) {
            card.classList.add('ring-2', 'ring-emerald-400');
            setTimeout(() => card.classList.remove('ring-2', 'ring-emerald-400'), 2000);
        }
    }

    window.cancelEdit = function () {
        if (currentEditingRow) {
            currentEditingRow.classList.remove('bg-emerald-100', 'dark:bg-emerald-950/40');
            currentEditingRow.classList.add('hover:bg-slate-50/30');
            currentEditingRow = null;
        }

        const form = document.getElementById('asset_form');
        if (!form) return;
        form.reset();
        form.action = getEndpoint('create');
        form.classList.remove('edit-mode');

        const qEl = document.getElementById('quantity');
        if (qEl) qEl.value = '1';

        const costInput = document.getElementById('purchase_cost');
        if (costInput) {
            costInput.readOnly = false;
            costInput.classList.remove('readonly-field');
            delete costInput.dataset.userEdited;
        }

        const titleEl = document.getElementById('form_title');
        const subEl = document.getElementById('form_subtitle');
        if (titleEl) titleEl.textContent = 'Yeni Varlık';
        if (subEl) subEl.textContent = 'Tek pozisyon, 1 kayıt';

        const hint = document.getElementById('edit_hint');
        if (hint) {
            hint.classList.add('hidden');
        }

        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(inp => { if (inp.id !== 'value') inp.disabled = false; });

        const submitBtn = document.getElementById('asset_submit_btn');
        if (submitBtn) {
            submitBtn.textContent = 'VARLIĞI KAYDET';
            submitBtn.classList.remove('ring-4', 'ring-emerald-300');
            submitBtn.style.display = 'block';
        }

        const cancelBtn = document.getElementById('asset_cancel_btn');
        if (cancelBtn) cancelBtn.classList.add('hidden');

        calculateValue();
    };

    function initAssetsManagement() {
        calculateValue();

        const costEl = document.getElementById('purchase_cost');
        if (costEl) {
            costEl.addEventListener('input', function () {
                this.dataset.userEdited = '1';
            });
        }

        const qEl = document.getElementById('quantity');
        const pEl = document.getElementById('unit_price');
        if (qEl) qEl.addEventListener('input', calculateValue);
        if (pEl) pEl.addEventListener('input', calculateValue);

        const mqEl = document.getElementById('modalQuantity');
        const mpEl = document.getElementById('modalUnitPrice');
        if (mqEl) mqEl.addEventListener('input', calculateModalValue);
        if (mpEl) mpEl.addEventListener('input', calculateModalValue);

        const sqEl = document.getElementById('sellQuantity');
        const spEl = document.getElementById('sellPrice');
        if (sqEl) sqEl.addEventListener('input', calculateSellTotal);
        if (spEl) spEl.addEventListener('input', calculateSellTotal);

        // Delete confirmation
        const deleteConfirmBtn = document.getElementById('deleteAssetConfirmBtn');
        if (deleteConfirmBtn) {
            deleteConfirmBtn.addEventListener('click', function () {
                if (!currentDeleteAssetId) return;

                const formData = new FormData();
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content
                    || document.querySelector('input[name="csrf_token"]')?.value;
                if (csrfToken) {
                    formData.append('csrf_token', csrfToken);
                }

                fetch(getEndpoint('delete', currentDeleteAssetId), {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json',
                    },
                    body: formData,
                })
                    .then(async response => {
                        const data = await response.json().catch(() => null);
                        if (!data) throw new Error('Sunucu yanıtı okunamadı');
                        return data;
                    })
                    .then(data => {
                        if (data.success) {
                            if (window.showToast) window.showToast(data.message || 'Varlık silindi', 'success');
                            window.closeDeleteAssetModal();
                            window.location.reload();
                        } else {
                            if (window.showToast) window.showToast(data.message || 'Silme başarısız', 'error');
                            window.closeDeleteAssetModal();
                        }
                    })
                    .catch(error => {
                        console.error('[AssetsManagement] Delete error:', error);
                        if (window.showToast) window.showToast('Silme sırasında bir hata oluştu.', 'error');
                        window.closeDeleteAssetModal();
                    });
            });
        }

        // Sell asset AJAX
        const sellForm = document.getElementById('sellAssetModalForm');
        if (sellForm) {
            sellForm.addEventListener('submit', function (e) {
                e.preventDefault();
                if (sellForm.dataset.submitting === 'true') return;
                sellForm.dataset.submitting = 'true';

                const submitBtn = sellForm.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.classList.add('opacity-75', 'pointer-events-none');
                    if (!submitBtn.dataset.originalHtml) submitBtn.dataset.originalHtml = submitBtn.innerHTML;
                    submitBtn.innerHTML = '<span class="inline-block animate-spin mr-1.5" aria-hidden="true">⏳</span> <span>İşleniyor...</span>';
                }

                const unlockSellBtn = () => {
                    sellForm.dataset.submitting = 'false';
                    delete sellForm.dataset.submitting;
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.classList.remove('opacity-75', 'pointer-events-none');
                        if (submitBtn.dataset.originalHtml) {
                            submitBtn.innerHTML = submitBtn.dataset.originalHtml;
                            delete submitBtn.dataset.originalHtml;
                        }
                    }
                };

                const assetId = document.getElementById('sellAssetId')?.value;
                const formData = new FormData(this);

                fetch(getEndpoint('sell', assetId), {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    },
                    body: formData
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            if (window.showToast) window.showToast(data.message || 'Varlık satıldı', 'success');
                            setTimeout(() => {
                                window.closeSellAssetModal();
                                window.location.reload();
                            }, 1200);
                        } else {
                            unlockSellBtn();
                            if (window.showToast) window.showToast(data.message || 'Bir hata oluştu', 'error');
                        }
                    })
                    .catch(err => {
                        unlockSellBtn();
                        console.error('[AssetsManagement] Sell error:', err);
                        if (window.showToast) window.showToast('Bir hata oluştu.', 'error');
                    });
            });
        }

        // Edit asset modal AJAX
        const editModalForm = document.getElementById('editAssetModalForm');
        if (editModalForm) {
            editModalForm.addEventListener('submit', function (e) {
                e.preventDefault();
                if (editModalForm.dataset.submitting === 'true') return;
                editModalForm.dataset.submitting = 'true';

                const submitBtn = editModalForm.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.classList.add('opacity-75', 'pointer-events-none');
                    if (!submitBtn.dataset.originalHtml) submitBtn.dataset.originalHtml = submitBtn.innerHTML;
                    submitBtn.innerHTML = '<span class="inline-block animate-spin mr-1.5" aria-hidden="true">⏳</span> <span>Kaydediliyor...</span>';
                }

                const unlockEditBtn = () => {
                    editModalForm.dataset.submitting = 'false';
                    delete editModalForm.dataset.submitting;
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.classList.remove('opacity-75', 'pointer-events-none');
                        if (submitBtn.dataset.originalHtml) {
                            submitBtn.innerHTML = submitBtn.dataset.originalHtml;
                            delete submitBtn.dataset.originalHtml;
                        }
                    }
                };

                const assetId = document.getElementById('modalAssetId')?.value;
                const formData = new FormData(this);

                fetch(getEndpoint('edit', assetId), {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    },
                    body: formData
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            window.closeAssetModal();
                            window.location.reload();
                        } else {
                            unlockEditBtn();
                            if (window.showToast) window.showToast(data.message || 'Bir hata oluştu', 'error');
                        }
                    })
                    .catch(err => {
                        unlockEditBtn();
                        console.error('[AssetsManagement] Edit modal error:', err);
                        if (window.showToast) window.showToast('Bir hata oluştu.', 'error');
                    });
            });
        }

        // DataTables init if jQuery and DataTables exist
        if (window.jQuery && $.fn.DataTable && document.getElementById('assetTable')) {
            const table = $('#assetTable').DataTable({
                order: [[2, 'desc']],
                pageLength: 50,
                lengthMenu: [[25, 50, 100, -1], [25, 50, 100, 'Tümü']],
                dom: '<"flex flex-wrap justify-between items-center gap-2 mb-3"lip>rtip',
                columnDefs: [
                    { orderable: false, targets: [6] }
                ],
                language: {
                    emptyTable: 'Kayıt bulunamadı',
                    info: '_TOTAL_ kayıttan _START_ - _END_ arası gösteriliyor',
                    infoEmpty: 'Kayıt yok',
                    lengthMenu: 'Sayfada _MENU_ kayıt göster',
                    paginate: { next: 'Sonraki', previous: 'Önceki' }
                }
            });

            const filterFn = function (settings, data, dataIndex) {
                if (settings.nTable.id !== 'assetTable') return true;
                const row = table.row(dataIndex).node();
                const $row = $(row);
                const type = $('#assetFilterType').val();
                const risk = $('#assetFilterRisk').val();
                const liquidity = $('#assetFilterLiquidity').val();
                const q = ($('#assetSearch').val() || '').toLowerCase().trim();
                if (type && $row.data('type') !== type) return false;
                if (risk && $row.data('risk') !== risk) return false;
                if (liquidity && $row.data('liquidity') !== liquidity) return false;
                if (q && ($row.data('search') || '').indexOf(q) === -1) return false;
                return true;
            };

            $.fn.dataTable.ext.search.push(filterFn);

            $('#assetSearch, #assetFilterType, #assetFilterRisk, #assetFilterLiquidity').on('keyup change', function () {
                table.draw();
            });
        }

        // Auto open edit from server if edit_id is passed
        const pageData = document.getElementById('assets-management-page');
        if (pageData) {
            try {
                const editId = pageData.getAttribute('data-edit-id');
                const editAssetData = JSON.parse(pageData.getAttribute('data-edit-asset-data') || '{}');
                if (editId && editAssetData && Object.keys(editAssetData).length > 0) {
                    fillEditFormDirect(editAssetData);
                }
            } catch (e) {
                console.error('[AssetsManagement] Server edit data error:', e);
            }
        }
    }

    document.addEventListener('DOMContentLoaded', initAssetsManagement);
})();
