/**
 * E-Cüzdan Offline Outbox & Sync Manager
 * Manages offline transaction queuing and seamless background synchronization.
 */

(function () {
    'use strict';

    const QUEUE_STORAGE_KEY = 'ecuzdan_offline_tx_queue';

    window.ECuzdanOffline = {
        /**
         * Get all pending transactions from local storage
         * @returns {Array<Object>}
         */
        getQueue: function () {
            try {
                const raw = localStorage.getItem(QUEUE_STORAGE_KEY);
                return raw ? JSON.parse(raw) : [];
            } catch (e) {
                console.error('[OfflineOutbox] Error reading queue:', e);
                return [];
            }
        },

        /**
         * Save pending transactions to local storage
         * @param {Array<Object>} queue
         */
        saveQueue: function (queue) {
            try {
                localStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(queue));
                this.updateUIBadge();
            } catch (e) {
                console.error('[OfflineOutbox] Error saving queue:', e);
            }
        },

        /**
         * Add a new transaction payload to the offline outbox
         * @param {FormData|Object} data
         * @returns {Object} Queued item
         */
        enqueue: function (data) {
            const queue = this.getQueue();
            const item = {
                id: 'offline_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5),
                timestamp: new Date().toISOString(),
                payload: data instanceof FormData ? Object.fromEntries(data.entries()) : data
            };
            queue.push(item);
            this.saveQueue(queue);

            if (window.showToast) {
                const count = queue.length;
                window.showToast(
                    'İşlem çevrimdışı kaydedildi. İnternet bağlantısı geldiğinde otomatik aktarılacak (' + count + ' bekleyen).',
                    'info'
                );
            }
            return item;
        },

        /**
         * Replay all pending offline transactions to the server
         */
        sync: async function () {
            if (!navigator.onLine) {
                return;
            }

            const queue = this.getQueue();
            if (queue.length === 0) {
                return;
            }

            console.log('[OfflineOutbox] Syncing ' + queue.length + ' pending items...');
            const remaining = [];
            let syncedCount = 0;

            // Get CSRF token
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
            const targetUrl = (window.ECuzdanEndpoints && window.ECuzdanEndpoints.transactions) ?
                window.ECuzdanEndpoints.transactions.create : '/transactions/create';

            for (const item of queue) {
                try {
                    const formData = new FormData();
                    formData.append('csrf_token', csrfToken);
                    Object.keys(item.payload).forEach((key) => {
                        if (key !== 'csrf_token') {
                            formData.append(key, item.payload[key]);
                        }
                    });

                    const res = await fetch(targetUrl, {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'Accept': 'application/json'
                        },
                        body: formData
                    });

                    if (res.ok) {
                        const json = await res.json();
                        if (json.success) {
                            syncedCount++;
                        } else {
                            // If business validation failed, keep it or alert
                            console.warn('[OfflineOutbox] Item rejected by server:', json.message);
                        }
                    } else {
                        // Server error, keep in queue
                        remaining.push(item);
                    }
                } catch (err) {
                    console.error('[OfflineOutbox] Network error during sync item:', err);
                    remaining.push(item);
                }
            }

            this.saveQueue(remaining);

            if (syncedCount > 0 && window.showToast) {
                window.showToast(
                    syncedCount + ' adet çevrimdışı işlem sunucuya başarıyla aktarıldı!',
                    'success'
                );
                // If on transactions or dashboard page, reload after 1 second to display new records
                if (window.location.pathname === '/' || window.location.pathname.startsWith('/transactions')) {
                    setTimeout(() => window.location.reload(), 1200);
                }
            }
        },

        /**
         * Update visual offline banner & pending queue badge
         */
        updateUIBadge: function () {
            const queue = this.getQueue();
            const badge = document.getElementById('offlineOutboxBadge');
            const banner = document.getElementById('offlineStatusBar');

            if (banner) {
                if (!navigator.onLine) {
                    banner.classList.remove('hidden');
                } else {
                    banner.classList.add('hidden');
                }
            }

            if (badge) {
                if (queue.length > 0) {
                    badge.classList.remove('hidden');
                    badge.textContent = queue.length.toString();
                    badge.title = queue.length + ' bekleyen çevrimdışı işlem';
                } else {
                    badge.classList.add('hidden');
                }
            }
        },

        /**
         * Initialize event listeners
         */
        init: function () {
            window.addEventListener('online', () => {
                this.updateUIBadge();
                if (window.showToast) {
                    window.showToast('İnternet bağlantısı yeniden kuruldu. Eşitleniyor...', 'info');
                }
                this.sync();
            });

            window.addEventListener('offline', () => {
                this.updateUIBadge();
                if (window.showToast) {
                    window.showToast('Çevrimdışı moddasınız. İşlemleriniz yerel olarak saklanacak.', 'warning');
                }
            });

            // Initial state check
            this.updateUIBadge();

            // Try sync if online on boot
            if (navigator.onLine && this.getQueue().length > 0) {
                setTimeout(() => this.sync(), 2500);
            }
        }
    };

    // Auto-init on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => window.ECuzdanOffline.init());
    } else {
        window.ECuzdanOffline.init();
    }
})();
