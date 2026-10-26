/* ==========================================================================
   E-Cüzdan — Categories & Taxonomy JavaScript (static/js/categories.js)
   Clean, User-Friendly Category Management, Search, Filters & Editing
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
    // ── Tab sistemi & Klavye Erişilebilirliği (a11y) ─────────────────────────
    const tabs = Array.from(document.querySelectorAll('.cat-tab'));
    tabs.forEach((tab, index) => {
        tab.addEventListener('click', () => {
            selectTab(tab);
        });

        // Klavye ile sekmeler arası geçiş (ArrowLeft, ArrowRight)
        tab.addEventListener('keydown', (e) => {
            let nextIndex = null;
            if (e.key === 'ArrowRight') {
                nextIndex = (index + 1) % tabs.length;
            } else if (e.key === 'ArrowLeft') {
                nextIndex = (index - 1 + tabs.length) % tabs.length;
            }
            if (nextIndex !== null) {
                e.preventDefault();
                tabs[nextIndex].focus();
                selectTab(tabs[nextIndex]);
            }
        });
    });

    function selectTab(tabOrName, updateUrl = true) {
        let tab = tabOrName;
        if (typeof tabOrName === 'string') {
            tab = document.querySelector(`.cat-tab[data-tab="${tabOrName}"]`);
        }
        if (!tab) return;
        const target = tab.dataset.tab;
        const allTabs = Array.from(document.querySelectorAll('.cat-tab'));
        allTabs.forEach(t => t.setAttribute('aria-selected', 'false'));
        document.querySelectorAll('.cat-panel').forEach(p => p.classList.remove('active'));
        tab.setAttribute('aria-selected', 'true');
        const targetPanel = document.querySelector(`[data-panel="${target}"]`);
        if (targetPanel) targetPanel.classList.add('active');
        if (updateUrl) {
            try {
                history.replaceState(null, '', '#' + target);
            } catch (e) {}
        }
    }
    window.selectTab = selectTab;

    // Escape tuşuna basıldığında aktif modalları veya düzenleme modunu kapat
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const catModal = document.getElementById('cat_modal');
            if (catModal && !catModal.classList.contains('hidden')) {
                closeCategoryModal();
                return;
            }
            const mergeModal = document.getElementById('merge_modal');
            if (mergeModal && !mergeModal.classList.contains('hidden')) {
                closeModal('merge_modal');
                return;
            }
            if (currentCatRow) cancelCatEdit();
            if (currentAssetTypeRow) cancelAssetTypeEdit();
            if (currentAssetSectorRow) cancelAssetSectorEdit();
        }
    });

    // ── Tür seçici event binding ──────────────────────────────────────────────
    document.querySelectorAll('input[name="type"][type="radio"]').forEach(radio => {
        radio.addEventListener('change', updateTypeVisual);
    });
    updateTypeVisual();

    // ── Renk paleti event binding ─────────────────────────────────────────────
    document.querySelectorAll('.color-dot').forEach(btn => {
        btn.addEventListener('click', function() {
            selectColor(this.dataset.color);
        });
    });
    document.querySelector('.color-clear-btn')?.addEventListener('click', function() {
        selectColor('');
    });

    // URL Hash sekme açılışı desteği (#categories, #asset-types, #sectors, #gl-reference)
    const initialHash = (window.location.hash || '').replace('#', '');
    if (initialHash) {
        const targetTab = tabs.find(t => t.dataset.tab === initialHash);
        if (targetTab) selectTab(targetTab, false);
    }

    // Form submit validation & whitespace trimming with double-submit lock
    const catForm = document.getElementById('cat_form');
    if (catForm) {
        catForm.addEventListener('submit', function(e) {
            if (catForm.dataset.submitting === 'true') {
                e.preventDefault();
                return;
            }
            const nameInput = document.getElementById('cat_name');
            if (!nameInput) return;
            const val = nameInput.value.trim();
            if (!val || val.length < 2) {
                e.preventDefault();
                alert('Kategori adı en az 2 karakter olmalıdır.');
                nameInput.focus();
                return;
            }
            if (val.length > 100) {
                e.preventDefault();
                alert('Kategori adı en fazla 100 karakter olabilir.');
                nameInput.focus();
                return;
            }
            nameInput.value = val;
            catForm.dataset.submitting = 'true';
            const submitBtn = catForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.classList.add('opacity-75', 'pointer-events-none');
            }
        });
    }

    // Başlangıç filtresi: Yalnızca aktifleri göster
    filterCats('all');
    updateParentCategoryOptions();
});

// ── Renk seçici ───────────────────────────────────────────────────────────
function selectColor(color) {
    const input = document.getElementById('cat_color');
    if (input) input.value = color || '';
    document.querySelectorAll('.color-dot').forEach(btn => {
        if (color && btn.dataset.color === color) {
            btn.classList.add('ring-2', 'ring-offset-2', 'ring-indigo-600', 'scale-110');
        } else {
            btn.classList.remove('ring-2', 'ring-offset-2', 'ring-indigo-600', 'scale-110');
        }
    });
}

// ── Üst Kategori Filtreleme (Seçilen Türe Göre Dinamik Eşleşme) ───────────
function updateParentCategoryOptions() {
    const selectedRadio = document.querySelector('input[name="type"][type="radio"]:checked');
    const standardInput = document.getElementById('cat_standard_type');
    const selectedType = (standardInput && !standardInput.disabled && standardInput.value)
        ? standardInput.value
        : (selectedRadio?.value || 'Gider');
    const parentSelect = document.getElementById('cat_parent_id');
    if (!parentSelect) return;
    const currentVal = parentSelect.value;
    Array.from(parentSelect.options).forEach(opt => {
        if (!opt.value) return; // 'Yok (Ana Kategori)' seçeneği her zaman aktif
        const optType = opt.dataset.type;
        const matches = !optType || optType === selectedType;
        opt.hidden = !matches;
        opt.disabled = !matches;
        if (!matches && opt.value === currentVal) {
            parentSelect.value = '';
        }
    });
}

// ── Tür seçici (radio buton görsel) ──────────────────────────────────────
function updateTypeVisual() {
    document.querySelectorAll('input[name="type"][type="radio"]').forEach(radio => {
        const div = radio.nextElementSibling;
        if (!div) return;
        if (radio.checked) {
            div.classList.add('border-current', 'shadow-sm');
        } else {
            div.classList.remove('border-current', 'shadow-sm');
        }
    });
    updateParentCategoryOptions();
}

// ── Kategori arama ────────────────────────────────────────────────────────
function searchCats(q) {
    const rows = document.querySelectorAll('#cats_tbody .cat-row');
    const lq = (q || '').toLowerCase();
    let visibleCount = 0;
    rows.forEach(row => {
        const name = (row.dataset.name || '').toLowerCase();
        const code = (row.dataset.code || '').toLowerCase();
        const matchesSearch = !lq || name.includes(lq) || code.includes(lq);
        const isActive = row.dataset.active !== 'false';
        let matchesFilter = true;
        if (activeFilter === 'archived') {
            matchesFilter = !isActive;
        } else {
            if (!isActive) {
                matchesFilter = false;
            } else if (activeFilter === 'budgeted') {
                matchesFilter = parseFloat(row.dataset.budget || '0') > 0;
            } else if (activeFilter === 'overbudget') {
                matchesFilter = row.dataset.overBudget === 'true' || parseFloat(row.dataset.pct || '0') > 100;
            } else if (activeFilter !== 'all') {
                matchesFilter = (row.dataset.type === activeFilter);
            }
        }
        const show = matchesSearch && matchesFilter;
        row.style.display = show ? '' : 'none';
        if (show) visibleCount++;
    });
    const countEl = document.getElementById('cats_count');
    if (countEl) countEl.textContent = visibleCount;

    const emptyRow = document.getElementById('cats_search_empty_row');
    if (emptyRow) {
        emptyRow.classList.toggle('hidden', visibleCount > 0);
    }
}

// ── Kategori filtrele (Gelir/Gider/Yatırım/Bütçeliler/Aşanlar/Arşivlenenler) ────────
let activeFilter = 'all';
function filterCats(type) {
    activeFilter = type;
    // Eğer kategoriler sekmesinde değilsek önce kategoriler sekmesine geç
    if (typeof window.selectTab === 'function') {
        window.selectTab('categories');
    }
    const searchVal = (document.getElementById('cat_search')?.value || '').toLowerCase();
    const rows = document.querySelectorAll('#cats_tbody .cat-row');
    let visibleCount = 0;
    rows.forEach(row => {
        const name = (row.dataset.name || '').toLowerCase();
        const code = (row.dataset.code || '').toLowerCase();
        const matchesSearch = !searchVal || name.includes(searchVal) || code.includes(searchVal);
        const isActive = row.dataset.active !== 'false';
        let matchesFilter = true;
        if (type === 'archived') {
            matchesFilter = !isActive;
        } else {
            if (!isActive) {
                matchesFilter = false;
            } else if (type === 'budgeted') {
                matchesFilter = parseFloat(row.dataset.budget || '0') > 0;
            } else if (type === 'overbudget') {
                matchesFilter = row.dataset.overBudget === 'true' || parseFloat(row.dataset.pct || '0') > 100;
            } else if (type !== 'all') {
                matchesFilter = (row.dataset.type === type);
            }
        }
        const show = matchesSearch && matchesFilter;
        row.style.display = show ? '' : 'none';
        if (show) visibleCount++;
    });
    const countEl = document.getElementById('cats_count');
    if (countEl) countEl.textContent = visibleCount;

    const emptyRow = document.getElementById('cats_search_empty_row');
    if (emptyRow) {
        emptyRow.classList.toggle('hidden', visibleCount > 0);
    }

    document.querySelectorAll('.filter-btn').forEach(btn => {
        const active = btn.dataset.filter === type;
        btn.classList.toggle('active', active);
        btn.classList.toggle('bg-slate-900', active);
        btn.classList.toggle('text-white', active);
        btn.classList.toggle('bg-slate-100', !active);
        btn.classList.toggle('text-slate-600', !active);
    });
}
window.filterCats = filterCats;

// ── Kategori Tablo Sıralaması ─────────────────────────────────────────────
let currentCatSort = { col: null, asc: true };

function sortCategoriesTable(col) {
    const tbody = document.getElementById('cats_tbody');
    if (!tbody) return;
    const rows = Array.from(tbody.querySelectorAll('.cat-row'));
    if (!rows.length) return;

    if (currentCatSort.col === col) {
        currentCatSort.asc = !currentCatSort.asc;
    } else {
        currentCatSort.col = col;
        currentCatSort.asc = true;
    }

    rows.sort((a, b) => {
        let valA = '';
        let valB = '';
        if (col === 'name') {
            valA = a.dataset.name || '';
            valB = b.dataset.name || '';
            return currentCatSort.asc ? valA.localeCompare(valB, 'tr') : valB.localeCompare(valA, 'tr');
        } else if (col === 'type') {
            valA = a.dataset.type || '';
            valB = b.dataset.type || '';
            return currentCatSort.asc ? valA.localeCompare(valB, 'tr') : valB.localeCompare(valA, 'tr');
        } else if (col === 'code') {
            valA = a.dataset.code || '';
            valB = b.dataset.code || '';
            return currentCatSort.asc ? valA.localeCompare(valB, 'tr') : valB.localeCompare(valA, 'tr');
        } else if (col === 'usage') {
            const numA = parseFloat(a.dataset.usage || '0');
            const numB = parseFloat(b.dataset.usage || '0');
            return currentCatSort.asc ? numA - numB : numB - numA;
        } else if (col === 'budget') {
            const pctA = parseFloat(a.dataset.pct || '0');
            const pctB = parseFloat(b.dataset.pct || '0');
            if (pctA !== pctB) {
                return currentCatSort.asc ? pctA - pctB : pctB - pctA;
            }
            const numA = parseFloat(a.dataset.budget || '0');
            const numB = parseFloat(b.dataset.budget || '0');
            return currentCatSort.asc ? numA - numB : numB - numA;
        }
        return 0;
    });

    rows.forEach(r => tbody.appendChild(r));

    // Sıralama göstergelerini güncelle
    ['name', 'type', 'code', 'usage', 'budget'].forEach(c => {
        const th = document.getElementById(`sort_cat_${c}`);
        if (!th) return;
        const ind = th.querySelector('.sort-indicator');
        if (!ind) return;
        if (c === col) {
            ind.textContent = currentCatSort.asc ? '▲' : '▼';
            ind.classList.remove('text-slate-400');
            ind.classList.add('text-indigo-600', 'font-black');
        } else {
            ind.textContent = '⇅';
            ind.classList.remove('text-indigo-600', 'font-black');
            ind.classList.add('text-slate-400');
        }
    });
}

// ── Kategorileri CSV Olarak Dışa Aktar ────────────────────────────────────
function exportCategoriesToCsv() {
    const rows = Array.from(document.querySelectorAll('#cats_tbody .cat-row')).filter(r => r.style.display !== 'none');
    if (!rows.length) {
        if (typeof window.showGlobalToast === 'function') {
            window.showGlobalToast('Dışa aktarılacak kategori bulunamadı', 'warning');
        } else {
            alert('Dışa aktarılacak kategori bulunamadı.');
        }
        return;
    }

    const headers = ['Kategori Adı', 'Tür', 'GL Kodu', 'Aylık Bütçe Limiti'];
    const csvRows = [headers.join(';')];

    rows.forEach(r => {
        const name = (r.querySelector('td:nth-child(1) span')?.textContent || '').trim();
        const type = (r.dataset.type || '').trim();
        const code = (r.dataset.code || '').trim().toUpperCase();
        const budget = (r.dataset.budget || '0').trim();
        csvRows.push([
            `"${name.replace(/"/g, '""')}"`,
            `"${type}"`,
            `"${code}"`,
            `"${budget}"`
        ].join(';'));
    });

    const blob = new Blob(['\uFEFF' + csvRows.join('\r\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kategoriler_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ── Kategori Düzenle ──────────────────────────────────────────────────────
let currentCatRow = null;

function editCategoryFromElement(el) {
    if (!el) return;
    const row = el.closest('tr');
    if (!row) return;
    const d = row.dataset;
    const id = parseInt(d.id, 10);
    const name = d.rawName || d.name || '';
    const type = d.type || 'Gider';
    const code = d.rawCode || d.code || '';
    const budget = parseFloat(d.budget || '0') > 0 ? d.budget : '';
    const version = parseInt(d.version || '1', 10);
    const isStandard = d.standard === 'true';
    const parentId = d.parentId || '';
    const color = d.color || '';
    const icon = d.icon || '';
    editCategory(id, name, type, code, budget, version, isStandard, parentId, color, icon, el);
}

function editCategory(id, name, type, code, budgetLimit, version, isStandard, parentId, color, icon, btn) {
    if (currentCatRow) currentCatRow.classList.remove('edit-mode-active');
    const row = btn ? btn.closest('tr') : null;
    if (row) {
        row.classList.add('edit-mode-active');
        currentCatRow = row;
    }

    const catIdInput = document.getElementById('cat_id');
    const catNameInput = document.getElementById('cat_name');
    const catCodeInput = document.getElementById('cat_code');
    const catBudgetInput = document.getElementById('cat_budget_limit');
    const catVersionInput = document.getElementById('cat_version');
    const catActionInput = document.getElementById('cat_action');
    const catForm = document.getElementById('cat_form');

    if (catIdInput) catIdInput.value = id;
    if (catNameInput) catNameInput.value = name;
    if (catCodeInput) catCodeInput.value = code || '';
    if (catBudgetInput) catBudgetInput.value = budgetLimit || '';
    if (catVersionInput) catVersionInput.value = version || 1;
    if (catActionInput) catActionInput.value = 'update_cat';
    if (catForm) catForm.action = '/update_category/' + id;

    const standardTypeInput = document.getElementById('cat_standard_type');
    const typeRadios = document.querySelectorAll('input[name="type"][type="radio"]');
    typeRadios.forEach(r => {
        r.checked = (r.value === type);
        r.disabled = Boolean(isStandard);
    });
    if (standardTypeInput) {
        standardTypeInput.value = type;
        standardTypeInput.disabled = !isStandard;
    }
    if (catNameInput) {
        catNameInput.readOnly = Boolean(isStandard);
        catNameInput.classList.toggle('bg-slate-100', Boolean(isStandard));
    }
    if (catCodeInput) {
        catCodeInput.readOnly = Boolean(isStandard);
        catCodeInput.classList.toggle('bg-slate-100', Boolean(isStandard));
    }
    if (catBudgetInput) catBudgetInput.disabled = false;

    const parentSelect = document.getElementById('cat_parent_id');
    if (parentSelect) {
        parentSelect.value = parentId || '';
        parentSelect.disabled = Boolean(isStandard);
        Array.from(parentSelect.options).forEach(opt => {
            opt.disabled = (opt.value && opt.value == id);
        });
    }

    selectColor(color || '');

    const iconSelect = document.getElementById('cat_icon');
    if (iconSelect) {
        iconSelect.value = icon || '';
        iconSelect.disabled = Boolean(isStandard);
    }

    updateTypeVisual();

    const titleEl = document.getElementById('cat_form_title');
    if (titleEl) {
        titleEl.textContent = isStandard ? 'Standart Kategori Bütçesini Düzenle' : 'Kategoriyi Düzenle';
    }
    const hintEl = document.getElementById('cat_edit_hint');
    if (hintEl) {
        hintEl.classList.remove('hidden');
        const span = hintEl.querySelector('span');
        if (span) {
            span.textContent = isStandard
                ? 'Standart kategori korunur; yalnızca aylık bütçe güncellenebilir.'
                : 'Düzenleme modu aktif — değişiklikler kaydedilecek';
        }
    }
    const btn2 = document.getElementById('cat_submit_btn');
    if (btn2) {
        btn2.textContent = isStandard ? 'AYLIK BÜTÇEYİ KAYDET' : 'KATEGORİYİ GÜNCELLE';
        btn2.classList.add('bg-amber-600');
        btn2.classList.remove('hover:bg-indigo-600');
    }
    const cancelBtn = document.getElementById('cat_cancel_btn');
    if (cancelBtn) cancelBtn.classList.remove('hidden');
    const advDetails = document.getElementById('cat_advanced_fields');
    if (advDetails) advDetails.open = true;

    const subTitleEl = document.getElementById('cat_modal_subtitle');
    if (subTitleEl) {
        subTitleEl.textContent = isStandard
            ? 'Standart sistem kategorisi. Yalnızca aylık bütçe limitini belirleyebilirsiniz.'
            : 'Kategori adını, türünü ve bütçe ayarlarını güncelleyin.';
    }

    openCategoryModal();

    const clickedBudget = btn && btn.closest && (btn.closest('td')?.cellIndex === 4 || btn.classList.contains('group'));
    if (isStandard || clickedBudget) {
        if (catBudgetInput) setTimeout(() => { catBudgetInput.focus(); catBudgetInput.select(); }, 150);
    } else {
        if (catNameInput) setTimeout(() => catNameInput.focus(), 150);
    }
}

function cancelCatEdit() {
    if (currentCatRow) {
        currentCatRow.classList.remove('edit-mode-active');
        currentCatRow = null;
    }
    const form = document.getElementById('cat_form');
    if (form) {
        form.reset();
        form.dataset.submitting = 'false';
        delete form.dataset.submitting;
        form.action = '/categories';
    }
    ['cat_id', 'cat_code', 'cat_budget_limit', 'cat_version', 'cat_standard_type'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    const catNameInput = document.getElementById('cat_name');
    const catCodeInput = document.getElementById('cat_code');
    if (catNameInput) {
        catNameInput.readOnly = false;
        catNameInput.classList.remove('bg-slate-100');
    }
    if (catCodeInput) {
        catCodeInput.readOnly = false;
        catCodeInput.classList.remove('bg-slate-100');
    }
    document.querySelectorAll('input[name="type"][type="radio"]').forEach(r => {
        r.disabled = false;
        if (r.value === 'Gider') r.checked = true;
    });
    const standardType = document.getElementById('cat_standard_type');
    if (standardType) standardType.disabled = true;
    const catAction = document.getElementById('cat_action');
    if (catAction) catAction.value = 'add_cat';
    const formTitle = document.getElementById('cat_form_title');
    if (formTitle) formTitle.textContent = 'Yeni Kategori Ekle';
    const subTitleEl = document.getElementById('cat_modal_subtitle');
    if (subTitleEl) subTitleEl.textContent = 'Gelir, gider veya yatırım işlemleriniz için kategori tanımlayın';
    const editHint = document.getElementById('cat_edit_hint');
    if (editHint) editHint.classList.add('hidden');
    const btn = document.getElementById('cat_submit_btn');
    if (btn) {
        btn.textContent = 'Kategori Oluştur';
        btn.disabled = false;
        btn.classList.remove('bg-amber-600', 'opacity-75', 'pointer-events-none');
        btn.classList.add('hover:bg-indigo-600');
    }

    const parentSelect = document.getElementById('cat_parent_id');
    if (parentSelect) {
        parentSelect.value = '';
        parentSelect.disabled = false;
        Array.from(parentSelect.options).forEach(opt => { opt.disabled = false; });
    }

    selectColor('');

    const iconSelect = document.getElementById('cat_icon');
    if (iconSelect) {
        iconSelect.value = '';
        iconSelect.disabled = false;
    }

    updateTypeVisual();

    const advDetails = document.getElementById('cat_advanced_fields');
    if (advDetails) advDetails.open = false;
}

// ── Kategori Birleştirme Modal & İşlemi ──────────────────────────────────
function openMergeModal(sourceId = null, sourceName = '') {
    const sourceSelect = document.getElementById('merge_source_id');
    if (sourceSelect && sourceId) {
        sourceSelect.value = sourceId;
    }
    updateMergeTargetOptions();
    if (typeof window.openModal === 'function') {
        window.openModal('merge_modal');
    } else {
        const modal = document.getElementById('merge_modal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.style.display = 'flex';
        }
    }
}

function updateMergeTargetOptions() {
    const sourceSelect = document.getElementById('merge_source_id');
    const targetSelect = document.getElementById('merge_target_id');
    if (!sourceSelect || !targetSelect) return;
    const selectedSource = sourceSelect.value;
    Array.from(targetSelect.options).forEach(opt => {
        if (opt.value && opt.value === selectedSource) {
            opt.disabled = true;
            if (targetSelect.value === opt.value) {
                targetSelect.value = '';
            }
        } else {
            opt.disabled = false;
        }
    });
}

// ── Kategori Geri Yükle (Arşivden Çıkar) ───────────────────────────────────
function restoreCategory(id, name) {
    const endpoint = '/restore_category/' + id;
    const execute = () => {
        const csrfToken = getCsrfToken();
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-CSRF-Token': csrfToken
            }
        }).then(res => {
            if (res.ok) {
                window.location.reload();
            } else {
                return res.json().then(data => {
                    alert(data.message || 'Kategori geri yüklenemedi.');
                }).catch(() => {
                    alert('Kategori geri yüklenirken bir hata oluştu.');
                });
            }
        }).catch(err => {
            console.error('Kategori geri yükleme hatası:', err);
            alert('Ağ hatası: Kategori geri yüklenemedi.');
        });
    };
    if (typeof window.showGlobalConfirm === 'function') {
        window.showGlobalConfirm('Kategori Geri Yükle', `"${name}" kategorisini arşivden geri yüklemek istiyor musunuz?`, execute, false);
    } else if (confirm(`"${name}" kategorisini arşivden geri yüklemek istiyor musunuz?`)) {
        execute();
    }
}

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
        || document.querySelector('input[name="csrf_token"]')?.value
        || '';
}

function confirmDeleteCategory(id, name) {
    const endpoint = window.ECuzdanEndpoints ? window.ECuzdanEndpoints.categories.delete(id) : ('/delete_category/' + id);
    const execute = () => {
        const csrfToken = getCsrfToken();
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-CSRF-Token': csrfToken
            }
        }).then(res => {
            if (res.ok) {
                window.location.reload();
            } else {
                return res.json().then(data => {
                    alert(data.message || 'Kategori silinemedi.');
                }).catch(() => {
                    alert('Kategori silinirken bir hata oluştu.');
                });
            }
        }).catch(err => {
            console.error('Kategori silme hatası:', err);
            alert('Ağ hatası: Kategori silinemedi.');
        });
    };
    if (typeof window.showGlobalConfirm === 'function') {
        window.showGlobalConfirm('Kategori Sil', `"${name}" kategorisini silmek istediğinizden emin misiniz?`, execute, true);
    } else if (confirm(`"${name}" kategorisini silmek istiyor musunuz?`)) {
        execute();
    }
}

// ── Varlık Sınıfı ─────────────────────────────────────────────────────────
let currentAssetTypeRow = null;

function editAssetType(id, name, btn) {
    if (currentAssetTypeRow) currentAssetTypeRow.classList.remove('edit-mode-active');
    const row = btn ? btn.closest('tr') : null;
    if (row) {
        row.classList.add('edit-mode-active');
        currentAssetTypeRow = row;
    }

    const idInput = document.getElementById('asset_type_id');
    const nameInput = document.getElementById('asset_type_name');
    const actionInput = document.getElementById('asset_type_action');
    const form = document.getElementById('asset_type_form');

    if (idInput) idInput.value = id;
    if (nameInput) nameInput.value = name;
    if (actionInput) actionInput.value = 'update_asset_type';
    if (form) form.action = '/update_asset_type/' + id;

    const titleEl = document.getElementById('asset_type_form_title');
    if (titleEl) titleEl.textContent = 'Varlık Sınıfını Düzenle';
    const hintEl = document.getElementById('asset_type_edit_hint');
    if (hintEl) hintEl.classList.remove('hidden');
    const btn2 = document.getElementById('asset_type_submit_btn');
    if (btn2) {
        btn2.textContent = 'SINIFI GÜNCELLE';
        btn2.classList.add('bg-amber-600');
        btn2.classList.remove('hover:bg-emerald-600');
    }
    const cancelBtn = document.getElementById('asset_type_cancel_btn');
    if (cancelBtn) cancelBtn.classList.remove('hidden');
    if (nameInput) setTimeout(() => nameInput.focus(), 100);
}

function cancelAssetTypeEdit() {
    if (currentAssetTypeRow) {
        currentAssetTypeRow.classList.remove('edit-mode-active');
        currentAssetTypeRow = null;
    }
    const form = document.getElementById('asset_type_form');
    if (form) form.reset();
    const idInput = document.getElementById('asset_type_id');
    const actionInput = document.getElementById('asset_type_action');
    if (idInput) idInput.value = '';
    if (actionInput) actionInput.value = 'add_asset_type';
    if (form) form.action = '/categories';
    const titleEl = document.getElementById('asset_type_form_title');
    if (titleEl) titleEl.textContent = 'Yeni Varlık Sınıfı';
    const hintEl = document.getElementById('asset_type_edit_hint');
    if (hintEl) hintEl.classList.add('hidden');
    const btn = document.getElementById('asset_type_submit_btn');
    if (btn) {
        btn.textContent = 'Sınıf Oluştur';
        btn.classList.remove('bg-amber-600');
        btn.classList.add('hover:bg-emerald-600');
    }
    const cancelBtn = document.getElementById('asset_type_cancel_btn');
    if (cancelBtn) cancelBtn.classList.add('hidden');
}

function confirmDeleteAssetType(id, name) {
    const endpoint = '/delete_asset_type/' + id;
    const execute = () => {
        const csrfToken = getCsrfToken();
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-CSRF-Token': csrfToken
            }
        }).then(res => {
            if (res.ok) {
                window.location.reload();
            } else {
                return res.json().then(data => {
                    alert(data.message || 'Varlık sınıfı silinemedi.');
                }).catch(() => {
                    alert('Varlık sınıfı silinirken bir hata oluştu.');
                });
            }
        }).catch(err => {
            console.error('Varlık sınıfı silme hatası:', err);
            alert('Ağ hatası: Varlık sınıfı silinemedi.');
        });
    };
    if (typeof window.showGlobalConfirm === 'function') {
        window.showGlobalConfirm('Varlık Sınıfı Sil', `"${name}" sınıfını silmek istediğinizden emin misiniz?`, execute, true);
    } else if (confirm(`"${name}" sınıfını silmek istiyor musunuz?`)) {
        execute();
    }
}

// ── Varlık Sektörü ─────────────────────────────────────────────────────────
let currentAssetSectorRow = null;

function editAssetSector(id, name, btn) {
    if (currentAssetSectorRow) currentAssetSectorRow.classList.remove('edit-mode-active');
    const row = btn ? btn.closest('tr') : null;
    if (row) {
        row.classList.add('edit-mode-active');
        currentAssetSectorRow = row;
    }

    const idInput = document.getElementById('asset_sector_id');
    const nameInput = document.getElementById('asset_sector_name');
    const actionInput = document.getElementById('asset_sector_action');
    const form = document.getElementById('asset_sector_form');

    if (idInput) idInput.value = id;
    if (nameInput) nameInput.value = name;
    if (actionInput) actionInput.value = 'update_asset_sector';
    if (form) form.action = '/update_asset_sector/' + id;

    const titleEl = document.getElementById('asset_sector_form_title');
    if (titleEl) titleEl.textContent = 'Sektörü Düzenle';
    const hintEl = document.getElementById('asset_sector_edit_hint');
    if (hintEl) hintEl.classList.remove('hidden');
    const btn2 = document.getElementById('asset_sector_submit_btn');
    if (btn2) {
        btn2.textContent = 'SEKTÖRÜ GÜNCELLE';
        btn2.classList.add('bg-amber-600');
        btn2.classList.remove('hover:bg-amber-600');
    }
    const cancelBtn = document.getElementById('asset_sector_cancel_btn');
    if (cancelBtn) cancelBtn.classList.remove('hidden');
    if (nameInput) setTimeout(() => nameInput.focus(), 100);
}

function cancelAssetSectorEdit() {
    if (currentAssetSectorRow) {
        currentAssetSectorRow.classList.remove('edit-mode-active');
        currentAssetSectorRow = null;
    }
    const form = document.getElementById('asset_sector_form');
    if (form) form.reset();
    const idInput = document.getElementById('asset_sector_id');
    const actionInput = document.getElementById('asset_sector_action');
    if (idInput) idInput.value = '';
    if (actionInput) actionInput.value = 'add_asset_sector';
    if (form) form.action = '/categories';
    const titleEl = document.getElementById('asset_sector_form_title');
    if (titleEl) titleEl.textContent = 'Yeni Sektör';
    const hintEl = document.getElementById('asset_sector_edit_hint');
    if (hintEl) hintEl.classList.add('hidden');
    const btn = document.getElementById('asset_sector_submit_btn');
    if (btn) {
        btn.textContent = 'Sektör Oluştur';
        btn.classList.remove('bg-amber-600');
    }
    const cancelBtn = document.getElementById('asset_sector_cancel_btn');
    if (cancelBtn) cancelBtn.classList.add('hidden');
}

function confirmDeleteAssetSector(id, name) {
    const endpoint = window.ECuzdanEndpoints ? window.ECuzdanEndpoints.categories.deleteAssetSector(id) : ('/delete_asset_sector/' + id);
    const execute = () => {
        const csrfToken = getCsrfToken();
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-CSRF-Token': csrfToken
            }
        }).then(res => {
            if (res.ok) {
                window.location.reload();
            } else {
                return res.json().then(data => {
                    alert(data.message || 'Sektör silinemedi.');
                }).catch(() => {
                    alert('Sektör silinirken bir hata oluştu.');
                });
            }
        }).catch(err => {
            console.error('Sektör silme hatası:', err);
            alert('Ağ hatası: Sektör silinemedi.');
        });
    };
    if (typeof window.showGlobalConfirm === 'function') {
        window.showGlobalConfirm('Sektör Sil', `"${name}" sektörünü silmek istediğinizden emin misiniz?`, execute, true);
    } else if (confirm(`"${name}" sektörünü silmek istiyor musunuz?`)) {
        execute();
    }
}

// ── Kategori Ekleme / Düzenleme Modal Yöneticisi ────────────────────────────
function openCategoryModal() {
    if (typeof window.openModal === 'function') {
        window.openModal('cat_modal');
    } else {
        const modal = document.getElementById('cat_modal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('active');
            modal.style.display = 'flex';
        }
    }
}

function closeCategoryModal() {
    if (typeof window.closeModal === 'function') {
        window.closeModal('cat_modal');
    } else {
        const modal = document.getElementById('cat_modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('active');
            modal.style.display = '';
        }
    }
    cancelCatEdit();
}

function openCreateCategoryModal() {
    cancelCatEdit();
    openCategoryModal();
    const nameInput = document.getElementById('cat_name');
    if (nameInput) setTimeout(() => nameInput.focus(), 150);
}

function handleCatModalBackdropClick(e) {
    if (e.target && e.target.id === 'cat_modal') {
        closeCategoryModal();
    }
}
