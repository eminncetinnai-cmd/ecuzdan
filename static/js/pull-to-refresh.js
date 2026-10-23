/**
 * E-Cüzdan Mobile Pull-to-Refresh Component
 * Provides native iOS elastic pull-down gesture to refresh live market rates & portfolio.
 */

(function () {
    'use strict';

    let startY = 0;
    let currentY = 0;
    let isPulling = false;
    let isRefreshing = false;
    const PULL_THRESHOLD = 70;
    const MAX_PULL = 110;
    const RESISTANCE = 0.42;

    let indicatorEl = null;

    function createIndicator() {
        if (indicatorEl) return indicatorEl;

        indicatorEl = document.createElement('div');
        indicatorEl.id = 'ecuzdanPullToRefresh';
        indicatorEl.className = 'fixed top-0 left-0 right-0 z-50 flex items-center justify-center pointer-events-none transition-transform duration-200';
        indicatorEl.style.transform = 'translateY(-100%)';

        indicatorEl.innerHTML = `
            <div class="mt-2 px-4 py-2 rounded-full bg-slate-900/95 dark:bg-slate-800/95 border border-slate-700/60 shadow-xl backdrop-blur flex items-center gap-2.5 text-white">
                <svg id="ptrIcon" class="w-4 h-4 text-sky-400 transition-transform duration-200" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3"/>
                </svg>
                <span id="ptrText" class="text-xs font-bold tracking-tight">Canlı Piyasaları Güncelle</span>
            </div>
        `;

        document.body.appendChild(indicatorEl);
        return indicatorEl;
    }

    function initPullToRefresh() {
        // Only activate on touch devices / mobile viewports
        if (!('ontouchstart' in window) && window.innerWidth > 1024) {
            return;
        }

        createIndicator();

        window.addEventListener('touchstart', function (e) {
            if (window.scrollY === 0 && !isRefreshing) {
                startY = e.touches[0].pageY;
                isPulling = true;
            }
        }, { passive: true });

        window.addEventListener('touchmove', function (e) {
            if (!isPulling || isRefreshing) return;

            currentY = e.touches[0].pageY;
            const diff = currentY - startY;

            if (diff > 0 && window.scrollY === 0) {
                const pullDistance = Math.min(diff * RESISTANCE, MAX_PULL);
                const progress = Math.min(pullDistance / PULL_THRESHOLD, 1);

                indicatorEl.style.transform = `translateY(${pullDistance - 50}px)`;

                const icon = document.getElementById('ptrIcon');
                const text = document.getElementById('ptrText');

                if (pullDistance >= PULL_THRESHOLD) {
                    if (icon) icon.style.transform = 'rotate(180deg)';
                    if (text) text.textContent = 'Bırak ve Yenile';
                    if (window.ECuzdanHaptics && !indicatorEl.dataset.hapticTriggered) {
                        window.ECuzdanHaptics.medium();
                        indicatorEl.dataset.hapticTriggered = 'true';
                    }
                } else {
                    if (icon) icon.style.transform = `rotate(${progress * 180}deg)`;
                    if (text) text.textContent = 'Aşağı Çek';
                    delete indicatorEl.dataset.hapticTriggered;
                }
            }
        }, { passive: true });

        window.addEventListener('touchend', function () {
            if (!isPulling || isRefreshing) return;
            isPulling = false;

            const diff = currentY - startY;
            const pullDistance = Math.min(diff * RESISTANCE, MAX_PULL);

            if (pullDistance >= PULL_THRESHOLD && window.scrollY === 0) {
                triggerRefresh();
            } else {
                resetIndicator();
            }
        }, { passive: true });
    }

    function triggerRefresh() {
        isRefreshing = true;
        indicatorEl.style.transform = 'translateY(16px)';

        const icon = document.getElementById('ptrIcon');
        const text = document.getElementById('ptrText');

        if (icon) {
            icon.classList.add('animate-spin');
            icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>';
        }
        if (text) text.textContent = 'Güncelleniyor...';

        // 1. Refresh live quotes (SSE/Polling)
        let refreshPromise;
        if (typeof window.refreshLiveQuotes === 'function') {
            refreshPromise = window.refreshLiveQuotes();
        } else {
            refreshPromise = fetch('/api/live-quotes', { cache: 'no-store' });
        }

        // Minimum 600ms visual duration for smooth feedback
        Promise.all([
            Promise.resolve(refreshPromise),
            new Promise((r) => setTimeout(r, 650))
        ])
        .then(() => {
            if (window.ECuzdanHaptics) {
                window.ECuzdanHaptics.success();
            }
            if (icon) icon.classList.remove('animate-spin');
            if (text) text.textContent = 'Güncellendi ✓';
            setTimeout(resetIndicator, 600);
        })
        .catch(() => {
            if (window.ECuzdanHaptics) {
                window.ECuzdanHaptics.error();
            }
            if (icon) icon.classList.remove('animate-spin');
            if (text) text.textContent = 'Bağlantı Hatası';
            setTimeout(resetIndicator, 800);
        });
    }

    function resetIndicator() {
        if (!indicatorEl) return;
        indicatorEl.style.transform = 'translateY(-100%)';
        delete indicatorEl.dataset.hapticTriggered;
        setTimeout(() => {
            isRefreshing = false;
            const icon = document.getElementById('ptrIcon');
            const text = document.getElementById('ptrText');
            if (icon) {
                icon.style.transform = 'rotate(0deg)';
                icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3"/>';
            }
            if (text) text.textContent = 'Canlı Piyasaları Güncelle';
        }, 220);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPullToRefresh);
    } else {
        initPullToRefresh();
    }
})();
