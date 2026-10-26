/* E-CUZDAN frontend API contract layer. */
(function installEcuzdanApi(global) {
    'use strict';

    const encodeId = value => encodeURIComponent(String(value));
    const withId = (template, value) => template.replace(':id', encodeId(value));

    const endpoints = Object.freeze({
        assets: Object.freeze({
            delete: id => withId('/delete_asset/:id', id),
            edit: id => withId('/edit_asset/:id', id),
            new: '/new_asset',
            sell: id => withId('/sell_asset/:id', id),
            update: '/update_asset',
            summary: '/api/portfolio/summary',
            list: '/api/portfolio/assets',
        }),
        market: Object.freeze({
            quotes: '/api/live-quotes',
            stream: '/api/live-stream',
        }),
        categories: Object.freeze({
            delete: id => withId('/delete_category/:id', id),
            deleteAssetSector: id => withId('/delete_asset_sector/:id', id),
            deleteAssetType: id => withId('/delete_asset_type/:id', id),
            update: id => withId('/update_category/:id', id),
        }),
        education: Object.freeze({
            achievements: '/api/achievements',
            progress: '/api/progress',
            progressUpdate: '/api/progress/update',
            quizHistory: '/api/quiz/history',
            quizStart: '/api/quiz/start',
            quizSubmit: '/api/quiz/submit',
        }),
        logbook: Object.freeze({
            assets: '/logbook/api/assets',
            calendarEvents: '/logbook/api/calendar-events',
            delete: id => withId('/logbook/:id/delete', id),
            entries: '/logbook/api/entries',
            timeline: '/logbook/timeline',
            transactions: '/logbook/api/transactions',
        }),
        monitoring: Object.freeze({
            alertsConfig: '/monitoring/api/alerts/config',
            alertsStatus: '/monitoring/api/alerts/status',
            health: '/monitoring/api/health',
            logs: '/monitoring/api/logs',
            logsArchive: '/monitoring/api/logs/archive',
            logsStream: '/monitoring/api/logs/stream',
            logsTimeline: '/monitoring/api/logs/timeline',
            logsUpload: '/monitoring/api/logs/upload',
            stats: '/monitoring/api/stats',
            summary: '/monitoring/api/summary',
        }),
        notifications: Object.freeze({
            all: '/notifications/api',
            delete: id => withId('/notifications/:id/delete', id),
            deleteRead: '/notifications/delete_read',
            markAllRead: '/notifications/read_all',
            markRead: id => withId('/notifications/:id/read', id),
            unreadCount: '/notifications/unread_count',
        }),
        plans: Object.freeze({
            addPayment: '/add_payment',
            detail: id => withId('/api/plans/:id', id),
            occurrences: id => withId('/api/plans/:id/occurrences', id),
            occurrencePay: id => withId('/api/occurrences/:id/pay', id),
            occurrenceSkip: id => withId('/api/occurrences/:id/skip', id),
            occurrenceCancel: id => withId('/api/occurrences/:id/cancel', id),
            setStatus: id => withId('/plans/:id/status', id),
            checkDelete: id => withId('/:id/check-delete', id),
            delete: id => withId('/:id/delete', id),
            list: '/plans',
            paymentCalendar: '/payment_calendar',
            paymentCalendarDailyBalance: '/payment_calendar/daily_balance',
            paymentCalendarMonthData: '/payment_calendar/month_data',
        }),
        profile: Object.freeze({
            history: '/profile/api/history',
            questions: '/profile/api/questions',
            submit: '/profile/api/submit',
        }),
        reconciliation: Object.freeze({
            summary: '/api/reconciliation',
            accounts: '/api/reconciliation/accounts',
            statements: '/api/reconciliation/statements',
        }),
        settings: Object.freeze({
            dbHealth: '/storage-health/api/db-health',
            language: lang => `/set_language/${encodeURIComponent(String(lang))}`,
            privacy: '/toggle_privacy_mode',
            theme: '/save_theme_preference',
            tuneUp: '/storage-health/api/tune-up',
        }),
        storageHealth: Object.freeze({
            cleanup: '/storage-health/api/cleanup',
            dbHealth: '/storage-health/api/db-health',
            history: '/storage-health/api/history',
            overview: '/storage-health/api/overview',
            tuneUp: '/storage-health/api/tune-up',
        }),
        strategy: Object.freeze({
            scenarios: '/strategy/api/mc-scenarios',
            settings: '/strategy/settings',
        }),
        transactions: Object.freeze({
            create: '/new_transaction',
            delete: id => withId('/delete_t/:id', id),
            detail: id => withId('/api/transactions/:id', id),
            edit: id => withId('/edit_t/:id', id),
            explorer: '/api/transactions',
            reconciliation: '/api/transactions/reconciliation',
            lineage: id => withId('/api/transactions/:id/lineage', id),
            adjust: id => withId('/api/transactions/:id/adjustments', id),
            adjustments: id => withId('/api/transactions/:id/adjustments', id),
            reverse: id => withId('/api/transactions/:id/reversal', id),
            reversal: id => withId('/api/transactions/:id/reversal', id),
            adjustmentAudit: id => withId('/api/ledger-adjustments/:id/audit', id),
            quickPay: id => withId('/transactions/:id/quick-pay', id),
        }),
    });

    function csrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
            || document.querySelector('input[name="csrf_token"]')?.value
            || '';
    }

    function assertRecord(name, value) {
        if (!value || typeof value !== 'object' || Array.isArray(value)) {
            throw new TypeError(`${name} response must be an object`);
        }
        return value;
    }

    function assertArrayField(name, payload, field) {
        assertRecord(name, payload);
        if (!Array.isArray(payload[field])) {
            throw new TypeError(`${name}.${field} must be an array`);
        }
        return payload;
    }



    function assertMonitoringResponse(name, payload, requiredFields = []) {
        assertRecord(name, payload);
        if (payload.success !== true) {
            throw new TypeError(`${name} response was not successful`);
        }
        assertRecord(`${name}.data`, payload.data);
        requiredFields.forEach(field => {
            if (!(field in payload.data)) {
                throw new TypeError(`${name}.data.${field} is required`);
            }
        });
        return payload.data;
    }

    const dto = Object.freeze({
        monitoringAlertsStatus: payload => assertMonitoringResponse('monitoringAlertsStatus', payload, ['enabled']),
        monitoringHealth: payload => assertMonitoringResponse('monitoringHealth', payload, ['status', 'components', 'issues']),
        monitoringLogs: payload => {
            const data = assertMonitoringResponse('monitoringLogs', payload, ['entries', 'logs', 'count', 'file']);
            if (!Array.isArray(data.entries) || !Array.isArray(data.logs)) {
                throw new TypeError('monitoringLogs.data.entries and logs must be arrays');
            }
            return data;
        },
        monitoringStats: payload => assertMonitoringResponse('monitoringStats', payload, [
            'total_logs', 'error_count', 'warning_count', 'critical_count',
            'security_count', 'log_files', 'recent_errors',
        ]),
        monitoringTimeline: payload => {
            const data = assertMonitoringResponse('monitoringTimeline', payload, ['points']);
            if (!Array.isArray(data.points)) throw new TypeError('monitoringTimeline.data.points must be an array');
            return data;
        },
        monitoringUpload: payload => assertMonitoringResponse('monitoringUpload', payload, ['entries', 'logs', 'count']),
        monitoringSummary: payload => assertMonitoringResponse('monitoringSummary', payload, ['health', 'stats', 'quick_metrics']),
        achievements: payload => assertArrayField('achievements', payload, 'achievements'),
        notifications: payload => assertArrayField('notifications', payload, 'items'),
        planDetail: payload => {
            assertRecord('planDetail', payload);
            if (payload.success !== true) throw new TypeError('planDetail response was not successful');
            assertRecord('planDetail.data', payload.data);
            ['plan', 'summary'].forEach(field => {
                if (!(field in payload.data)) throw new TypeError(`planDetail.data.${field} is required`);
            });
            assertRecord('planDetail.data.plan', payload.data.plan);
            assertRecord('planDetail.data.summary', payload.data.summary);
            return payload.data;
        },
        profileQuestions: payload => assertArrayField('profileQuestions', payload, 'questions'),
        standard: (payload, name = 'api') => assertRecord(name, payload),
        transactions: payload => {
            assertArrayField('transactions', payload, 'transactions');
            assertRecord('transactions.summary', payload.summary);
            if (typeof payload.has_more !== 'boolean') {
                throw new TypeError('transactions.has_more must be a boolean');
            }
            if ('success' in payload && payload.success !== true) {
                throw new TypeError('transactions response was not successful');
            }
            ['total_count', 'total_amount', 'total_income', 'total_expense', 'total_net', 'total_pending']
                .forEach(field => {
                    if (field in payload.summary && payload.summary[field] !== null
                        && typeof payload.summary[field] !== 'string'
                        && typeof payload.summary[field] !== 'number') {
                        throw new TypeError(`transactions.summary.${field} must be a number, string or null`);
                    }
                });
            if ('pagination' in payload) {
                assertRecord('transactions.pagination', payload.pagination);
                ['page', 'per_page', 'total', 'has_next'].forEach(field => {
                    if (!(field in payload.pagination)) throw new TypeError(`transactions.pagination.${field} is required`);
                });
                if (!Number.isInteger(payload.pagination.page) || !Number.isInteger(payload.pagination.per_page)
                    || !Number.isInteger(payload.pagination.total) || typeof payload.pagination.has_next !== 'boolean') {
                    throw new TypeError('transactions.pagination type contract is invalid');
                }
            }
            if ('filters' in payload) assertRecord('transactions.filters', payload.filters);
            if ('accounts' in payload && !Array.isArray(payload.accounts)) {
                throw new TypeError('transactions.accounts must be an array');
            }
            return payload;
        },
        reconciliation: payload => {
            assertRecord('reconciliation', payload);
            if (payload.success !== true) {
                throw new TypeError('reconciliation response was not successful');
            }
            [
                'as_of', 'status_code', 'book_balance', 'cleared_balance',
                'pending_net', 'statement_balance', 'difference', 'reconciled',
                'pending_count', 'pending_summary', 'pending_items', 'issues',
                'recommendations', 'accounts', 'scope', 'currency',
            ].forEach(field => {
                if (!(field in payload)) {
                    throw new TypeError(`reconciliation.${field} is required`);
                }
            });
            if (!Array.isArray(payload.accounts) || !Array.isArray(payload.pending_items)
                || !Array.isArray(payload.issues) || !Array.isArray(payload.recommendations)) {
                throw new TypeError('reconciliation detail fields must be arrays');
            }
            assertRecord('reconciliation.pending_summary', payload.pending_summary);
            return payload;
        },
        transactionsReconciliation: payload => {
            assertRecord('transactionsReconciliation', payload);
            if (payload.success !== true) {
                throw new TypeError('transactionsReconciliation response was not successful');
            }
            [
                'as_of', 'status_code', 'book_balance', 'cleared_balance',
                'pending_net', 'statement_balance', 'difference', 'reconciled',
                'pending_count', 'pending_summary', 'pending_items', 'issues',
                'recommendations',
            ].forEach(field => {
                if (!(field in payload)) {
                    throw new TypeError(`transactionsReconciliation.${field} is required`);
                }
            });
            if (!Array.isArray(payload.pending_items) || !Array.isArray(payload.issues) || !Array.isArray(payload.recommendations)) {
                throw new TypeError('transactionsReconciliation detail fields must be arrays');
            }
            assertRecord('transactionsReconciliation.pending_summary', payload.pending_summary);
            return payload;
        },
    });

    function notifyConnectionError(message) {
        const msg = message || 'Bağlantı hatası: Lütfen internet bağlantınızı kontrol edin.';
        if (typeof window !== 'undefined' && typeof window.showToast === 'function') {
            window.showToast(msg, 'error');
        } else if (typeof document !== 'undefined') {
            const container = document.getElementById('toast-container');
            if (container) {
                const toast = document.createElement('div');
                toast.className = 'toast-item bg-rose-600 text-white px-6 py-4 rounded-2xl shadow-2xl flex items-center gap-3';
                toast.textContent = msg;
                container.appendChild(toast);
                setTimeout(() => toast.remove(), 4000);
            }
        }
        if (typeof window !== 'undefined' && typeof window.dispatchEvent === 'function') {
            try {
                window.dispatchEvent(new CustomEvent('ecuzdan:network-error', { detail: { message: msg } }));
            } catch (e) {
                // Ignore CustomEvent errors in older environments
            }
        }
    }

    function unlockLoadingButtons() {
        if (typeof document === 'undefined') return;

        // Unlock buttons that were disabled or put in loading state
        const buttons = document.querySelectorAll('button:disabled, input[type="submit"]:disabled, [data-loading="true"], .btn-loading, .is-loading');
        buttons.forEach(btn => {
            if (btn.dataset.originalText) {
                if ('value' in btn && btn.type === 'submit') {
                    btn.value = btn.dataset.originalText;
                } else {
                    btn.textContent = btn.dataset.originalText;
                }
                delete btn.dataset.originalText;
            } else if (btn.textContent && btn.textContent.includes('Yükleniyor')) {
                btn.textContent = btn.dataset.defaultText || 'Kaydet';
            }
            btn.disabled = false;
            btn.removeAttribute('data-loading');
            btn.classList.remove('opacity-50', 'btn-loading', 'is-loading', 'pointer-events-none');
        });

        // Also re-enable forms if ECuzdanForms exists
        if (typeof window !== 'undefined' && window.ECuzdanForms && typeof window.ECuzdanForms.enableForm === 'function') {
            document.querySelectorAll('form').forEach(form => {
                if (form.id) {
                    window.ECuzdanForms.enableForm(form.id);
                }
            });
        }

        if (typeof window !== 'undefined' && typeof window.dispatchEvent === 'function') {
            try {
                window.dispatchEvent(new CustomEvent('ecuzdan:buttons-unlocked'));
            } catch (e) {}
        }
    }

    if (typeof window !== 'undefined') {
        window.addEventListener('offline', () => {
            notifyConnectionError('İnternet bağlantısı kesildi. Çevrimdışı moddasınız.');
            unlockLoadingButtons();
        });

        window.addEventListener('online', () => {
            if (typeof window.showToast === 'function') {
                window.showToast('İnternet bağlantısı yeniden sağlandı.', 'success');
            }
        });

        if (typeof document !== 'undefined') {
            document.addEventListener('submit', (e) => {
                const target = e.target;
                if (target && target.querySelector) {
                    const submitBtn = target.querySelector('button[type="submit"], input[type="submit"]');
                    if (submitBtn && !submitBtn.dataset.originalText) {
                        submitBtn.dataset.originalText = submitBtn.textContent || submitBtn.value || '';
                    }
                }
            }, true);
        }
    }

    async function request(path, options = {}) {
        if (typeof navigator !== 'undefined' && navigator.onLine === false) {
            unlockLoadingButtons();
            notifyConnectionError('Bağlantı hatası: İnternet bağlantınız bulunmuyor.');
            const offlineError = new Error('Bağlantı hatası: İnternet bağlantınız bulunmuyor.');
            offlineError.isNetworkError = true;
            offlineError.status = 0;
            throw offlineError;
        }

        const method = String(options.method || 'GET').toUpperCase();
        const headers = new Headers(options.headers || {});
        headers.set('Accept', headers.get('Accept') || 'application/json');
        if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
            const token = csrfToken();
            if (token && !headers.has('X-CSRF-Token')) headers.set('X-CSRF-Token', token);
        }

        let response;
        try {
            response = await fetch(path, {
                ...options,
                credentials: options.credentials || 'same-origin',
                headers,
                method,
            });
        } catch (fetchErr) {
            unlockLoadingButtons();
            notifyConnectionError('Bağlantı hatası: Sunucuya erişilemiyor. Lütfen internet bağlantınızı kontrol edin.');
            const networkError = new Error('Bağlantı hatası: Sunucuya erişilemiyor. Lütfen internet bağlantınızı kontrol edin.');
            networkError.isNetworkError = true;
            networkError.originalError = fetchErr;
            networkError.status = 0;
            throw networkError;
        }

        const contentType = response.headers.get('content-type') || '';
        const payload = contentType.includes('application/json')
            ? await response.json().catch(() => ({}))
            : await response.text();

        if (!response.ok) {
            unlockLoadingButtons();
            const message = payload && typeof payload === 'object'
                ? (payload.message || payload.error || `HTTP ${response.status}`)
                : `HTTP ${response.status}`;
            const error = new Error(message);
            error.status = response.status;
            error.payload = payload;
            error.response = response;
            throw error;
        }
        return payload;
    }

    const api = Object.freeze({
        csrfToken,
        dto,
        endpoints,
        get: (path, options = {}) => request(path, { ...options, method: 'GET' }),
        post: (path, options = {}) => request(path, { ...options, method: 'POST' }),
        request,
        unlockButtons: unlockLoadingButtons,
        notifyConnectionError,
        isOnline: () => (typeof navigator !== 'undefined' ? navigator.onLine : true),
    });

    global.ECuzdanApi = api;
    global.ECuzdanEndpoints = endpoints;
}(window));
