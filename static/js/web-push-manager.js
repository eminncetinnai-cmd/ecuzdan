/**
 * E-Cüzdan Apple Web Push & Notification Manager
 * Handles W3C Web Notifications & Push Subscriptions for iOS 16.4+ / Android PWAs.
 */

(function () {
    'use strict';

    window.ECuzdanWebPush = {
        /**
         * Check if Notifications & Service Worker are supported
         */
        isSupported: function () {
            return ('Notification' in window) && ('serviceWorker' in navigator);
        },

        getPermissionState: function () {
            if (!('Notification' in window)) return 'unsupported';
            return Notification.permission;
        },

        /**
         * Request notification permission from user
         */
        requestPermission: async function () {
            if (!this.isSupported()) {
                if (window.showToast) {
                    window.showToast('Bu tarayıcı veya cihaz kilit ekranı bildirimlerini desteklemiyor.', 'warning');
                }
                return false;
            }

            try {
                const permission = await Notification.requestPermission();
                this.updateUI();

                if (permission === 'granted') {
                    if (window.ECuzdanHaptics) window.ECuzdanHaptics.success();
                    if (window.showToast) {
                        window.showToast('Kilit ekranı bildirimleri başarıyla aktifleştirildi!', 'success');
                    }
                    this.sendLocalNotification(
                        'E-Cüzdan Bildirimleri Aktif 🔔',
                        'Ödeme hatırlatıcıları ve kritik finansal uyarılar artık kilit ekranınıza iletilecek.',
                        '/'
                    );
                    return true;
                } else if (permission === 'denied') {
                    if (window.showToast) {
                        window.showToast('Bildirim izni reddedildi. iPhone Ayarlarından izin verebilirsiniz.', 'info');
                    }
                    return false;
                }
            } catch (err) {
                console.error('[WebPush] Permission request error:', err);
                return false;
            }
        },

        /**
         * Dispatch a local notification via the Service Worker
         */
        sendLocalNotification: async function (title, body, url) {
            if (!this.isSupported() || Notification.permission !== 'granted') {
                return;
            }

            try {
                const reg = await navigator.serviceWorker.ready;
                if (reg && reg.showNotification) {
                    await reg.showNotification(title, {
                        body: body,
                        icon: '/static/apple-touch-icon.png',
                        badge: '/static/favicon-32x32.png',
                        vibrate: [100, 50, 100],
                        data: { url: url || '/' }
                    });
                }
            } catch (err) {
                console.warn('[WebPush] Error showing notification:', err);
            }
        },

        /**
         * Trigger an immediate test notification
         */
        sendTestNotification: async function () {
            if (this.getPermissionState() !== 'granted') {
                const granted = await this.requestPermission();
                if (!granted) return;
            }

            await this.sendLocalNotification(
                'E-Cüzdan Kilit Ekranı Testi ⚡',
                'Tebrikler! Kilit ekranı bildirimleriniz kusursuz çalışıyor.',
                '/payment_calendar'
            );
            if (window.ECuzdanHaptics) window.ECuzdanHaptics.success();
            if (window.showToast) {
                window.showToast('Test bildirimi kilit ekranınıza gönderildi!', 'success');
            }
        },

        updateUI: function () {
            const btnRequest = document.getElementById('btnRequestPushPermission');
            const btnTest = document.getElementById('btnTestPushNotification');
            const badge = document.getElementById('pushPermissionBadge');
            const state = this.getPermissionState();

            if (badge) {
                if (state === 'granted') {
                    badge.textContent = 'İzin Verildi (Aktif) ✓';
                    badge.className = 'text-xs font-bold text-emerald-600 dark:text-emerald-400';
                } else if (state === 'denied') {
                    badge.textContent = 'Engellendi';
                    badge.className = 'text-xs font-bold text-rose-500';
                } else {
                    badge.textContent = 'İzin Bekleniyor';
                    badge.className = 'text-xs font-bold text-slate-400';
                }
            }

            if (btnRequest) {
                btnRequest.classList.toggle('hidden', state === 'granted');
            }
            if (btnTest) {
                btnTest.classList.toggle('hidden', state !== 'granted');
            }
        },

        init: function () {
            this.updateUI();
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => window.ECuzdanWebPush.init());
    } else {
        window.ECuzdanWebPush.init();
    }
})();
