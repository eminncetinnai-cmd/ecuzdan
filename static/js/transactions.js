/**
 * Transactions Hub Client Logic
 * EAFGS Compliant - DataTables, Lineage, Immutable Actions, QuickPay & Modal Handlers
 */

(function() {
    let txDataTable = null;

    function getUiCopy() {
        return window.transactionUiCopy || {
            tableEmpty: 'Kayıt bulunamadı.',
            tableInfo: '_TOTAL_ kayıttan _START_ - _END_ arası gösteriliyor',
            tableInfoEmpty: 'Kayıt yok',
            tableLength: '_MENU_ kayıt göster',
            tableNext: 'Sonraki',
            tablePrevious: 'Önceki',
            tableAll: 'Tümü',
            deleteTitle: 'İşlemi Sil',
            deleteConfirm: 'Bu işlemi silmek istediğinize emin misiniz?',
            deleteSuccess: 'İşlem başarıyla silindi.',
            updateSuccess: 'İşlem başarıyla güncellendi.',
            createSuccess: 'Yeni işlem başarıyla oluşturuldu.',
            genericError: 'Bir hata oluştu.'
        };
    }

    function initTransactionsTable() {
        if (typeof $ === 'undefined' || !$.fn.DataTable) {
            setTimeout(initTransactionsTable, 50);
            return;
        }

        const uiCopy = getUiCopy();
        const pageEl = document.getElementById('transactions-page-container');
        const initialTab = pageEl ? pageEl.getAttribute('data-active-tab') || 'all' : 'all';
        const initialOrder = initialTab === 'pending' ? [[0, 'asc']] : [[0, 'desc']];

        // Initialize DataTable
        txDataTable = $('#transTable').DataTable({
            autoWidth: false,
            order: initialOrder,
            pageLength: 50,
            lengthMenu: [[25, 50, 100, -1], [25, 50, 100, uiCopy.tableAll]],
            dom: '<"flex flex-wrap justify-between items-center gap-3 mb-3"l>rt<"flex flex-wrap justify-between items-center gap-3 mt-4"ip>',
            columnDefs: [
                { orderable: false, targets: [7] }
            ],
            drawCallback: function() {
                if (typeof updateLiveKpis === 'function') {
                    updateLiveKpis();
                }
                if (typeof updateBulkActionBar === 'function') {
                    updateBulkActionBar();
                }
                if (window.ECuzdanTables && typeof window.ECuzdanTables.applyDataLabels === 'function') {
                    window.ECuzdanTables.applyDataLabels('transTable');
                }
            },
            language: {
                emptyTable: uiCopy.tableEmpty,
                info: uiCopy.tableInfo,
                infoEmpty: uiCopy.tableInfoEmpty,
                lengthMenu: uiCopy.tableLength,
                paginate: { next: uiCopy.tableNext, previous: uiCopy.tablePrevious }
            }
        });

        window.txDataTable = txDataTable;
        window.currentTxTab = initialTab;
        window.currentTxDateRange = null;

        // Initialize Flatpickr for Date Range Filter
        if (typeof flatpickr !== 'undefined' && document.getElementById('txFilterDateRange')) {
            window.txFlatpickr = flatpickr('#txFilterDateRange', {
                mode: 'range',
                dateFormat: 'Y-m-d',
                altInput: true,
                altFormat: 'j M Y',
                locale: (typeof flatpickr.l10ns !== 'undefined' && flatpickr.l10ns.tr) ? flatpickr.l10ns.tr : 'default',
                onChange: function(selectedDates) {
                    if (selectedDates.length === 2) {
                        window.currentTxDateRange = selectedDates;
                        updateDateRangeIndicator(selectedDates);
                        $('.tx-date-preset-btn').removeClass('active');
                        txDataTable.draw();
                    } else if (selectedDates.length === 0) {
                        window.currentTxDateRange = null;
                        updateDateRangeIndicator(null);
                        txDataTable.draw();
                    }
                }
            });
        }

        // Custom search filter
        const filterFn = function(settings, data, dataIndex) {
            if (settings.nTable.id !== 'transTable') return true;
            const row = txDataTable.row(dataIndex).node();
            if (!row) return true;
            const $row = $(row);

            const category = $('#txFilterCategory').val();
            const type = $('#txFilterType').val();
            const status = $('#txFilterStatus').val();
            const q = ($('#txSearch').val() || '').toLowerCase().trim();

            const paidVal = pageEl ? pageEl.getAttribute('data-status-paid') || 'Ödendi' : 'Ödendi';
            const pendingVal = pageEl ? pageEl.getAttribute('data-status-pending') || 'Bekliyor' : 'Bekliyor';

            if (window.currentTxTab === 'paid' && $row.data('status') !== paidVal) return false;
            if (window.currentTxTab === 'pending' && $row.data('status') !== pendingVal) return false;
            if (window.currentTxTab === 'plan' && $row.data('source-type') !== 'plan') return false;

            if (category && $row.data('category') !== category) return false;
            if (type && $row.data('type') !== type) return false;
            if (status && $row.data('status') !== status) return false;
            if (q && ($row.data('search') || '').indexOf(q) === -1) return false;

            // Date Range Filter
            if (window.currentTxDateRange && window.currentTxDateRange.length === 2) {
                const dateOrder = $row.find('td').eq(0).attr('data-order');
                if (dateOrder) {
                    const rowDate = new Date(dateOrder);
                    const startDate = new Date(window.currentTxDateRange[0]);
                    startDate.setHours(0, 0, 0, 0);
                    const endDate = new Date(window.currentTxDateRange[1]);
                    endDate.setHours(23, 59, 59, 999);
                    if (rowDate < startDate || rowDate > endDate) return false;
                }
            }

            return true;
        };

        $.fn.dataTable.ext.search.push(filterFn);

        $('#txSearch, #txFilterCategory, #txFilterType, #txFilterStatus').on('keyup change', function() {
            txDataTable.draw();
        });

        // Event Delegations
        $('#transTable tbody').on('click', '.edit-tx-btn', function(e) {
            e.preventDefault();
            openEditModal(this);
        });

        $('#transTable tbody').on('click', '.delete-tx-btn', function(e) {
            e.preventDefault();
            const transactionId = parseInt(this.dataset.id, 10);
            deleteTransaction(transactionId);
        });

        $('#transTable tbody').on('click', '.quick-pay-tx-btn', function(e) {
            e.preventDefault();
            const btn = $(this);
            const txId = btn.data('id');
            const desc = btn.data('description') || 'İşlem';
            const amount = btn.data('amount') || '';
            const sym = window.BASE_CURRENCY_SYMBOL || '₺';

            if (btn.prop('disabled')) return;

            const confirmMsg = `"${desc}" (${amount} ${sym}) kaydını "Ödendi" olarak işaretlemek istediğinizden emin misiniz?`;

            const executeQuickPay = () => {
                btn.prop('disabled', true).addClass('opacity-50');
                const csrfToken = document.querySelector('input[name="csrf_token"]')?.value || '';
                const quickPayUrl = (window.ECuzdanEndpoints && window.ECuzdanEndpoints.transactions && window.ECuzdanEndpoints.transactions.quickPay)
                    ? window.ECuzdanEndpoints.transactions.quickPay(txId)
                    : `/transactions/${txId}/quick_pay`;

                fetch(quickPayUrl, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ csrf_token: csrfToken })
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        if (typeof window.showToast === 'function') {
                            window.showToast(data.message || 'İşlem başarıyla ödendi olarak işaretlendi.', 'success');
                        }
                        const $row = btn.closest('tr');
                        if ($row.length) {
                            $row.attr('data-status', 'Ödendi');
                            $row.data('status', 'Ödendi');

                            const statusCell = $row.find('td').eq(6);
                            if (statusCell.length) {
                                statusCell.html(`
                                    <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                                        <svg class="w-3 h-3 text-emerald-600 dark:text-emerald-400 shrink-0" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                                        Ödendi
                                    </span>
                                `);
                            }

                            const actionsContainer = $row.find('.tx-table-actions');
                            if (actionsContainer.length) {
                                btn.remove();
                                actionsContainer.find('.edit-tx-btn').remove();
                                actionsContainer.find('.delete-tx-btn').remove();

                                const txIdStr = String(txId);
                                const adjBtn = `
                                    <button data-macro="button_secondary" type="button" class="adjustment-tx-btn tx-table-action tx-table-action-adjustment"
                                            data-testid="transaction-adjustment-${txIdStr}"
                                            data-id="${txIdStr}"
                                            title="Düzeltme"
                                            aria-label="Düzeltme">
                                        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true" class="w-3.5 h-3.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m6-6H6"/></svg>
                                        <span class="hidden 2xl:inline">Düzeltme</span>
                                    </button>
                                    <button data-macro="button_secondary" type="button" class="reversal-tx-btn tx-table-action tx-table-action-reversal"
                                            data-testid="transaction-reversal-${txIdStr}"
                                            data-id="${txIdStr}"
                                            title="Ters Kayıt"
                                            aria-label="Ters Kayıt">
                                        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true" class="w-3.5 h-3.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 7H5v4m0-4 4 4m6-4a7 7 0 1 1-4.95 11.95"/></svg>
                                        <span class="hidden 2xl:inline">Ters Kayıt</span>
                                    </button>
                                `;
                                actionsContainer.append(adjBtn);
                            }

                            if (txDataTable) {
                                txDataTable.row($row).invalidate().draw(false);
                            }
                            updateLiveKpis();
                        } else {
                            setTimeout(() => window.location.reload(), 400);
                        }
                    } else {
                        btn.prop('disabled', false).removeClass('opacity-50');
                        if (typeof window.showToast === 'function') {
                            window.showToast(data.message || uiCopy.genericError, 'error');
                        }
                    }
                })
                .catch(err => {
                    console.error('Quick pay error:', err);
                    btn.prop('disabled', false).removeClass('opacity-50');
                    if (typeof window.showToast === 'function') {
                        window.showToast(uiCopy.genericError, 'error');
                    }
                });
            };

            if (typeof window.showGlobalConfirm === 'function') {
                window.showGlobalConfirm('Ödemeyi Onayla', confirmMsg, executeQuickPay, false);
            } else if (confirm(confirmMsg)) {
                executeQuickPay();
            }
        });

        // Activate initial tab if specified
        if (window.currentTxTab && window.currentTxTab !== 'all') {
            const targetBtn = document.querySelector(`.tx-tab-btn[data-tab="${window.currentTxTab}"]`);
            if (targetBtn) {
                switchTxTab(window.currentTxTab, targetBtn);
            }
        }

        // Setup Forms, Currency Sync & Accessibility
        setupForms();
        setupLineageAndImmutable();
        setupBankAccountCurrencySync();
        setupWaiAriaTabs();
    }

    function switchTxTab(tabId, btn) {
        window.currentTxTab = tabId;
        $('.tx-tab-btn').removeClass('active').attr('aria-selected', 'false');
        if (btn) {
            $(btn).addClass('active').attr('aria-selected', 'true');
        } else {
            $(`.tx-tab-btn[data-tab="${tabId}"]`).addClass('active').attr('aria-selected', 'true');
        }

        const url = new URL(window.location);
        url.searchParams.set('tab', tabId);
        window.history.replaceState({}, '', url);

        if (txDataTable) {
            // Akıllı Dinamik Sıralama: Bekleyenler için en yakın tarihli en üstte (ASC), diğer sekmeler için en yeni işlem en üstte (DESC)
            if (tabId === 'pending') {
                txDataTable.order([[0, 'asc']]);
            } else {
                txDataTable.order([[0, 'desc']]);
            }
            txDataTable.draw();
        }
    }

    function updateLiveKpis() {
        if (!txDataTable) return;
        const pageEl = document.getElementById('transactions-page-container');
        const paidVal = pageEl ? pageEl.getAttribute('data-status-paid') || 'Ödendi' : 'Ödendi';
        const pendingVal = pageEl ? pageEl.getAttribute('data-status-pending') || 'Bekliyor' : 'Bekliyor';
        const sym = window.BASE_CURRENCY_SYMBOL || '₺';

        const totalCountEl = document.getElementById('summaryTotalCount');
        const countsSubEl = document.getElementById('summaryCountsSub');
        const paidIncomeEl = document.getElementById('summaryPaidIncome');
        const paidExpenseEl = document.getElementById('summaryPaidExpense');
        const paidNetEl = document.getElementById('summaryPaidNet');
        const netDotEl = document.getElementById('summaryNetDot');
        const pendingExpenseEl = document.getElementById('summaryPendingExpense');
        const pendingSubEl = document.getElementById('summaryPendingSub');
        const filterBadge = document.getElementById('txActiveFilterBadge');

        if (!totalCountEl) return;

        const filteredRows = txDataTable.rows({ search: 'applied' }).nodes();
        const visibleCount = filteredRows.length;
        const totalCount = txDataTable.rows().nodes().length;

        let paidCount = 0;
        let pendingCount = 0;
        let paidIncome = 0;
        let paidExpense = 0;
        let pendingExpense = 0;

        for (let i = 0; i < filteredRows.length; i++) {
            const row = filteredRows[i];
            const st = row.getAttribute('data-status');
            const tp = row.getAttribute('data-type');
            const amt = parseFloat(row.getAttribute('data-amount')) || 0;

            if (st === paidVal) {
                paidCount++;
                if (tp === 'Gelir') {
                    paidIncome += amt;
                } else if (tp === 'Gider') {
                    paidExpense += amt;
                }
            } else if (st === pendingVal) {
                pendingCount++;
                if (tp === 'Gider') {
                    pendingExpense += amt;
                }
            }
        }

        const net = paidIncome - paidExpense;

        const formatMoney = (n) => {
            return (n || 0).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        };

        totalCountEl.textContent = visibleCount;
        if (countsSubEl) countsSubEl.textContent = `${paidCount} Ödenen · ${pendingCount} Bekleyen`;
        if (paidIncomeEl) paidIncomeEl.innerHTML = `+${formatMoney(paidIncome)} <span class="text-xs font-bold text-emerald-700/70 dark:text-emerald-300">${sym}</span>`;
        if (paidExpenseEl) paidExpenseEl.innerHTML = `-${formatMoney(paidExpense)} <span class="text-xs font-bold text-rose-700/70 dark:text-rose-300">${sym}</span>`;
        if (paidNetEl) {
            paidNetEl.className = `text-2xl font-black ${net >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'} tracking-tight`;
            paidNetEl.innerHTML = `${formatMoney(net)} <span class="text-xs font-bold opacity-75">${sym}</span>`;
        }
        if (netDotEl) {
            netDotEl.className = `inline-block w-1.5 h-1.5 rounded-full ${net >= 0 ? 'bg-emerald-500' : 'bg-rose-500'}`;
        }
        if (pendingExpenseEl) pendingExpenseEl.innerHTML = `-${formatMoney(pendingExpense)} <span class="text-xs font-bold text-amber-700/80 dark:text-amber-300">${sym}</span>`;
        if (pendingSubEl) pendingSubEl.textContent = `${pendingCount} Bekleyen Yükümlülük`;

        const isFiltered = (visibleCount < totalCount) || (window.currentTxTab && window.currentTxTab !== 'all') || Boolean(($('#txSearch').val() || '').trim()) || Boolean($('#txFilterCategory').val()) || Boolean($('#txFilterType').val()) || Boolean($('#txFilterStatus').val()) || Boolean(window.currentTxDateRange);
        if (filterBadge) {
            if (isFiltered) {
                filterBadge.classList.remove('hidden');
                filterBadge.textContent = `${visibleCount} / ${totalCount} Filtrelendi`;
            } else {
                filterBadge.classList.add('hidden');
            }
        }

        // Dynamically sync tab badges across the entire dataset
        const allNodes = txDataTable.rows().nodes();
        let totalAllCount = allNodes.length;
        let totalPaidCount = 0;
        let totalPendingCount = 0;
        let totalPlanCount = 0;

        for (let j = 0; j < allNodes.length; j++) {
            const rn = allNodes[j];
            const rStatus = rn.getAttribute('data-status');
            const rSource = rn.getAttribute('data-source-type');
            if (rStatus === paidVal) totalPaidCount++;
            if (rStatus === pendingVal) totalPendingCount++;
            if (rSource === 'plan') totalPlanCount++;
        }

        const bAll = document.getElementById('badgeAllCount'); if (bAll) bAll.textContent = totalAllCount;
        const bPaid = document.getElementById('badgePaidCount'); if (bPaid) bPaid.textContent = totalPaidCount;
        const bPending = document.getElementById('badgePendingCount'); if (bPending) bPending.textContent = totalPendingCount;
        const bPlan = document.getElementById('badgePlanCount'); if (bPlan) bPlan.textContent = totalPlanCount;
    }

    function applyTxDatePreset(preset) {
        $('.tx-date-preset-btn').removeClass('active');
        $(`.tx-date-preset-btn[data-preset="${preset}"]`).addClass('active');

        const now = new Date();
        let startDate = null;
        let endDate = null;

        if (preset === 'all') {
            window.currentTxDateRange = null;
            if (window.txFlatpickr) window.txFlatpickr.clear();
            updateDateRangeIndicator(null);
            if (txDataTable) txDataTable.draw();
            return;
        } else if (preset === 'this_month') {
            startDate = new Date(now.getFullYear(), now.getMonth(), 1);
            endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0);
        } else if (preset === 'last_month') {
            startDate = new Date(now.getFullYear(), now.getMonth() - 1, 1);
            endDate = new Date(now.getFullYear(), now.getMonth(), 0);
        } else if (preset === 'last_30_days') {
            startDate = new Date(now);
            startDate.setDate(now.getDate() - 30);
            endDate = new Date(now);
        } else if (preset === 'this_year') {
            startDate = new Date(now.getFullYear(), 0, 1);
            endDate = new Date(now.getFullYear(), 11, 31);
        }

        if (startDate && endDate) {
            window.currentTxDateRange = [startDate, endDate];
            if (window.txFlatpickr) {
                window.txFlatpickr.setDate([startDate, endDate], false);
            }
            updateDateRangeIndicator([startDate, endDate]);
            if (txDataTable) txDataTable.draw();
        }
    }

    function updateDateRangeIndicator(dates) {
        const ind = document.getElementById('txDateRangeIndicator');
        const txt = document.getElementById('txDateRangeText');
        if (!ind || !txt) return;
        if (dates && dates.length === 2) {
            const fmt = (d) => d.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric' });
            txt.textContent = `${fmt(dates[0])} – ${fmt(dates[1])}`;
            ind.classList.remove('hidden');
        } else {
            ind.classList.add('hidden');
            txt.textContent = '';
        }
    }

    function resetAllTxFilters() {
        $('#txSearch').val('');
        $('#txFilterCategory').val('');
        $('#txFilterType').val('');
        $('#txFilterStatus').val('');
        window.currentTxDateRange = null;
        if (window.txFlatpickr) window.txFlatpickr.clear();
        updateDateRangeIndicator(null);
        $('.tx-date-preset-btn').removeClass('active');
        $(`.tx-date-preset-btn[data-preset="all"]`).addClass('active');
        switchTxTab('all');
        if (txDataTable) {
            txDataTable.draw();
        }
        if (typeof clearBulkSelection === 'function') {
            clearBulkSelection();
        }
        if (typeof window.showToast === 'function') {
            window.showToast('Filtreler sıfırlandı.', 'info');
        }
    }

    function exportVisibleTransactionsToCsv() {
        if (!txDataTable) return;
        const filteredRows = txDataTable.rows({ search: 'applied' }).nodes();
        if (!filteredRows || filteredRows.length === 0) {
            if (typeof window.showToast === 'function') {
                window.showToast('Dışa aktarılacak işlem bulunamadı.', 'warning');
            }
            return;
        }

        const headers = ['Tarih', 'Kategori', 'Banka / Hesap', 'Açıklama', 'Not', 'Tutar', 'Tür', 'Durum', 'Kaynak'];
        const csvRows = [headers.join(';')];

        for (let i = 0; i < filteredRows.length; i++) {
            const row = filteredRows[i];
            const cells = row.querySelectorAll('td');
            if (!cells || cells.length < 7) continue;

            const date = (cells[0]?.textContent || '').trim().replace(/\s+/g, ' ');
            const category = (row.getAttribute('data-category') || cells[1]?.textContent || '').trim();
            const account = (cells[2]?.textContent || '').trim().replace('—', '');
            const desc = (cells[3]?.querySelector('.font-bold')?.textContent || cells[3]?.textContent || '').trim();
            const note = (cells[4]?.textContent || '').trim().replace('—', '');
            const amount = (row.getAttribute('data-amount') || '').trim();
            const type = (row.getAttribute('data-type') || '').trim();
            const status = (row.getAttribute('data-status') || '').trim();
            const sourceType = (row.getAttribute('data-source-type') || '').trim();

            const clean = (val) => `"${String(val || '').replace(/"/g, '""')}"`;
            csvRows.push([
                clean(date),
                clean(category),
                clean(account),
                clean(desc),
                clean(note),
                clean(amount),
                clean(type),
                clean(status),
                clean(sourceType)
            ].join(';'));
        }

        const csvContent = '\uFEFF' + csvRows.join('\r\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        const today = new Date().toISOString().slice(0, 10);
        link.setAttribute('href', url);
        link.setAttribute('download', `e_cuzdan_islemler_${today}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        if (typeof window.showToast === 'function') {
            window.showToast(`${filteredRows.length} işlem CSV olarak indirildi.`, 'success');
        }
    }

    function openEditModal(btn) {
        const d = btn.dataset;
        const setVal = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.value = val;
        };

        setVal('modalTransactionId', d.id || '');
        setVal('modalTransactionVersion', d.version || '1');
        setVal('modalDate', d.date || '');
        setVal('modalCategory', d.category || '');
        setVal('modalAmount', d.amount || '');
        setVal('modalDescription', d.description || '');
        setVal('modalNote', d.note || '');
        setVal('modalStatus', d.status || 'Bekliyor');
        setVal('modalBankAccount', d.bankAccountId || '');

        const curOpt = document.querySelector(`#modalBankAccount option[value="${d.bankAccountId || ''}"]`);
        const cur = curOpt ? curOpt.getAttribute('data-currency') : '';
        const editBadge = document.getElementById('modalCurrencyBadge');
        if (editBadge) {
            const symbolMap = { 'TRY': '₺', 'TL': '₺', 'USD': '$', 'EUR': '€', 'GBP': '£', 'XAU': 'gr' };
            editBadge.textContent = symbolMap[cur] || cur || (window.BASE_CURRENCY_SYMBOL || '₺');
        }

        if (typeof window.openModal === 'function') {
            window.openModal('editModal');
        } else {
            const modal = document.getElementById('editModal');
            if (modal) {
                modal.classList.remove('hidden');
                modal.classList.add('active');
                modal.style.display = 'flex';
            }
        }
        setTimeout(() => document.getElementById('modalAmount')?.focus(), 100);
    }

    function closeEditTransactionModal() {
        if (typeof window.closeModal === 'function') {
            window.closeModal('editModal');
        } else {
            const modal = document.getElementById('editModal');
            if (modal) {
                modal.classList.add('hidden');
                modal.classList.remove('active');
                modal.style.display = 'none';
            }
        }
        const form = document.getElementById('editModalForm');
        if (form) form.reset();
    }

    function openNewTransactionModal() {
        const pageEl = document.getElementById('transactions-page-container');
        const todayStr = pageEl ? pageEl.getAttribute('data-today-display') || '' : '';
        const dateInput = document.getElementById('newTxDate');
        if (dateInput && !dateInput.value.trim() && todayStr) {
            dateInput.value = todayStr;
        }

        const newBadge = document.getElementById('newTxCurrencyBadge');
        if (newBadge) {
            newBadge.textContent = window.BASE_CURRENCY_SYMBOL || '₺';
        }

        if (typeof window.openModal === 'function') {
            window.openModal('newTransactionModal');
        } else {
            const modal = document.getElementById('newTransactionModal');
            if (modal) {
                modal.classList.remove('hidden');
                modal.classList.add('active');
                modal.style.display = 'flex';
            }
        }
        setTimeout(() => document.getElementById('newTxAmount')?.focus(), 100);
    }

    function closeNewTransactionModal() {
        if (typeof window.closeModal === 'function') {
            window.closeModal('newTransactionModal');
        } else {
            const modal = document.getElementById('newTransactionModal');
            if (modal) {
                modal.classList.add('hidden');
                modal.classList.remove('active');
                modal.style.display = 'none';
            }
        }
        const form = document.getElementById('newTransactionForm');
        if (form) form.reset();
    }

    function setNewTxAmount(delta, reset = false) {
        const input = document.getElementById('newTxAmount');
        if (!input) return;
        if (reset) {
            input.value = '';
            input.focus();
            return;
        }
        const current = parseFloat(input.value) || 0;
        input.value = (current + delta).toFixed(2);
        input.focus();
    }

    function deleteTransaction(transactionId) {
        const uiCopy = getUiCopy();
        if (typeof window.showGlobalConfirm === 'function') {
            window.showGlobalConfirm(uiCopy.deleteTitle, uiCopy.deleteConfirm, () => {
                performDelete(transactionId);
            }, true);
        } else if (confirm(uiCopy.deleteConfirm)) {
            performDelete(transactionId);
        }
    }

    function performDelete(transactionId) {
        const uiCopy = getUiCopy();
        const deleteUrl = (window.ECuzdanEndpoints && window.ECuzdanEndpoints.transactions && window.ECuzdanEndpoints.transactions.delete)
            ? window.ECuzdanEndpoints.transactions.delete(transactionId)
            : `/delete_t/${transactionId}`;

        const csrfToken = document.querySelector('input[name="csrf_token"]')?.value || '';

        fetch(deleteUrl, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (typeof window.showToast === 'function') {
                    window.showToast(data.message || uiCopy.deleteSuccess, 'success');
                }
                const rowEl = document.querySelector(`#transTable tbody button.delete-tx-btn[data-id="${transactionId}"]`)?.closest('tr');
                if (rowEl) {
                    const $row = $(rowEl);
                    $row.fadeOut(200, function() {
                        if (txDataTable) {
                            txDataTable.row($row).remove().draw(false);
                        } else {
                            $row.remove();
                        }
                        updateLiveKpis();
                    });
                } else {
                    setTimeout(() => window.location.reload(), 400);
                }
            } else {
                if (typeof window.showToast === 'function') {
                    window.showToast(data.message || uiCopy.genericError, 'error');
                }
            }
        })
        .catch(error => {
            console.error('Delete error:', error);
            if (typeof window.showToast === 'function') {
                window.showToast(uiCopy.genericError, 'error');
            }
        });
    }

    function toggleSelectAllTx(master) {
        if (!txDataTable) return;
        const isChecked = master.checked;
        const visibleRows = txDataTable.rows({ search: 'applied' }).nodes();
        $(visibleRows).find('.tx-row-select').prop('checked', isChecked);
        updateBulkActionBar();
    }

    function onTxRowSelectChange() {
        updateBulkActionBar();
    }

    function updateBulkActionBar() {
        const bar = document.getElementById('txBulkActionBar');
        const countEl = document.getElementById('bulkSelectedCount');
        const btnPay = document.getElementById('btnBulkQuickPay');
        const btnDel = document.getElementById('btnBulkDelete');
        const hintEl = document.getElementById('bulkPendingHint');
        const master = document.getElementById('selectAllTx');

        const selected = $('.tx-row-select:checked');
        const count = selected.length;

        if (countEl) countEl.textContent = count;

        if (count > 0) {
            if (bar) bar.classList.remove('hidden');

            const pageEl = document.getElementById('transactions-page-container');
            const pendingVal = pageEl ? pageEl.getAttribute('data-status-pending') || 'Bekliyor' : 'Bekliyor';

            let pendingCount = 0;
            selected.each(function() {
                if ($(this).attr('data-status') === pendingVal) pendingCount++;
            });

            if (btnPay) {
                btnPay.disabled = (pendingCount === 0);
                btnPay.title = pendingCount === 0 ? 'Yalnızca bekleyen işlemler ödendi yapılabilir' : `${pendingCount} bekleyen işlemi öde`;
            }
            if (hintEl) {
                if (pendingCount < count) {
                    hintEl.textContent = `(${pendingCount} bekleyen, ${count - pendingCount} zaten ödenmiş)`;
                } else {
                    hintEl.textContent = `(Tümü bekleyen işlem)`;
                }
            }
        } else {
            if (bar) bar.classList.add('hidden');
            if (master) master.checked = false;
        }
    }

    function clearBulkSelection() {
        $('.tx-row-select').prop('checked', false);
        const master = document.getElementById('selectAllTx');
        if (master) master.checked = false;
        updateBulkActionBar();
    }

    function executeBulkQuickPay() {
        const pageEl = document.getElementById('transactions-page-container');
        const pendingVal = pageEl ? pageEl.getAttribute('data-status-pending') || 'Bekliyor' : 'Bekliyor';
        const pendingCheckboxes = $('.tx-row-select:checked').filter(function() {
            return $(this).attr('data-status') === pendingVal;
        });

        if (pendingCheckboxes.length === 0) {
            if (typeof window.showToast === 'function') {
                window.showToast('Ödendi olarak işaretlenebilecek bekleyen işlem seçilmedi.', 'warning');
            }
            return;
        }

        const count = pendingCheckboxes.length;
        const confirmMsg = `Seçili ${count} bekleyen işlemi "Ödendi" olarak işaretlemek istediğinizden emin misiniz?`;

        const doBulkPay = () => {
            const btnPay = document.getElementById('btnBulkQuickPay');
            if (btnPay) btnPay.disabled = true;

            const csrfToken = document.querySelector('input[name="csrf_token"]')?.value || '';
            const promises = [];

            pendingCheckboxes.each(function() {
                const txId = $(this).attr('data-id');
                const quickPayUrl = (window.ECuzdanEndpoints && window.ECuzdanEndpoints.transactions && window.ECuzdanEndpoints.transactions.quickPay)
                    ? window.ECuzdanEndpoints.transactions.quickPay(txId)
                    : `/transactions/${txId}/quick_pay`;

                const p = fetch(quickPayUrl, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ csrf_token: csrfToken })
                }).then(r => r.json());
                promises.push(p);
            });

            Promise.allSettled(promises).then(results => {
                let successCount = 0;
                results.forEach((res, idx) => {
                    if (res.status === 'fulfilled' && res.value && res.value.success) {
                        successCount++;
                        const cb = pendingCheckboxes.eq(idx);
                        cb.attr('data-status', 'Ödendi');
                        const $row = cb.closest('tr');
                        if ($row.length) {
                            $row.attr('data-status', 'Ödendi');
                            $row.data('status', 'Ödendi');
                            const statusCell = $row.find('td').eq(6);
                            if (statusCell.length) {
                                statusCell.html(`
                                    <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                                        <svg class="w-3 h-3 text-emerald-600 dark:text-emerald-400 shrink-0" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                                        Ödendi
                                    </span>
                                `);
                            }
                            const actions = $row.find('.tx-table-actions');
                            if (actions.length) {
                                actions.find('.quick-pay-tx-btn, .edit-tx-btn, .delete-tx-btn').remove();
                                const txIdStr = cb.attr('data-id');
                                actions.append(`
                                    <button data-macro="button_secondary" type="button" class="adjustment-tx-btn tx-table-action tx-table-action-adjustment" data-id="${txIdStr}" title="Düzeltme" aria-label="Düzeltme">
                                        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" class="w-3.5 h-3.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m6-6H6"/></svg>
                                        <span class="hidden 2xl:inline">Düzeltme</span>
                                    </button>
                                    <button data-macro="button_secondary" type="button" class="reversal-tx-btn tx-table-action tx-table-action-reversal" data-id="${txIdStr}" title="Ters Kayıt" aria-label="Ters Kayıt">
                                        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" class="w-3.5 h-3.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 7H5v4m0-4 4 4m6-4a7 7 0 1 1-4.95 11.95"/></svg>
                                        <span class="hidden 2xl:inline">Ters Kayıt</span>
                                    </button>
                                `);
                            }
                        }
                    }
                });

                if (txDataTable) {
                    txDataTable.rows().invalidate().draw(false);
                }
                clearBulkSelection();
                updateLiveKpis();

                if (typeof window.showToast === 'function') {
                    window.showToast(`${successCount} işlem başarıyla ödendi olarak güncellendi.`, 'success');
                }
            }).catch(err => {
                console.error('Bulk quick-pay error:', err);
                if (typeof window.showToast === 'function') {
                    window.showToast('Toplu işlem sırasında hata oluştu.', 'error');
                }
            });
        };

        if (typeof window.showGlobalConfirm === 'function') {
            window.showGlobalConfirm('Toplu Ödeme Onayı', confirmMsg, doBulkPay, false);
        } else if (confirm(confirmMsg)) {
            doBulkPay();
        }
    }

    function executeBulkDelete() {
        const selected = $('.tx-row-select:checked');
        const count = selected.length;
        if (count === 0) return;

        const confirmMsg = `Seçilen ${count} işlemi silmek istediğinize emin misiniz? (Ödenmiş muhasebe kayıtları silinemez, atlanacaktır)`;

        const doBulkDelete = () => {
            const csrfToken = document.querySelector('input[name="csrf_token"]')?.value || '';
            const promises = [];

            selected.each(function() {
                const txId = $(this).attr('data-id');
                const deleteUrl = (window.ECuzdanEndpoints && window.ECuzdanEndpoints.transactions && window.ECuzdanEndpoints.transactions.delete)
                    ? window.ECuzdanEndpoints.transactions.delete(txId)
                    : `/delete_t/${txId}`;

                const p = fetch(deleteUrl, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json',
                        'X-CSRFToken': csrfToken
                    }
                }).then(r => r.json());
                promises.push(p);
            });

            Promise.allSettled(promises).then(results => {
                let deletedCount = 0;
                results.forEach((res, idx) => {
                    if (res.status === 'fulfilled' && res.value && res.value.success) {
                        deletedCount++;
                        const cb = selected.eq(idx);
                        const $row = cb.closest('tr');
                        if ($row.length && txDataTable) {
                            txDataTable.row($row).remove();
                        } else if ($row.length) {
                            $row.remove();
                        }
                    }
                });

                if (txDataTable) {
                    txDataTable.draw(false);
                }
                clearBulkSelection();
                updateLiveKpis();

                if (typeof window.showToast === 'function') {
                    window.showToast(`${deletedCount} işlem silindi.`, 'success');
                }
            }).catch(err => {
                console.error('Bulk delete error:', err);
                if (typeof window.showToast === 'function') {
                    window.showToast('Toplu silme sırasında hata oluştu.', 'error');
                }
            });
        };

        if (typeof window.showGlobalConfirm === 'function') {
            window.showGlobalConfirm('Toplu Silme Onayı', confirmMsg, doBulkDelete, true);
        } else if (confirm(confirmMsg)) {
            doBulkDelete();
        }
    }

    function setupBankAccountCurrencySync() {
        const symbolMap = { 'TRY': '₺', 'TL': '₺', 'USD': '$', 'EUR': '€', 'GBP': '£', 'XAU': 'gr' };
        const resolveSym = (code) => symbolMap[code] || code || (window.BASE_CURRENCY_SYMBOL || '₺');

        const bindSync = (selectId, badgeId) => {
            const selectEl = document.getElementById(selectId);
            const badgeEl = document.getElementById(badgeId);
            if (!selectEl || !badgeEl) return;

            selectEl.addEventListener('change', function() {
                const opt = this.options[this.selectedIndex];
                const cur = opt ? opt.getAttribute('data-currency') : '';
                badgeEl.textContent = resolveSym(cur);
            });
        };

        bindSync('newTxBankAccount', 'newTxCurrencyBadge');
        bindSync('modalBankAccount', 'modalCurrencyBadge');
    }

    function setupWaiAriaTabs() {
        const tabList = document.querySelector('[role="tablist"]');
        if (!tabList) return;
        const tabs = Array.from(tabList.querySelectorAll('[role="tab"]'));
        tabList.addEventListener('keydown', function(e) {
            const activeTab = document.activeElement;
            const idx = tabs.indexOf(activeTab);
            if (idx === -1) return;
            let nextIdx = null;
            if (e.key === 'ArrowRight') nextIdx = (idx + 1) % tabs.length;
            else if (e.key === 'ArrowLeft') nextIdx = (idx - 1 + tabs.length) % tabs.length;
            else if (e.key === 'Home') nextIdx = 0;
            else if (e.key === 'End') nextIdx = tabs.length - 1;
            if (nextIdx !== null) {
                e.preventDefault();
                tabs[nextIdx].focus();
                tabs[nextIdx].click();
            }
        });
    }

    function protectFinancialForm(form, withIdempotency) {
        if (!form) return;
        form.addEventListener('submit', function(event) {
            if (form.dataset.submitting === 'true') {
                event.preventDefault();
                event.stopImmediatePropagation();
                return;
            }
            form.dataset.submitting = 'true';
            form.querySelectorAll('button[type="submit"], input[type="submit"]').forEach(button => { button.disabled = true; });
            if (withIdempotency && !form.querySelector('input[name="idempotency_key"]')) {
                const key = (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`);
                const hidden = document.createElement('input');
                hidden.type = 'hidden'; hidden.name = 'idempotency_key'; hidden.value = key;
                form.appendChild(hidden);
            }
        }, true);
    }

    function setupForms() {
        const uiCopy = getUiCopy();

        // Edit form AJAX
        const editForm = document.getElementById('editModalForm');
        if (editForm) {
            protectFinancialForm(editForm, false);
            editForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                const transactionId = document.getElementById('modalTransactionId')?.value;
                if (!transactionId) return;

                const editUrl = (window.ECuzdanEndpoints && window.ECuzdanEndpoints.transactions && window.ECuzdanEndpoints.transactions.edit)
                    ? window.ECuzdanEndpoints.transactions.edit(transactionId)
                    : `/edit_t/${transactionId}`;

                fetch(editUrl, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    },
                    body: formData
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        if (typeof window.showToast === 'function') {
                            window.showToast(data.message || uiCopy.updateSuccess, 'success');
                        }
                        setTimeout(() => {
                            closeEditTransactionModal();
                            window.location.reload();
                        }, 1000);
                    } else {
                        editForm.dataset.submitting = 'false';
                        editForm.querySelectorAll('button[type="submit"]').forEach(b => { b.disabled = false; });
                        if (typeof window.showToast === 'function') {
                            window.showToast(data.message || uiCopy.genericError, 'error');
                        }
                    }
                })
                .catch(err => {
                    console.error('Edit error:', err);
                    editForm.dataset.submitting = 'false';
                    editForm.querySelectorAll('button[type="submit"]').forEach(b => { b.disabled = false; });
                    if (typeof window.showToast === 'function') {
                        window.showToast(uiCopy.genericError, 'error');
                    }
                });
            });
        }

        // New transaction form AJAX
        const newForm = document.getElementById('newTransactionForm');
        if (newForm) {
            protectFinancialForm(newForm, true);
            newForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const dateInput = document.getElementById('newTxDate');
                const pageEl = document.getElementById('transactions-page-container');
                const todayStr = pageEl ? pageEl.getAttribute('data-today-display') || '' : '';
                if (dateInput && !dateInput.value.trim() && todayStr) {
                    dateInput.value = todayStr;
                }
                const formData = new FormData(this);
                if (dateInput) {
                    formData.set('date', dateInput.value.trim());
                }

                const createUrl = (window.ECuzdanEndpoints && window.ECuzdanEndpoints.transactions && window.ECuzdanEndpoints.transactions.create)
                    ? window.ECuzdanEndpoints.transactions.create
                    : '/new_transaction';

                fetch(createUrl, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    },
                    body: formData
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        if (typeof window.showToast === 'function') {
                            window.showToast(data.message || uiCopy.createSuccess, 'success');
                        }
                        setTimeout(() => {
                            closeNewTransactionModal();
                            window.location.reload();
                        }, 1000);
                    } else {
                        newForm.dataset.submitting = 'false';
                        newForm.querySelectorAll('button[type="submit"]').forEach(b => { b.disabled = false; });
                        if (typeof window.showToast === 'function') {
                            window.showToast(data.message || uiCopy.genericError, 'error');
                        }
                    }
                })
                .catch(err => {
                    console.error('Create error:', err);
                    newForm.dataset.submitting = 'false';
                    newForm.querySelectorAll('button[type="submit"]').forEach(b => { b.disabled = false; });
                    if (typeof window.showToast === 'function') {
                        window.showToast(uiCopy.genericError, 'error');
                    }
                });
            });
        }
    }

    function setupLineageAndImmutable() {
        let immutableTransactionId = null;
        let immutableKind = 'adjustment';

        const escapeHtml = value => String(value ?? '')
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');

        const drawer = document.getElementById('transactionLineageDrawer');
        const drawerContent = document.getElementById('lineageDrawerContent');
        const actionModal = document.getElementById('immutableActionModal');
        const actionForm = document.getElementById('immutableActionForm');
        const actionFeedback = document.getElementById('immutableActionFeedback');
        const actionTitle = document.getElementById('immutableActionTitle');
        const deltaField = document.getElementById('immutableDeltaField');
        const deltaInput = document.getElementById('immutableDelta');
        const reasonCodeInput = document.getElementById('immutableReasonCode');
        const reasonTextInput = document.getElementById('immutableReasonText');

        const openDrawer = () => {
            if (drawer) {
                drawer.classList.remove('hidden');
                drawer.setAttribute('aria-hidden', 'false');
            }
        };

        const closeDrawer = () => {
            if (drawer) {
                drawer.classList.add('hidden');
                drawer.setAttribute('aria-hidden', 'true');
            }
        };

        const openImmutableModal = (transactionId, kind) => {
            immutableTransactionId = transactionId;
            immutableKind = kind;
            if (!actionModal) return;

            actionFeedback?.classList.add('hidden');
            if (actionFeedback) actionFeedback.textContent = '';
            actionForm?.reset();

            if (kind === 'adjustment') {
                actionTitle.textContent = 'Düzeltme Kaydı';
                deltaField.classList.remove('hidden');
                deltaInput.required = true;
            } else {
                actionTitle.textContent = 'Ters Kayıt (İptal)';
                deltaField.classList.add('hidden');
                deltaInput.required = false;
            }

            actionModal.classList.remove('hidden');
            actionModal.classList.add('flex');
            actionModal.setAttribute('aria-hidden', 'false');
            document.documentElement.classList.add('modal-open');
            document.body.style.overflow = 'hidden';
            setTimeout(() => (kind === 'adjustment' ? deltaInput : reasonTextInput)?.focus(), 50);
        };

        const closeImmutableModal = () => {
            if (actionModal) {
                actionModal.classList.add('hidden');
                actionModal.classList.remove('flex');
                actionModal.setAttribute('aria-hidden', 'true');
            }
            document.documentElement.classList.remove('modal-open');
            document.body.style.overflow = '';
            immutableTransactionId = null;
        };

        document.querySelectorAll('[data-lineage-close]').forEach(el => el.addEventListener('click', closeDrawer));
        document.querySelectorAll('[data-immutable-close]').forEach(el => el.addEventListener('click', closeImmutableModal));

        // Lineage click delegation
        $('#transTable tbody').on('click', '.lineage-tx-btn', function(e) {
            e.preventDefault();
            const transactionId = this.dataset.id;
            if (!transactionId) return;

            openDrawer();
            if (drawerContent) drawerContent.textContent = 'Yükleniyor...';

            const lineageUrl = (window.ECuzdanEndpoints && window.ECuzdanEndpoints.transactions && window.ECuzdanEndpoints.transactions.lineage)
                ? window.ECuzdanEndpoints.transactions.lineage(transactionId)
                : `/transactions/${transactionId}/lineage`;

            fetch(lineageUrl, { headers: { 'Accept': 'application/json' } })
                .then(r => r.json())
                .then(data => {
                    if (!data.success) {
                        drawerContent.innerHTML = `<div class="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-700">${escapeHtml(data.message || 'Hata')}</div>`;
                        return;
                    }
                    const tx = data.transaction || {};
                    const events = data.lineage_events || [];
                    const adjustments = data.adjustments || [];

                    let html = `
                        <div class="space-y-4">
                            <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700">
                                <p class="text-xs font-bold text-slate-400 uppercase">İşlem Detayı</p>
                                <p class="text-base font-black text-slate-900 dark:text-white mt-1">${escapeHtml(tx.description || '')}</p>
                                <p class="text-xs font-bold text-slate-600 dark:text-slate-300 mt-1">${escapeHtml(tx.amount || '0')} ${escapeHtml(window.BASE_CURRENCY_SYMBOL || '₺')} • ${escapeHtml(tx.date || '')}</p>
                            </div>
                            <div>
                                <h4 class="text-xs font-bold uppercase text-slate-500 mb-2">Denetim Olayları (${events.length})</h4>
                                <div class="space-y-2">
                                    ${events.map(ev => `
                                        <div class="p-3 rounded-lg border border-slate-100 dark:border-slate-800 text-xs">
                                            <span class="font-bold text-slate-800 dark:text-slate-200">${escapeHtml(ev.action || '')}</span>
                                            <span class="text-slate-400 block text-[10px]">${escapeHtml(ev.timestamp || '')}</span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                    `;
                    drawerContent.innerHTML = html;
                })
                .catch(err => {
                    console.error('Lineage error:', err);
                    drawerContent.innerHTML = '<div class="text-xs text-rose-600">Denetim izi yüklenirken hata oluştu.</div>';
                });
        });

        // Adjustment & Reversal delegation
        $('#transTable tbody').on('click', '.adjustment-tx-btn', function(e) {
            e.preventDefault();
            openImmutableModal(this.dataset.id, 'adjustment');
        });

        $('#transTable tbody').on('click', '.reversal-tx-btn', function(e) {
            e.preventDefault();
            openImmutableModal(this.dataset.id, 'reversal');
        });

        actionForm?.addEventListener('submit', function(e) {
            e.preventDefault();
            if (!immutableTransactionId) return;

            const submitBtn = actionForm.querySelector('button[type="submit"]');
            if (submitBtn) submitBtn.disabled = true;

            const payload = {
                reason_code: reasonCodeInput.value,
                reason_text: reasonTextInput.value.trim()
            };
            if (immutableKind === 'adjustment') {
                payload.amount_delta = parseFloat(deltaInput.value);
            }

            const targetUrl = immutableKind === 'adjustment'
                ? (window.ECuzdanEndpoints?.transactions?.adjustments
                    ? window.ECuzdanEndpoints.transactions.adjustments(immutableTransactionId)
                    : (window.ECuzdanEndpoints?.transactions?.adjust
                        ? window.ECuzdanEndpoints.transactions.adjust(immutableTransactionId)
                        : `/api/transactions/${immutableTransactionId}/adjustments`))
                : (window.ECuzdanEndpoints?.transactions?.reversal
                    ? window.ECuzdanEndpoints.transactions.reversal(immutableTransactionId)
                    : (window.ECuzdanEndpoints?.transactions?.reverse
                        ? window.ECuzdanEndpoints.transactions.reverse(immutableTransactionId)
                        : `/api/transactions/${immutableTransactionId}/reversal`));

            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
                || document.querySelector('input[name="csrf_token"]')?.value
                || '';

            const idempotencyKey = window.crypto?.randomUUID
                ? window.crypto.randomUUID()
                : (immutableKind + '-' + immutableTransactionId + '-' + Date.now() + '-' + Math.random().toString(36).substring(2, 9));

            fetch(targetUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Idempotency-Key': idempotencyKey
                },
                body: JSON.stringify(payload)
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    closeImmutableModal();
                    if (typeof window.showToast === 'function') {
                        window.showToast(data.message || 'İşlem uygulandı', 'success');
                    }
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    if (submitBtn) submitBtn.disabled = false;
                    if (actionFeedback) {
                        actionFeedback.textContent = data.message || 'Hata oluştu';
                        actionFeedback.classList.remove('hidden');
                    }
                }
            })
            .catch(err => {
                console.error('Immutable error:', err);
                if (submitBtn) submitBtn.disabled = false;
                if (actionFeedback) {
                    actionFeedback.textContent = 'İstek gönderilirken hata oluştu';
                    actionFeedback.classList.remove('hidden');
                }
            });
        });

        // Auto-open modal if URL has ?modal=new or ?edit=<id>, or auto-filter by ?month=&year=
        try {
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('modal') === 'new') {
                openNewTransactionModal();
            } else if (urlParams.get('edit')) {
                const editId = urlParams.get('edit');
                const targetBtn = document.querySelector(`button[onclick*="openEditModal"][onclick*="${editId}"]`);
                if (targetBtn) {
                    targetBtn.click();
                }
            } else if (urlParams.get('month') && urlParams.get('year')) {
                const m = parseInt(urlParams.get('month'), 10);
                const y = parseInt(urlParams.get('year'), 10);
                if (m >= 1 && m <= 12 && y > 2000) {
                    const firstDay = new Date(y, m - 1, 1);
                    const lastDay = new Date(y, m, 0);
                    window.currentTxDateRange = [firstDay, lastDay];
                    if (window.txFlatpickr) {
                        window.txFlatpickr.setDate([firstDay, lastDay]);
                    }
                    if (typeof updateDateRangeIndicator === 'function') {
                        updateDateRangeIndicator([firstDay, lastDay]);
                    }
                    if (txDataTable) {
                        txDataTable.draw();
                    }
                }
            } else if (urlParams.get('category')) {
                const catParam = urlParams.get('category');
                const catSelect = document.getElementById('txFilterCategory');
                if (catSelect) {
                    catSelect.value = catParam;
                    if (txDataTable) {
                        txDataTable.draw();
                    }
                }
            } else if (urlParams.get('date')) {
                const dateParam = urlParams.get('date');
                const targetDay = new Date(dateParam);
                if (!isNaN(targetDay.getTime())) {
                    window.currentTxDateRange = [targetDay, targetDay];
                    if (window.txFlatpickr) {
                        window.txFlatpickr.setDate([targetDay, targetDay]);
                    }
                    if (typeof updateDateRangeIndicator === 'function') {
                        updateDateRangeIndicator([targetDay, targetDay]);
                    }
                    if (txDataTable) {
                        txDataTable.draw();
                    }
                }
            }
        } catch (e) {
            console.warn('[Transactions] URL parameter parse error:', e);
        }
        // Global Escape key modal closer
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeEditTransactionModal();
                closeNewTransactionModal();
                const closeDrawerBtn = document.querySelector('[data-lineage-close]');
                if (closeDrawerBtn) closeDrawerBtn.click();
                const closeImmutableBtn = document.querySelector('[data-immutable-close]');
                if (closeImmutableBtn) closeImmutableBtn.click();
            }
        });
    }

    function toggleTxFiltersMobile() {
        const panel = document.getElementById('txFilterPanel');
        const badge = document.getElementById('mobileFilterStateBadge');
        if (panel) {
            panel.classList.toggle('hidden');
            if (badge) {
                badge.textContent = panel.classList.contains('hidden') ? 'Kapalı' : 'Açık';
            }
        }
    }

    // Expose globals
    window.toggleTxFiltersMobile = toggleTxFiltersMobile;
    window.switchTxTab = switchTxTab;
    window.openEditModal = openEditModal;
    window.closeEditTransactionModal = closeEditTransactionModal;
    window.openNewTransactionModal = openNewTransactionModal;
    window.closeNewTransactionModal = closeNewTransactionModal;
    window.setNewTxAmount = setNewTxAmount;
    window.deleteTransaction = deleteTransaction;
    window.resetAllTxFilters = resetAllTxFilters;
    window.exportVisibleTransactionsToCsv = exportVisibleTransactionsToCsv;
    window.updateLiveKpis = updateLiveKpis;
    window.toggleSelectAllTx = toggleSelectAllTx;
    window.onTxRowSelectChange = onTxRowSelectChange;
    window.clearBulkSelection = clearBulkSelection;
    window.executeBulkQuickPay = executeBulkQuickPay;
    window.executeBulkDelete = executeBulkDelete;
    window.applyTxDatePreset = applyTxDatePreset;

    $(document).ready(initTransactionsTable);
})();
