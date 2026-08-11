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

// Toast Notifications
export function showToast(message, type = 'success', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    const bgColor = type === 'success' ? 'bg-emerald-600' :
                   type === 'error' ? 'bg-rose-600' :
                   type === 'warning' ? 'bg-amber-600' : 'bg-blue-600';

    toast.className = `toast-item ${bgColor}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, duration);
}

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
    if (!mobileSidebar) return;

    const isHidden = mobileSidebar.classList.toggle('hidden');
    document.body.style.overflow = isHidden ? '' : 'hidden';

    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    if (mobileMenuBtn) {
        mobileMenuBtn.setAttribute('aria-expanded', (!isHidden).toString());
    }
}

// Close modal on backdrop and overlay click
document.addEventListener('click', (e) => {
    if (e.target.matches('.edit-modal-backdrop, .delete-modal-backdrop, .modal-overlay, .modal')) {
        closeModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
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
