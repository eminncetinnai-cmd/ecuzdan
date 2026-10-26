/* ============================================================
   E-Cüzdan · layout-shell.js
   layout.html içinden ayrıştırıldı: header, bildirim paneli,
   global arama (Ctrl+K), dropdown ve canlı ticker yenileme.
   Çeviriler window.ECuzdanI18n kataloğundan okunur (layout.html).
   ============================================================ */
var __LAYOUT_I18N_FALLBACK = {
    notifications_load_failed: 'Bildirimler yüklenemedi.',
    notifications_empty_text: 'Henüz bildiriminiz bulunmuyor.',
    nav_transactions: 'İşlemler',
    nav_settings: 'Ayarlar',
    nav_investor_profile: 'Yatırımcı Profili',
    nav_financial_education: 'Finansal Eğitim'
};
function __t(key) {
    var catalog = window.ECuzdanI18n || {};
    return catalog[key] || __LAYOUT_I18N_FALLBACK[key] || key;
}

// Header scroll effect
window.addEventListener('scroll', function() {
    const header = document.getElementById('headerBar');
    if (header) {
        if (window.scrollY > 10) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    }
});

// Quick Actions Toggle
function toggleQuickActions() {
    const panel = document.getElementById('quickActionsPanel');
    if (panel) {
        panel.classList.toggle('hidden');
    }
}
window.toggleQuickActions = toggleQuickActions;

// User Dropdown Toggle
function toggleUserDropdown() {
    const panel = document.getElementById('userDropdownPanel');
    if (panel) {
        panel.classList.toggle('hidden');
    }
}
window.toggleUserDropdown = toggleUserDropdown;

// Notification Modal Functions
const NOTIFICATION_POLL_INTERVAL_MS = 30000;
const NOTIFICATION_MAX_BACKOFF_MS = 5 * 60 * 1000;
const notificationCountState = {
    request: null,
    timer: null,
    nextAllowedAt: 0,
    backoffMs: NOTIFICATION_POLL_INTERVAL_MS,
};

function notificationRetryDelay(response) {
    const retryAfter = Number(response?.headers?.get('Retry-After'));
    if (Number.isFinite(retryAfter) && retryAfter >= 0) return Math.max(1000, retryAfter * 1000);
    return notificationCountState.backoffMs;
}

function scheduleNotificationCountPoll(delay = NOTIFICATION_POLL_INTERVAL_MS) {
    if (notificationCountState.timer) window.clearTimeout(notificationCountState.timer);
    notificationCountState.timer = window.setTimeout(() => {
        notificationCountState.timer = null;
        if (document.visibilityState === 'visible') fetchUnreadCount();
        scheduleNotificationCountPoll(NOTIFICATION_POLL_INTERVAL_MS);
    }, Math.max(1000, delay));
}

function openNotificationModal() {

    const modal = document.getElementById('notificationModal');
    if (modal) {
        modal.classList.remove('hidden');
        loadNotifications();
    }
    // Close user dropdown
    const panel = document.getElementById('userDropdownPanel');
    if (panel) {
        panel.classList.add('hidden');
    }
}

function closeNotificationModal() {
    const modal = document.getElementById('notificationModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

async function loadNotifications() {
    const list = document.getElementById('notificationList');
    if (!list) return;
    
    try {
        const response = await fetch(ECuzdanEndpoints.notifications.all);
                const data = await response.json().catch(() => ({}));
        if (response.status === 429) return;
        if (data.success) {

            renderNotifications(data.items || []);
            updateNotificationBadge(data.unread || 0);
        } else {

            // Show error message only if there's an actual error, not just empty results
            if (data.message) {
                list.innerHTML = '<div class="text-center py-8 text-slate-500 dark:text-slate-400 text-sm">' + __t('notifications_load_failed') + '</div>';
            } else {
                list.innerHTML = '<div class="text-center py-8 text-slate-500 dark:text-slate-400 text-sm">' + __t('notifications_empty_text') + '</div>';
            }
        }
        } catch (error) {
        list.innerHTML = '<div class="text-center py-8 text-slate-500 dark:text-slate-400 text-sm">' + __t('notifications_load_failed') + '</div>';
    }

}

function renderNotifications(items) {
    const list = document.getElementById('notificationList');
    if (!list) return;
    
        if (!items || items.length === 0) {

        list.innerHTML = '<div class="text-center py-8 text-slate-500 dark:text-slate-400 text-sm">' + __t('notifications_empty_text') + '</div>';
        return;
    }
    
    list.innerHTML = items.map(item => `
        <div class="notification-item p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/60 transition cursor-pointer ${item.is_read ? 'opacity-60' : ''}" onclick="markAsRead(${item.id})">
            <div class="flex items-start gap-3">
                <div class="flex-shrink-0 w-2 h-2 rounded-full mt-2 ${getSeverityColor(item.severity)}"></div>
                <div class="flex-1 min-w-0">
                    <p class="text-xs font-semibold text-slate-800 dark:text-slate-100 truncate">${escapeHtml(item.title)}</p>
                    <p class="text-[10px] text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">${escapeHtml(item.body)}</p>
                    <p class="text-[9px] text-slate-400 dark:text-slate-500 mt-1">${item.created_at}</p>
                </div>
            </div>
        </div>
    `).join('');
}

function getSeverityColor(severity) {
    const colors = {
        'info': 'bg-blue-500',
        'success': 'bg-green-500',
        'warning': 'bg-yellow-500',
        'error': 'bg-red-500',
        'critical': 'bg-red-600'
    };
    return colors[severity] || 'bg-slate-500';
}

async function markAsRead(notificationId) {
    try {
        const response = await fetch(ECuzdanEndpoints.notifications.markRead(notificationId), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        
        if (data.success) {
            updateNotificationBadge(data.unread);
            loadNotifications(); // Reload to update UI
                }
    } catch (error) {
        // Keep the header quiet; the next scheduled poll will retry safely.
    }

}

async function markAllAsRead() {
    try {
        const response = await fetch(ECuzdanEndpoints.notifications.markAllRead, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        
        if (data.success) {
            updateNotificationBadge(0);
            loadNotifications(); // Reload to update UI
                }
    } catch (error) {
        // Keep the header quiet; the next scheduled poll will retry safely.
    }

}

function updateNotificationBadge(count) {
    const badge = document.getElementById('notificationBadge');
    const dropdownBadge = document.getElementById('dropdownNotificationBadge');
    const sidebarBadges = document.querySelectorAll('.sidebar-notification-badge');
    
    const displayCount = count > 99 ? '99+' : count;

    if (count > 0) {
        if (badge) {
            badge.textContent = displayCount;
            badge.classList.remove('hidden');
        }
        if (dropdownBadge) {
            dropdownBadge.textContent = displayCount;
            dropdownBadge.classList.remove('hidden');
        }
        sidebarBadges.forEach(el => {
            el.textContent = displayCount;
            el.classList.remove('hidden');
        });
    } else {
        if (badge) badge.classList.add('hidden');
        if (dropdownBadge) dropdownBadge.classList.add('hidden');
        sidebarBadges.forEach(el => {
            el.classList.add('hidden');
        });
    }
}

async function fetchUnreadCount(options = {}) {
    const force = options.force === true;
    if (document.visibilityState === 'hidden' && !force) return null;
    if (notificationCountState.request) return notificationCountState.request;
    if (!force && Date.now() < notificationCountState.nextAllowedAt) return null;

    notificationCountState.request = (async () => {
        try {
            const response = await fetch(ECuzdanEndpoints.notifications.unreadCount, {
                headers: { 'Accept': 'application/json' },
                credentials: 'same-origin',
            });
            if (response.status === 429) {
                const delay = notificationRetryDelay(response);
                notificationCountState.nextAllowedAt = Date.now() + delay;
                notificationCountState.backoffMs = Math.min(
                    NOTIFICATION_MAX_BACKOFF_MS,
                    Math.max(NOTIFICATION_POLL_INTERVAL_MS, delay * 2),
                );
                return null;
            }
            if (!response.ok) throw new Error(`Notification count HTTP ${response.status}`);
            const data = await response.json();
            if (data.success) updateNotificationBadge(data.unread);
            notificationCountState.backoffMs = NOTIFICATION_POLL_INTERVAL_MS;
            notificationCountState.nextAllowedAt = 0;
            return data;
        } catch (error) {
            const delay = notificationCountState.backoffMs;
            notificationCountState.nextAllowedAt = Date.now() + delay;
            notificationCountState.backoffMs = Math.min(NOTIFICATION_MAX_BACKOFF_MS, delay * 2);
            return null;
        } finally {
            notificationCountState.request = null;
        }
    })();
    return notificationCountState.request;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load unread count on page load without creating overlapping requests.
document.addEventListener('DOMContentLoaded', function() {
    fetchUnreadCount({ force: true });
    scheduleNotificationCountPoll();
});
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') fetchUnreadCount({ force: true });
});

// Theme Toggle
function updateThemeIcon(isDark) {
    document.querySelectorAll(".theme-toggle-btn .dark-icon").forEach(function(icon) {
        icon.classList.toggle("hidden", !isDark);
    });
    document.querySelectorAll(".theme-toggle-btn .light-icon").forEach(function(icon) {
        icon.classList.toggle("hidden", isDark);
    });
    document.querySelectorAll("[data-theme-toggle]").forEach(function(toggle) {
        const nextThemeLabel = isDark ? "Açık temaya geç" : "Koyu temaya geç";
        toggle.dataset.themeState = isDark ? "dark" : "light";
        toggle.setAttribute("aria-pressed", String(isDark));
        toggle.setAttribute("aria-label", nextThemeLabel);
        toggle.setAttribute("title", nextThemeLabel);
    });
}

function saveThemePreference(theme) {
    const token = document.querySelector("meta[name=\"csrf-token\"]")?.content || "";
    const body = new URLSearchParams();
    body.set("csrf_token", token);
    body.set("theme", theme);
    return fetch(ECuzdanEndpoints.settings.theme, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body
    }).then(response => response.json());
}

function updateStatusBarTheme(isDark) {
    const themeColorMeta = document.querySelector('meta[name="theme-color"]');
    const appleStatusMeta = document.querySelector('meta[name="apple-mobile-web-app-status-bar-style"]');
    if (themeColorMeta) {
        themeColorMeta.setAttribute('content', isDark ? 'rgb(15, 23, 42)' : 'rgb(248, 250, 252)');
    }
    if (appleStatusMeta) {
        appleStatusMeta.setAttribute('content', isDark ? 'black-translucent' : 'default');
    }
}

function setTheme(theme, options = {}) {
    const normalized = String(theme || "light").toLowerCase();
    if (!["light", "dark"].includes(normalized)) return Promise.reject(new Error("Unsupported theme"));
    const html = document.documentElement;
    const isDark = normalized === "dark";
    const toggles = document.querySelectorAll("[data-theme-toggle]");
    html.classList.add("theme-transition");
    toggles.forEach(function(toggle) {
        toggle.classList.add("is-switching");
        toggle.setAttribute("aria-busy", "true");
        toggle.disabled = true;
    });
    html.classList.toggle("dark", isDark);
    html.setAttribute("data-user-theme", normalized);
    html.setAttribute("data-theme", normalized);
    updateThemeIcon(isDark);
    updateStatusBarTheme(isDark);
    window.dispatchEvent(new CustomEvent("ecuzdan:theme-changed", {
        detail: { theme: normalized }
    }));
    const persist = options.persist !== false;
    const finalize = function() {
        toggles.forEach(function(toggle) {
            toggle.classList.remove("is-switching");
            toggle.removeAttribute("aria-busy");
            toggle.disabled = false;
        });
        window.setTimeout(function() {
            html.classList.remove("theme-transition");
        }, 320);
    };
    if (!persist) {
        finalize();
        return Promise.resolve({ success: true, theme: normalized });
    }
    return saveThemePreference(normalized).then(data => {
        if (!data || !data.success) throw new Error((data && data.message) || "Tema tercihi kaydedilemedi.");
        localStorage.setItem("theme", normalized);
        return data;
    }).finally(finalize);
}

function toggleTheme() {
    const current = document.documentElement.classList.contains("dark") ? "dark" : "light";
    const target = current === "dark" ? "light" : "dark";
    return setTheme(target).catch(error => {
        setTheme(current, { persist: false });
        if (window.showToast) window.showToast(error.message || "Tema tercihi kaydedilemedi.", "error");
        throw error;
    });
}

window.ECuzdanUI = window.ECuzdanUI || {};
window.ECuzdanUI.setTheme = setTheme;
// Initialize theme, collapsible sections, and sidebar rail mode
document.addEventListener("DOMContentLoaded", function() {
    const initialDark = document.documentElement.classList.contains("dark");
    updateThemeIcon(initialDark);
    updateStatusBarTheme(initialDark);

    // Initialize collapsible sections with localStorage persistence
    initCollapsibleSections();

    // Initialize Outlook/WhatsApp-style collapsible icon rail & hover-peek
    initSidebarRail();
});

// Collapsible Sections with localStorage Persistence
const COLLAPSED_SECTIONS_STORAGE_KEY = 'ecuzdan_collapsed_sections';

function getSavedCollapsedSections() {
    try {
        const raw = localStorage.getItem(COLLAPSED_SECTIONS_STORAGE_KEY);
        const parsed = raw ? JSON.parse(raw) : [];
        return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
        return [];
    }
}

function saveCollapsedSections(sectionIds) {
    try {
        localStorage.setItem(COLLAPSED_SECTIONS_STORAGE_KEY, JSON.stringify(sectionIds));
    } catch (e) {
        // Ignore storage quota errors
    }
}

function setSectionCollapsedState(titleElement, contentElement, isCollapsed) {
    if (!titleElement || !contentElement) return;
    titleElement.classList.toggle('collapsed', isCollapsed);
    contentElement.classList.toggle('collapsed', isCollapsed);
    titleElement.setAttribute('aria-expanded', String(!isCollapsed));
}

function toggleSection(sectionId, titleElement) {
    const content = document.getElementById(sectionId);
    if (content && titleElement) {
        const nextCollapsed = !content.classList.contains('collapsed');
        setSectionCollapsedState(titleElement, content, nextCollapsed);
        const saved = new Set(getSavedCollapsedSections());
        if (nextCollapsed) {
            saved.add(sectionId);
        } else {
            saved.delete(sectionId);
        }
        saveCollapsedSections(Array.from(saved));
    }
}

function initCollapsibleSections() {
    const collapsibles = document.querySelectorAll('.nav-section-title.collapsible');
    const savedCollapsed = new Set(getSavedCollapsedSections());

    collapsibles.forEach(title => {
        if (title.dataset.collapsibleBound === 'true') return;
        title.dataset.collapsibleBound = 'true';

        const targetId = title.getAttribute('data-target');
        const content = targetId ? document.getElementById(targetId) : null;

        if (content && targetId) {
            const hasActiveChild = Boolean(content.querySelector('.nav-link.active'));
            const shouldCollapse = savedCollapsed.has(targetId) && !hasActiveChild;
            setSectionCollapsedState(title, content, shouldCollapse);
        }

        title.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const id = this.getAttribute('data-target');
            if (id) toggleSection(id, this);
        });

        title.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                e.stopPropagation();
                const id = this.getAttribute('data-target');
                if (id) toggleSection(id, this);
            }
        });
    });
}

// ============================================================
// Outlook / WhatsApp / Teams-Style Collapsible Icon Rail Mode
// ============================================================
const SIDEBAR_MODE_STORAGE_KEY = 'ecuzdan_sidebar_mode';
let railPeekEnterTimer = null;
let railPeekLeaveTimer = null;
let suppressPeekUntilMouseLeave = false;

function getSidebarRailMode() {
    return document.documentElement.getAttribute('data-sidebar-mode') === 'rail' ? 'rail' : 'expanded';
}

function syncSidebarRailUI(mode) {
    const isRail = mode === 'rail';
    const labelEl = document.getElementById('sidebarRailModeLabel');
    const railText = (labelEl && labelEl.getAttribute('data-rail-text')) || 'Menüyü Genişlet';
    const expandedText = (labelEl && labelEl.getAttribute('data-expanded-text')) || 'Menüyü Daralt (Rail)';
    if (labelEl) {
        labelEl.textContent = isRail ? railText : expandedText;
    }
    const toggleBtn = document.getElementById('sidebarRailToggleBtn');
    const footerBtn = document.getElementById('sidebarRailFooterBtn');
    const currentTitle = isRail ? (railText + ' (Ctrl+B)') : (expandedText + ' (Ctrl+B)');
    if (toggleBtn) {
        toggleBtn.setAttribute('aria-pressed', String(isRail));
        toggleBtn.setAttribute('aria-expanded', String(!isRail));
        toggleBtn.setAttribute('title', currentTitle);
        toggleBtn.setAttribute('aria-label', currentTitle);
    }
    if (footerBtn) {
        footerBtn.setAttribute('aria-pressed', String(isRail));
        footerBtn.setAttribute('aria-expanded', String(!isRail));
        footerBtn.setAttribute('title', currentTitle);
        footerBtn.setAttribute('aria-label', currentTitle);
    }
    const collapseIcon = document.querySelector('.rail-icon-collapse');
    const expandIcon = document.querySelector('.rail-icon-expand');
    if (collapseIcon) collapseIcon.classList.toggle('hidden', isRail);
    if (expandIcon) expandIcon.classList.toggle('hidden', !isRail);
}

function setSidebarRailMode(mode, options = {}) {
    const normalized = mode === 'rail' ? 'rail' : 'expanded';
    document.documentElement.setAttribute('data-sidebar-mode', normalized);

    const sidebar = document.getElementById('desktopSidebar');
    if (sidebar) {
        sidebar.classList.remove('rail-peek');
    }

    if (normalized === 'rail') {
        suppressPeekUntilMouseLeave = true;
        if (railPeekEnterTimer) {
            clearTimeout(railPeekEnterTimer);
            railPeekEnterTimer = null;
        }
    }

    if (options.persist !== false) {
        try {
            localStorage.setItem(SIDEBAR_MODE_STORAGE_KEY, normalized);
        } catch (e) {
            // Ignore storage errors
        }
    }

    syncSidebarRailUI(normalized);
    window.dispatchEvent(new CustomEvent('ecuzdan:sidebar-mode-changed', {
        detail: { mode: normalized }
    }));

    // Trigger window resize event after transition (250ms) so canvas & charts adapt
    setTimeout(function() {
        window.dispatchEvent(new Event('resize'));
    }, 260);

    return normalized;
}

function toggleSidebarRailMode() {
    if (document.activeElement && typeof document.activeElement.blur === 'function') {
        document.activeElement.blur();
    }
    const nextMode = getSidebarRailMode() === 'rail' ? 'expanded' : 'rail';
    return setSidebarRailMode(nextMode);
}
window.toggleSidebarRailMode = toggleSidebarRailMode;
window.ECuzdanUI.setSidebarRailMode = setSidebarRailMode;

function initSidebarRail() {
    syncSidebarRailUI(getSidebarRailMode());

    const sidebar = document.getElementById('desktopSidebar');
    if (!sidebar || sidebar.dataset.railBound === 'true') return;
    sidebar.dataset.railBound = 'true';

    // Keyboard accessibility: expand when navigating with Tab (:focus-visible)
    sidebar.addEventListener('focusin', function(e) {
        if (getSidebarRailMode() === 'rail' && e.target && e.target.matches && e.target.matches(':focus-visible')) {
            sidebar.classList.add('rail-peek');
        }
    });

    sidebar.addEventListener('focusout', function(e) {
        if (sidebar.contains(e.relatedTarget)) return;
        sidebar.classList.remove('rail-peek');
    });
}

// Global Search Command Palette (Ctrl+K)
let searchSelectedIndex = -1;

function updateSearchItemHighlight() {
    const resultsContainer = document.getElementById('searchResults');
    if (!resultsContainer) return;
    const items = resultsContainer.querySelectorAll('.search-result-item');
    items.forEach((item, index) => {
        item.classList.toggle('is-selected', index === searchSelectedIndex);
        if (index === searchSelectedIndex) {
            item.scrollIntoView({ block: 'nearest' });
        }
    });
}

function openGlobalSearch() {
    const paletteModal = document.getElementById('commandPaletteModal');
    if (paletteModal) {
        paletteModal.classList.remove('hidden');
        paletteModal.classList.add('active');
        paletteModal.style.display = 'flex';
        paletteModal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        const paletteInput = document.getElementById('commandPaletteInput');
        if (paletteInput) {
            paletteInput.value = '';
            paletteInput.dispatchEvent(new Event('input'));
            setTimeout(() => paletteInput.focus(), 50);
        }
        return;
    }
    searchSelectedIndex = -1;
    const existingModal = document.getElementById('globalSearchModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    const modal = document.createElement('div');
    modal.id = 'globalSearchModal';
    modal.className = 'fixed inset-0 z-[100] flex items-start justify-center pt-20 px-4';
    modal.innerHTML = `
        <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" onclick="closeGlobalSearch()"></div>
        <div class="relative w-full max-w-2xl bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-slate-200/70 dark:border-slate-800 overflow-hidden">
            <div class="flex items-center gap-3 p-4 border-b border-slate-100 dark:border-slate-800">
                <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
                <input type="text" id="globalSearchInput" placeholder="Ara... (sayfalar, işlemler, kategoriler)" class="flex-1 bg-transparent border-none outline-none text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 text-sm font-medium" autocomplete="off" oninput="handleSearchInput(this.value)">
                <div class="flex items-center gap-1">
                    <span class="text-[10px] font-mono bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 px-1.5 py-0.5 rounded border border-slate-200 dark:border-slate-700">ESC</span>
                </div>
                <button data-macro="button_secondary" type="button" onclick="closeGlobalSearch()" class="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
            <div id="searchResults" class="p-4 max-h-[65vh] overflow-y-auto">
                <div class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Hızlı Aksiyonlar</div>
                <div class="grid grid-cols-3 gap-2 mb-4">
                    <a href="#" onclick="closeGlobalSearch(); openGlobalQuickTxModal(); return false;" class="search-result-item flex items-center gap-2.5 p-2.5 rounded-xl bg-gradient-to-r from-sky-500/10 to-sky-600/10 hover:from-sky-500/20 hover:to-sky-600/20 border border-sky-500/20 transition cursor-pointer">
                        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-400 to-sky-600 flex items-center justify-center text-white flex-shrink-0">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"/></svg>
                        </div>
                        <div class="min-w-0">
                            <div class="text-xs font-bold text-slate-800 dark:text-slate-100 truncate">Hızlı İşlem</div>
                            <div class="text-[10px] text-slate-500 dark:text-slate-400 truncate">Gelir / Gider</div>
                        </div>
                    </a>
                    <a href="/plans?modal=new" onclick="closeGlobalSearch()" class="search-result-item flex items-center gap-2.5 p-2.5 rounded-xl bg-gradient-to-r from-indigo-500/10 to-indigo-600/10 hover:from-indigo-500/20 hover:to-indigo-600/20 border border-indigo-500/20 transition cursor-pointer">
                        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-400 to-indigo-600 flex items-center justify-center text-white flex-shrink-0">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"/></svg>
                        </div>
                        <div class="min-w-0">
                            <div class="text-xs font-bold text-slate-800 dark:text-slate-100 truncate">Plan Ekle</div>
                            <div class="text-[10px] text-slate-500 dark:text-slate-400 truncate">Taksit / Fatura</div>
                        </div>
                    </a>
                    <a href="/assets?modal=new" onclick="closeGlobalSearch()" class="search-result-item flex items-center gap-2.5 p-2.5 rounded-xl bg-gradient-to-r from-emerald-500/10 to-emerald-600/10 hover:from-emerald-500/20 hover:to-emerald-600/20 border border-emerald-500/20 transition cursor-pointer">
                        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center text-white flex-shrink-0">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        </div>
                        <div class="min-w-0">
                            <div class="text-xs font-bold text-slate-800 dark:text-slate-100 truncate">Varlık Ekle</div>
                            <div class="text-[10px] text-slate-500 dark:text-slate-400 truncate">Altın / Hisse</div>
                        </div>
                    </a>
                </div>
                <div class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Hızlı Erişim</div>
                <div class="grid grid-cols-2 gap-2">
                    <a href="/" onclick="closeGlobalSearch()" class="search-result-item flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition">
                        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-sky-400 to-sky-600 flex items-center justify-center">
                            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
                        </div>
                        <div>
                            <div class="text-sm font-bold text-slate-800 dark:text-slate-100">Dashboard</div>
                            <div class="text-xs text-slate-500 dark:text-slate-400">Genel bakış</div>
                        </div>
                    </a>
                    <a href="/transactions" onclick="closeGlobalSearch()" class="search-result-item flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition">
                        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-400 to-indigo-600 flex items-center justify-center">
                            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
                        </div>
                        <div>
                            <div class="text-sm font-bold text-slate-800 dark:text-slate-100">${__t('nav_transactions')}</div>
                            <div class="text-xs text-slate-500 dark:text-slate-400">Tüm hareketler</div>
                        </div>
                    </a>
                    <a href="/assets" onclick="closeGlobalSearch()" class="search-result-item flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition">
                        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center">
                            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        </div>
                        <div>
                            <div class="text-sm font-bold text-slate-800 dark:text-slate-100">Varlıklar</div>
                            <div class="text-xs text-slate-500 dark:text-slate-400">Yatırımlar</div>
                        </div>
                    </a>
                    <a href="/settings" onclick="closeGlobalSearch()" class="search-result-item flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition">
                        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center">
                            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/></svg>
                        </div>
                        <div>
                            <div class="text-sm font-bold text-slate-800 dark:text-slate-100">${__t('nav_settings')}</div>
                            <div class="text-xs text-slate-500 dark:text-slate-400">Sistem ayarları</div>
                        </div>
                    </a>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    
    setTimeout(() => {
        const input = document.getElementById('globalSearchInput');
        if (input) {
            input.focus();
            input.addEventListener('keydown', function(e) {
                const resultsContainer = document.getElementById('searchResults');
                if (!resultsContainer) return;
                const items = resultsContainer.querySelectorAll('.search-result-item');
                if (items.length === 0) return;

                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    searchSelectedIndex = (searchSelectedIndex + 1) % items.length;
                    updateSearchItemHighlight();
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    searchSelectedIndex = (searchSelectedIndex - 1 + items.length) % items.length;
                    updateSearchItemHighlight();
                } else if (e.key === 'Enter') {
                    if (searchSelectedIndex >= 0 && searchSelectedIndex < items.length) {
                        e.preventDefault();
                        items[searchSelectedIndex].click();
                    } else if (items.length > 0) {
                        e.preventDefault();
                        items[0].click();
                    }
                }
            });
        }
    }, 100);
}

function handleSearchInput(query) {
    searchSelectedIndex = -1;
    const resultsContainer = document.getElementById('searchResults');
    if (!resultsContainer) return;
    
    const lowerQuery = query.toLowerCase().trim();
    
    if (lowerQuery === '') {
        resultsContainer.innerHTML = `
            <div class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Hızlı Aksiyonlar</div>
            <div class="grid grid-cols-3 gap-2 mb-4">
                <a href="#" onclick="closeGlobalSearch(); openGlobalQuickTxModal(); return false;" class="search-result-item flex items-center gap-2.5 p-2.5 rounded-xl bg-gradient-to-r from-sky-500/10 to-sky-600/10 hover:from-sky-500/20 hover:to-sky-600/20 border border-sky-500/20 transition cursor-pointer">
                    <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-400 to-sky-600 flex items-center justify-center text-white flex-shrink-0">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"/></svg>
                    </div>
                    <div class="min-w-0">
                        <div class="text-xs font-bold text-slate-800 dark:text-slate-100 truncate">Hızlı İşlem</div>
                        <div class="text-[10px] text-slate-500 dark:text-slate-400 truncate">Gelir / Gider</div>
                    </div>
                </a>
                <a href="/plans?modal=new" onclick="closeGlobalSearch()" class="search-result-item flex items-center gap-2.5 p-2.5 rounded-xl bg-gradient-to-r from-indigo-500/10 to-indigo-600/10 hover:from-indigo-500/20 hover:to-indigo-600/20 border border-indigo-500/20 transition cursor-pointer">
                    <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-400 to-indigo-600 flex items-center justify-center text-white flex-shrink-0">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"/></svg>
                    </div>
                    <div class="min-w-0">
                        <div class="text-xs font-bold text-slate-800 dark:text-slate-100 truncate">Plan Ekle</div>
                        <div class="text-[10px] text-slate-500 dark:text-slate-400 truncate">Taksit / Fatura</div>
                    </div>
                </a>
                <a href="/assets?modal=new" onclick="closeGlobalSearch()" class="search-result-item flex items-center gap-2.5 p-2.5 rounded-xl bg-gradient-to-r from-emerald-500/10 to-emerald-600/10 hover:from-emerald-500/20 hover:to-emerald-600/20 border border-emerald-500/20 transition cursor-pointer">
                    <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center text-white flex-shrink-0">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                    </div>
                    <div class="min-w-0">
                        <div class="text-xs font-bold text-slate-800 dark:text-slate-100 truncate">Varlık Ekle</div>
                        <div class="text-[10px] text-slate-500 dark:text-slate-400 truncate">Altın / Hisse</div>
                    </div>
                </a>
            </div>
            <div class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Hızlı Erişim</div>
            <div class="grid grid-cols-2 gap-2">
                <a href="/" onclick="closeGlobalSearch()" class="search-result-item flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition">
                    <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-sky-400 to-sky-600 flex items-center justify-center">
                        <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
                    </div>
                    <div>
                        <div class="text-sm font-bold text-slate-800 dark:text-slate-100">Dashboard</div>
                        <div class="text-xs text-slate-500 dark:text-slate-400">Genel bakış</div>
                    </div>
                </a>
                <a href="/transactions" onclick="closeGlobalSearch()" class="search-result-item flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition">
                    <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-400 to-indigo-600 flex items-center justify-center">
                        <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
                    </div>
                    <div>
                        <div class="text-sm font-bold text-slate-800 dark:text-slate-100">${__t('nav_transactions')}</div>
                        <div class="text-xs text-slate-500 dark:text-slate-400">Tüm hareketler</div>
                    </div>
                </a>
                <a href="/assets" onclick="closeGlobalSearch()" class="search-result-item flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition">
                    <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center">
                        <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                    </div>
                    <div>
                        <div class="text-sm font-bold text-slate-800 dark:text-slate-100">Varlıklar</div>
                        <div class="text-xs text-slate-500 dark:text-slate-400">Yatırımlar</div>
                    </div>
                </a>
                <a href="/settings" onclick="closeGlobalSearch()" class="search-result-item flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition">
                    <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center">
                        <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/></svg>
                    </div>
                    <div>
                        <div class="text-sm font-bold text-slate-800 dark:text-slate-100">${__t('nav_settings')}</div>
                        <div class="text-xs text-slate-500 dark:text-slate-400">Sistem ayarları</div>
                    </div>
                </a>
            </div>
        `;
        return;
    }
    
    const searchItems = [
        // Hızlı Aksiyonlar
        { name: '＋ Hızlı İşlem Ekle', url: '#', action: 'quick-tx', keywords: ['işlem ekle', 'hızlı işlem', 'yeni işlem', 'gelir ekle', 'gider ekle', 'quick', 'add transaction'], icon: '⚡', category: 'Aksiyon' },
        { name: '＋ Düzenli İşlem / Plan Ekle', url: '/plans?modal=new', keywords: ['plan ekle', 'düzenli işlem ekle', 'taksit ekle', 'fatura ekle', 'yeni plan', 'recurring'], icon: '🔄', category: 'Aksiyon' },
        { name: '＋ Yeni Varlık Ekle', url: '/assets?modal=new', keywords: ['varlık ekle', 'yeni varlık', 'yatırım ekle', 'hisse ekle', 'altın ekle', 'add asset'], icon: '💰', category: 'Aksiyon' },
        // Genel Bakış (Overview)
        { name: 'Nakit Akışı / Dashboard', url: '/', keywords: ['dashboard', 'genel', 'bakış', 'ana', 'nakit', 'cash flow', 'özet'], icon: '📊', category: 'Genel Bakış' },
        { name: `${__t('nav_transactions')}`, url: '/transactions', keywords: ['işlem', 'transaction', 'hareket', 'gelir', 'gider', 'harcama'], icon: '💰', category: 'Genel Bakış' },
        { name: `${__t('nav_plans') || 'Düzenli İşlemler'}`, url: '/plans', keywords: ['plan', 'düzenli', 'taksit', 'abonelik', 'fatura', 'maaş', 'recurring'], icon: '🔄', category: 'Genel Bakış' },
        { name: 'Aylık Dashboard', url: '/monthly_dashboard', keywords: ['aylık', 'monthly', 'rapor', 'report', 'bütçe'], icon: '📈', category: 'Genel Bakış' },
        { name: 'Ödeme Takvimi', url: '/payment_calendar', keywords: ['takvim', 'calendar', 'ödeme', 'payment', 'vade'], icon: '📅', category: 'Genel Bakış' },
        // Varlıklar & Analiz
        { name: 'Varlık Yönetimi', url: '/assets', keywords: ['varlık', 'asset', 'yatırım', 'portfolio', 'altın', 'döviz', 'hisse', 'fon'], icon: '💼', category: 'Varlıklar & Analiz' },
        { name: 'Yatırım Performansı', url: '/investment_performance', keywords: ['performans', 'getiri', 'roi', 'kar', 'zarar', 'investment'], icon: '🚀', category: 'Varlıklar & Analiz' },
        { name: 'Finansal Sağlık Analizi', url: '/analysis', keywords: ['analiz', 'sağlık', 'health', 'skor', 'kpi', 'risk'], icon: '🛡️', category: 'Varlıklar & Analiz' },
        // Strateji Merkezi
        { name: 'Finansal Özgürlük (FIRE)', url: '/financial_freedom', keywords: ['fire', 'özgürlük', 'freedom', 'emeklilik', 'hedef'], icon: '⚡', category: 'Strateji Merkezi' },
        { name: 'Strateji Paneli', url: '/strategy', keywords: ['strateji', 'strategy', 'senaryo', 'ai', 'öneri', 'simülasyon'], icon: '🧭', category: 'Strateji Merkezi' },
        { name: 'Piyasa Analizi', url: '/financial_dashboard', keywords: ['piyasa', 'market', 'borsa', 'bist', 'tefas', 'kur', 'enflasyon'], icon: '📉', category: 'Strateji Merkezi' },
        { name: 'Yatırım Günlüğü (Logbook)', url: '/logbook', keywords: ['günlük', 'logbook', 'not', 'karar', 'journal'], icon: '📓', category: 'Strateji Merkezi' },
        { name: 'Merkez Bankası Rezervleri', url: '/central-bank-reserves', keywords: ['merkez bankası', 'tcmb', 'rezerv', 'reserves', 'swap', 'altın rezerv'], icon: '🏦', category: 'Strateji Merkezi' },
        { name: 'Küresel Rasyolar', url: '/global-ratios', keywords: ['küresel', 'global', 'rasyo', 'ratio', 'altın gümüş', 'spx', 'makro'], icon: '🌍', category: 'Strateji Merkezi' },
        // Ayarlar & Kaynaklar
        { name: `${__t('nav_investor_profile')}`, url: '/profile', keywords: ['profil', 'profile', 'kullanıcı', 'user', 'yatırımcı', 'risk'], icon: '👤', category: `${__t('nav_settings')}` },
        { name: 'Bildirimler', url: '/notifications', keywords: ['bildirim', 'notification', 'uyarı', 'alarm', 'mesaj'], icon: '🔔', category: `${__t('nav_settings')}` },
        { name: 'Kategoriler', url: '/categories', keywords: ['kategori', 'category', 'sınıflandırma', 'etiket'], icon: '🏷️', category: `${__t('nav_settings')}` },
        { name: `${__t('nav_settings')}`, url: '/settings', keywords: ['ayar', 'settings', 'sistem', 'tercih', 'tema', 'para birimi'], icon: '⚙️', category: `${__t('nav_settings')}` },
        { name: 'Dil Ayarları', url: '/settings#language', keywords: ['dil', 'language', 'lang', 'türkçe', 'english', 'deutsch', 'italiano'], icon: '🌐', category: `${__t('nav_settings')}` },
        { name: 'Güvenlik Ayarları', url: '/settings#security', keywords: ['güvenlik', 'security', 'şifre', 'password', '2fa'], icon: '🔒', category: `${__t('nav_settings')}` },
        { name: 'Kullanıcı Rehberi', url: '/user_guide', keywords: ['rehber', 'guide', 'yardım', 'help', 'doküman', 'nasıl'], icon: '📖', category: 'Kaynaklar' },
        { name: `${__t('nav_financial_education')}`, url: '/financial_education', keywords: ['eğitim', 'education', 'öğren', 'kurs', 'akademi', 'quiz'], icon: '🎓', category: 'Kaynaklar' },
        { name: 'Sistem İzleme (Monitoring)', url: '/monitoring/', keywords: ['monitoring', 'izleme', 'sistem', 'sağlık', 'performans', 'log'], icon: '📡', category: 'Kaynaklar' },
        { name: 'Depolama Sağlığı (Storage Health)', url: '/storage-health/', keywords: ['depolama', 'storage', 'veritabanı', 'sqlite', 'yedek', 'backup'], icon: '💾', category: 'Kaynaklar' },
        { name: 'Yönetim Paneli (Admin)', url: '/admin/', keywords: ['admin', 'yönetim', 'kullanıcılar', 'yetki', 'tenant'], icon: '🛠️', category: 'Kaynaklar' },
    ];
    
    const filtered = searchItems.filter(item => {
        return item.name.toLowerCase().includes(lowerQuery) || 
               item.keywords.some(keyword => keyword.includes(lowerQuery));
    });
    
    if (filtered.length === 0) {
        resultsContainer.innerHTML = `
            <div class="text-center py-8">
                <div class="text-4xl mb-3">🔍</div>
                <div class="text-sm font-semibold text-slate-600 dark:text-slate-300">Sonuç bulunamadı</div>
                <div class="text-xs text-slate-400 dark:text-slate-500 mt-1">Başka bir arama terimi deneyin</div>
            </div>
        `;
        return;
    }
    
    let html = '<div class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Arama Sonuçları</div>';
    
    filtered.forEach(item => {
        const isQuickTx = item.action === 'quick-tx';
        const clickHandler = isQuickTx ? 'closeGlobalSearch(); openGlobalQuickTxModal(); return false;' : 'closeGlobalSearch()';
        const href = isQuickTx ? '#' : item.url;
        html += `
            <a href="${href}" onclick="${clickHandler}" class="search-result-item flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition mb-2 cursor-pointer">
                <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-800 dark:to-slate-700 flex items-center justify-center text-lg">
                    ${item.icon}
                </div>
                <div class="flex-1">
                    <div class="text-sm font-bold text-slate-800 dark:text-slate-100">${item.name}</div>
                    <div class="text-xs text-slate-500 dark:text-slate-400">${item.category}</div>
                </div>
                <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
            </a>
        `;
    });
    
    resultsContainer.innerHTML = html;
}

function closeGlobalSearch() {
    const paletteModal = document.getElementById('commandPaletteModal');
    if (paletteModal) {
        paletteModal.classList.remove('active');
        paletteModal.classList.add('hidden');
        paletteModal.style.display = '';
        paletteModal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    }
    searchSelectedIndex = -1;
    const modal = document.getElementById('globalSearchModal');
    if (modal) {
        modal.remove();
    }
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(e) {
    const quickActionsBtn = document.querySelector('.quick-actions-btn');
    const quickActionsPanel = document.getElementById('quickActionsPanel');
    const userDropdownBtn = document.querySelector('.user-dropdown-btn');
    const userDropdownPanel = document.getElementById('userDropdownPanel');
    
    if (quickActionsBtn && quickActionsPanel && !quickActionsBtn.contains(e.target) && !quickActionsPanel.contains(e.target)) {
        quickActionsPanel.classList.add('hidden');
    }
    
    if (userDropdownBtn && userDropdownPanel && !userDropdownBtn.contains(e.target) && !userDropdownPanel.contains(e.target)) {
        userDropdownPanel.classList.add('hidden');
    }
});

// Keyboard shortcuts: Global search (Ctrl+K), Rail toggle (Ctrl+B), Section jump (Alt+1..5), Escape peek dismiss
document.addEventListener('keydown', function(e) {
    const activeTag = document.activeElement ? document.activeElement.tagName : '';
    const isTyping = ['INPUT', 'TEXTAREA', 'SELECT'].includes(activeTag) || (document.activeElement && document.activeElement.isContentEditable);

    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        openGlobalSearch();
    } else if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'b') {
        if (!isTyping) {
            e.preventDefault();
            toggleSidebarRailMode();
        }
    } else if (e.key === 'Escape') {
        const modal = document.getElementById('globalSearchModal');
        if (modal) {
            e.preventDefault();
            closeGlobalSearch();
            return;
        }
        const sidebar = document.getElementById('desktopSidebar');
        if (sidebar && sidebar.classList.contains('rail-peek')) {
            e.preventDefault();
            sidebar.classList.remove('rail-peek');
        }
    } else if (e.altKey && !isTyping && ['1', '2', '3', '4', '5'].includes(e.key)) {
        const sectionMap = {
            '1': 'overview-section',
            '2': 'assets-section',
            '3': 'strategy-section',
            '4': 'settings-section',
            '5': 'resources-section'
        };
        const targetId = sectionMap[e.key];
        const sectionEl = document.getElementById(targetId);
        if (sectionEl) {
            e.preventDefault();
            const titleEl = document.querySelector(`.nav-section-title[data-target="${targetId}"]`);
            if (sectionEl.classList.contains('collapsed') && titleEl) {
                toggleSection(targetId, titleEl);
            }
            const firstLink = sectionEl.querySelector('.nav-link');
            if (firstLink) firstLink.focus();
        }
    }
});

// Live Ticker Auto-Refresh (Polling without page reload)
(function() {
    function pollLiveQuotes() {
        fetch('/api/live-quotes')
            .then(function(res) {
                if (!res.ok) throw new Error('Live quotes fetch failed: ' + res.status);
                return res.json();
            })
            .then(function(data) {
                if (!data || !data.success || !data.quotes) return;
                var q = data.quotes;
                var usdEl = document.getElementById('ticker-usd-val');
                var eurEl = document.getElementById('ticker-eur-val');
                var goldEl = document.getElementById('ticker-gold-val');
                var weatherEl = document.getElementById('ticker-weather-val');

                if (usdEl && q.usd && q.usd !== '--') usdEl.textContent = q.usd + ' ₺';
                if (eurEl && q.eur && q.eur !== '--') eurEl.textContent = q.eur + ' ₺';
                if (goldEl && q.gold && q.gold !== '--') goldEl.textContent = q.gold + ' ₺';
                if (weatherEl && q.weather && q.weather !== '--') weatherEl.textContent = q.weather;
            })
            .catch(function() { /* Silently fall back to existing displayed values */ });
    }
    // Initial fetch shortly after DOM load, then poll every 30 seconds
    setTimeout(pollLiveQuotes, 800);
    setInterval(pollLiveQuotes, 30000);
})();
