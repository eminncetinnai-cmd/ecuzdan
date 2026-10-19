/* E-CÜZDAN v15.0 - Consolidated Core JS Bundle (auto-generated from core modules) */

// === utils.js ===
/**
 * E-CÜZDAN v15.0 - Utils JavaScript
 * Additional utility functions
 */

// Date Utilities
export function addDays(date, days) {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
}

export function addMonths(date, months) {
    const result = new Date(date);
    result.setMonth(result.getMonth() + months);
    return result;
}

export function addYears(date, years) {
    const result = new Date(date);
    result.setFullYear(result.getFullYear() + years);
    return result;
}

export function diffDays(date1, date2) {
    const oneDay = 24 * 60 * 60 * 1000;
    return Math.round((date2 - date1) / oneDay);
}

export function diffMonths(date1, date2) {
    const months = (date2.getFullYear() - date1.getFullYear()) * 12;
    return months - date1.getMonth() + date2.getMonth();
}

export function isToday(date) {
    const today = new Date();
    return date.getDate() === today.getDate() &&
           date.getMonth() === today.getMonth() &&
           date.getFullYear() === today.getFullYear();
}

export function isThisWeek(date) {
    const today = new Date();
    const startOfWeek = new Date(today.setDate(today.getDate() - today.getDay()));
    const endOfWeek = new Date(today.setDate(today.getDate() - today.getDay() + 6));
    return date >= startOfWeek && date <= endOfWeek;
}

export function isThisMonth(date) {
    const today = new Date();
    return date.getMonth() === today.getMonth() &&
           date.getFullYear() === today.getFullYear();
}

// String Utilities
export function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

export function capitalizeWords(str) {
    return str.split(' ').map(word => capitalize(word)).join(' ');
}

export function truncate(str, length, suffix = '...') {
    if (str.length <= length) return str;
    return str.slice(0, length) + suffix;
}

export function slugify(str) {
    return str
        .toLowerCase()
        .trim()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_-]+/g, '-')
        .replace(/^-+|-+$/g, '');
}

export function removeAccents(str) {
    return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

// Array Utilities
export function unique(arr) {
    return [...new Set(arr)];
}

export function chunk(arr, size) {
    const chunks = [];
    for (let i = 0; i < arr.length; i += size) {
        chunks.push(arr.slice(i, i + size));
    }
    return chunks;
}

export function shuffle(arr) {
    const shuffled = [...arr];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

export function groupBy(arr, key) {
    return arr.reduce((result, item) => {
        (result[item[key]] = result[item[key]] || []).push(item);
        return result;
    }, {});
}

export function sortBy(arr, key, direction = 'asc') {
    return [...arr].sort((a, b) => {
        if (direction === 'asc') {
            return a[key] > b[key] ? 1 : -1;
        } else {
            return a[key] < b[key] ? 1 : -1;
        }
    });
}

// Object Utilities
export function deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
}

export function mergeDeep(target, ...sources) {
    const isObject = (obj) => obj && typeof obj === 'object';
    
    if (!sources.length) return target;
    const source = sources.shift();

    if (isObject(target) && isObject(source)) {
        for (const key in source) {
            if (isObject(source[key])) {
                if (!target[key]) Object.assign(target, { [key]: {} });
                mergeDeep(target[key], source[key]);
            } else {
                Object.assign(target, { [key]: source[key] });
            }
        }
    }
    
    return mergeDeep(target, ...sources);
}

export function pick(obj, keys) {
    return keys.reduce((result, key) => {
        if (obj.hasOwnProperty(key)) {
            result[key] = obj[key];
        }
        return result;
    }, {});
}

export function omit(obj, keys) {
    const result = { ...obj };
    keys.forEach(key => delete result[key]);
    return result;
}

// Number Utilities
export function clamp(num, min, max) {
    return Math.min(Math.max(num, min), max);
}

export function random(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

export function round(num, decimals = 2) {
    return Number(Math.round(num + 'e' + decimals) + 'e-' + decimals);
}

export function percentage(value, total) {
    return total > 0 ? (value / total) * 100 : 0;
}

// Color Utilities
export function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

export function rgbToHex(r, g, b) {
    return '#' + [r, g, b].map(x => {
        const hex = x.toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    }).join('');
}

export function lightenColor(hex, percent) {
    const rgb = hexToRgb(hex);
    if (!rgb) return hex;
    
    const amount = Math.round(2.55 * percent);
    const r = clamp(rgb.r + amount, 0, 255);
    const g = clamp(rgb.g + amount, 0, 255);
    const b = clamp(rgb.b + amount, 0, 255);
    
    return rgbToHex(r, g, b);
}

export function darkenColor(hex, percent) {
    const rgb = hexToRgb(hex);
    if (!rgb) return hex;
    
    const amount = Math.round(2.55 * percent);
    const r = clamp(rgb.r - amount, 0, 255);
    const g = clamp(rgb.g - amount, 0, 255);
    const b = clamp(rgb.b - amount, 0, 255);
    
    return rgbToHex(r, g, b);
}

// DOM Utilities
export function createElement(tag, classes = [], attributes = {}, content = '') {
    const element = document.createElement(tag);
    
    if (classes.length) {
        element.classList.add(...classes);
    }
    
    Object.keys(attributes).forEach(key => {
        element.setAttribute(key, attributes[key]);
    });
    
    if (content) {
        element.textContent = content;
    }
    
    return element;
}

export function removeElement(element) {
    if (element && element.parentNode) {
        element.parentNode.removeChild(element);
    }
}

export function insertAfter(newNode, referenceNode) {
    referenceNode.parentNode.insertBefore(newNode, referenceNode.nextSibling);
}

export function insertBefore(newNode, referenceNode) {
    referenceNode.parentNode.insertBefore(newNode, referenceNode);
}

// Event Utilities
export function on(element, event, handler, options = {}) {
    element.addEventListener(event, handler, options);
}

export function off(element, event, handler, options = {}) {
    element.removeEventListener(event, handler, options);
}

export function once(element, event, handler, options = {}) {
    element.addEventListener(event, handler, { ...options, once: true });
}

// Toast Notification System
export function showToast(message, type = 'success', duration = 4000, action = null) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    
    // Color scheme based on type
    const colors = {
        success: 'bg-emerald-600',
        error: 'bg-rose-600',
        warning: 'bg-amber-500',
        info: 'bg-blue-600'
    };
    
    const icons = {
        success: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>',
        error: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>',
        warning: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>',
        info: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
    };

    const bgColor = colors[type] || colors.info;
    const icon = icons[type] || icons.info;

    toast.className = `toast-item ${bgColor} text-white px-5 py-3.5 rounded-2xl shadow-2xl flex items-center gap-3 transform transition-all duration-300 translate-x-full opacity-0 pointer-events-auto`;
    
    let actionBtnHtml = '';
    if (action && action.text) {
        actionBtnHtml = `<button type="button" class="toast-action-btn flex-shrink-0 px-2.5 py-1 bg-white/25 hover:bg-white/35 active:scale-95 text-white rounded-lg text-xs font-bold transition shadow-sm cursor-pointer">${action.text}</button>`;
    }

    toast.innerHTML = `
        <div class="flex-shrink-0">${icon}</div>
        <div class="flex-1 font-semibold text-sm leading-snug">${message}</div>
        ${actionBtnHtml}
        <button type="button" class="toast-close-btn flex-shrink-0 hover:opacity-80 transition cursor-pointer p-0.5" aria-label="Kapat">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
    `;

    const removeToast = () => {
        if (!toast.parentElement) return;
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
        }, 300);
    };

    const closeBtn = toast.querySelector('.toast-close-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', removeToast);
    }

    if (action && (action.onClick || action.callback)) {
        const actionCallback = action.onClick || action.callback;
        const actionBtn = toast.querySelector('.toast-action-btn');
        if (actionBtn) {
            actionBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                try {
                    actionCallback();
                } catch (err) {
                    console.error('Toast action failed:', err);
                }
                removeToast();
            });
        }
    }

    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.classList.remove('translate-x-full', 'opacity-0');
    });

    // Auto remove
    let autoRemoveTimer = setTimeout(removeToast, duration);

    // Pause on hover
    toast.addEventListener('mouseenter', () => clearTimeout(autoRemoveTimer));
    toast.addEventListener('mouseleave', () => {
        autoRemoveTimer = setTimeout(removeToast, 2000);
    });
}

// Pop-up notification for completed operations
export function showPopupNotification(title, message, type = 'success') {
    const popup = document.createElement('div');
    
    const colors = {
        success: 'from-emerald-500 to-emerald-600',
        error: 'from-rose-500 to-rose-600',
        warning: 'from-amber-500 to-amber-600',
        info: 'from-blue-500 to-blue-600'
    };
    
    const gradient = colors[type] || colors.info;

    popup.className = `fixed top-0 left-0 right-0 z-[100] bg-gradient-to-r ${gradient} text-white px-6 py-4 shadow-2xl transform transition-all duration-300 -translate-y-full`;
    popup.innerHTML = `
        <div class="max-w-6xl mx-auto flex items-center justify-between">
            <div class="flex items-center gap-4">
                <div class="font-black text-lg uppercase tracking-wider">${title}</div>
                <div class="font-semibold text-sm opacity-90">${message}</div>
            </div>
            <button onclick="this.closest('.fixed').remove()" class="hover:opacity-80 transition">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
        </div>
    `;

    document.body.appendChild(popup);

    // Animate in
    requestAnimationFrame(() => {
        popup.classList.remove('-translate-y-full');
    });

    // Auto remove
    setTimeout(() => {
        popup.classList.add('-translate-y-full');
        setTimeout(() => {
            if (popup.parentElement) {
                popup.parentElement.removeChild(popup);
            }
        }, 300);
    }, 5000);
}

// Export for global access
window.ECuzdanUtils = {
    addDays,
    addMonths,
    addYears,
    diffDays,
    diffMonths,
    isToday,
    isThisWeek,
    isThisMonth,
    capitalize,
    capitalizeWords,
    truncate,
    slugify,
    removeAccents,
    unique,
    chunk,
    shuffle,
    groupBy,
    sortBy,
    deepClone,
    mergeDeep,
    pick,
    omit,
    clamp,
    random,
    round,
    percentage,
    hexToRgb,
    rgbToHex,
    lightenColor,
    darkenColor,
    createElement,
    removeElement,
    insertAfter,
    insertBefore,
    on,
    off,
    once,
    showToast,
    showPopupNotification
};

// Make showToast and showPopupNotification globally available
window.showToast = showToast;
window.showPopupNotification = showPopupNotification;

// === main.js ===
/**
 * E-CÜZDAN v15.0 - Main JavaScript
 * Global initialization and utility functions
 */

// Utility Functions
export function formatMoneyTr(value) {
    var val = value;
    if (typeof value === 'string') {
        val = parseFloat(value);
        if (isNaN(val)) val = 0;
    }
    return new Intl.NumberFormat('tr-TR', { 
        style: 'currency', 
        currency: 'TRY' 
    }).format(val);
}

export function formatNumber(value, decimals = 2) {
    return new Intl.NumberFormat('tr-TR', { 
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value);
}

export function formatDate(date) {
    return new Intl.DateTimeFormat('tr-TR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    }).format(new Date(date));
}

export function formatDateTime(date) {
    return new Intl.DateTimeFormat('tr-TR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(date));
}

// Toast Notifications (re-exported from utils.js)

// Global access for inline scripts
window.showToast = showToast;
window.openModal = openModal;
window.closeModal = closeModal;
window.toggleMobileMenu = toggleMobileMenu;
window.showLoading = showLoading;
window.hideLoading = hideLoading;

// Modal Functions
export function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal && !modal.classList.contains('active')) {
        modal.classList.remove('hidden');
        modal.classList.add('active');
        modal.setAttribute('aria-hidden', 'false');
        if (modal.classList.contains('modal') || modal.classList.contains('modal-overlay') || modal.classList.contains('edit-modal') || modal.classList.contains('delete-modal')) {
            modal.style.display = 'flex';
        } else {
            modal.style.display = 'block';
        }
        document.body.style.overflow = 'hidden';
    }
}

export function closeModal(modalId = null) {
    const closeModalElement = (modal) => {
        modal.classList.remove('active');
        modal.classList.add('hidden');
        modal.setAttribute('aria-hidden', 'true');
        if (modal.classList.contains('modal') || modal.classList.contains('modal-overlay') || modal.classList.contains('edit-modal') || modal.classList.contains('delete-modal')) {
            modal.style.display = 'none';
        }
    };

    const selectors = '.modal.active, .modal:not(.hidden), .edit-modal.active, .edit-modal:not(.hidden), .delete-modal.active, .delete-modal:not(.hidden), .modal-overlay.active, .modal-overlay:not(.hidden)';

    if (modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            closeModalElement(modal);
        }
    } else {
        document.querySelectorAll(selectors).forEach(modal => {
            closeModalElement(modal);
        });
    }

    const stillOpen = document.querySelector(selectors);
    if (!stillOpen) {
        document.body.style.overflow = '';
    }
}

export function toggleMobileMenu() {
    const mobileSidebar = document.getElementById('mobile-sidebar');
    const sidebar = document.querySelector('.sidebar-premium');
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');

    if (mobileSidebar) {
        const isHidden = mobileSidebar.classList.toggle('hidden');
        document.body.style.overflow = isHidden ? '' : 'hidden';
        if (mobileMenuBtn) {
            mobileMenuBtn.setAttribute('aria-expanded', (!isHidden).toString());
        }
    } else if (sidebar) {
        const isOpen = sidebar.classList.toggle('open');
        document.body.style.overflow = isOpen ? 'hidden' : '';
        if (mobileMenuBtn) {
            mobileMenuBtn.setAttribute('aria-expanded', isOpen.toString());
        }
    }
}

// Close modal on backdrop and overlay click
document.addEventListener('click', (e) => {
    if (e.target.matches('.edit-modal-backdrop, .delete-modal-backdrop, .modal-overlay, .modal')) {
        closeModal();
    }
});

// Close modal & mobile menu on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const mobileSidebar = document.getElementById('mobile-sidebar');
        if (mobileSidebar && !mobileSidebar.classList.contains('hidden')) {
            toggleMobileMenu();
        }
        document.querySelectorAll('.edit-modal.active, .delete-modal.active, .modal-overlay.active').forEach(modal => {
            closeModal(modal.id);
        });
    }
});

// Loading State
export function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="skeleton" style="height: 100%;"></div>';
    }
}

export function hideLoading(elementId, content) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = content;
    }
}

// Debounce Function
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle Function
export function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Copy to Clipboard
export async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Kopyalandı!', 'success');
    } catch (err) {
        console.error('Failed to copy:', err);
        showToast('Kopyalama başarısız', 'error');
    }
}

// Download File
export function downloadFile(content, filename, type = 'text/plain') {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Local Storage Helpers
export function saveToLocalStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (err) {
        console.error('Failed to save to localStorage:', err);
    }
}

export function getFromLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (err) {
        console.error('Failed to get from localStorage:', err);
        return defaultValue;
    }
}

export function removeFromLocalStorage(key) {
    try {
        localStorage.removeItem(key);
    } catch (err) {
        console.error('Failed to remove from localStorage:', err);
    }
}

// Preserve key helpers for inline templates
window.openModal = openModal;
window.closeModal = closeModal;
window.toggleMobileMenu = toggleMobileMenu;
window.copyToClipboard = copyToClipboard;
window.downloadFile = downloadFile;
window.saveToLocalStorage = saveToLocalStorage;
window.getFromLocalStorage = getFromLocalStorage;

// URL Helpers
export function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

export function updateQueryParam(param, value) {
    const url = new URL(window.location);
    url.searchParams.set(param, value);
    window.history.pushState({}, '', url);
}

// Validation Helpers
export function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

export function isValidPhone(phone) {
    const re = /^(\+90|0)?[0-9]{10}$/;
    return re.test(phone.replace(/\s/g, ''));
}

export function isValidUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize all tooltips
    const tooltips = document.querySelectorAll('.tooltip');
    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseenter', (e) => {
            const tooltipText = tooltip.getAttribute('data-tooltip');
            // Tooltip logic here if needed
        });
    });

        // Initialize navigation helper functions when available
        if (window.ECuzdanNavigation) {
            window.ECuzdanNavigation.initNavigationSearch('nav-search', 'sidebar-nav');
            window.ECuzdanNavigation.renderBreadcrumbs('breadcrumbs');
            window.ECuzdanNavigation.initCollapsibleNavigation();
            window.ECuzdanNavigation.initKeyboardShortcuts();
        }
    });

// === tables.js ===
/**
 * E-CÜZDAN v15.0 - Tables JavaScript
 * DataTables initialization and helper functions
 */

// Default DataTable Options
export const DEFAULT_DATATABLE_OPTIONS = {
    language: {
        url: '//cdn.datatables.net/plug-ins/1.13.4/i18n/tr.json'
    },
    pageLength: 10,
    lengthMenu: [10, 25, 50, 100],
    order: [[0, 'desc']],
    responsive: true,
    columnDefs: [
        { orderable: false, targets: -1 } // Last column not sortable
    ],
    dom: '<"flex justify-between items-center mb-4"lf>rt<"flex justify-between items-center mt-4"ip>'
};

// Initialize DataTable
export function initDataTable(tableId, options = {}) {
    const table = $(`#${tableId}`);
    if (table.length) {
        return table.DataTable({
            ...DEFAULT_DATATABLE_OPTIONS,
            ...options
        });
    }
    return null;
}

// Initialize Multiple DataTables
export function initDataTables(tableIds, options = {}) {
    const tables = {};
    tableIds.forEach(id => {
        tables[id] = initDataTable(id, options[id] || options);
    });
    return tables;
}

// Destroy DataTable
export function destroyDataTable(tableId) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().destroy();
    }
}

// Reload DataTable
export function reloadDataTable(tableId) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().ajax.reload();
    }
}

// Add Row to DataTable
export function addRowToDataTable(tableId, data) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().row.add(data).draw();
    }
}

// Update Row in DataTable
export function updateRowInDataTable(tableId, rowIndex, data) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().row(rowIndex).data(data).draw();
    }
}

// Delete Row from DataTable
export function deleteRowFromDataTable(tableId, rowIndex) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().row(rowIndex).remove().draw();
    }
}

// Search DataTable
export function searchDataTable(tableId, searchTerm) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().search(searchTerm).draw();
    }
}

// Filter DataTable by Column
export function filterDataTableByColumn(tableId, columnIndex, value) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().column(columnIndex).search(value).draw();
    }
}

// Get Selected Rows
export function getSelectedRows(tableId) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        return table.DataTable().rows('.selected').data().toArray();
    }
    return [];
}

// Select Row
export function selectRow(tableId, rowIndex) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().row(rowIndex).select();
    }
}

// Deselect All Rows
export function deselectAllRows(tableId) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().rows().deselect();
    }
}

// Apply column header text as data-label to all cells in a table
export function applyDataLabels(tableOrId) {
    const table = typeof tableOrId === 'string' ? document.getElementById(tableOrId) : tableOrId;
    if (!table) return;

    const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
    if (headers.length === 0) return;

    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        const cells = Array.from(row.querySelectorAll('td'));
        cells.forEach((cell, idx) => {
            if (headers[idx] && !cell.hasAttribute('data-label')) {
                cell.setAttribute('data-label', headers[idx]);
            }
        });
    });
}

// Automatically scan and enable responsive mobile stacked cards on tables
export function initResponsiveStackedTables() {
    const tables = document.querySelectorAll('.responsive-card-table, .table-card-mobile, .data-table, #transTable');
    tables.forEach(table => {
        applyDataLabels(table);

        // Watch for row updates (e.g. search filtering or pagination)
        const tbody = table.querySelector('tbody');
        if (tbody && !tbody._responsiveObserved) {
            tbody._responsiveObserved = true;
            const observer = new MutationObserver(() => {
                applyDataLabels(table);
            });
            observer.observe(tbody, { childList: true, subtree: false });
        }
    });
}

// Self-initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initResponsiveStackedTables();
    });
} else {
    initResponsiveStackedTables();
}

// Export for global access
window.ECuzdanTables = {
    DEFAULT_DATATABLE_OPTIONS,
    initDataTable,
    initDataTables,
    destroyDataTable,
    reloadDataTable,
    addRowToDataTable,
    updateRowInDataTable,
    deleteRowFromDataTable,
    searchDataTable,
    filterDataTableByColumn,
    getSelectedRows,
    selectRow,
    deselectAllRows,
    applyDataLabels,
    initResponsiveStackedTables
};


// === forms.js ===
/**
 * E-CÜZDAN v15.0 - Forms JavaScript
 * Form validation, dynamic field feedback, loading states, and modal handling
 */

// Field Validation
export function validateField(input) {
    if (!input || input.disabled || input.type === 'hidden') {
        return { isValid: true };
    }

    // Skip validation for inputs in closed templates or inactive tabs
    if (!input.offsetParent && input.type !== 'file') {
        // Hidden element
    }

    const value = (input.value || '').trim();
    let isValid = true;
    let errorMessage = '';

    // 1. Required Check
    if (input.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'Bu alan zorunludur.';
    }

    // 2. Numeric / Currency / Quantity Checks
    if (isValid && value && (input.type === 'number' || input.inputMode === 'decimal')) {
        const num = parseFloat(value);
        if (isNaN(num)) {
            isValid = false;
            errorMessage = 'Geçerli bir sayı giriniz.';
        } else {
            const minAttr = input.getAttribute('min');
            const maxAttr = input.getAttribute('max');
            
            if (minAttr !== null && num < parseFloat(minAttr)) {
                isValid = false;
                errorMessage = `Değer en az ${minAttr} olmalıdır.`;
            } else if (maxAttr !== null && num > parseFloat(maxAttr)) {
                isValid = false;
                errorMessage = `Değer en fazla ${maxAttr} olmalıdır.`;
            } else {
                // If it's a financial field without negative allowance, ensure > 0
                const fieldName = (input.name || input.id || '').toLowerCase();
                const isFinancialAmount = /amount|tutar|fiyat|price|quantity|adet|miktar|purchase_cost|maliyet|value|deger/.test(fieldName);
                if (isFinancialAmount && minAttr === null && num <= 0) {
                    isValid = false;
                    errorMessage = 'Tutar veya miktar 0\'dan büyük olmalıdır.';
                }
            }
        }
    }

    // 3. Email Check
    if (isValid && value && input.type === 'email') {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!re.test(value)) {
            isValid = false;
            errorMessage = 'Geçerli bir e-posta adresi giriniz.';
        }
    }

    // 4. Date Check
    if (isValid && value && input.type === 'date') {
        const d = new Date(value);
        if (isNaN(d.getTime())) {
            isValid = false;
            errorMessage = 'Geçerli bir tarih seçiniz.';
        }
    }

    // Apply or clean visual feedback
    if (!isValid) {
        input.classList.add('form-input-error', 'ring-2', 'ring-rose-500', 'border-rose-500');
        input.setAttribute('aria-invalid', 'true');
        setFieldErrorDisplay(input, errorMessage);
    } else {
        clearFieldValidation(input);
    }

    return { isValid, message: errorMessage };
}

// Display error badge/text under the input
function setFieldErrorDisplay(input, message) {
    let errorSpan = findFieldErrorElement(input);
    if (!errorSpan) {
        errorSpan = document.createElement('span');
        errorSpan.className = 'field-error-message text-rose-500 text-[10px] font-semibold flex items-center gap-1 mt-1 animate-fade-in';
        errorSpan.setAttribute('role', 'alert');
        errorSpan.innerHTML = `
            <svg class="w-3 h-3 flex-shrink-0 text-rose-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            <span class="error-text">${message}</span>
        `;
        // Insert right after the input or its parent container if input is inside an input-group
        const parent = input.parentElement;
        if (parent && parent.classList.contains('relative')) {
            parent.parentElement.appendChild(errorSpan);
        } else if (parent) {
            parent.appendChild(errorSpan);
        }
    } else {
        const textElem = errorSpan.querySelector('.error-text') || errorSpan;
        textElem.textContent = message;
        errorSpan.style.display = 'flex';
    }
}

// Find existing error message element for input
function findFieldErrorElement(input) {
    const parent = input.parentElement;
    if (!parent) return null;
    let span = parent.querySelector('.field-error-message, .form-error');
    if (!span && parent.parentElement) {
        span = parent.parentElement.querySelector('.field-error-message, .form-error');
    }
    return span;
}

// Clear single field validation
export function clearFieldValidation(input) {
    if (!input) return;
    input.classList.remove('form-input-error', 'ring-2', 'ring-rose-500', 'border-rose-500');
    input.removeAttribute('aria-invalid');
    const errorSpan = findFieldErrorElement(input);
    if (errorSpan) {
        errorSpan.remove();
    }
}

// Form Validation
export function validateForm(formOrId) {
    const form = typeof formOrId === 'string' ? document.getElementById(formOrId) : formOrId;
    if (!form) return false;

    const inputs = form.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]), select, textarea');
    let isValid = true;
    let firstInvalid = null;

    inputs.forEach(input => {
        const res = validateField(input);
        if (!res.isValid) {
            isValid = false;
            if (!firstInvalid) firstInvalid = input;
        }
    });

    if (!isValid && firstInvalid) {
        firstInvalid.focus();
        
        // Shake animation
        const shakeContainer = firstInvalid.closest('.form-group') || firstInvalid.parentElement || firstInvalid;
        shakeContainer.classList.remove('animate-shake');
        void shakeContainer.offsetWidth; // Force reflow
        shakeContainer.classList.add('animate-shake');

        if (window.showToast) {
            window.showToast('Lütfen formdaki eksik veya hatalı alanları kontrol ediniz.', 'warning');
        }
        return false;
    }

    return isValid;
}

// Set custom error on a field (e.g. from server response)
export function setFormFieldError(inputOrName, message, formElement) {
    let input = null;
    if (typeof inputOrName === 'string') {
        const scope = formElement || document;
        input = scope.querySelector(`[name="${inputOrName}"]`) || scope.getElementById(inputOrName);
    } else {
        input = inputOrName;
    }

    if (input) {
        input.classList.add('form-input-error', 'ring-2', 'ring-rose-500', 'border-rose-500');
        input.setAttribute('aria-invalid', 'true');
        setFieldErrorDisplay(input, message);
    }
}

// Clear all form errors
export function clearFormErrors(formOrId) {
    const form = typeof formOrId === 'string' ? document.getElementById(formOrId) : formOrId;
    if (!form) return;
    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => clearFieldValidation(input));
}

// Validate Email
export function validateEmail(input) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = re.test(input.value);
    if (!isValid) {
        input.classList.add('ring-2', 'ring-rose-500');
    } else {
        input.classList.remove('ring-2', 'ring-rose-500');
    }
    return isValid;
}

// Validate Phone
export function validatePhone(input) {
    const re = /^(\+90|0)?[0-9]{10}$/;
    const isValid = re.test(input.value.replace(/\s/g, ''));
    if (!isValid) {
        input.classList.add('ring-2', 'ring-rose-500');
    } else {
        input.classList.remove('ring-2', 'ring-rose-500');
    }
    return isValid;
}

// Validate Number Range
export function validateNumberRange(input, min, max) {
    const value = parseFloat(input.value);
    const isValid = value >= min && value <= max;
    if (!isValid) {
        input.classList.add('ring-2', 'ring-rose-500');
    } else {
        input.classList.remove('ring-2', 'ring-rose-500');
    }
    return isValid;
}

// Reset Form
export function resetForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.reset();
        clearFormErrors(form);
    }
}

// Get Form Data as Object
export function getFormData(formId) {
    const form = document.getElementById(formId);
    if (!form) return {};
    const formData = new FormData(form);
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });
    return data;
}

// Set Form Data from Object
export function setFormData(formId, data) {
    const form = document.getElementById(formId);
    if (!form) return;
    Object.keys(data).forEach(key => {
        const input = form.querySelector(`[name="${key}"]`);
        if (input) {
            input.value = data[key];
        }
    });
}

// Disable Form
export function disableForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        const inputs = form.querySelectorAll('input, select, textarea, button');
        inputs.forEach(input => {
            input.disabled = true;
        });
    }
}

// Enable Form
export function enableForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        const inputs = form.querySelectorAll('input, select, textarea, button');
        inputs.forEach(input => {
            input.disabled = false;
        });
    }
}

// Show Form Loading State
export function showFormLoading(formOrId, submitButtonOrId) {
    const form = typeof formOrId === 'string' ? document.getElementById(formOrId) : formOrId;
    let submitButton = null;
    if (submitButtonOrId) {
        submitButton = typeof submitButtonOrId === 'string' ? document.getElementById(submitButtonOrId) : submitButtonOrId;
    } else if (form) {
        submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
    }

    if (submitButton && !submitButton.classList.contains('btn-loading')) {
        submitButton.disabled = true;
        submitButton.classList.add('btn-loading', 'opacity-75');
        if (!submitButton.getAttribute('data-original-html')) {
            submitButton.setAttribute('data-original-html', submitButton.innerHTML);
        }
        submitButton.innerHTML = `
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 inline text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Kaydediliyor...</span>
        `;

        // Safety timeout: restore after 8 seconds in case of slow connection or unhandled client state
        setTimeout(() => {
            if (submitButton && submitButton.classList.contains('btn-loading')) {
                hideFormLoading(form, submitButton);
            }
        }, 8000);
    }
}

// Hide Form Loading State
export function hideFormLoading(formOrId, submitButtonOrId, originalText = null) {
    const form = typeof formOrId === 'string' ? document.getElementById(formOrId) : formOrId;
    let submitButton = null;
    if (submitButtonOrId) {
        submitButton = typeof submitButtonOrId === 'string' ? document.getElementById(submitButtonOrId) : submitButtonOrId;
    } else if (form) {
        submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
    }

    if (submitButton) {
        submitButton.disabled = false;
        submitButton.classList.remove('btn-loading', 'opacity-75');
        const origHtml = submitButton.getAttribute('data-original-html');
        if (originalText) {
            submitButton.textContent = originalText;
        } else if (origHtml) {
            submitButton.innerHTML = origHtml;
            submitButton.removeAttribute('data-original-html');
        }
    }

    if (form) {
        enableForm(form.id || form);
    }
}

// Auto-resize Textarea
export function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// Initialize Auto-resize Textareas
export function initAutoResizeTextareas() {
    const textareas = document.querySelectorAll('textarea[data-auto-resize]');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', () => autoResizeTextarea(textarea));
        autoResizeTextarea(textarea);
    });
}

// Character Counter
export function updateCharacterCounter(inputId, counterId, maxLength) {
    const input = document.getElementById(inputId);
    const counter = document.getElementById(counterId);
    if (input && counter) {
        const remaining = maxLength - input.value.length;
        counter.textContent = `${remaining} karakter kaldı`;
        if (remaining < 0) {
            counter.classList.add('text-rose-600');
        } else {
            counter.classList.remove('text-rose-600');
        }
    }
}

// Initialize Character Counters
export function initCharacterCounters() {
    const inputs = document.querySelectorAll('input[data-max-length], textarea[data-max-length]');
    inputs.forEach(input => {
        const maxLength = parseInt(input.getAttribute('data-max-length'), 10);
        const counterId = input.getAttribute('data-counter-id');
        if (counterId) {
            input.addEventListener('input', () => {
                updateCharacterCounter(input.id, counterId, maxLength);
            });
            updateCharacterCounter(input.id, counterId, maxLength);
        }
    });
}

// Form Submit Handler helper
export function handleFormSubmit(formId, callback) {
    const form = document.getElementById(formId);
    if (!form) return;
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        if (validateForm(formId)) {
            const formData = getFormData(formId);
            callback(formData);
        }
    });
}

// Global Validation Initializer: automatically watches forms & inputs
export function initGlobalFormValidation() {
    // 0. Disable browser native bubbles on target forms so our custom validator takes control
    const setupNovalidate = () => {
        document.querySelectorAll('form[data-validate="true"], form[method="POST"], form[method="post"], .modal form, .edit-modal-body').forEach(form => {
            if (form.getAttribute('data-no-validate') !== 'true') {
                form.setAttribute('novalidate', 'true');
            }
        });
    };
    setupNovalidate();

    // Catch any native invalid events before browser default tooltips
    document.addEventListener('invalid', (e) => {
        const form = e.target.form;
        if (form && form.getAttribute('data-no-validate') !== 'true') {
            e.preventDefault();
            validateField(e.target);
            form.setAttribute('novalidate', 'true');
        }
    }, true);

    // Ensure novalidate is on form before submit button click triggers validation
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('button[type="submit"], input[type="submit"]');
        if (btn && btn.form && btn.form.getAttribute('data-no-validate') !== 'true') {
            btn.form.setAttribute('novalidate', 'true');
        }
    }, true);

    // 1. Live clear on input/change
    document.addEventListener('input', (e) => {
        if (e.target.matches('input, select, textarea')) {
            if (e.target.classList.contains('form-input-error')) {
                validateField(e.target);
            }
        }
    });

    document.addEventListener('change', (e) => {
        if (e.target.matches('select, input[type="date"], input[type="checkbox"], input[type="radio"]')) {
            if (e.target.classList.contains('form-input-error')) {
                validateField(e.target);
            }
        }
    });

    // 2. Intercept submit on forms that need validation
    document.addEventListener('submit', (e) => {
        const form = e.target;
        if (!form || form.tagName !== 'FORM') return;

        // Skip forms marked with data-no-validate
        if (form.getAttribute('data-no-validate') === 'true') return;

        // Only validate POST forms or forms marked with data-validate or modal forms
        const isPost = (form.method || '').toUpperCase() === 'POST';
        const isModalForm = !!form.closest('.modal-content, .edit-modal-content, .asset-modal-body, .edit-modal-body, .modal');
        const hasValidateAttr = form.getAttribute('data-validate') === 'true';

        if (isPost || isModalForm || hasValidateAttr) {
            const isValid = validateForm(form);
            if (!isValid) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }

            // Valid form: show loading state on submit button
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn) {
                showFormLoading(form, submitBtn);
            }
        }
    });
}

// Self-initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initGlobalFormValidation();
        initAutoResizeTextareas();
        initCharacterCounters();
    });
} else {
    initGlobalFormValidation();
    initAutoResizeTextareas();
    initCharacterCounters();
}

// Export for global access
window.ECuzdanForms = {
    validateField,
    validateForm,
    clearFieldValidation,
    setFormFieldError,
    clearFormErrors,
    validateEmail,
    validatePhone,
    validateNumberRange,
    resetForm,
    getFormData,
    setFormData,
    disableForm,
    enableForm,
    showFormLoading,
    hideFormLoading,
    autoResizeTextarea,
    initAutoResizeTextareas,
    updateCharacterCounter,
    initCharacterCounters,
    handleFormSubmit,
    initGlobalFormValidation
};

// === navigation.js ===
/**
 * E-CÜZDAN v15.0 - Navigation JavaScript
 * Navigation optimization and search functionality
 */

// Navigation Search
export function initNavigationSearch(searchInputId, navContainerId) {
    const searchInput = document.getElementById(searchInputId);
    const navContainer = document.getElementById(navContainerId);

    if (!searchInput || !navContainer) return;

    const sectionBlocks = Array.from(navContainer.querySelectorAll('.nav-section-title')).map(section => {
        const items = [];
        let sibling = section.nextElementSibling;

        while (sibling && !sibling.classList.contains('nav-section-title')) {
            if (sibling.classList.contains('nav-link')) {
                items.push(sibling);
            }
            sibling = sibling.nextElementSibling;
        }

        return { section, items };
    });

    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();

        sectionBlocks.forEach(({ section, items }) => {
            let anyVisible = false;

            items.forEach(link => {
                const text = link.textContent.toLowerCase();
                const visible = text.includes(searchTerm);

                link.style.display = visible ? 'flex' : 'none';
                anyVisible = anyVisible || visible;
            });

            section.style.display = anyVisible ? 'block' : 'none';
        });
    });
}

// Breadcrumb Generation
export function generateBreadcrumbs() {
    const path = window.location.pathname;
    const breadcrumbs = [];
    
    // Home
    breadcrumbs.push({ text: 'Ana Sayfa', url: '/' });
    
    // Parse path
    const segments = path.split('/').filter(Boolean);
    const pathMap = {
        'transactions': 'İşlemler',
        'plans': 'Düzenli İşlemler',
        'monthly_dashboard': 'Aylık Dashboard',
        'payment_calendar': 'Ödeme Takvimi',
        'assets': 'Varlık Yönetimi',
        'assets_management': 'Varlık Yönetimi',
        'assets_view': 'Varlık Görünümü',
        'investment_performance': 'Yatırım Performansı',
        'analysis': 'Finansal Sağlık',
        'financial_freedom': 'Finansal Özgürlük',
        'strategy': 'Strateji Paneli',
        'financial_dashboard': 'Piyasa Analizi',
        'logbook': 'Yatırım Günlüğü',
        'central-bank-reserves': 'Merkez Bankası Rezervleri',
        'global-ratios': 'Küresel Rasyolar',
        'profile': 'Yatırımcı Profili',
        'notifications': 'Bildirimler',
        'categories': 'Kategoriler',
        'settings': 'Ayarlar',
        'user_guide': 'Kullanıcı Rehberi',
        'financial_education': 'Finansal Eğitim',
        'monitoring': 'İzleme',
        'storage-health': 'Depolama Sağlığı',
        'admin': 'Yönetim Paneli'
    };
    
    let currentPath = '';
    segments.forEach((segment, index) => {
        currentPath += '/' + segment;
        const text = pathMap[segment] || segment;
        const isLast = index === segments.length - 1;
        
        breadcrumbs.push({
            text: text,
            url: isLast ? null : currentPath
        });
    });
    
    return breadcrumbs;
}

// Render Breadcrumbs
export function renderBreadcrumbs(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const breadcrumbs = generateBreadcrumbs();

    container.innerHTML = `
        <nav class="flex items-center gap-2 text-xs" aria-label="Breadcrumb">
            ${breadcrumbs.map((crumb, index) => {
                const isLast = index === breadcrumbs.length - 1;
                const separator = index > 0 ? `<span class="text-slate-400">/</span>` : '';

                return `
                    ${separator}
                    ${crumb.url 
                        ? `<a href="${crumb.url}" class="text-slate-500 hover:text-slate-700 transition">${crumb.text}</a>`
                        : `<span class="text-slate-700 font-semibold">${crumb.text}</span>`
                    }
                `;
            }).join('')}
        </nav>
    `;
}

// Recently Visited Pages
export function addToRecentlyVisited(pageTitle, pageUrl, maxItems = 5) {
    const recent = getRecentlyVisited();

    // Remove if already exists
    const filtered = recent.filter(item => item.url !== pageUrl);

    // Add to beginning
    filtered.unshift({
        title: pageTitle,
        url: pageUrl,
        timestamp: Date.now()
    });

    // Keep only max items
    const trimmed = filtered.slice(0, maxItems);

    if (window.saveToLocalStorage) {
        window.saveToLocalStorage('recently_visited', trimmed);
    }
}

export function getRecentlyVisited() {
    if (window.getFromLocalStorage) {
        return window.getFromLocalStorage('recently_visited', []);
    }

    return [];
}

export function renderRecentlyVisited(containerId, maxItems = 5) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const recent = getRecentlyVisited().slice(0, maxItems);
    
    if (recent.length === 0) {
        container.innerHTML = '<p class="text-xs text-slate-400">Henüz ziyaret edilen sayfa yok</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="space-y-1">
            ${recent.map(item => `
                <a href="${item.url}" class="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-100 transition">
                    <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <span class="text-xs text-slate-600">${item.title}</span>
                </a>
            `).join('')}
        </div>
    `;
}

// Quick Navigation Shortcuts
export function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        const activeTag = document.activeElement ? document.activeElement.tagName : '';
        if (['INPUT', 'TEXTAREA', 'SELECT'].includes(activeTag) || (document.activeElement && document.activeElement.isContentEditable)) {
            return;
        }

        // Alt + H - Home
        if (e.altKey && e.key === 'h') {
            e.preventDefault();
            window.location.href = '/';
        }
        
        // Alt + T - Transactions
        if (e.altKey && e.key === 't') {
            e.preventDefault();
            window.location.href = '/transactions';
        }
        
        // Alt + P - Plans
        if (e.altKey && e.key === 'p') {
            e.preventDefault();
            window.location.href = '/plans';
        }
        
        // Alt + A - Assets
        if (e.altKey && e.key === 'a') {
            e.preventDefault();
            window.location.href = '/assets';
        }
        
        // Alt + S - Settings
        if (e.altKey && e.key === 's') {
            e.preventDefault();
            window.location.href = '/settings';
        }
        
        // Alt + ? - Help
        if (e.altKey && e.key === '?') {
            e.preventDefault();
            window.location.href = '/user_guide';
        }
    });
}

// Navigation Grouping (Collapsible Sections)
export function initCollapsibleNavigation() {
    const sectionTitles = document.querySelectorAll('.nav-section-title');
    
    sectionTitles.forEach(title => {
        // Skip sections already managed by layout-shell.js (which use data-target + .collapsible)
        if (title.classList.contains('collapsible') || title.hasAttribute('data-target') || title.dataset.collapsibleBound === 'true') {
            return;
        }
        title.dataset.collapsibleBound = 'true';
        title.style.cursor = 'pointer';
        title.addEventListener('click', () => {
            const nextElement = title.nextElementSibling;
            if (nextElement) {
                const isHidden = nextElement.style.display === 'none';
                nextElement.style.display = isHidden ? 'block' : 'none';
                title.classList.toggle('collapsed');
            }
        });
    });
}

// Export for global access
window.ECuzdanNavigation = {
    initNavigationSearch,
    generateBreadcrumbs,
    renderBreadcrumbs,
    addToRecentlyVisited,
    getRecentlyVisited,
    renderRecentlyVisited,
    initKeyboardShortcuts,
    initCollapsibleNavigation
};

// === undo.js ===
/**
 * E-CÜZDAN v15.0 - Undo JavaScript
 * Undo functionality for destructive actions
 */

// Undo Queue
let undoQueue = [];
const MAX_UNDO_ITEMS = 10;

// Add Action to Undo Queue
export function addToUndoQueue(action) {
    undoQueue.push({
        ...action,
        timestamp: Date.now()
    });
    
    // Keep only max items
    if (undoQueue.length > MAX_UNDO_ITEMS) {
        undoQueue.shift();
    }
    
    // Save to localStorage
    saveToLocalStorage('undo_queue', undoQueue);
}

// Get Undo Queue
export function getUndoQueue() {
    return undoQueue;
}

// Undo Last Action
export function undoLastAction() {
    if (undoQueue.length === 0) {
        showToast('Geri alınacak işlem yok', 'warning');
        return;
    }
    
    const action = undoQueue.pop();
    saveToLocalStorage('undo_queue', undoQueue);
    
    // Execute undo callback
    if (action.undoCallback && typeof action.undoCallback === 'function') {
        try {
            action.undoCallback(action.data);
            showToast(`${action.description} geri alındı`, 'success');
        } catch (error) {
            console.error('Undo failed:', error);
            showToast('Geri alma başarısız', 'error');
        }
    }
}

// Show Undo Toast
export function showUndoToast(message, undoCallback, data = null, duration = 6000) {
    if (typeof window.showToast === 'function') {
        window.showToast(message, 'info', duration, {
            text: 'Geri Al',
            onClick: () => {
                if (typeof undoCallback === 'function') {
                    try {
                        undoCallback(data);
                        window.showToast('İşlem geri alındı', 'success');
                    } catch (error) {
                        console.error('Undo failed:', error);
                        window.showToast('Geri alma başarısız', 'error');
                    }
                }
            }
        });
        return;
    }

    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = 'toast-item bg-slate-800 text-white px-5 py-3 rounded-2xl shadow-2xl flex items-center gap-3';
    toast.innerHTML = `
        <span class="text-sm font-semibold">${message}</span>
        <button type="button" class="undo-btn text-emerald-400 font-bold text-xs hover:underline cursor-pointer">
            Geri Al
        </button>
    `;
    
    const btn = toast.querySelector('.undo-btn');
    if (btn) {
        btn.addEventListener('click', () => {
            if (typeof undoCallback === 'function') {
                try {
                    undoCallback(data);
                    if (typeof window.showToast === 'function') {
                        window.showToast('İşlem geri alındı', 'success');
                    }
                } catch (error) {
                    console.error('Undo failed:', error);
                }
            }
            toast.remove();
        });
    }
    
    container.appendChild(toast);
    setTimeout(() => {
        if (toast.parentNode) toast.remove();
    }, duration);
}

// Execute Undo from Toast
export function executeUndo(button) {
    const toast = button.closest('.toast-item');
    if (toast && toast.undoCallback) {
        try {
            toast.undoCallback(toast.undoData);
            if (typeof window.showToast === 'function') {
                window.showToast('İşlem geri alındı', 'success');
            }
        } catch (error) {
            console.error('Undo failed:', error);
            if (typeof window.showToast === 'function') {
                window.showToast('Geri alma başarısız', 'error');
            }
        }
        toast.remove();
    }
}

// Recently Deleted Items
export function addToRecentlyDeleted(item, type) {
    const recent = getFromLocalStorage('recently_deleted', []);
    
    recent.unshift({
        ...item,
        type: type,
        timestamp: Date.now()
    });
    
    // Keep only max items
    const trimmed = recent.slice(0, 20);
    saveToLocalStorage('recently_deleted', trimmed);
}

export function getRecentlyDeleted() {
    return getFromLocalStorage('recently_deleted', []);
}

export function restoreFromRecentlyDeleted(id) {
    const recent = getRecentlyDeleted();
    const item = recent.find(item => item.id === id);
    
    if (item) {
        // Remove from recently deleted
        const filtered = recent.filter(i => i.id !== id);
        saveToLocalStorage('recently_deleted', filtered);
        
        return item;
    }
    
    return null;
}

// Render Recently Deleted Panel
export function renderRecentlyDeletedPanel(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const recent = getRecentlyDeleted();
    
    if (recent.length === 0) {
        container.innerHTML = '<p class="text-xs text-slate-400">Son silinen öğe yok</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="space-y-2">
            ${recent.map(item => `
                <div class="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-200">
                    <div class="flex items-center gap-2">
                        <span class="text-lg">${item.icon || '📄'}</span>
                        <div>
                            <p class="text-xs font-semibold text-slate-700">${item.name || item.title || 'Öğe'}</p>
                            <p class="text-[10px] text-slate-400">${item.type || 'Genel'}</p>
                        </div>
                    </div>
                    <button onclick="restoreItem('${item.id}')" class="text-emerald-600 font-bold text-[10px] hover:underline">
                        Geri Yükle
                    </button>
                </div>
            `).join('')}
        </div>
    `;
}

// Restore Item
function restoreItem(id) {
    const item = restoreFromRecentlyDeleted(id);
    
    if (item) {
        // Trigger restore callback (would be implemented per use case)
        console.log('Restoring item:', item);
        showToast('Öğe geri yüklendi', 'success');
        
        // Refresh panel
        renderRecentlyDeletedPanel('recently-deleted-panel');
    }
}

// Clear Undo Queue
export function clearUndoQueue() {
    undoQueue = [];
    saveToLocalStorage('undo_queue', []);
}

// Clear Recently Deleted
export function clearRecentlyDeleted() {
    saveToLocalStorage('recently_deleted', []);
}

// Export for global access
window.showUndoToast = showUndoToast;
window.executeUndo = executeUndo;
window.restoreItem = restoreItem;

window.ECuzdanUndo = {
    addToUndoQueue,
    getUndoQueue,
    undoLastAction,
    showUndoToast,
    addToRecentlyDeleted,
    getRecentlyDeleted,
    restoreFromRecentlyDeleted,
    renderRecentlyDeletedPanel,
    clearUndoQueue,
    clearRecentlyDeleted
};

// === lazyload.js ===
/**
 * E-CÜZDAN v15.0 - Lazy Loading JavaScript
 * Lazy loading for images, charts, and components
 */

// Image Lazy Loading
export function initLazyImages() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    }, {
        rootMargin: '50px 0px',
        threshold: 0.01
    });
    
    images.forEach(img => {
        img.classList.add('lazy');
        imageObserver.observe(img);
    });
}

// Chart Lazy Loading
export function initLazyCharts() {
    const chartContainers = document.querySelectorAll('[data-lazy-chart]');
    
    const chartObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const container = entry.target;
                const chartId = container.dataset.lazyChart;
                let chartData = {};
                try {
                    chartData = JSON.parse(container.dataset.chartData || '{}');
                } catch (e) {
                    console.error('[lazyload] Failed to parse chartData for', chartId, e);
                }
                if (window.ECuzdanCharts && window.ECuzdanCharts[chartType]) {
                    const ctx = document.getElementById(chartId);
                    if (ctx) {
                        window.ECuzdanCharts[chartType](ctx, chartData);
                    }
                }
                
                container.removeAttribute('data-lazy-chart');
                observer.unobserve(container);
            }
        });
    }, {
        rootMargin: '100px 0px',
        threshold: 0.1
    });
    
    chartContainers.forEach(container => {
        chartObserver.observe(container);
    });
}

// Component Lazy Loading
export function initLazyComponents() {
    const components = document.querySelectorAll('[data-lazy-component]');
    
    const componentObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const component = entry.target;
                const componentUrl = component.dataset.lazyComponent;
                
                // Load component content
                fetch(componentUrl)
                    .then(response => response.text())
                    .then(html => {
                        component.innerHTML = html;
                        component.removeAttribute('data-lazy-component');
                        
                        // Re-initialize any scripts in the loaded content
                        const scripts = component.querySelectorAll('script');
                        scripts.forEach(script => {
                            const newScript = document.createElement('script');
                            newScript.textContent = script.textContent;
                            component.appendChild(newScript);
                            script.remove();
                        });
                    })
                    .catch(error => {
                        console.error('Failed to load component:', error);
                        component.innerHTML = '<p class="text-red-500">Yükleme hatası</p>';
                    });
                
                observer.unobserve(component);
            }
        });
    }, {
        rootMargin: '50px 0px',
        threshold: 0.1
    });
    
    components.forEach(component => {
        componentObserver.observe(component);
    });
}

// Data Lazy Loading (for tables, lists)
export function initLazyData(loadMoreCallback, containerId, initialItems = 20, itemsPerLoad = 20) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    let loadedItems = initialItems;
    let isLoading = false;
    let hasMore = true;
    
    // Load more button
    const loadMoreBtn = document.createElement('button');
    loadMoreBtn.className = 'w-full mt-4 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg transition';
    loadMoreBtn.textContent = (window.ECuzdanI18n && window.ECuzdanI18n['ui_auto_17a41349037a'] || "Daha Fazla Göster");
    
    loadMoreBtn.addEventListener('click', async () => {
        if (isLoading || !hasMore) return;
        
        isLoading = true;
        loadMoreBtn.textContent = 'Yükleniyor...';
        loadMoreBtn.disabled = true;
        
        try {
            const newItems = await loadMoreCallback(loadedItems, itemsPerLoad);
            
            if (newItems && newItems.length > 0) {
                // Append new items to container
                newItems.forEach(item => {
                    const itemElement = document.createElement('div');
                    itemElement.innerHTML = item;
                    container.appendChild(itemElement);
                });
                
                loadedItems += newItems.length;
                
                if (newItems.length < itemsPerLoad) {
                    hasMore = false;
                    loadMoreBtn.textContent = (window.ECuzdanI18n && window.ECuzdanI18n['ui_auto_9792f0920af8'] || "Tüm öğeler yüklendi");
                    loadMoreBtn.disabled = true;
                } else {
                    loadMoreBtn.textContent = (window.ECuzdanI18n && window.ECuzdanI18n['ui_auto_17a41349037a'] || "Daha Fazla Göster");
                    loadMoreBtn.disabled = false;
                }
            } else {
                hasMore = false;
                loadMoreBtn.textContent = (window.ECuzdanI18n && window.ECuzdanI18n['ui_auto_9792f0920af8'] || "Tüm öğeler yüklendi");
                loadMoreBtn.disabled = true;
            }
        } catch (error) {
            console.error('Failed to load more items:', error);
            loadMoreBtn.textContent = (window.ECuzdanI18n && window.ECuzdanI18n['ui_auto_ce3b7a0ce97b'] || "Yükleme Hatası");
            loadMoreBtn.disabled = false;
        }
        
        isLoading = false;
    });
    
    container.parentNode.insertBefore(loadMoreBtn, container.nextSibling);
}

// Background Image Lazy Loading
export function initLazyBackgrounds() {
    const elements = document.querySelectorAll('[data-bg-src]');
    
    const bgObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                element.style.backgroundImage = `url(${element.dataset.bgSrc})`;
                element.removeAttribute('data-bg-src');
                observer.unobserve(element);
            }
        });
    }, {
        rootMargin: '50px 0px',
        threshold: 0.1
    });
    
    elements.forEach(element => {
        bgObserver.observe(element);
    });
}

// Initialize All Lazy Loading
export function initAllLazyLoading() {
    initLazyImages();
    initLazyCharts();
    initLazyComponents();
    initLazyBackgrounds();
}

// Export for global access
window.ECuzdanLazyLoad = {
    initLazyImages,
    initLazyCharts,
    initLazyComponents,
    initLazyData,
    initLazyBackgrounds,
    initAllLazyLoading
};

// === date-picker.js ===
/**
 * Tarih alanları: gg/aa/yyyy manuel giriş + takvim, geçersiz tarih reddi.
 */
(function () {
    const DATE_PATTERN = /^(\d{2})\/(\d{2})\/(\d{4})$/;

    function isValidDateParts(day, month, year) {
        if (year < 1990 || year > 2100) return false;
        if (month < 1 || month > 12) return false;
        if (day < 1 || day > 31) return false;
        const d = new Date(year, month - 1, day);
        return d.getFullYear() === year && d.getMonth() === month - 1 && d.getDate() === day;
    }

    window.validateDateTr = function (value) {
        if (!value || !String(value).trim()) return false;
        const m = String(value).trim().match(DATE_PATTERN);
        if (!m) return false;
        return isValidDateParts(parseInt(m[1], 10), parseInt(m[2], 10), parseInt(m[3], 10));
    };

    function setInvalid(input, invalid) {
        input.classList.toggle('ring-2', invalid);
        input.classList.toggle('ring-rose-500', invalid);
        input.classList.toggle('border-rose-500', invalid);
        input.setCustomValidity(invalid ? 'Geçerli bir tarih girin (gg/aa/yyyy).' : '');
    }

    function maskWhileTyping(el) {
        const digits = el.value.replace(/\D/g, '').slice(0, 8);
        if (digits.length <= 2) el.value = digits;
        else if (digits.length <= 4) el.value = digits.slice(0, 2) + '/' + digits.slice(2);
        else el.value = digits.slice(0, 2) + '/' + digits.slice(2, 4) + '/' + digits.slice(4);
    }

    function initDateField(input) {
        if (input.dataset.dateInited) return;
        input.dataset.dateInited = '1';

        input.addEventListener('input', function () {
            if (!input._flatpickr) maskWhileTyping(input);
            if (input.classList.contains('ring-rose-500')) setInvalid(input, false);
        });

        if (typeof flatpickr === 'undefined') {
            input.addEventListener('blur', function () {
                const v = input.value.trim();
                if (!v) { setInvalid(input, input.required); return; }
                setInvalid(input, !validateDateTr(v));
            });
            return;
        }

        flatpickr(input, {
            locale: flatpickr.l10ns.tr,
            dateFormat: 'd/m/Y',
            allowInput: true,
            disableMobile: false,
            clickOpens: true,
            monthSelectorType: 'dropdown',
            prevArrow: '‹',
            nextArrow: '›',
            onReady: function (_, __, inst) {
                const wrap = input.closest('.date-field-wrap');
                const btn = wrap && wrap.querySelector('.date-picker-btn');
                if (btn) {
                    btn.addEventListener('click', function (e) {
                        e.preventDefault();
                        inst.open();
                    });
                }
            },
            onChange: function () {
                setInvalid(input, false);
            },
            onClose: function (selectedDates, dateStr) {
                if (!dateStr.trim()) {
                    setInvalid(input, input.required);
                    return;
                }
                const ok = selectedDates.length > 0 || validateDateTr(dateStr);
                setInvalid(input, !ok);
                if (!ok && selectedDates.length === 0) {
                    input.value = dateStr;
                }
            }
        });

        input.addEventListener('blur', function () {
            const v = input.value.trim();
            if (!v) {
                setInvalid(input, input.required);
                return;
            }
            setInvalid(input, !validateDateTr(v));
        });
    }

    function initAll() {
        document.querySelectorAll('.date-tr').forEach(initDateField);
    }

    document.addEventListener('submit', function (e) {
        const form = e.target;
        if (!form || form.tagName !== 'FORM') return;
        let firstInvalid = null;
        form.querySelectorAll('.date-tr').forEach(function (input) {
            const v = input.value.trim();
            if (input.required && !v) {
                setInvalid(input, true);
                if (!firstInvalid) firstInvalid = input;
                return;
            }
            if (v && !validateDateTr(v)) {
                setInvalid(input, true);
                if (!firstInvalid) firstInvalid = input;
            }
        });
        if (firstInvalid) {
            e.preventDefault();
            e.stopImmediatePropagation();
            firstInvalid.reportValidity();
            firstInvalid.focus();
        }
    }, true);

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
    } else {
        initAll();
    }
})();
