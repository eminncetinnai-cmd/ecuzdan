/* ============================================================
   E-Cüzdan · layout-core.js
   layout.html içinden ayrıştırıldı. Senkron (defer'siz) yüklenir;
   showToast / confirm / hesap makinesi / hızlı işlem gibi global
   fonksiyonlar type=module scriptlerinden ÖNCE hazır olmalıdır.
   ============================================================ */
/* ============================================================
   CORE GLOBAL FUNCTIONS - Inline, no module dependency
   Bu fonksiyonlar type=module beklenmeden anında kullanılabilir
============================================================ */

// ---- TOAST ----
window.showToast = function(message, type, duration) {
    type = type || 'success';
    duration = duration || 4000;
    const container = document.getElementById('toast-container');
    if (!container) return;

    const colors = {
        success: 'bg-emerald-600 text-white',
        error:   'bg-rose-600 text-white',
        warning: 'bg-amber-500 text-white',
        info:    'bg-sky-600 text-white'
    };
    const icons = {
        success: '<svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>',
        error:   '<svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>',
        warning: '<svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>',
        info:    '<svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
    };
    const el = document.createElement('div');
    el.className = 'flex items-center gap-3 px-4 py-3 rounded-xl shadow-xl font-bold text-sm max-w-sm transition-all duration-300 translate-x-full opacity-0 ' + (colors[type] || colors.success);
    el.style.position = 'relative';
    el.innerHTML = (icons[type] || icons.success) + '<span class="flex-1">' + message + '</span>';
    const closeBtn = document.createElement('button');
    closeBtn.setAttribute('data-macro', 'button_icon');
    closeBtn.type = 'button';
    closeBtn.className = 'opacity-70 hover:opacity-100 transition ml-2 flex-shrink-0';
    closeBtn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>';
    el.appendChild(closeBtn);
    // Progress bar
    const progress = document.createElement('div');
    progress.style.cssText = 'position:absolute;bottom:0;left:0;height:3px;border-radius:0 0 0.75rem 0.75rem;background:rgba(255,255,255,0.4);animation:toastProgress ' + duration + 'ms linear forwards';
    el.appendChild(progress);
    container.appendChild(el);

    var _dismissToast = function(toastEl) {
        toastEl.classList.add('translate-x-full', 'opacity-0');
        setTimeout(function() { if (toastEl.parentNode) toastEl.remove(); }, 400);
    };
    closeBtn.onclick = function() { _dismissToast(el); };

    requestAnimationFrame(function() {
        requestAnimationFrame(function() {
            el.classList.remove('translate-x-full', 'opacity-0');
        });
    });

    setTimeout(function() { _dismissToast(el); }, duration);
};

// ---- MODAL OPEN / CLOSE ----
window.openModal = function(modalId) {
    var modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.remove('hidden');
    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');
    if (modal.classList.contains('edit-modal') ||
        modal.classList.contains('delete-modal') ||
        modal.classList.contains('modal-overlay') ||
        modal.classList.contains('modal')) {
        modal.style.display = 'flex';
    } else {
        modal.style.display = 'block';
    }
    document.body.style.overflow = 'hidden';
    document.documentElement.classList.add('modal-open');
};

window.closeModal = function(modalId) {
    var closeOne = function(modal) {
        modal.classList.remove('active');
        modal.classList.add('hidden');
        modal.setAttribute('aria-hidden', 'true');
        modal.style.display = '';
    };
    if (modalId) {
        var m = document.getElementById(modalId);
        if (m) closeOne(m);
    } else {
        document.querySelectorAll('.modal.active, .edit-modal.active, .delete-modal.active, .modal-overlay.active, .notification-modal.active, .asset-modal.active, [role="dialog"].active').forEach(closeOne);
    }
    var stillOpen = document.querySelector('.modal.active, .edit-modal.active, .delete-modal.active, .modal-overlay.active, .notification-modal.active, .asset-modal.active, [role="dialog"].active');
    if (!stillOpen) {
        document.body.style.overflow = '';
        document.documentElement.classList.remove('modal-open');
    }
};

// ---- CALCULATOR ----
var calculatorState = {
    current: '0',
    previous: '',
    operator: null,
    waitingForOperand: false,
    history: ''
};

window.openCalculator = function() {
    var modal = document.getElementById('calculatorModal');
    if (!modal) return;
    modal.classList.remove('hidden');
    modal.classList.add('active');
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    document.documentElement.classList.add('modal-open');
    calculatorClear();
};

window.closeCalculator = function() {
    var modal = document.getElementById('calculatorModal');
    if (!modal) return;
    modal.classList.remove('active');
    modal.classList.add('hidden');
    modal.style.display = '';
    var stillOpen = document.querySelector('.modal.active, .edit-modal.active, .delete-modal.active, .modal-overlay.active, .notification-modal.active, .asset-modal.active, [role="dialog"].active');
    if (!stillOpen) {
        document.body.style.overflow = '';
        document.documentElement.classList.remove('modal-open');
    }
};

window.updateCalculatorDisplay = function() {
    var display = document.getElementById('calculatorDisplay');
    var history = document.getElementById('calculatorHistory');
    if (display) {
        display.textContent = calculatorState.current;
    }
    if (history) {
        history.textContent = calculatorState.history;
    }
};

window.calculatorNumber = function(num) {
    if (calculatorState.waitingForOperand) {
        calculatorState.current = num;
        calculatorState.waitingForOperand = false;
    } else {
        calculatorState.current = calculatorState.current === '0' ? num : calculatorState.current + num;
    }
    updateCalculatorDisplay();
};

window.calculatorOperator = function(op) {
    var current = parseFloat(calculatorState.current);
    if (calculatorState.operator && !calculatorState.waitingForOperand) {
        var previous = parseFloat(calculatorState.previous);
        var result;
        switch (calculatorState.operator) {
            case '+': result = previous + current; break;
            case '-': result = previous - current; break;
            case '*': result = previous * current; break;
            case '/': result = previous / current; break;
        }
        calculatorState.current = String(result);
        calculatorState.previous = '';
    } else {
        calculatorState.previous = calculatorState.current;
    }

    // Operatör sembolünü güncelle
    var opSymbol = '';
    switch(op) {
        case '+': opSymbol = '+'; break;
        case '-': opSymbol = '−'; break;
        case '*': opSymbol = '×'; break;
        case '/': opSymbol = '÷'; break;
    }

    calculatorState.history = calculatorState.previous + ' ' + opSymbol;
    calculatorState.operator = op;
    calculatorState.waitingForOperand = true;
    updateCalculatorDisplay();
};

window.calculatorDecimal = function() {
    if (calculatorState.waitingForOperand) {
        calculatorState.current = '0.';
        calculatorState.waitingForOperand = false;
    } else if (calculatorState.current.indexOf('.') === -1) {
        calculatorState.current += '.';
    }
    updateCalculatorDisplay();
};

window.calculatorClear = function() {
    calculatorState.current = '0';
    calculatorState.previous = '';
    calculatorState.operator = null;
    calculatorState.waitingForOperand = false;
    calculatorState.history = '';
    updateCalculatorDisplay();
};

window.calculatorBackspace = function() {
    if (calculatorState.waitingForOperand) {
        calculatorState.operator = null;
        calculatorState.waitingForOperand = false;
        calculatorState.history = '';
    } else if (calculatorState.current.length > 1) {
        calculatorState.current = calculatorState.current.slice(0, -1);
    } else {
        calculatorState.current = '0';
    }
    updateCalculatorDisplay();
};

window.calculatorEquals = function() {
    if (!calculatorState.operator || calculatorState.waitingForOperand) return;
    var current = parseFloat(calculatorState.current);
    var previous = parseFloat(calculatorState.previous);
    var result;
    switch (calculatorState.operator) {
        case '+': result = previous + current; break;
        case '-': result = previous - current; break;
        case '*': result = previous * current; break;
        case '/': result = current !== 0 ? previous / current : 'Error'; break;
    }

    // Geçmişe işlemi ekle
    var opSymbol = '';
    switch (calculatorState.operator) {
        case '+': opSymbol = '+'; break;
        case '-': opSymbol = '−'; break;
        case '*': opSymbol = '×'; break;
        case '/': opSymbol = '÷'; break;
    }
    calculatorState.history = calculatorState.previous + ' ' + opSymbol + ' ' + current + ' =';

    calculatorState.current = String(result);
    calculatorState.previous = '';
    calculatorState.operator = null;
    calculatorState.waitingForOperand = true;
    updateCalculatorDisplay();
};

// Klavye desteği
document.addEventListener('keydown', function(e) {
    var modal = document.getElementById('calculatorModal');
    if (!modal || modal.classList.contains('hidden')) return;

    var key = e.key;

    // Sayılar
    if (key >= '0' && key <= '9') {
        e.preventDefault();
        calculatorNumber(key);
    }
    // Ondalık nokta
    else if (key === '.' || key === ',') {
        e.preventDefault();
        calculatorDecimal();
    }
    // Operatörler
    else if (key === '+') {
        e.preventDefault();
        calculatorOperator('+');
    }
    else if (key === '-') {
        e.preventDefault();
        calculatorOperator('-');
    }
    else if (key === '*') {
        e.preventDefault();
        calculatorOperator('*');
    }
    else if (key === '/') {
        e.preventDefault();
        calculatorOperator('/');
    }
    // Enter veya = için eşittir
    else if (key === 'Enter' || key === '=') {
        e.preventDefault();
        calculatorEquals();
    }
    // Backspace
    else if (key === 'Backspace') {
        e.preventDefault();
        calculatorBackspace();
    }
    // Escape ile kapat
    else if (key === 'Escape') {
        e.preventDefault();
        closeCalculator();
    }
    // Delete veya C ile temizle
    else if (key === 'Delete' || key.toLowerCase() === 'c') {
        e.preventDefault();
        calculatorClear();
    }
});

// ---- GLOBAL QUICK TX MODAL ----
window.openGlobalQuickTxModal = function() {
    try {
        var modal = document.getElementById('globalQuickTxModal');
        if (modal && (modal.classList.contains('active') || !modal.classList.contains('hidden'))) {
            window.closeGlobalQuickTxModal();
            return;
        }

        var form = document.getElementById('globalQuickTxForm');

        if (form) {
            form.reset();
        }
        var dateInput = document.getElementById('globalQuickTxDate');

        if (dateInput) {
            dateInput.value = new Date().toISOString().slice(0, 10);
        }

        updateGlobalQuickTxCategory();

        window.openModal('globalQuickTxModal');

    } catch (e) {

        window.showToast('Modal açılırken hata oluştu: ' + e.message, 'error');
    }
};

window.closeGlobalQuickTxModal = function() {
    window.closeModal('globalQuickTxModal');
};

window.setQuickTxAmount = function(delta) {
    var input = document.getElementById('globalQuickTxAmount');
    if (!input) return;
    var current = parseFloat(input.value) || 0;
    input.value = (current + delta).toFixed(2);
    input.focus();
};

window.setQuickTxPreset = function(flowType, category, description) {
    var flowSelect = document.getElementById('globalQuickTxFlowType');
    if (flowSelect) {
        flowSelect.value = flowType;
        if (typeof updateGlobalQuickTxCategory === 'function') {
            updateGlobalQuickTxCategory();
        }
    }
    var catSelect = document.getElementById('globalQuickTxCategory');
    if (catSelect && category) {
        var found = false;
        for (var i = 0; i < catSelect.options.length; i++) {
            var optVal = catSelect.options[i].value.toLowerCase();
            var optTxt = catSelect.options[i].text.toLowerCase();
            var target = category.toLowerCase();
            if (optVal.includes(target) || optTxt.includes(target)) {
                catSelect.selectedIndex = i;
                found = true;
                break;
            }
        }
        if (!found && catSelect.options.length > 0) {
            catSelect.selectedIndex = 0;
        }
    }
    var descInput = document.querySelector('#globalQuickTxForm input[name="description"]');
    if (descInput && description) {
        descInput.value = description;
    }
    var amountInput = document.getElementById('globalQuickTxAmount');
    if (amountInput) {
        amountInput.focus();
    }
};

const globalCatData = {
    'Gelir': (function() {
        const sidebar = document.querySelector('.sidebar-premium');
        try {
            if (!sidebar) return [];
            const val = sidebar.getAttribute('data-global-income-cats');
            if (!val || val.trim() === '' || val === 'null' || val === 'undefined' || val === '""') return [];
            if (val === '[]' || val === '[' || val.length < 3) return [];  // Handle incomplete JSON
            const parsed = JSON.parse(val);
            return Array.isArray(parsed) ? parsed : [];
        } catch(e) {

            return [];  // Return empty array on error instead of throwing
        }
    })(),
    'Gider': (function() {
        const sidebar = document.querySelector('.sidebar-premium');
        try {
            if (!sidebar) return [];
            const val = sidebar.getAttribute('data-global-expense-cats');
            if (!val || val.trim() === '' || val === 'null' || val === 'undefined' || val === '""') return [];
            if (val === '[]' || val === '[' || val.length < 3) return [];  // Handle incomplete JSON
            const parsed = JSON.parse(val);
            return Array.isArray(parsed) ? parsed : [];
        } catch(e) {

            return [];  // Return empty array on error instead of throwing
        }
    })(),
    'Yatırım': (function() {
        const sidebar = document.querySelector('.sidebar-premium');
        try {
            if (!sidebar) return [];
            const val = sidebar.getAttribute('data-global-investment-cats');
            if (!val || val.trim() === '' || val === 'null' || val === 'undefined' || val === '""') return [];
            if (val === '[]' || val === '[' || val.length < 3) return [];  // Handle incomplete JSON
            const parsed = JSON.parse(val);
            return Array.isArray(parsed) ? parsed : [];
        } catch(e) {

            return [];  // Return empty array on error instead of throwing
        }
    })()
};

window.updateGlobalQuickTxCategory = function() {
    try {
        const flowSelect = document.getElementById('globalQuickTxFlowType');
        const catSelect = document.getElementById('globalQuickTxCategory');
        if (!flowSelect || !catSelect) {

            return;
        }
        const flow = flowSelect.value;
        catSelect.innerHTML = '';
        const cats = globalCatData[flow] || [];
        cats.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c;
            opt.textContent = c;
            catSelect.appendChild(opt);
        });
    } catch (e) {

    }
};

// Form submit listener will be attached in DOMContentLoaded

// ---- MOBILE MENU ----
window.toggleMobileMenu = function() {
    var mobileSidebar = document.getElementById('mobile-sidebar');
    var sidebar = document.querySelector('.sidebar-premium');
    var btn = document.getElementById('mobile-menu-btn');
    if (mobileSidebar) {
        var isHidden = mobileSidebar.classList.toggle('hidden');
        document.body.style.overflow = isHidden ? '' : 'hidden';
        document.documentElement.classList.toggle('mobile-menu-open', !isHidden);
        if (btn) btn.setAttribute('aria-expanded', String(!isHidden));
    } else if (sidebar) {
        var isOpen = sidebar.classList.toggle('open');
        document.body.style.overflow = isOpen ? 'hidden' : '';
        document.documentElement.classList.toggle('mobile-menu-open', isOpen);
        if (btn) btn.setAttribute('aria-expanded', String(isOpen));
    }
};

// ---- GLOBAL CONFIRM MODAL ----
var _gcCallback = null;

window.showGlobalConfirm = function(title, message, callback, isDanger) {
    document.getElementById('globalConfirmTitle').textContent = title;
    document.getElementById('globalConfirmMessage').textContent = message;
    var btn = document.getElementById('globalConfirmBtn');
    var iconCont = document.getElementById('globalConfirmIconContainer');
    var icon = document.getElementById('globalConfirmIcon');
    if (isDanger) {
        btn.className = 'flex-1 px-4 py-3 rounded-xl font-black text-[11px] uppercase text-white shadow-lg transition cursor-pointer bg-rose-600 hover:bg-rose-700';
        btn.textContent = 'Evet, Sil';
        iconCont.className = 'w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0 bg-rose-100 text-rose-600';
        icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>';
    } else {
        btn.className = 'flex-1 px-4 py-3 rounded-xl font-black text-[11px] uppercase text-white shadow-lg transition cursor-pointer bg-indigo-600 hover:bg-indigo-700';
        btn.textContent = 'Onayla';
        iconCont.className = 'w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0 bg-indigo-100 text-indigo-600';
        icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>';
    }
    _gcCallback = callback;
    document.getElementById('globalConfirmModal').classList.remove('hidden');
    document.getElementById('globalConfirmModal').style.display = 'flex';
};

window.closeGlobalConfirm = function() {
    document.getElementById('globalConfirmModal').classList.add('hidden');
    document.getElementById('globalConfirmModal').style.display = '';
    _gcCallback = null;
};

// ---- COMMAND PALETTE & GLOBAL SEARCH (⌘K) ----
window.openGlobalSearch = function() {
    var modal = document.getElementById('commandPaletteModal');
    if (modal) modal.style.display = 'flex';
    var modal = document.getElementById('commandPaletteModal');
    if (!modal) return;
    modal.classList.remove('hidden');
    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    var input = document.getElementById('commandPaletteInput');
    if (input) {
        input.value = '';
        if (typeof filterPaletteItems === 'function') {
            filterPaletteItems('');
        }
        setTimeout(function() { input.focus(); }, 50);
    }
};

window.closeGlobalSearch = function() {
    var modal = document.getElementById('commandPaletteModal');
    if (modal) modal.style.display = '';
    var modal = document.getElementById('commandPaletteModal');
    if (!modal) return;
    modal.classList.remove('active');
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
};

window.navigateToUrl = function(url) {
    window.closeGlobalSearch();
    window.location.href = url;
};

window.executePaletteAction = function(action) {
    window.closeGlobalSearch();
    if (action === 'quick_tx') {
        if (typeof window.openGlobalQuickTxModal === 'function') {
            window.openGlobalQuickTxModal();
        } else {
            window.location.href = '/transactions?modal=new';
        }
    } else if (action === 'new_plan') {
        window.location.href = '/plans?modal=new';
    } else if (action === 'new_asset') {
        window.location.href = '/assets?modal=new';
    } else if (action === 'calculator') {
        if (typeof window.openCalculator === 'function') {
            window.openCalculator();
        }
    } else if (action === 'toggle_theme') {
        if (typeof window.toggleTheme === 'function') {
            window.toggleTheme();
        }
    } else if (action === 'toggle_privacy') {
        if (window.privacyMode && typeof window.privacyMode.toggle === 'function') {
            window.privacyMode.toggle();
        }
    }
};

function filterPaletteItems(query) {
    var q = (query || '').toLowerCase().trim();
    var normalize = function(str) {
        return (str || '').toLowerCase()
            .replace(/i̇/g, 'i')
            .replace(/ı/g, 'i')
            .replace(/ğ/g, 'g')
            .replace(/ü/g, 'u')
            .replace(/ş/g, 's')
            .replace(/ö/g, 'o')
            .replace(/ç/g, 'c');
    };
    var nq = normalize(q);
    var items = document.querySelectorAll('.palette-item');
    var visibleCount = 0;

    items.forEach(function(item) {
        var text = normalize(item.textContent);
        var keywords = normalize(item.getAttribute('data-keywords') || '');
        if (!nq || text.indexOf(nq) !== -1 || keywords.indexOf(nq) !== -1) {
            item.classList.remove('hidden');
            visibleCount++;
        } else {
            item.classList.add('hidden');
        }
    });

    document.querySelectorAll('.palette-group').forEach(function(group) {
        var hasVisible = group.querySelectorAll('.palette-item:not(.hidden)').length > 0;
        if (hasVisible) {
            group.classList.remove('hidden');
        } else {
            group.classList.add('hidden');
        }
    });

    var emptyEl = document.getElementById('commandPaletteEmpty');
    if (emptyEl) {
        if (visibleCount === 0) {
            emptyEl.classList.remove('hidden');
        } else {
            emptyEl.classList.add('hidden');
        }
    }

    highlightPaletteItem(0);
}

function highlightPaletteItem(index) {
    var visible = Array.from(document.querySelectorAll('.palette-item:not(.hidden)'));
    visible.forEach(function(el) {
        el.classList.remove('bg-indigo-50', 'dark:bg-slate-800', 'ring-1', 'ring-indigo-500/30', 'palette-active');
    });
    if (visible.length > 0 && index >= 0 && index < visible.length) {
        visible[index].classList.add('bg-indigo-50', 'dark:bg-slate-800', 'ring-1', 'ring-indigo-500/30', 'palette-active');
        visible[index].scrollIntoView({ block: 'nearest' });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    var confirmBtn = document.getElementById('globalConfirmBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            if (_gcCallback) {
                var cb = _gcCallback;
                confirmBtn.disabled = true;
                confirmBtn.classList.add('opacity-75');
                var prevText = confirmBtn.textContent;
                confirmBtn.textContent = 'İşleniyor...';
                try {
                    var res = cb();
                    if (res && typeof res.then === 'function') {
                        res.finally(function() {
                            confirmBtn.disabled = false;
                            confirmBtn.classList.remove('opacity-75');
                            confirmBtn.textContent = prevText;
                            window.closeGlobalConfirm();
                        });
                        return;
                    }
                } catch(e) {
                    // ignore
                }
                confirmBtn.disabled = false;
                confirmBtn.classList.remove('opacity-75');
                confirmBtn.textContent = prevText;
                window.closeGlobalConfirm();
            } else {
                window.closeGlobalConfirm();
            }
        });
    }

    // Command palette input and navigation listeners
    var paletteInput = document.getElementById('commandPaletteInput');
    if (paletteInput) {
        paletteInput.addEventListener('input', function(e) {
            filterPaletteItems(e.target.value);
        });
        paletteInput.addEventListener('keydown', function(e) {
            var visible = Array.from(document.querySelectorAll('.palette-item:not(.hidden)'));
            var currentIndex = visible.findIndex(function(el) { return el.classList.contains('palette-active'); });
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                var nextIndex = currentIndex < visible.length - 1 ? currentIndex + 1 : 0;
                highlightPaletteItem(nextIndex);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                var prevIndex = currentIndex > 0 ? currentIndex - 1 : visible.length - 1;
                highlightPaletteItem(prevIndex);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (currentIndex >= 0 && visible[currentIndex]) {
                    visible[currentIndex].click();
                } else if (visible.length > 0) {
                    visible[0].click();
                }
            }
        });
    }

    // Global ⌘K / Ctrl+K shortcut listener
    document.addEventListener('keydown', function(e) {
        if ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')) {
            e.preventDefault();
            var modal = document.getElementById('commandPaletteModal');
            if (modal && !modal.classList.contains('hidden')) {
                window.closeGlobalSearch();
            } else {
                window.openGlobalSearch();
            }
        }
    });

    // Global single-key shortcuts: 'N' (Quick Tx), 'P' (New Plan), 'A' (New Asset), '?' (Command Palette)
    document.addEventListener('keydown', function(e) {
        var tag = (e.target && e.target.tagName) ? e.target.tagName.toLowerCase() : '';
        var isInput = tag === 'input' || tag === 'textarea' || tag === 'select' || (e.target && e.target.isContentEditable);
        if (isInput || e.metaKey || e.ctrlKey || e.altKey) return;

        var activeModal = document.querySelector('.modal.active:not(.hidden), .modal-overlay.active:not(.hidden), #commandPaletteModal.active:not(.hidden)');
        if (activeModal) return;

        if (e.key === 'n' || e.key === 'N') {
            e.preventDefault();
            if (typeof window.openGlobalQuickTxModal === 'function') {
                window.openGlobalQuickTxModal();
            }
        } else if (e.key === 'p' || e.key === 'P') {
            e.preventDefault();
            window.location.href = '/plans?modal=new';
        } else if (e.key === 'a' || e.key === 'A') {
            e.preventDefault();
            window.location.href = '/assets?modal=new';
        } else if (e.key === '?' || (e.shiftKey && e.key === '/')) {
            e.preventDefault();
            window.openGlobalSearch();
        }
    });

    // Backdrop click closes modal
    document.addEventListener('click', function(e) {
        if (e.target.matches('.edit-modal-backdrop, .delete-modal-backdrop, .modal-overlay, .modal')) {
            window.closeModal();
        }
    });

    // Escape key closes modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            window.closeModal();
            window.closeGlobalConfirm();
            window.closeGlobalSearch();
        }
    });

    // Show any pending flash toasts
    if (window._pendingToasts) {
        window._pendingToasts.forEach(function(t) {
            window.showToast(t.msg, t.cat);
        });
    }

    // Navigation helpers
    if (window.ECuzdanNavigation) {
        var pageTitle = document.title.split('|')[0].trim();
        ECuzdanNavigation.addToRecentlyVisited(pageTitle, window.location.pathname);
    }
    if (window.ECuzdanLazyLoad) {
        ECuzdanLazyLoad.initAllLazyLoading();
    }

    // Attach form submit listener for quick transaction modal
    var quickTxForm = document.getElementById('globalQuickTxForm');
    if (quickTxForm) {
        quickTxForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (this.dataset.submitting === 'true') {
                return;
            }
            if (window.ECuzdanForms && !window.ECuzdanForms.validateForm(this)) {
                return;
            }
            const formElem = this;
            const submitBtn = formElem.querySelector('button[type="submit"]');
            const formData = new FormData(this);

            // Çevrimdışı kontrolü: İnternet yoksa doğrudan yerel outbox kuyruğuna al
            if (!navigator.onLine && window.ECuzdanOffline) {
                window.ECuzdanOffline.enqueue(formData);
                if (typeof closeGlobalQuickTxModal === 'function') {
                    closeGlobalQuickTxModal();
                }
                formElem.reset();
                return;
            }

            if (window.ECuzdanForms) {
                window.ECuzdanForms.showFormLoading(formElem, submitBtn);
            }
            fetch(ECuzdanEndpoints.transactions.create, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                },
                body: formData
            })
            .then(response => response.json().then(data => ({ ok: response.ok, data })))
            .then(result => {
                const data = result.data;
                if (result.ok && data.success) {
                    window.showToast(data.message || 'İşlem başarıyla eklendi', 'success');
                    setTimeout(() => window.location.reload(), 800);
                } else {
                    if (window.ECuzdanForms) {
                        window.ECuzdanForms.hideFormLoading(formElem, submitBtn);
                        if (data.errors && typeof data.errors === 'object') {
                            Object.keys(data.errors).forEach(key => {
                                window.ECuzdanForms.setFormFieldError(key, data.errors[key], formElem);
                            });
                        }
                    }
                    window.showToast(data.message || 'İşlem eklenirken bir hata oluştu', 'error');
                }
            })
            .catch(error => {
                if (window.ECuzdanForms) {
                    window.ECuzdanForms.hideFormLoading(formElem, submitBtn);
                }
                // Ağ kopması durumunda da çevrimdışı kuyruğa al
                if ((!navigator.onLine || (error && error.name === 'TypeError')) && window.ECuzdanOffline) {
                    window.ECuzdanOffline.enqueue(formData);
                    if (typeof closeGlobalQuickTxModal === 'function') {
                        closeGlobalQuickTxModal();
                    }
                    formElem.reset();
                    return;
                }
                window.showToast('Sunucu bağlantı hatası oluştu', 'error');
            });
        });
    }

    // Mobil alt menü gezinme bağlantılarına tıklandığında açık modal veya menü varsa kapat
    var mobileNavLinks = document.querySelectorAll('.mobile-bottom-nav a');
    mobileNavLinks.forEach(function(link) {
        link.addEventListener('click', function() {
            if (document.documentElement.classList.contains('modal-open') || 
                document.body.classList.contains('modal-open') || 
                document.querySelector('.modal.active, .edit-modal.active, .delete-modal.active, .modal-overlay.active, .notification-modal.active')) {
                if (typeof window.closeModal === 'function') {
                    window.closeModal();
                }
            }
            var mobileSidebar = document.getElementById('mobile-sidebar');
            if (mobileSidebar && !mobileSidebar.classList.contains('hidden')) {
                if (typeof window.toggleMobileMenu === 'function') {
                    window.toggleMobileMenu();
                }
            }
        });
    });
});
