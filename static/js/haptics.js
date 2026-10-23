/**
 * E-Cüzdan Native Haptics Engine
 * Provides tactile vibration feedback for iOS/Android mobile devices.
 */

(function () {
    'use strict';

    window.ECuzdanHaptics = {
        /**
         * Check if vibration is supported on this browser/device
         */
        isSupported: function () {
            return typeof navigator !== 'undefined' && 'vibrate' in navigator;
        },

        /**
         * Ultra-light click tick (10ms)
         */
        light: function () {
            if (this.isSupported()) {
                try { navigator.vibrate(12); } catch (e) {}
            }
        },

        /**
         * Crisp medium tap (25ms)
         */
        medium: function () {
            if (this.isSupported()) {
                try { navigator.vibrate(25); } catch (e) {}
            }
        },

        /**
         * Heavy affirmative tap (45ms)
         */
        heavy: function () {
            if (this.isSupported()) {
                try { navigator.vibrate(45); } catch (e) {}
            }
        },

        /**
         * Double-pulse success signature
         */
        success: function () {
            if (this.isSupported()) {
                try { navigator.vibrate([15, 40, 25]); } catch (e) {}
            }
        },

        /**
         * Staccato warning pattern
         */
        warning: function () {
            if (this.isSupported()) {
                try { navigator.vibrate([30, 40, 30]); } catch (e) {}
            }
        },

        /**
         * Triple alert error signature
         */
        error: function () {
            if (this.isSupported()) {
                try { navigator.vibrate([40, 50, 40, 50, 60]); } catch (e) {}
            }
        }
    };

    // Auto-hook into document interactions
    document.addEventListener('DOMContentLoaded', function () {
        // 1. Delegated listener for navigation and buttons
        document.addEventListener('click', function (e) {
            var target = e.target;
            var button = target.closest(
                'button, [role="button"], a.mobile-bottom-nav, .mobile-bottom-nav button, .modal-submit, .btn-action'
            );
            if (!button) return;

            var hapticType = button.getAttribute('data-haptic');
            if (hapticType === 'medium') {
                ECuzdanHaptics.medium();
            } else if (hapticType === 'heavy') {
                ECuzdanHaptics.heavy();
            } else if (hapticType === 'success') {
                ECuzdanHaptics.success();
            } else if (hapticType === 'none') {
                // explicit skip
            } else {
                ECuzdanHaptics.light();
            }
        }, { passive: true });

        // 2. Intercept window.showToast for automatic haptic accompaniment
        if (typeof window.showToast === 'function') {
            var originalShowToast = window.showToast;
            window.showToast = function (message, type) {
                if (type === 'success') {
                    ECuzdanHaptics.success();
                } else if (type === 'error' || type === 'danger') {
                    ECuzdanHaptics.error();
                } else if (type === 'warning') {
                    ECuzdanHaptics.warning();
                } else {
                    ECuzdanHaptics.light();
                }
                return originalShowToast.apply(this, arguments);
            };
        }
    });
})();
