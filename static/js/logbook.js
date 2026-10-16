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
    
    // ESC key listener for modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
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

function saveEntry() {
    const entryIdEl = document.getElementById('entryId');
    const entryId = entryIdEl ? entryIdEl.value : '';
    const form = document.getElementById('entryForm');
    if (!form) return;
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
            showToast(data.message || logbookT('logbook_save_failed'), 'error');
        }
    })
    .catch(error => {
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
