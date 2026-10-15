/**
 * Live Market Ticker Client Logic
 * Server-Sent Events (SSE) with graceful JSON polling fallback
 * Connects Database/Background Service to Frontend UI in real-time
 */
(function() {
    'use strict';

    let eventSource = null;
    let pollTimer = null;
    const POLL_INTERVAL_MS = 45000;

    function updateTickerElement(elementId, newValue, suffix) {
        const el = document.getElementById(elementId);
        if (!el || !newValue || newValue === '--') return;

        const formatted = suffix ? (newValue + ' ' + suffix) : newValue;
        if (el.textContent.trim() !== formatted.trim()) {
            el.textContent = formatted;
            // Visual pulse
            el.classList.add('transition-colors', 'duration-500', 'text-amber-500');
            setTimeout(function() {
                el.classList.remove('text-amber-500');
            }, 1000);
        }
    }

    function applyQuotes(quotes) {
        if (!quotes) return;
        if (quotes.usd) updateTickerElement('ticker-usd-val', quotes.usd, '₺');
        if (quotes.eur) updateTickerElement('ticker-eur-val', quotes.eur, '₺');
        if (quotes.gold) updateTickerElement('ticker-gold-val', quotes.gold, '₺');
        if (quotes.weather) updateTickerElement('ticker-weather-val', quotes.weather, '');

        // Stale / Offline badge toggle
        const staleBadge = document.getElementById('ticker-stale-badge');
        if (staleBadge) {
            if (quotes.is_stale) {
                staleBadge.classList.remove('hidden');
                staleBadge.classList.add('flex');
            } else {
                staleBadge.classList.remove('flex');
                staleBadge.classList.add('hidden');
            }
        }
    }

    function fetchPolling() {
        if (document.visibilityState === 'hidden') return;
        fetch('/api/live-quotes', {
            headers: { 'Accept': 'application/json' },
            cache: 'no-store'
        })
        .then(function(res) {
            if (!res.ok) throw new Error('Network error');
            return res.json();
        })
        .then(function(data) {
            if (data && data.success && data.quotes) {
                applyQuotes(data.quotes);
            }
        })
        .catch(function(err) {
            console.debug('Live ticker poll skipped:', err);
        });
    }

    function initSSE() {
        if (typeof window.EventSource === 'undefined') {
            startPolling();
            return;
        }

        try {
            eventSource = new EventSource('/api/live-stream');

            eventSource.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    applyQuotes(data);
                } catch (e) {
                    console.debug('SSE parse error:', e);
                }
            };

            eventSource.onerror = function() {
                // If stream breaks, close and fallback to polling
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                }
                startPolling();
            };
        } catch (e) {
            startPolling();
        }
    }

    function startPolling() {
        if (pollTimer) clearInterval(pollTimer);
        fetchPolling();
        pollTimer = setInterval(fetchPolling, POLL_INTERVAL_MS);
    }

    function stopLiveStream() {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    // Handle tab visibility to save background bandwidth
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'visible') {
            fetchPolling();
            if (!eventSource && !pollTimer) {
                initSSE();
            }
        } else {
            stopLiveStream();
        }
    });

    // Start on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSSE);
    } else {
        initSSE();
    }
})();
