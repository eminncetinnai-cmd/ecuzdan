/**
 * E-Cüzdan — Investment Logbook JS
 */

const logbookI18n = window.ECuzdanI18n || {};
function logbookT(key, vars) {
    let value = logbookI18n[key] || key;
    Object.entries(vars || {}).forEach(([name, replacement]) => { value = value.replace(`{${name}}`, String(replacement)); });
    return value;
}

// Toast notification function
function showToast(message, type) {
    if (typeof window.showToast === 'function') {
        window.showToast(message, type || 'info');
        return;
    }
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    const bgColor = type === 'success' ? 'bg-emerald-500' : type === 'error' ? 'bg-rose-500' : 'bg-amber-500';
    const textColor = 'text-white';
    toast.className = `px-4 py-2 rounded shadow ${bgColor} ${textColor} animate-fade-in`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => { toast.remove(); }, 4000);
}

document.addEventListener('DOMContentLoaded', function() {
    const entryDateInput = document.getElementById('entry_date');
    if (entryDateInput && !entryDateInput.value) {
        entryDateInput.value = new Date().toISOString().split('T')[0];
    }
    
    // Check for open_edit parameter in URL
    const urlParams = new URLSearchParams(window.location.search);
    const openEditId = urlParams.get('open_edit');
    if (openEditId) {
        showEditModal(parseInt(openEditId));
        window.history.replaceState({}, document.title, window.location.pathname);
    }
    const openEditIbanId = urlParams.get('open_edit_iban');
    if (openEditIbanId) {
        showEditIbanModal(parseInt(openEditIbanId));
        window.history.replaceState({}, document.title, window.location.pathname + '?tab=ibans');
    }
    const openEditReminderId = urlParams.get('open_edit_reminder');
    if (openEditReminderId) {
        showEditReminderModal(parseInt(openEditReminderId));
        window.history.replaceState({}, document.title, window.location.pathname + '?tab=reminders');
    }
    if (urlParams.get('tab') === 'reminders') {
        switchLogbookTab('reminders', false);
    } else if (urlParams.get('tab') === 'ibans') {
        switchLogbookTab('ibans', false);
    }
    
    // ESC key listener for modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const qrModal = document.getElementById('ibanQrModal');
            if (qrModal && !qrModal.classList.contains('hidden')) {
                hideIbanQrModal();
                return;
            }
            const remModal = document.getElementById('reminderModal');
            if (remModal && !remModal.classList.contains('hidden')) {
                hideReminderModal();
                return;
            }
            const ibanModal = document.getElementById('ibanModal');
            if (ibanModal && !ibanModal.classList.contains('hidden')) {
                hideIbanModal();
                return;
            }
            const modal = document.getElementById('entryModal');
            if (modal && (modal.classList.contains('active') || (!modal.classList.contains('hidden') && modal.style.display !== 'none'))) {
                hideModal();
            }
        }
    });
});

function searchLogbookEntries(query) {
    const term = (query || '').trim().toLowerCase();
    const items = document.querySelectorAll('.timeline-item');
    items.forEach(item => {
        const title = (item.querySelector('.timeline-entry-title')?.textContent || '').toLowerCase();
        const content = (item.querySelector('.timeline-entry-content')?.textContent || '').toLowerCase();
        const meta = (item.querySelector('.timeline-entry-meta')?.textContent || '').toLowerCase();
        const matches = !term || title.includes(term) || content.includes(term) || meta.includes(term);
        item.style.display = matches ? '' : 'none';
    });
}

function showCreateModal() {
    const modalTitle = document.getElementById('modalTitle');
    if (modalTitle) modalTitle.textContent = logbookT('logbook_new_entry');
    const entryForm = document.getElementById('entryForm');
    if (entryForm) entryForm.reset();
    const entryId = document.getElementById('entryId');
    if (entryId) entryId.value = '';
    const entryDate = document.getElementById('entry_date');
    if (entryDate) entryDate.value = new Date().toISOString().split('T')[0];
    if (typeof window.openModal === 'function') {
        window.openModal('entryModal');
    }
    setTimeout(() => {
        const titleInput = document.getElementById('title');
        if (titleInput) titleInput.focus();
    }, 50);
}

function showEditModal(entryId) {
    fetch(`/logbook/${entryId}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(logbookT('logbook_not_found'));
        }
        return response.json();
    })
    .then(data => {
        if (data.success && data.entry) {
            const entry = data.entry;
            const modalTitle = document.getElementById('modalTitle');
            if (modalTitle) modalTitle.textContent = logbookT('logbook_edit_entry');
            const entryIdEl = document.getElementById('entryId');
            if (entryIdEl) entryIdEl.value = entry.id;
            const titleEl = document.getElementById('title');
            if (titleEl) titleEl.value = entry.title;
            const contentEl = document.getElementById('content');
            if (contentEl) contentEl.value = entry.content;
            const dateEl = document.getElementById('entry_date');
            if (dateEl) dateEl.value = entry.entry_date;
            const catEl = document.getElementById('category');
            if (catEl) catEl.value = entry.category;
            if (typeof window.openModal === 'function') {
                window.openModal('entryModal');
            }
            setTimeout(() => {
                const titleInput = document.getElementById('title');
                if (titleInput) titleInput.focus();
            }, 50);
        } else {
            showToast(data.message || logbookT('logbook_load_failed'), 'error');
        }
    })
    .catch(error => {
        console.error('Error loading entry:', error);
        showToast(logbookT('logbook_load_error') + ' ' + error.message, 'error');
    });
}

function hideModal() {
    if (typeof window.closeModal === 'function') {
        window.closeModal('entryModal');
    }
    const form = document.getElementById('entryForm');
    if (form) form.reset();
}

function saveEntry(triggerBtn) {
    if (window._isSavingEntry) return;

    const entryIdEl = document.getElementById('entryId');
    const entryId = entryIdEl ? entryIdEl.value : '';
    const form = document.getElementById('entryForm');
    if (!form) return;

    const title = (document.getElementById('title')?.value || '').trim();
    const contentVal = (document.getElementById('content')?.value || '').trim();
    if (!title) {
        showToast('Lütfen başlık giriniz.', 'warning');
        document.getElementById('title')?.focus();
        return;
    }
    if (!contentVal) {
        showToast('Lütfen not içeriği giriniz.', 'warning');
        document.getElementById('content')?.focus();
        return;
    }

    const submitBtn = triggerBtn || document.getElementById('btnSaveEntry');
    window._isSavingEntry = true;
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.classList.add('opacity-75', 'pointer-events-none');
        if (!submitBtn.dataset.originalHtml) submitBtn.dataset.originalHtml = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="inline-block animate-spin mr-1.5" aria-hidden="true">⏳</span> <span>Kaydediliyor...</span>';
    }

    function unlockEntryButton() {
        window._isSavingEntry = false;
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('opacity-75', 'pointer-events-none');
            if (submitBtn.dataset.originalHtml) {
                submitBtn.innerHTML = submitBtn.dataset.originalHtml;
                delete submitBtn.dataset.originalHtml;
            }
        }
    }

    const formData = new FormData(form);
    const url = entryId ? `/logbook/${entryId}/update` : '/logbook/create';

    fetch(url, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            hideModal();
            location.reload();
        } else {
            unlockEntryButton();
            showToast(data.message || logbookT('logbook_save_failed'), 'error');
        }
    })
    .catch(error => {
        unlockEntryButton();
        console.error('Error saving entry:', error);
        showToast(logbookT('logbook_save_error') + ' ' + error.message, 'error');
    });
}

function deleteEntry(entryId) {
    if (typeof window.showGlobalConfirm === 'function') {
        window.showGlobalConfirm(logbookT('logbook_delete'), logbookT('logbook_delete_confirm'), function() {
            const formData = new FormData();
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
            formData.append('csrf_token', csrfToken);
            
            const endpoint = (window.ECuzdanEndpoints && window.ECuzdanEndpoints.logbook && typeof window.ECuzdanEndpoints.logbook.delete === 'function')
                ? window.ECuzdanEndpoints.logbook.delete(entryId)
                : `/logbook/${entryId}/delete`;

            fetch(endpoint, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    showToast(data.message || logbookT('logbook_delete_failed'), 'error');
                }
            })
            .catch(error => {
                console.error('Error deleting entry:', error);
                showToast(logbookT('logbook_delete_error'), 'error');
            });
        }, true);
    } else {
        if (confirm(logbookT('logbook_delete_confirm'))) {
            const formData = new FormData();
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
            formData.append('csrf_token', csrfToken);
            
            const endpoint = (window.ECuzdanEndpoints && window.ECuzdanEndpoints.logbook && typeof window.ECuzdanEndpoints.logbook.delete === 'function')
                ? window.ECuzdanEndpoints.logbook.delete(entryId)
                : `/logbook/${entryId}/delete`;

            fetch(endpoint, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    showToast(data.message || logbookT('logbook_delete_failed'), 'error');
                }
            })
            .catch(error => {
                console.error('Error deleting entry:', error);
                showToast(logbookT('logbook_delete_error'), 'error');
            });
        }
    }
}

function applyFilters() {
    const categoryEl = document.getElementById('filter-category');
    const dateEl = document.getElementById('filter-date');
    const category = categoryEl ? categoryEl.value : '';
    const date = dateEl ? dateEl.value : '';
    const url = new URL(window.location);
    if (category) url.searchParams.set('category', category);
    else url.searchParams.delete('category');
    if (date) url.searchParams.set('date', date);
    else url.searchParams.delete('date');
    window.location = url.toString();
}

function resetLogbookFilters() {
    const url = new URL(window.location);
    url.searchParams.delete('category');
    url.searchParams.delete('date');
    window.location = url.pathname;
}

// ── IBAN Management & Directory ──────────────────────────────────────────────

const TR_BANK_CODES = {
    '00010': 'T.C. Ziraat Bankası',
    '00012': 'Türkiye Halk Bankası (Halkbank)',
    '00015': 'Türkiye Vakıflar Bankası (VakıfBank)',
    '00032': 'Türk Ekonomi Bankası (TEB)',
    '00046': 'Akbank',
    '00059': 'Şekerbank',
    '00062': 'Garanti BBVA',
    '00064': 'Türkiye İş Bankası',
    '00067': 'Yapı ve Kredi Bankası',
    '00099': 'ING Bank',
    '00103': 'Fibabanka',
    '00108': 'Burgan Bank',
    '00111': 'QNB Finansbank',
    '00123': 'HSBC Bank',
    '00124': 'Alternatif Bank',
    '00125': 'Burgan Bank',
    '00134': 'DenizBank',
    '00135': 'Anadolubank',
    '00143': 'Aktif Yatırım Bankası',
    '00146': 'Odeabank',
    '00203': 'Albaraka Türk Katılım Bankası',
    '00205': 'Kuveyt Türk Katılım Bankası',
    '00206': 'Türkiye Finans Katılım Bankası',
    '00209': 'Ziraat Katılım Bankası',
    '00210': 'Vakıf Katılım Bankası',
    '00211': 'Türkiye Emlak Katılım Bankası',
    '00801': 'Papara',
    '00802': 'Paycell',
    '00803': 'İninal',
    '00804': 'Enpara',
    '00805': 'Hayhay',
    '00806': 'PeP',
    '00807': 'Param'
};

function switchLogbookTab(tabName, updateUrl = true) {
    const notesTabBtn = document.getElementById('tab-btn-notes');
    const ibansTabBtn = document.getElementById('tab-btn-ibans');
    const remindersTabBtn = document.getElementById('tab-btn-reminders');
    const timelineView = document.getElementById('timeline-view');
    const ibanView = document.getElementById('iban-view');
    const reminderView = document.getElementById('reminder-view');
    const filterNotes = document.getElementById('filter-panel-notes');
    const filterIbans = document.getElementById('filter-panel-ibans');
    const filterReminders = document.getElementById('filter-panel-reminders');
    const btnCreateNote = document.getElementById('btn-create-note');
    const btnCreateIban = document.getElementById('btn-create-iban');
    const btnCreateReminder = document.getElementById('btn-create-reminder');
    const sectionTitle = document.getElementById('logbookSectionTitle');

    // Deactivate all
    [notesTabBtn, ibansTabBtn, remindersTabBtn].forEach(b => b?.classList.remove('active'));
    [timelineView, ibanView, reminderView, filterNotes, filterIbans, filterReminders, btnCreateNote, btnCreateIban, btnCreateReminder].forEach(el => el?.classList.add('hidden'));

    if (tabName === 'reminders') {
        remindersTabBtn?.classList.add('active');
        reminderView?.classList.remove('hidden');
        filterReminders?.classList.remove('hidden');
        btnCreateReminder?.classList.remove('hidden');
        if (sectionTitle) sectionTitle.textContent = 'Hatırlatıcılar & Poliçeler';

        if (updateUrl) {
            const url = new URL(window.location);
            url.searchParams.set('tab', 'reminders');
            window.history.replaceState({}, '', url.toString());
        }
    } else if (tabName === 'ibans') {
        ibansTabBtn?.classList.add('active');
        ibanView?.classList.remove('hidden');
        filterIbans?.classList.remove('hidden');
        btnCreateIban?.classList.remove('hidden');
        if (sectionTitle) sectionTitle.textContent = 'Kayıtlı IBAN Numaralarım';

        if (updateUrl) {
            const url = new URL(window.location);
            url.searchParams.set('tab', 'ibans');
            window.history.replaceState({}, '', url.toString());
        }
    } else {
        notesTabBtn?.classList.add('active');
        timelineView?.classList.remove('hidden');
        filterNotes?.classList.remove('hidden');
        btnCreateNote?.classList.remove('hidden');
        if (sectionTitle) sectionTitle.textContent = 'Finansal Notlar & Kararlar';

        if (updateUrl) {
            const url = new URL(window.location);
            url.searchParams.delete('tab');
            window.history.replaceState({}, '', url.pathname);
        }
    }
}

function copyIban(btn) {
    if (!btn) return;
    const iban = btn.getAttribute('data-iban') || '';
    if (!iban) return;

    function onCopied() {
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<span>✓</span> <span>Kopyalandı!</span>';
        btn.classList.add('copied');
        showToast('IBAN başarıyla kopyalandı: ' + iban, 'success');
        setTimeout(() => {
            btn.innerHTML = originalHtml;
            btn.classList.remove('copied');
        }, 2200);
    }

    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(iban).then(onCopied).catch(() => {
            fallbackCopyText(iban, onCopied);
        });
    } else {
        fallbackCopyText(iban, onCopied);
    }
}

function copyIbanBox(box) {
    if (!box) return;
    const iban = box.getAttribute('data-iban') || '';
    if (!iban) return;

    function onCopied() {
        const badge = box.querySelector('.iban-touch-badge');
        const origHtml = badge ? badge.innerHTML : '';
        box.classList.add('copied');
        if (badge) {
            badge.innerHTML = '<span>✓</span> <span>Kopyalandı!</span>';
        }
        showToast('IBAN kopyalandı: ' + iban, 'success');
        setTimeout(() => {
            box.classList.remove('copied');
            if (badge) badge.innerHTML = origHtml;
        }, 2000);
    }

    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(iban).then(onCopied).catch(() => {
            fallbackCopyText(iban, onCopied);
        });
    } else {
        fallbackCopyText(iban, onCopied);
    }
}

function toggleIbanMenu(btn, event) {
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }
    const wrapper = btn.closest('.iban-menu-wrapper');
    const dropdown = wrapper ? wrapper.querySelector('.iban-menu-dropdown') : null;
    if (!dropdown) return;

    const isHidden = dropdown.classList.contains('hidden');
    // Close other open menus
    document.querySelectorAll('.iban-menu-dropdown').forEach(dd => dd.classList.add('hidden'));

    if (isHidden) {
        dropdown.classList.remove('hidden');
    }
}

// Global click listener to dismiss floating menus
document.addEventListener('click', function(e) {
    if (!e.target.closest('.iban-menu-wrapper')) {
        document.querySelectorAll('.iban-menu-dropdown').forEach(dd => dd.classList.add('hidden'));
    }
});

function toggleIbanAdvanced() {
    const sec = document.getElementById('ibanAdvancedSection');
    const toggle = document.querySelector('.iban-advanced-toggle');
    if (!sec) return;
    const isHidden = sec.classList.contains('hidden');
    if (isHidden) {
        sec.classList.remove('hidden');
        if (toggle) toggle.classList.add('open');
    } else {
        sec.classList.add('hidden');
        if (toggle) toggle.classList.remove('open');
    }
}

function shareIban(btn) {
    if (!btn) return;
    const shareText = btn.getAttribute('data-share') || '';
    if (!shareText) return;

    function onShared() {
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<span>✓</span> <span>Paylaşıldı!</span>';
        btn.classList.add('copied');
        showToast('Hesap bilgileri paylaşıma hazır kopyalandı!', 'success');
        setTimeout(() => {
            btn.innerHTML = originalHtml;
            btn.classList.remove('copied');
        }, 2200);
    }

    if (navigator.share && window.isSecureContext && /Mobi|Android|iPhone/i.test(navigator.userAgent)) {
        navigator.share({
            title: 'Hesap Bilgileri',
            text: shareText
        }).catch(() => {
            copyText(shareText, 'Hesap bilgileri panoya kopyalandı!');
            onShared();
        });
    } else {
        copyText(shareText, 'Hesap bilgileri panoya kopyalandı!');
        onShared();
    }
}

function copyText(text, successMsg) {
    if (!text) return;
    function onSuccess() {
        showToast(successMsg || 'Panoya kopyalandı.', 'success');
    }
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(onSuccess).catch(() => {
            fallbackCopyText(text, onSuccess);
        });
    } else {
        fallbackCopyText(text, onSuccess);
    }
}

function toggleFavoriteIban(ibanId, btn) {
    const formData = new FormData();
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    formData.append('csrf_token', csrfToken);

    fetch(`/logbook/ibans/${ibanId}/toggle-favorite`, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            const card = btn.closest('.iban-card');
            if (data.is_favorite) {
                btn.classList.add('active');
                btn.title = 'Favorilerden Çıkar';
                if (card) card.classList.add('is-favorite');
            } else {
                btn.classList.remove('active');
                btn.title = 'Favorilere Ekle';
                if (card) card.classList.remove('is-favorite');
            }
            // Smoothly re-sort or refresh tab to reflect favorite ordering
            setTimeout(() => {
                const targetUrl = new URL(window.location);
                targetUrl.searchParams.set('tab', 'ibans');
                window.location = targetUrl.toString();
            }, 600);
        } else {
            showToast(data.message || 'İşlem başarısız.', 'error');
        }
    })
    .catch(err => {
        showToast('Favori güncelleme hatası: ' + err.message, 'error');
    });
}

function startTxFromIban(title, bank, category, iban) {
    if (typeof window.openGlobalQuickTxModal === 'function') {
        window.openGlobalQuickTxModal();
        const flowSelect = document.getElementById('globalQuickTxFlowType');
        if (flowSelect) {
            flowSelect.value = category === 'kendi_hesabim' ? 'Yatırım' : 'Gider';
            if (typeof window.updateGlobalQuickTxCategory === 'function') {
                window.updateGlobalQuickTxCategory();
            }
        }
        const descInput = document.querySelector('#globalQuickTxForm input[name="description"]');
        if (descInput) {
            const shortIban = iban ? iban.slice(-7) : '';
            descInput.value = `${title} (${bank ? bank + ' ' : ''}...${shortIban})`;
        }
        const amountInput = document.querySelector('#globalQuickTxForm input[name="amount"]');
        if (amountInput) {
            setTimeout(() => amountInput.focus(), 150);
        }
        showToast(`Hızlı işlem başlatıldı: ${title}`, 'info');
    } else {
        const shortIban = iban ? iban.slice(-7) : '';
        const desc = encodeURIComponent(`${title} (${bank ? bank + ' ' : ''}...${shortIban})`);
        const flow = category === 'kendi_hesabim' ? 'Yatırım' : 'Gider';
        window.location = `/transactions?action=new&description=${desc}&type=${flow}`;
    }
}

function fallbackCopyText(text, callback) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        const successful = document.execCommand('copy');
        if (successful && typeof callback === 'function') callback();
    } catch (err) {
        showToast('Panoya kopyalanamadı.', 'error');
    }
    document.body.removeChild(textArea);
}

function onIbanFieldInput(input) {
    if (!input) return;
    let raw = (input.value || '').replace(/[\s\-_.:]+/g, '').toUpperCase();
    if (!raw.startsWith('TR') && raw.length > 0 && /^\d/.test(raw)) {
        raw = 'TR' + raw;
    }
    
    // Auto-detect bank from digits 5 to 9 (e.g. TRxx 00062 ...)
    if (raw.startsWith('TR') && raw.length >= 9) {
        const bankCode = raw.substring(4, 9);
        const bankName = TR_BANK_CODES[bankCode];
        const bankInput = document.getElementById('ibanBankName');
        const bankIndicator = document.getElementById('ibanBankIndicator');
        if (bankName) {
            if (bankInput && (!bankInput.value || bankInput.getAttribute('data-auto') === 'true')) {
                bankInput.value = bankName;
                bankInput.setAttribute('data-auto', 'true');
            }
            if (bankIndicator) {
                bankIndicator.textContent = bankName;
                bankIndicator.classList.remove('hidden');
            }
        }
    }

    // Format into 4-character chunks
    const chunks = [];
    for (let i = 0; i < raw.length && i < 26; i += 4) {
        chunks.push(raw.substring(i, i + 4));
    }
    input.value = chunks.join(' ');
}

function showCreateIbanModal() {
    const form = document.getElementById('ibanForm');
    if (form) form.reset();
    const idEl = document.getElementById('ibanId');
    if (idEl) idEl.value = '';
    const modalTitle = document.getElementById('ibanModalTitle');
    if (modalTitle) modalTitle.textContent = 'Yeni IBAN Kaydet';
    const bankIndicator = document.getElementById('ibanBankIndicator');
    if (bankIndicator) {
        bankIndicator.textContent = '';
        bankIndicator.classList.add('hidden');
    }
    const bankInput = document.getElementById('ibanBankName');
    if (bankInput) bankInput.removeAttribute('data-auto');
    const favInput = document.getElementById('ibanIsFavorite');
    if (favInput) favInput.checked = false;
    const easyType = document.getElementById('ibanEasyType');
    if (easyType) easyType.value = '';
    const easyVal = document.getElementById('ibanEasyValue');
    if (easyVal) easyVal.value = '';

    // Reset progressive disclosure section
    const advSec = document.getElementById('ibanAdvancedSection');
    if (advSec) advSec.classList.add('hidden');
    const advToggle = document.querySelector('.iban-advanced-toggle');
    if (advToggle) advToggle.classList.remove('open');

    if (typeof window.openModal === 'function') {
        window.openModal('ibanModal');
    } else {
        const modal = document.getElementById('ibanModal');
        if (modal) modal.classList.remove('hidden');
    }
    setTimeout(() => {
        const titleInput = document.getElementById('ibanTitle');
        if (titleInput) titleInput.focus();
    }, 50);
}

function showEditIbanModal(ibanId) {
    fetch(`/logbook/ibans/${ibanId}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => {
        if (!response.ok) throw new Error('IBAN yüklenemedi.');
        return response.json();
    })
    .then(data => {
        if (data.success && data.iban) {
            const item = data.iban;
            const modalTitle = document.getElementById('ibanModalTitle');
            if (modalTitle) modalTitle.textContent = 'IBAN Düzenle';

            const idEl = document.getElementById('ibanId');
            if (idEl) idEl.value = item.id;
            const titleEl = document.getElementById('ibanTitle');
            if (titleEl) titleEl.value = item.title;
            const ibanEl = document.getElementById('ibanNumber');
            if (ibanEl) ibanEl.value = item.formatted_iban || item.iban;
            const bankEl = document.getElementById('ibanBankName');
            if (bankEl) {
                bankEl.value = item.bank_name || '';
                bankEl.removeAttribute('data-auto');
            }
            const holderEl = document.getElementById('ibanAccountHolder');
            if (holderEl) holderEl.value = item.account_holder || '';
            const catEl = document.getElementById('ibanCategory');
            if (catEl) catEl.value = item.category || 'kendi_hesabim';
            const noteEl = document.getElementById('ibanNote');
            if (noteEl) noteEl.value = item.note || '';
            const favInput = document.getElementById('ibanIsFavorite');
            if (favInput) favInput.checked = !!item.is_favorite;
            const easyType = document.getElementById('ibanEasyType');
            if (easyType) easyType.value = item.easy_address_type || '';
            const easyVal = document.getElementById('ibanEasyValue');
            if (easyVal) easyVal.value = item.easy_address || '';

            // If advanced fields exist, expand the advanced section
            const advSec = document.getElementById('ibanAdvancedSection');
            const advToggle = document.querySelector('.iban-advanced-toggle');
            if (item.easy_address || item.bank_name || item.note || item.category !== 'kendi_hesabim' || item.is_favorite) {
                if (advSec) advSec.classList.remove('hidden');
                if (advToggle) advToggle.classList.add('open');
            } else {
                if (advSec) advSec.classList.add('hidden');
                if (advToggle) advToggle.classList.remove('open');
            }

            const bankIndicator = document.getElementById('ibanBankIndicator');
            if (bankIndicator && item.bank_name) {
                bankIndicator.textContent = item.bank_name;
                bankIndicator.classList.remove('hidden');
            }

            if (typeof window.openModal === 'function') {
                window.openModal('ibanModal');
            } else {
                const modal = document.getElementById('ibanModal');
                if (modal) modal.classList.remove('hidden');
            }
        } else {
            showToast(data.message || 'IBAN bulunamadı.', 'error');
        }
    })
    .catch(err => {
        showToast('IBAN bilgisi alınırken hata: ' + err.message, 'error');
    });
}

function hideIbanModal() {
    if (typeof window.closeModal === 'function') {
        window.closeModal('ibanModal');
    } else {
        const modal = document.getElementById('ibanModal');
        if (modal) modal.classList.add('hidden');
    }
    const form = document.getElementById('ibanForm');
    if (form) form.reset();
}

function saveIban(triggerBtn) {
    if (window._isSavingIban) return;

    const idEl = document.getElementById('ibanId');
    const ibanId = idEl ? idEl.value : '';
    const form = document.getElementById('ibanForm');
    if (!form) return;

    const title = (document.getElementById('ibanTitle')?.value || '').trim();
    const iban = (document.getElementById('ibanNumber')?.value || '').trim();

    if (!title) {
        showToast('Lütfen hesap başlığı giriniz.', 'warning');
        document.getElementById('ibanTitle')?.focus();
        return;
    }
    if (!iban) {
        showToast('Lütfen geçerli bir IBAN giriniz.', 'warning');
        document.getElementById('ibanNumber')?.focus();
        return;
    }

    const submitBtn = triggerBtn || document.getElementById('btnSaveIban');
    window._isSavingIban = true;
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.classList.add('opacity-75', 'pointer-events-none');
        if (!submitBtn.dataset.originalHtml) submitBtn.dataset.originalHtml = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="inline-block animate-spin mr-1.5" aria-hidden="true">⏳</span> <span>Kaydediliyor...</span>';
    }

    function unlockIbanButton() {
        window._isSavingIban = false;
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('opacity-75', 'pointer-events-none');
            if (submitBtn.dataset.originalHtml) {
                submitBtn.innerHTML = submitBtn.dataset.originalHtml;
                delete submitBtn.dataset.originalHtml;
            }
        }
    }

    const formData = new FormData(form);
    const url = ibanId ? `/logbook/ibans/${ibanId}/update` : '/logbook/ibans/create';

    fetch(url, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errData => {
                throw new Error(errData.message || 'Kayıt başarısız.');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            hideIbanModal();
            showToast(data.message || 'IBAN başarıyla kaydedildi.', 'success');
            const targetUrl = new URL(window.location);
            targetUrl.searchParams.set('tab', 'ibans');
            window.location = targetUrl.toString();
        } else {
            unlockIbanButton();
            showToast(data.message || 'Kayıt başarısız.', 'error');
        }
    })
    .catch(err => {
        unlockIbanButton();
        showToast(err.message || 'İşlem sırasında hata oluştu.', 'error');
    });
}

function deleteIban(ibanId) {
    const confirmMessage = 'Bu IBAN numarasını silmek istediğinize emin misiniz?';
    function doDelete() {
        const formData = new FormData();
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        formData.append('csrf_token', csrfToken);

        fetch(`/logbook/ibans/${ibanId}/delete`, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast(data.message || 'IBAN silindi.', 'success');
                const targetUrl = new URL(window.location);
                targetUrl.searchParams.set('tab', 'ibans');
                window.location = targetUrl.toString();
            } else {
                showToast(data.message || 'Silme işlemi başarısız.', 'error');
            }
        })
        .catch(err => {
            showToast('Silme hatası: ' + err.message, 'error');
        });
    }

    if (typeof window.showGlobalConfirm === 'function') {
        window.showGlobalConfirm('IBAN Sil', confirmMessage, doDelete, true);
    } else if (confirm(confirmMessage)) {
        doDelete();
    }
}

function searchIbanCards(query) {
    const term = (query || '').trim().toLowerCase();
    const cards = document.querySelectorAll('.iban-card');
    cards.forEach(card => {
        const title = (card.querySelector('.iban-title')?.textContent || '').toLowerCase();
        const holder = (card.querySelector('.iban-holder')?.textContent || '').toLowerCase();
        const bank = (card.querySelector('.bank-badge')?.textContent || '').toLowerCase();
        const iban = (card.querySelector('.iban-text')?.textContent || '').toLowerCase().replace(/\s+/g, '');
        const note = (card.querySelector('.iban-note')?.textContent || '').toLowerCase();
        const easy = (card.querySelector('.iban-easy-address-val')?.textContent || '').toLowerCase();

        const matches = !term || title.includes(term) || holder.includes(term) || bank.includes(term) || iban.includes(term.replace(/\s+/g, '')) || note.includes(term) || easy.includes(term);
        card.style.display = matches ? '' : 'none';
    });
}

function filterIbanCategory(cat) {
    const cards = document.querySelectorAll('.iban-card');
    cards.forEach(card => {
        const category = card.getAttribute('data-category') || '';
        if (!cat || category === cat) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

// ==========================================================================
// Reminders & Special Days JS Controller
// ==========================================================================

function onReminderFrequencyChange(freq) {
    const grpDay = document.getElementById('grpReminderDay');
    const grpMonth = document.getElementById('grpReminderMonth');
    const grpDate = document.getElementById('grpReminderDate');

    if (freq === 'Aylık') {
        grpDay?.classList.remove('hidden');
        grpMonth?.classList.add('hidden');
        grpDate?.classList.add('hidden');
    } else if (freq === 'Yıllık') {
        grpDay?.classList.remove('hidden');
        grpMonth?.classList.remove('hidden');
        grpDate?.classList.add('hidden');
    } else if (freq === 'Tek Seferlik') {
        grpDay?.classList.add('hidden');
        grpMonth?.classList.add('hidden');
        grpDate?.classList.remove('hidden');
    }
}

const REMINDER_TEMPLATES = {
    'mtv1': {
        title: 'MTV (Motorlu Taşıtlar Vergisi) 1. Taksit',
        category: 'Sigorta / Vergi',
        frequency: 'Yıllık',
        due_month: 1,
        due_day: 31,
        note: '1. Taksit son ödeme günü (Gelir İdaresi Başkanlığı)'
    },
    'mtv2': {
        title: 'MTV (Motorlu Taşıtlar Vergisi) 2. Taksit',
        category: 'Sigorta / Vergi',
        frequency: 'Yıllık',
        due_month: 7,
        due_day: 31,
        note: '2. Taksit son ödeme günü (Gelir İdaresi Başkanlığı)'
    },
    'emlak1': {
        title: 'Emlak Vergisi 1. Taksit',
        category: 'Sigorta / Vergi',
        frequency: 'Yıllık',
        due_month: 5,
        due_day: 31,
        note: 'Belediye emlak vergisi 1. taksit son ödeme günü'
    },
    'emlak2': {
        title: 'Emlak Vergisi 2. Taksit',
        category: 'Sigorta / Vergi',
        frequency: 'Yıllık',
        due_month: 11,
        due_day: 30,
        note: 'Belediye emlak vergisi 2. taksit son ödeme günü'
    },
    'trafik': {
        title: 'Zorunlu Trafik Sigortası Yenileme',
        category: 'Sigorta / Vergi',
        frequency: 'Yıllık',
        due_month: new Date().getMonth() + 1,
        due_day: 15,
        note: 'Araç zorunlu trafik sigortası poliçe yenileme'
    },
    'kasko': {
        title: 'Kasko Poliçesi Yenileme',
        category: 'Sigorta / Vergi',
        frequency: 'Yıllık',
        due_month: new Date().getMonth() + 1,
        due_day: 15,
        note: 'Araç kasko poliçesi bitiş ve yenileme tarihi'
    },
    'dask': {
        title: 'DASK Zorunlu Deprem Sigortası',
        category: 'Sigorta / Vergi',
        frequency: 'Yıllık',
        due_month: new Date().getMonth() + 1,
        due_day: 15,
        note: 'Konut DASK deprem sigortası poliçe yenileme tarihi'
    },
    'kira_beyan': {
        title: 'Gelir Vergisi / Kira Beyannamesi',
        category: 'Sigorta / Vergi',
        frequency: 'Yıllık',
        due_month: 3,
        due_day: 31,
        note: 'Yıllık gelir vergisi beyannamesi ve 1. taksit son günü'
    },
    'arac_bakim': {
        title: 'Periyodik Araç Bakımı (10.000 KM)',
        category: 'Araç & Bakım',
        frequency: 'Yıllık',
        due_month: 5,
        due_day: 15,
        note: 'Motor yağı, filtreler, fren balataları kontrolü ve periyodik servis'
    },
    'tuvturk': {
        title: 'TÜVTÜRK Araç Muayenesi',
        category: 'Araç & Bakım',
        frequency: 'Tek Seferlik',
        note: 'Araç periyodik muayene ve randevu son günü'
    },
    'lastik_kis': {
        title: 'Kışlık Lastik Değişimi',
        category: 'Araç & Bakım',
        frequency: 'Yıllık',
        due_month: 11,
        due_day: 15,
        note: 'Zorunlu kış lastiği takılması (1 Aralık öncesi)'
    },
    'lastik_yaz': {
        title: 'Yazlık Lastik Değişimi',
        category: 'Araç & Bakım',
        frequency: 'Yıllık',
        due_month: 4,
        due_day: 15,
        note: 'Kışlık lastiklerin çıkarılıp yazlık lastiklerin takılması'
    },
    'egzoz': {
        title: 'Egzoz Gazı Emisyon Ölçümü',
        category: 'Araç & Bakım',
        frequency: 'Tek Seferlik',
        note: 'TÜVTÜRK öncesi egzoz emisyon pulu yenileme'
    }
};

function applyReminderTemplate(key) {
    const tpl = REMINDER_TEMPLATES[key];
    if (!tpl) return;

    const titleInput = document.getElementById('reminderTitle');
    if (titleInput) titleInput.value = tpl.title;

    const catSelect = document.getElementById('reminderCategory');
    if (catSelect) catSelect.value = tpl.category;

    const freqSelect = document.getElementById('reminderFrequency');
    if (freqSelect) {
        freqSelect.value = tpl.frequency;
        onReminderFrequencyChange(tpl.frequency);
    }

    const monthSelect = document.getElementById('reminderMonth');
    if (monthSelect && tpl.due_month) {
        monthSelect.value = tpl.due_month;
    }

    const dayInput = document.getElementById('reminderDay');
    if (dayInput && tpl.due_day) {
        dayInput.value = tpl.due_day;
    }

    const dateInput = document.getElementById('reminderDate');
    if (dateInput && tpl.due_date) {
        dateInput.value = tpl.due_date;
    }

    const noteInput = document.getElementById('reminderNote');
    if (noteInput && !noteInput.value) {
        noteInput.value = tpl.note;
    }

    if (window.ECuzdanHaptics) window.ECuzdanHaptics.light();
    if (typeof showToast === 'function') {
        showToast(`"${tpl.title}" şablonu uygulandı.`, 'info');
    }
}

function showCreateReminderModal() {
    const modalTitle = document.getElementById('reminderModalTitle');
    if (modalTitle) modalTitle.textContent = 'Yeni Hatırlatıcı Ekle';

    const form = document.getElementById('reminderForm');
    if (form) form.reset();

    const idInput = document.getElementById('reminderId');
    if (idInput) idInput.value = '';

    const curDocBox = document.getElementById('reminderCurrentDocBox');
    if (curDocBox) curDocBox.classList.add('hidden');

    const rmBox = document.getElementById('reminderRemoveDoc');
    if (rmBox) rmBox.checked = false;

    const docInput = document.getElementById('reminderDocument');
    if (docInput) docInput.value = '';

    const freqSelect = document.getElementById('reminderFrequency');
    if (freqSelect) {
        freqSelect.value = 'Aylık';
        onReminderFrequencyChange('Aylık');
    }

    if (typeof window.openModal === 'function') {
        window.openModal('reminderModal');
    } else {
        const m = document.getElementById('reminderModal');
        if (m) m.classList.remove('hidden');
    }

    setTimeout(() => {
        document.getElementById('reminderTitle')?.focus();
    }, 60);
}

function hideReminderModal() {
    if (typeof window.closeModal === 'function') {
        window.closeModal('reminderModal');
    } else {
        const m = document.getElementById('reminderModal');
        if (m) m.classList.add('hidden');
    }
}

function showEditReminderModal(id) {
    fetch(`/logbook/reminders/${id}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(r => {
        if (!r.ok) throw new Error('Hatırlatıcı bilgisi alınamadı.');
        return r.json();
    })
    .then(data => {
        if (!data.success || !data.reminder) {
            throw new Error(data.message || 'Kayıt bulunamadı.');
        }
        const rem = data.reminder;

        const modalTitle = document.getElementById('reminderModalTitle');
        if (modalTitle) modalTitle.textContent = 'Hatırlatıcıyı Düzenle';

        const idInput = document.getElementById('reminderId');
        if (idInput) idInput.value = rem.id;

        const titleInput = document.getElementById('reminderTitle');
        if (titleInput) titleInput.value = rem.title || '';

        const catSelect = document.getElementById('reminderCategory');
        if (catSelect) catSelect.value = rem.category || 'Genel';

        const freqSelect = document.getElementById('reminderFrequency');
        if (freqSelect) {
            freqSelect.value = rem.frequency || 'Aylık';
            onReminderFrequencyChange(rem.frequency || 'Aylık');
        }

        const dayInput = document.getElementById('reminderDay');
        if (dayInput && rem.due_day) dayInput.value = rem.due_day;

        const monthSelect = document.getElementById('reminderMonth');
        if (monthSelect && rem.due_month) monthSelect.value = rem.due_month;

        const dateInput = document.getElementById('reminderDate');
        if (dateInput && rem.due_date) dateInput.value = rem.due_date;

        const amtInput = document.getElementById('reminderAmount');
        if (amtInput) amtInput.value = rem.amount !== null && rem.amount !== undefined ? rem.amount : '';

        const noteInput = document.getElementById('reminderNote');
        if (noteInput) noteInput.value = rem.note || '';

        const curDocBox = document.getElementById('reminderCurrentDocBox');
        const previewLink = document.getElementById('reminderDocPreviewLink');
        const rmBox = document.getElementById('reminderRemoveDoc');
        const docInput = document.getElementById('reminderDocument');
        if (docInput) docInput.value = '';
        if (rmBox) rmBox.checked = false;

        if (rem.document_url && curDocBox && previewLink) {
            previewLink.href = rem.document_url;
            curDocBox.classList.remove('hidden');
        } else if (curDocBox) {
            curDocBox.classList.add('hidden');
        }

        if (typeof window.openModal === 'function') {
            window.openModal('reminderModal');
        } else {
            const m = document.getElementById('reminderModal');
            if (m) m.classList.remove('hidden');
        }
    })
    .catch(err => {
        showToast(err.message, 'error');
    });
}

function saveReminder(triggerBtn) {
    if (window._isSavingReminder) return;

    const form = document.getElementById('reminderForm');
    if (!form) return;

    const title = (document.getElementById('reminderTitle')?.value || '').trim();
    if (!title) {
        showToast('Lütfen bir başlık girin.', 'warning');
        document.getElementById('reminderTitle')?.focus();
        return;
    }

    const submitBtn = triggerBtn || document.getElementById('btnSaveReminder');
    window._isSavingReminder = true;
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.classList.add('opacity-75', 'pointer-events-none');
        if (!submitBtn.dataset.originalHtml) submitBtn.dataset.originalHtml = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="inline-block animate-spin mr-1.5" aria-hidden="true">⏳</span> <span>Kaydediliyor...</span>';
    }

    function unlockReminderButton() {
        window._isSavingReminder = false;
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('opacity-75', 'pointer-events-none');
            if (submitBtn.dataset.originalHtml) {
                submitBtn.innerHTML = submitBtn.dataset.originalHtml;
                delete submitBtn.dataset.originalHtml;
            }
        }
    }

    const reminderId = (document.getElementById('reminderId')?.value || '').trim();
    const url = reminderId ? `/logbook/reminders/${reminderId}/update` : '/logbook/reminders/create';

    const formData = new FormData(form);

    fetch(url, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            if (window.ECuzdanHaptics) window.ECuzdanHaptics.success();
            showToast(data.message || 'Hatırlatıcı kaydedildi.', 'success');
            hideReminderModal();
            const targetUrl = new URL(window.location);
            targetUrl.searchParams.set('tab', 'reminders');
            window.location = targetUrl.toString();
        } else {
            unlockReminderButton();
            if (window.ECuzdanHaptics) window.ECuzdanHaptics.error();
            showToast(data.message || 'Kaydetme işlemi başarısız.', 'error');
        }
    })
    .catch(err => {
        unlockReminderButton();
        if (window.ECuzdanHaptics) window.ECuzdanHaptics.error();
        showToast('Hata: ' + err.message, 'error');
    });
}

function toggleCompleteReminder(id) {
    fetch(`/logbook/reminders/${id}/toggle-complete`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            if (window.ECuzdanHaptics) window.ECuzdanHaptics.success();
            showToast(data.message, 'success');
            const targetUrl = new URL(window.location);
            targetUrl.searchParams.set('tab', 'reminders');
            window.location = targetUrl.toString();
        } else {
            showToast(data.message || 'Durum değiştirilemedi.', 'error');
        }
    })
    .catch(err => {
        showToast('Hata: ' + err.message, 'error');
    });
}

function deleteReminder(id) {
    const confirmMessage = 'Bu hatırlatıcıyı silmek istediğinize emin misiniz?';

    function doDelete() {
        fetch(`/logbook/reminders/${id}/delete`, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                if (window.ECuzdanHaptics) window.ECuzdanHaptics.heavy();
                showToast(data.message || 'Hatırlatıcı silindi.', 'success');
                const targetUrl = new URL(window.location);
                targetUrl.searchParams.set('tab', 'reminders');
                window.location = targetUrl.toString();
            } else {
                showToast(data.message || 'Silme işlemi başarısız.', 'error');
            }
        })
        .catch(err => {
            showToast('Silme hatası: ' + err.message, 'error');
        });
    }

    if (typeof window.showGlobalConfirm === 'function') {
        window.showGlobalConfirm('Hatırlatıcıyı Sil', confirmMessage, doDelete, true);
    } else if (confirm(confirmMessage)) {
        doDelete();
    }
}

function searchReminderCards(query) {
    const term = (query || '').trim().toLowerCase();
    const cards = document.querySelectorAll('.reminder-card');
    cards.forEach(card => {
        const searchData = (card.getAttribute('data-search') || '').toLowerCase();
        const matches = !term || searchData.includes(term);
        card.style.display = matches ? '' : 'none';
    });
}

function filterReminderCategory(cat) {
    const cards = document.querySelectorAll('.reminder-card');
    cards.forEach(card => {
        const category = card.getAttribute('data-category') || '';
        if (!cat || category === cat) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

function filterReminderStatus(status) {
    const cards = document.querySelectorAll('.reminder-card');
    cards.forEach(card => {
        const itemStatus = card.getAttribute('data-status') || 'active';
        if (!status || status === 'all' || itemStatus === status) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

function startTxFromReminder(title, amount, category) {
    if (typeof window.openQuickTxModal === 'function') {
        window.openQuickTxModal({
            description: title,
            amount: amount,
            type: 'Gider',
            category: category === 'Ödeme' || category === 'Fatura' ? 'Fatura' : 'Diğer'
        });
    } else {
        const form = document.getElementById('globalQuickTxForm');
        if (form) {
            const descInput = document.getElementById('globalQuickTxDesc') || form.querySelector('input[name="description"]');
            const amtInput = document.getElementById('globalQuickTxAmount');
            if (descInput) descInput.value = title;
            if (amtInput) amtInput.value = amount;
            if (typeof window.openModal === 'function') {
                window.openModal('quickTxModal');
            }
        }
    }
}

// ── TR Karekod / FAST IBAN QR Code Generator ─────────────────────────
let currentQrData = {
    title: '',
    holder: '',
    iban: '',
    formattedIban: '',
    bankName: '',
    mode: 'fast',
    amount: ''
};

function formatTlv(tag, value) {
    if (!value) return '';
    const valStr = String(value);
    const len = String(valStr.length).padStart(2, '0');
    return `${tag}${len}${valStr}`;
}

function computeCrc16(str) {
    let crc = 0xFFFF;
    for (let i = 0; i < str.length; i++) {
        let c = str.charCodeAt(i);
        crc ^= (c << 8);
        for (let j = 0; j < 8; j++) {
            if ((crc & 0x8000) !== 0) {
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF;
            } else {
                crc = (crc << 1) & 0xFFFF;
            }
        }
    }
    return crc.toString(16).toUpperCase().padStart(4, '0');
}

function buildFastPayload(iban, name, amount) {
    const cleanIban = String(iban || '').replace(/[^A-Za-z0-9]/g, '').toUpperCase();
    const cleanName = String(name || '').trim().toUpperCase();
    const hasAmt = amount && !isNaN(parseFloat(amount)) && parseFloat(amount) > 0;

    // Sub-TLVs for Tag 26 (FAST Transfer info)
    const subTlv = formatTlv('00', 'TR.FAST') +
                   formatTlv('01', cleanIban) +
                   (cleanName ? formatTlv('02', cleanName) : '');

    let payload = '000201' + // Payload Format Indicator
                  (hasAmt ? '010212' : '010211') + // Point of Initiation Method (12 dynamic, 11 static)
                  formatTlv('26', subTlv) +
                  '52040000' + // MCC
                  '5303949';   // Currency (TRY = 949)

    if (hasAmt) {
        payload += formatTlv('54', parseFloat(amount).toFixed(2));
    }

    payload += '5802TR' + // Country
               formatTlv('59', cleanName || 'ALICI') +
               formatTlv('60', 'TURKIYE') +
               '6304';

    const crc = computeCrc16(payload);
    return payload + crc;
}

function getActiveQrPayload() {
    const cleanIban = String(currentQrData.iban || '').replace(/[^A-Za-z0-9]/g, '').toUpperCase();
    const cleanName = (currentQrData.holder || currentQrData.title || '').trim();
    const amt = currentQrData.amount;

    if (currentQrData.mode === 'fast') {
        return buildFastPayload(cleanIban, cleanName, amt);
    } else {
        if (amt && !isNaN(parseFloat(amt)) && parseFloat(amt) > 0) {
            return `IBAN: ${currentQrData.formattedIban || cleanIban}\nAlıcı: ${cleanName}\nTutar: ${parseFloat(amt).toFixed(2)} TL`;
        }
        return `IBAN: ${currentQrData.formattedIban || cleanIban}\nAlıcı: ${cleanName}`;
    }
}

function renderIbanQr() {
    const container = document.getElementById('ibanQrSvgContainer');
    if (!container) return;

    const payload = getActiveQrPayload();
    if (!payload || typeof qrcode !== 'function') {
        container.innerHTML = '<div class="text-xs text-rose-500">QR kod üretilemedi.</div>';
        return;
    }

    try {
        const qr = qrcode(0, 'M');
        qr.addData(payload);
        qr.make();
        container.innerHTML = qr.createSvgTag({ scalable: true, margin: 1 });
        const svg = container.querySelector('svg');
        if (svg) {
            svg.setAttribute('width', '100%');
            svg.setAttribute('height', '100%');
            svg.classList.add('w-full', 'h-full');
        }
    } catch (err) {
        console.error('QR code generation error:', err);
        container.innerHTML = `<div class="text-xs text-rose-500">QR kod üretimi başarısız: ${err.message}</div>`;
    }
}

function showIbanQrModal(title, holder, iban, formattedIban, bankName) {
    currentQrData = {
        title: title || '',
        holder: holder || '',
        iban: iban || '',
        formattedIban: formattedIban || iban || '',
        bankName: bankName || '',
        mode: 'fast',
        amount: ''
    };

    const titleEl = document.getElementById('qrModalTitle');
    if (titleEl) titleEl.textContent = title;

    const bankBadge = document.getElementById('qrModalBankBadge');
    if (bankBadge) {
        if (bankName) {
            bankBadge.textContent = bankName;
            bankBadge.classList.remove('hidden');
        } else {
            bankBadge.classList.add('hidden');
        }
    }

    const holderEl = document.getElementById('qrModalHolder');
    if (holderEl) {
        holderEl.textContent = holder ? `👤 ${holder}` : '';
        holderEl.style.display = holder ? '' : 'none';
    }

    const ibanEl = document.getElementById('qrModalFormattedIban');
    if (ibanEl) ibanEl.textContent = formattedIban || iban;

    const amtInput = document.getElementById('qrAmountInput');
    if (amtInput) amtInput.value = '';

    setQrMode('fast', false);
    renderIbanQr();

    if (typeof window.openModal === 'function') {
        window.openModal('ibanQrModal');
    } else {
        const m = document.getElementById('ibanQrModal');
        if (m) m.classList.remove('hidden');
    }

    if (window.ECuzdanHaptics) window.ECuzdanHaptics.light();
}

function hideIbanQrModal() {
    if (typeof window.closeModal === 'function') {
        window.closeModal('ibanQrModal');
    } else {
        const m = document.getElementById('ibanQrModal');
        if (m) m.classList.add('hidden');
    }
}

function setQrMode(mode, reRender = true) {
    currentQrData.mode = mode;
    const tabFast = document.getElementById('qr-tab-fast');
    const tabPlain = document.getElementById('qr-tab-plain');

    if (mode === 'fast') {
        tabFast?.classList.add('bg-white', 'dark:bg-slate-700', 'text-indigo-600', 'dark:text-indigo-300', 'shadow-sm');
        tabFast?.classList.remove('text-slate-500', 'dark:text-slate-400');
        tabPlain?.classList.remove('bg-white', 'dark:bg-slate-700', 'text-indigo-600', 'dark:text-indigo-300', 'shadow-sm');
        tabPlain?.classList.add('text-slate-500', 'dark:text-slate-400');
    } else {
        tabPlain?.classList.add('bg-white', 'dark:bg-slate-700', 'text-indigo-600', 'dark:text-indigo-300', 'shadow-sm');
        tabPlain?.classList.remove('text-slate-500', 'dark:text-slate-400');
        tabFast?.classList.remove('bg-white', 'dark:bg-slate-700', 'text-indigo-600', 'dark:text-indigo-300', 'shadow-sm');
        tabFast?.classList.add('text-slate-500', 'dark:text-slate-400');
    }

    if (reRender) renderIbanQr();
}

function onQrAmountChange() {
    const amtInput = document.getElementById('qrAmountInput');
    currentQrData.amount = amtInput ? amtInput.value.trim() : '';
    renderIbanQr();
}

function copyQrPayload() {
    const payload = getActiveQrPayload();
    if (!payload) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(payload).then(() => {
            if (window.ECuzdanHaptics) window.ECuzdanHaptics.success();
            if (typeof showToast === 'function') {
                showToast('Karekod verisi panoya kopyalandı!', 'success');
            }
        });
    } else {
        copyText(payload, 'Karekod verisi kopyalandı!');
    }
}

function downloadQrSvg() {
    const container = document.getElementById('ibanQrSvgContainer');
    const svgEl = container?.querySelector('svg');
    if (!svgEl) return;
    const serializer = new XMLSerializer();
    const source = '<?xml version="1.0" standalone="no"?>\r\n' + serializer.serializeToString(svgEl);
    const url = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(source);
    const a = document.createElement('a');
    const cleanIban = String(currentQrData.iban || 'iban').replace(/[^A-Za-z0-9]/g, '');
    a.download = `FAST_QR_${cleanIban}.svg`;
    a.href = url;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    if (window.ECuzdanHaptics) window.ECuzdanHaptics.success();
    if (typeof showToast === 'function') {
        showToast('QR Kod SVG formatında indirildi.', 'success');
    }
}

