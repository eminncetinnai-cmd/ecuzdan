/**
 * E-Cüzdan Mobile Row Swipe-to-Action
 * iOS-style swipe left to Delete, swipe right to Mark as Paid with haptics.
 */

(function () {
    'use strict';

    let activeRow = null;
    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let isSwiping = false;
    let isHorizontal = null;
    const SWIPE_THRESHOLD = 75;
    const MAX_DRAG = 110;

    function onTouchStart(e) {
        const row = e.target.closest('.tx-row, [data-swipe-row]');
        if (!row || e.target.closest('button, input, select, a')) return;

        activeRow = row;
        startX = e.touches[0].pageX;
        startY = e.touches[0].pageY;
        currentX = startX;
        isSwiping = true;
        isHorizontal = null;

        activeRow.style.transition = 'none';
        activeRow.style.position = 'relative';
    }

    function onTouchMove(e) {
        if (!isSwiping || !activeRow) return;

        const touchX = e.touches[0].pageX;
        const touchY = e.touches[0].pageY;
        const diffX = touchX - startX;
        const diffY = touchY - startY;

        // Determine scroll vs swipe on initial movement
        if (isHorizontal === null) {
            if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 8) {
                isHorizontal = true;
            } else if (Math.abs(diffY) > 8) {
                isHorizontal = false;
            }
        }

        if (!isHorizontal) return;

        currentX = touchX;
        // Clamp and dampen movement
        const clampedDiff = Math.max(-MAX_DRAG, Math.min(MAX_DRAG, diffX * 0.7));
        activeRow.style.transform = `translateX(${clampedDiff}px)`;

        // Visual feedback based on swipe direction
        if (clampedDiff < -SWIPE_THRESHOLD) {
            activeRow.classList.add('bg-rose-50/70', 'dark:bg-rose-950/30');
            activeRow.classList.remove('bg-emerald-50/70', 'dark:bg-emerald-950/30');
        } else if (clampedDiff > SWIPE_THRESHOLD) {
            activeRow.classList.add('bg-emerald-50/70', 'dark:bg-emerald-950/30');
            activeRow.classList.remove('bg-rose-50/70', 'dark:bg-rose-950/30');
        } else {
            activeRow.classList.remove('bg-rose-50/70', 'dark:bg-rose-950/30', 'bg-emerald-50/70', 'dark:bg-emerald-950/30');
        }
    }

    function onTouchEnd() {
        if (!isSwiping || !activeRow) return;

        const diffX = currentX - startX;
        activeRow.style.transition = 'transform 0.25s cubic-bezier(0.2, 0.8, 0.2, 1), background-color 0.25s ease';

        if (isHorizontal && diffX < -SWIPE_THRESHOLD) {
            // Swipe LEFT -> Trigger Delete
            if (window.ECuzdanHaptics) window.ECuzdanHaptics.heavy();
            const deleteBtn = activeRow.querySelector('.delete-tx-btn');
            if (deleteBtn) {
                deleteBtn.click();
            }
        } else if (isHorizontal && diffX > SWIPE_THRESHOLD) {
            // Swipe RIGHT -> Trigger Quick-Pay / Mark Paid
            const quickPayBtn = activeRow.querySelector('.quick-pay-tx-btn');
            if (quickPayBtn) {
                if (window.ECuzdanHaptics) window.ECuzdanHaptics.success();
                quickPayBtn.click();
            } else if (window.showToast) {
                window.showToast('Bu işlem zaten ödendi olarak kayıtlı.', 'info');
            }
        }

        // Reset row position
        activeRow.style.transform = 'translateX(0px)';
        activeRow.classList.remove('bg-rose-50/70', 'dark:bg-rose-950/30', 'bg-emerald-50/70', 'dark:bg-emerald-950/30');

        isSwiping = false;
        activeRow = null;
        isHorizontal = null;
    }

    function initSwipeActions() {
        if (!('ontouchstart' in window) && window.innerWidth > 1024) return;

        document.addEventListener('touchstart', onTouchStart, { passive: true });
        document.addEventListener('touchmove', onTouchMove, { passive: true });
        document.addEventListener('touchend', onTouchEnd, { passive: true });
        document.addEventListener('touchcancel', onTouchEnd, { passive: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSwipeActions);
    } else {
        initSwipeActions();
    }
})();
