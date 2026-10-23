/**
 * E-Cüzdan Service Worker (Armor PWA v2)
 * Provides instant app-shell startup, offline navigation fallback,
 * background push notifications, and high-speed asset caching.
 */

const CACHE_NAME = 'ecuzdan-pwa-v2';
const OFFLINE_URL = '/offline';

const PRECACHE_ASSETS = [
    '/',
    OFFLINE_URL,
    '/static/css/main.css',
    '/static/css/components.css',
    '/static/css/layout.css',
    '/static/css/design-tokens.css',
    '/static/js/layout-core.js',
    '/static/js/layout-shell.js',
    '/static/js/haptics.js',
    '/static/js/pull-to-refresh.js',
    '/static/js/biometrics.js',
    '/static/js/web-push-manager.js',
    '/static/js/offline-outbox.js',
    '/static/img/logo-icon.svg',
    '/static/apple-touch-icon.png',
    '/static/pwa-icon-192.png',
    '/static/pwa-icon-512.png',
    '/static/favicon.svg'
];

// 1. Install Event: Precache core assets & activate immediately
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(PRECACHE_ASSETS).catch((err) => {
                console.warn('[SW] Precache partial error (ignored during boot):', err);
            });
        }).then(() => self.skipWaiting())
    );
});

// 2. Activate Event: Clean up outdated caches & claim clients
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((name) => {
                    if (name !== CACHE_NAME) {
                        return caches.delete(name);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// 3. Fetch Event: Tailored strategy per request type
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Only handle HTTP/HTTPS GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Do NOT intercept API calls, Keep-Alive, or Auth actions
    if (url.pathname.startsWith('/api/') || 
        url.pathname.startsWith('/auth/') || 
        url.pathname.startsWith('/login') || 
        url.pathname.startsWith('/logout') ||
        url.pathname.startsWith('/healthz')) {
        return;
    }

    // A) Navigation requests (HTML pages)
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request)
                .then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        const copy = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
                    }
                    return networkResponse;
                })
                .catch(async () => {
                    // Try to serve cached version of this exact page
                    const cachedResponse = await caches.match(request);
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    // Fall back to offline page
                    return caches.match(OFFLINE_URL);
                })
        );
        return;
    }

    // B) Static Assets (CSS, JS, Fonts, Images)
    if (url.pathname.startsWith('/static/') || url.hostname.includes('fonts.g')) {
        event.respondWith(
            caches.match(request).then((cachedResponse) => {
                const fetchPromise = fetch(request).then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        const copy = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
                    }
                    return networkResponse;
                }).catch(() => null);

                // Stale-While-Revalidate
                return cachedResponse || fetchPromise;
            })
        );
        return;
    }
});

// 4. Push Event: Handle background push messages
self.addEventListener('push', function (event) {
    let payload = {
        title: 'E-Cüzdan Finansal Kasa',
        body: 'Yeni bir finansal bildiriminiz var.',
        url: '/'
    };

    if (event.data) {
        try {
            payload = event.data.json();
        } catch (e) {
            payload.body = event.data.text();
        }
    }

    const options = {
        body: payload.body,
        icon: '/static/apple-touch-icon.png',
        badge: '/static/favicon-32x32.png',
        vibrate: [100, 50, 100],
        data: { url: payload.url || '/' }
    };

    event.waitUntil(self.registration.showNotification(payload.title, options));
});

// 5. Notification Click Event: Focus existing window or open target
self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    const targetUrl = (event.notification.data && event.notification.data.url) ? event.notification.data.url : '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (clientList) {
            for (let client of clientList) {
                if (client.url.includes(targetUrl) && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});
