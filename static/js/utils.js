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
export function showToast(message, type = 'success', duration = 4000) {
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

    toast.className = `toast-item ${bgColor} text-white px-6 py-4 rounded-2xl shadow-2xl flex items-center gap-3 transform transition-all duration-300 translate-x-full opacity-0`;
    toast.innerHTML = `
        <div class="flex-shrink-0">${icon}</div>
        <div class="flex-1 font-semibold text-sm">${message}</div>
        <button onclick="this.parentElement.remove()" class="flex-shrink-0 hover:opacity-80 transition">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
    `;

    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.classList.remove('translate-x-full', 'opacity-0');
    });

    // Auto remove
    setTimeout(() => {
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
        }, 300);
    }, duration);
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
