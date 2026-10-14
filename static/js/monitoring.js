/* Monitoring dashboard: typed API consumption, safe rendering and SSE live updates. */

(() => {
    'use strict';

    let refreshInterval = null;
    let logsRequestController = null;
    let loadedLogs = [];
    let liveLogSource = null;
    let liveReconnectTimer = null;
    let liveStreamConnected = false;
    let timelineChart = null;
    let activeInspectorEntry = null;

    const endpoint = name => window.ECuzdanEndpoints?.monitoring?.[name] || `/monitoring/api/${name}`;
    const api = () => window.ECuzdanApi;

    function formatNumber(value) {
        return Number(value || 0).toLocaleString('tr-TR');
    }

    function setText(id, text, state = '') {
        const element = document.getElementById(id);
        if (!element) return;
        element.textContent = text;
        if (state) element.dataset.state = state;
    }

    function setPanelError(id, message) {
        const element = document.getElementById(id);
        if (!element) return;
        element.textContent = message;
        element.dataset.state = 'error';
        element.classList.add('monitoring-error-state');
    }

    function clearPanelError(id) {
        const element = document.getElementById(id);
        if (element) element.classList.remove('monitoring-error-state');
    }

    async function getPayload(url) {
        if (api()?.get) return api().get(url, { credentials: 'same-origin' });
        const response = await fetch(url, { credentials: 'same-origin' });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
        return payload;
    }

    function decodePayload(name, payload, validator) {
        if (validator) return validator(payload);
        if (!payload || payload.success !== true || !payload.data) {
            throw new Error(payload?.error || `${name} response is invalid`);
        }
        return payload.data;
    }

    function monitoringDto(name) {
        return api()?.dto?.[name];
    }

    function updateLastUpdated() {
        const element = document.getElementById('last-updated');
        if (element) {
            element.textContent = new Date().toLocaleTimeString('tr-TR', {
                hour: '2-digit', minute: '2-digit', second: '2-digit',
            });
        }
    }

    function statusLabel(value) {
        return ({ healthy: 'SAĞLIKLI', degraded: 'BOZULMUŞ', critical: 'KRİTİK', warning: 'UYARI', unhealthy: 'SAĞLIKSIZ', unknown: 'BİLİNMİYOR' })[value] || String(value || 'BİLİNMİYOR').toUpperCase();
    }

    function renderHealthStatus(health) {
        const statusElement = document.getElementById('health-status');
        const componentsElement = document.getElementById('health-components');
        if (!statusElement || !componentsElement) return;
        clearPanelError('health-status');

        const status = ['healthy', 'degraded', 'critical'].includes(health.status) ? health.status : 'unknown';
        statusElement.className = `health-status ${status}`;
        statusElement.replaceChildren();
        const indicator = document.createElement('span');
        indicator.className = 'status-indicator';
        const label = document.createElement('span');
        label.className = 'font-semibold';
        label.textContent = `Sistem durumu: ${statusLabel(status)}`;
        statusElement.append(indicator, label);

        componentsElement.replaceChildren();
        const componentNames = {
            database: 'Veritabanı',
            logs: 'Log dosyaları',
            disk_space: 'Disk alanı',
            background_service: 'Arka Plan Servisleri',
            outbox_queue: 'Outbox Olay Kuyruğu',
        };
        Object.entries(health.components || {}).forEach(([component, value]) => {
            const row = document.createElement('div');
            row.className = 'component-item';
            const dot = document.createElement('div');
            dot.className = `component-status-dot ${String(value)}`;
            const text = document.createElement('span');
            text.className = 'text-sm';
            text.textContent = `${componentNames[component] || component}: ${statusLabel(value)}`;
            row.append(dot, text);
            componentsElement.appendChild(row);
        });

        const disk = health.disk_usage;
        const diskElement = document.getElementById('disk-usage-info');
        if (diskElement && disk) {
            diskElement.textContent = `Kullanılan ${Number(disk.used_gb || 0).toFixed(1)} GB / ${Number(disk.total_gb || 0).toFixed(1)} GB · ${Number(disk.free_percent || 0).toFixed(1)}% boş`;
        }
    }

    function renderAlertStatus(status) {
        const element = document.getElementById('alert-status');
        if (!element) return;
        clearPanelError('alert-status');
        element.replaceChildren();
        if (!status.enabled) {
            element.textContent = (window.ECuzdanI18n && window.ECuzdanI18n['ui_auto_a100c3d23a60'] || "Log alarmı kapalı. Aktifleştirmek için LOG_ALERTS_ENABLED=true ayarlanmalıdır.");
            return;
        }
        const counts = status.counts || {};
        const thresholds = status.thresholds || {};
        const breached = status.breached || {};
        const grid = document.createElement('div');
        grid.className = 'alert-status-grid';
        [
            ['CRITICAL', counts.CRITICAL || 0, thresholds.critical || 1, breached.critical],
            ['ERROR', counts.ERROR || 0, thresholds.error || 10, breached.error],
        ].forEach(([level, count, threshold, isBreached]) => {
            const card = document.createElement('div');
            card.className = `stat-card ${isBreached ? 'critical' : ''}`;
            const label = document.createElement('div');
            label.className = 'stat-label';
            label.textContent = `${level} · son ${thresholds.window_minutes || 1} dk`;
            const value = document.createElement('div');
            value.className = 'stat-value';
            value.textContent = `${count} / ${threshold}`;
            card.append(label, value);
            grid.appendChild(card);
        });
        const state = document.createElement('div');
        state.className = 'alert-policy-state';
        state.textContent = breached.critical || breached.error ? 'Eşik aşıldı' : 'Normal';
        element.append(grid, state);
    }

    function renderRecentErrors(errors) {
        const element = document.getElementById('recent-errors-info');
        if (!element) return;
        element.replaceChildren();
        if (!Array.isArray(errors) || errors.length === 0) {
            element.textContent = (window.ECuzdanI18n && window.ECuzdanI18n['ui_auto_8744a7512d1b'] || "Son hata sinyali bulunmuyor.");
            return;
        }
        const list = document.createElement('div');
        list.className = 'recent-errors-list';
        errors.slice().reverse().forEach(entry => {
            const row = document.createElement('div');
            row.className = `recent-error-row ${String(entry.level || 'ERROR').toLowerCase()}`;
            const meta = document.createElement('span');
            meta.className = 'recent-error-meta';
            meta.textContent = `${entry.timestamp || '-'} · ${entry.logger || entry.module || 'uygulama'}`;
            const message = document.createElement('span');
            message.className = 'recent-error-message';
            message.textContent = entry.message || entry.raw || '-';
            row.append(meta, message);
            list.appendChild(row);
        });
        element.appendChild(list);
    }

    function renderStats(stats) {
        clearPanelError('recent-errors-info');
        const values = {
            'total-logs': stats.total_logs,
            'error-count': stats.error_count,
            'warning-count': stats.warning_count,
            'critical-count': stats.critical_count,
            'security-count': stats.security_count,
        };
        Object.entries(values).forEach(([id, value]) => setText(id, formatNumber(value)));

        const filesElement = document.getElementById('log-files-info');
        if (filesElement) {
            filesElement.replaceChildren();
            const list = document.createElement('div');
            list.className = 'log-files-list';
            Object.entries(stats.log_files || {}).forEach(([key, info]) => {
                const row = document.createElement('div');
                row.className = `log-file-row ${info.exists ? 'available' : 'missing'}`;
                const name = document.createElement('span');
                name.className = 'log-file-name';
                name.textContent = info.filename || key;
                const details = document.createElement('span');
                details.className = 'log-file-details';
                const levelSummary = Object.entries(info.levels || {}).map(([level, count]) => `${level} ${formatNumber(count)}`).join(' · ');
                details.textContent = info.exists
                    ? `${formatNumber(info.entry_count)} kayıt · ${Number(info.size_mb || 0).toFixed(2)} MB${levelSummary ? ` · ${levelSummary}` : ''}`
                    : 'Henüz oluşturulmadı';
                row.append(name, details);
                list.appendChild(row);
            });
            filesElement.appendChild(list);
        }
        renderRecentErrors(stats.recent_errors || []);
    }

    function renderTimeline(data) {
        const points = Array.isArray(data?.points) ? data.points : [];

        // 1. Chart.js Canvas Rendering
        const canvas = document.getElementById('incident-timeline-chart');
        if (canvas && window.Chart) {
            const isDark = document.documentElement.classList.contains('dark') || document.body.classList.contains('dark');
            const textColor = isDark ? '#94a3b8' : '#64748b';
            const gridColor = isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.05)';

            const labels = points.map(p => p.hour || '');
            const errorCriticalData = points.map(p => (p.ERROR || 0) + (p.CRITICAL || 0));
            const warningData = points.map(p => p.WARNING || 0);
            const infoData = points.map(p => p.INFO || 0);

            if (timelineChart) {
                timelineChart.data.labels = labels;
                timelineChart.data.datasets[0].data = errorCriticalData;
                timelineChart.data.datasets[1].data = warningData;
                timelineChart.data.datasets[2].data = infoData;
                timelineChart.update();
            } else {
                const ctx = canvas.getContext('2d');
                timelineChart = new window.Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels,
                        datasets: [
                            {
                                label: 'Hata & Kritik',
                                data: errorCriticalData,
                                backgroundColor: '#ef4444',
                                borderRadius: 3,
                                stack: 'events',
                            },
                            {
                                label: 'Uyarı',
                                data: warningData,
                                backgroundColor: '#f59e0b',
                                borderRadius: 3,
                                stack: 'events',
                            },
                            {
                                label: 'Bilgi',
                                data: infoData,
                                backgroundColor: '#6366f1',
                                borderRadius: 3,
                                stack: 'events',
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {
                            mode: 'index',
                            intersect: false,
                        },
                        plugins: {
                            legend: {
                                position: 'top',
                                align: 'end',
                                labels: {
                                    boxWidth: 10,
                                    boxHeight: 10,
                                    usePointStyle: true,
                                    pointStyle: 'circle',
                                    color: textColor,
                                    font: { size: 11, weight: '500' }
                                }
                            },
                            tooltip: {
                                padding: 10,
                                cornerRadius: 8,
                            }
                        },
                        scales: {
                            x: {
                                stacked: true,
                                grid: { display: false },
                                ticks: {
                                    color: textColor,
                                    font: { size: 10 },
                                    maxRotation: 0,
                                    autoSkip: true,
                                    maxTicksLimit: 12
                                }
                            },
                            y: {
                                stacked: true,
                                beginAtZero: true,
                                grid: {
                                    color: gridColor
                                },
                                ticks: {
                                    color: textColor,
                                    font: { size: 10 },
                                    precision: 0
                                }
                            }
                        }
                    }
                });
            }
        }

        // 2. Fallback Element (#log-timeline)
        const element = document.getElementById('log-timeline');
        if (!element) return;
        element.replaceChildren();
        if (points.length === 0) {
            element.textContent = (window.ECuzdanI18n && window.ECuzdanI18n['ui_auto_0327cf1e733b'] || "Son 24 saatte ERROR, WARNING veya CRITICAL sinyali bulunmuyor.");
            return;
        }
        const max = Math.max(1, ...points.map(point => (point.ERROR || 0) + (point.WARNING || 0) + (point.CRITICAL || 0) + (point.INFO || 0)));
        points.forEach(point => {
            const row = document.createElement('div');
            row.className = 'timeline-row';
            row.setAttribute('role', 'listitem');
            const label = document.createElement('span');
            label.className = 'timeline-label';
            label.textContent = point.hour || '-';
            const bar = document.createElement('div');
            bar.className = 'timeline-bar';
            const total = (point.ERROR || 0) + (point.WARNING || 0) + (point.CRITICAL || 0) + (point.INFO || 0);
            bar.style.setProperty('--timeline-scale', `${Math.max(4, (total / max) * 100)}%`);
            bar.title = `ERROR ${point.ERROR || 0} · WARNING ${point.WARNING || 0} · CRITICAL ${point.CRITICAL || 0} · INFO ${point.INFO || 0}`;
            const count = document.createElement('span');
            count.className = 'timeline-count';
            count.textContent = formatNumber(total);
            row.append(label, bar, count);
            element.appendChild(row);
        });
    }

    async function loadHealthStatus(param = '') {
        try {
            const payload = await getPayload(`${endpoint('health')}${param}`);
            renderHealthStatus(decodePayload('monitoringHealth', payload, monitoringDto('monitoringHealth')));
        } catch (error) {
            setText('health-status', `Sağlık verisi alınamadı: ${error.message}`, 'error');
            setPanelError('health-components', 'Bileşen durumu alınamadı.');
        }
    }

    async function loadStats(param = '') {
        try {
            const payload = await getPayload(`${endpoint('stats')}${param}`);
            renderStats(decodePayload('monitoringStats', payload, monitoringDto('monitoringStats')));
        } catch (error) {
            ['total-logs', 'error-count', 'warning-count', 'critical-count', 'security-count'].forEach(id => setText(id, '—', 'error'));
            setPanelError('log-files-info', `İstatistikler alınamadı: ${error.message}`);
            setPanelError('recent-errors-info', 'Son hata sinyalleri alınamadı.');
        }
    }

    async function loadAlertStatus() {
        try {
            const payload = await getPayload(endpoint('alertsStatus'));
            renderAlertStatus(decodePayload('monitoringAlertsStatus', payload, monitoringDto('monitoringAlertsStatus')));
        } catch (error) {
            setPanelError('alert-status', `Alarm durumu alınamadı: ${error.message}`);
        }
    }

    async function loadTimeline() {
        try {
            const payload = await getPayload(endpoint('logsTimeline'));
            renderTimeline(decodePayload('monitoringTimeline', payload, monitoringDto('monitoringTimeline')));
        } catch (error) {
            setPanelError('log-timeline', `Zaman çizelgesi alınamadı: ${error.message}`);
        }
    }

    function getLogFilters() {
        const level = document.getElementById('log-level-select')?.value || '';
        const search = document.getElementById('log-search-input')?.value.trim() || '';
        const requestId = document.getElementById('log-request-id-input')?.value.trim() || '';
        const traceId = document.getElementById('log-trace-id-input')?.value.trim() || '';
        const lines = Math.max(10, Math.min(1000, Number.parseInt(document.getElementById('log-lines-input')?.value, 10) || 100));
        const preset = document.getElementById('log-preset-select')?.value || '';
        let resolvedLevel = level;
        if (preset === 'errors_only') resolvedLevel = 'ERROR';
        if (preset === 'critical_only') resolvedLevel = 'CRITICAL';
        let since = '';
        if (preset === 'last_hour') since = new Date(Date.now() - 60 * 60 * 1000).toISOString();
        if (preset === 'last_24h') since = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
        return { level: resolvedLevel, search, requestId, traceId, lines, since };
    }

    function buildLogQuery() {
        const source = document.getElementById('log-file-select')?.value || 'main';
        const filters = getLogFilters();
        const params = new URLSearchParams({ file: source, lines: String(filters.lines) });
        if (filters.level) params.set('level', filters.level);
        if (filters.search) params.set('search', filters.search);
        if (filters.requestId) params.set('request_id', filters.requestId);
        if (filters.traceId) params.set('trace_id', filters.traceId);
        if (filters.since) params.set('since', filters.since);
        return params;
    }

    function normalizeEntry(entry) {
        if (typeof entry === 'string') {
            return {
                timestamp: extractTimestamp(entry),
                level: extractLogLevel(entry),
                message: entry,
                raw: entry,
            };
        }
        return entry || { timestamp: '', level: 'INFO', message: '', raw: '' };
    }

    function renderLogEntries(entries) {
        const container = document.getElementById('log-container');
        if (!container) return;
        container.replaceChildren();
        if (!Array.isArray(entries) || entries.length === 0) {
            const empty = document.createElement('div');
            empty.className = 'obs-empty-state';
            empty.textContent = (window.ECuzdanI18n && window.ECuzdanI18n['ui_auto_384b26b24495'] || "Seçilen filtrelerle log bulunamadı.");
            container.appendChild(empty);
            return;
        }
        const fragment = document.createDocumentFragment();
        entries.forEach(rawEntry => {
            const entry = normalizeEntry(rawEntry);
            const level = String(entry.level || 'INFO').toUpperCase();
            const row = document.createElement('div');
            row.className = `log-entry ${level.toLowerCase()} cursor-pointer hover:bg-slate-900/60 transition`;
            row.dataset.level = level;
            row.setAttribute('title', 'Log detaylarını ve izleme bilgisini görmek için tıklayın');
            row.setAttribute('role', 'button');
            row.setAttribute('tabindex', '0');
            row.setAttribute('aria-label', `${level} log kaydı detayı`);

            row.addEventListener('click', () => {
                const selection = window.getSelection();
                if (selection && selection.toString().length > 0) return;
                openLogInspector(entry);
            });
            row.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    openLogInspector(entry);
                }
            });

            const timestamp = document.createElement('span');
            timestamp.className = 'log-timestamp';
            timestamp.textContent = entry.timestamp || '-';
            const badge = document.createElement('span');
            badge.className = `log-level ${level}`;
            badge.textContent = level;
            const source = document.createElement('span');
            source.className = 'log-source';
            source.textContent = entry.logger || entry.module || entry.category || 'application';
            const message = document.createElement('span');
            message.className = 'log-message';
            message.innerHTML = highlightSyntax(entry.message || entry.raw || '');
            row.append(timestamp, badge, source, message);

            const context = [];
            if (entry.request_id) context.push(`request ${entry.request_id}`);
            if (entry.trace_id) context.push(`trace ${entry.trace_id}`);
            if (entry.exception_type) context.push(entry.exception_type);
            if (context.length) {
                const contextElement = document.createElement('span');
                contextElement.className = 'log-context';
                contextElement.textContent = context.join(' · ');
                row.appendChild(contextElement);
            }
            fragment.appendChild(row);
        });
        container.appendChild(fragment);
    }

    function openLogInspector(entry) {
        activeInspectorEntry = entry;
        const drawer = document.getElementById('log-inspector-drawer');
        const backdrop = document.getElementById('log-inspector-backdrop');
        if (!drawer) return;

        const level = String(entry.level || 'INFO').toUpperCase();
        const badge = document.getElementById('drawer-badge');
        if (badge) {
            badge.textContent = level;
            badge.className = `px-2.5 py-1 text-xs font-bold rounded-lg ${
                level === 'ERROR' || level === 'CRITICAL' ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400' :
                level === 'WARNING' ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400' :
                'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
            }`;
        }

        setText('drawer-timestamp', entry.timestamp || '—');
        setText('drawer-logger', entry.logger || entry.module || entry.category || 'application');
        setText('drawer-function', (entry.function || entry.func_name || entry.line || entry.lineno) ? `${entry.function || entry.func_name || '—'} : ${entry.line || entry.lineno || '—'}` : '—');
        setText('drawer-thread', (entry.thread || entry.process) ? `${entry.thread || '—'} / ${entry.process || '—'}` : '—');
        setText('drawer-request-id', entry.request_id || '—');
        setText('drawer-trace-id', entry.trace_id || '—');
        setText('drawer-message', entry.message || entry.raw || '—');

        const traceFilterBtn = document.getElementById('drawer-filter-trace-btn');
        if (traceFilterBtn) {
            const hasTrace = Boolean(entry.trace_id && entry.trace_id !== '—');
            traceFilterBtn.disabled = !hasTrace;
            traceFilterBtn.classList.toggle('opacity-50', !hasTrace);
            traceFilterBtn.classList.toggle('cursor-not-allowed', !hasTrace);
        }

        const exceptionSection = document.getElementById('drawer-exception-section');
        const stacktraceEl = document.getElementById('drawer-stacktrace');
        const stacktrace = entry.stacktrace || entry.traceback || entry.exception || entry.exc_info;
        if (exceptionSection && stacktraceEl) {
            if (stacktrace) {
                stacktraceEl.textContent = typeof stacktrace === 'string' ? stacktrace : JSON.stringify(stacktrace, null, 2);
                exceptionSection.classList.remove('hidden');
            } else {
                exceptionSection.classList.add('hidden');
            }
        }

        const rawJsonEl = document.getElementById('drawer-raw-json');
        if (rawJsonEl) {
            rawJsonEl.textContent = JSON.stringify(entry, null, 2);
        }

        drawer.classList.remove('hidden');
        if (backdrop) backdrop.classList.remove('hidden');
        window.requestAnimationFrame(() => {
            drawer.classList.remove('translate-x-full');
            drawer.classList.add('translate-x-0');
        });
    }

    function closeLogInspector() {
        const drawer = document.getElementById('log-inspector-drawer');
        const backdrop = document.getElementById('log-inspector-backdrop');
        if (!drawer) return;
        drawer.classList.remove('translate-x-0');
        drawer.classList.add('translate-x-full');
        if (backdrop) backdrop.classList.add('hidden');
        window.setTimeout(() => {
            drawer.classList.add('hidden');
        }, 300);
    }

    function renderLogs(logs) {
        renderLogEntries((logs || []).map(normalizeEntry));
    }

    async function loadLogs() {
        if (logsRequestController) logsRequestController.abort();
        logsRequestController = new AbortController();
        try {
            const response = await fetch(`${endpoint('logs')}?${buildLogQuery()}`, {
                signal: logsRequestController.signal,
                credentials: 'same-origin',
                headers: { Accept: 'application/json' },
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
            const data = decodePayload('monitoringLogs', payload, monitoringDto('monitoringLogs'));
            const entries = Array.isArray(data.entries) ? data.entries : [];
            loadedLogs = entries.map(normalizeEntry);
            renderLogEntries(loadedLogs);
        } catch (error) {
            if (error.name === 'AbortError') return;
            setPanelError('log-container', `Loglar alınamadı: ${error.message}`);
        }
    }

    function highlightSyntax(message) {
        const div = document.createElement('div');
        div.textContent = String(message);
        return div.innerHTML.replace(/\n/g, '<br>');
    }

    function extractLogLevel(log) {
        const levels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'];
        return levels.find(level => String(log).includes(level)) || 'INFO';
    }

    function extractTimestamp(log) {
        const match = String(log).match(/\d{4}-\d{2}-\d{2}(?:T| )\d{2}:\d{2}:\d{2}/);
        return match ? match[0] : '';
    }

    function clearLogs() {
        loadedLogs = [];
        renderLogEntries([]);
    }

    function csvEscape(value) {
        const text = String(value ?? '');
        return /[,"\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
    }

    function downloadLogs() {
        if (!loadedLogs.length) {
            setPanelError('log-container', 'İndirilecek log yok. Önce logları getirin.');
            return;
        }
        const format = window.prompt('Format seçin: 1=TXT, 2=CSV, 3=JSON', '1');
        if (!format) return;
        const source = document.getElementById('log-file-select')?.value || 'logs';
        const stamp = new Date().toISOString().replace(/[:.]/g, '-');
        const entries = loadedLogs.map(normalizeEntry);
        let content;
        let mime;
        let extension;
        if (format === '2') {
            content = [
                'Timestamp,Level,Logger,Request ID,Trace ID,Message',
                ...entries.map(entry => [entry.timestamp, entry.level, entry.logger, entry.request_id, entry.trace_id, entry.message].map(csvEscape).join(',')),
            ].join('\n');
            mime = 'text/csv';
            extension = 'csv';
        } else if (format === '3') {
            content = JSON.stringify(entries, null, 2);
            mime = 'application/json';
            extension = 'json';
        } else {
            content = entries.map(entry => entry.raw || entry.message).join('\n');
            mime = 'text/plain';
            extension = 'txt';
        }
        const url = URL.createObjectURL(new Blob([content], { type: mime }));
        const link = document.createElement('a');
        link.href = url;
        link.download = `logs_${source}_${stamp}.${extension}`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    }

    function getSseFilters() {
        const filters = getLogFilters();
        return filters;
    }

    function liveEntryMatches(entry) {
        const filters = getSseFilters();
        const source = document.getElementById('log-file-select')?.value || 'main';
        const level = String(entry.level || '').toUpperCase();
        if (['errors', 'errors_structured'].includes(source) && !['ERROR', 'CRITICAL'].includes(level)) return false;
        if (source === 'security' && entry.category !== 'security') return false;
        if (filters.level && level !== filters.level) return false;
        if (filters.search) {
            const haystack = [entry.message, entry.logger, entry.module, entry.raw, entry.request_id, entry.trace_id]
                .filter(Boolean).join(' ').toLowerCase();
            if (!haystack.includes(filters.search.toLowerCase())) return false;
        }
        if (filters.requestId && !String(entry.request_id || entry.raw || '').includes(filters.requestId)) return false;
        if (filters.traceId && !String(entry.trace_id || entry.raw || '').includes(filters.traceId)) return false;
        if (filters.since && entry.timestamp) {
            const timestamp = Date.parse(entry.timestamp);
            if (!Number.isNaN(timestamp) && timestamp < Date.parse(filters.since)) return false;
        }
        return true;
    }

    function appendLiveLog(rawEntry) {
        const entry = normalizeEntry(rawEntry);
        if (!liveEntryMatches(entry)) return;
        loadedLogs.unshift(entry);
        loadedLogs = loadedLogs.slice(0, 500);
        renderLogEntries(loadedLogs);
    }

    function setLiveStreamStatus(message, state) {
        const element = document.getElementById('live-stream-status');
        if (element) {
            element.textContent = message;
            element.dataset.state = state;
        }
    }

    function connectLiveLogStream() {
        if (!window.EventSource) {
            setLiveStreamStatus('Canlı akış desteklenmiyor', 'error');
            return;
        }
        if (liveLogSource) liveLogSource.close();
        setLiveStreamStatus('Canlı akış bağlanıyor…', 'connecting');
        liveLogSource = new EventSource(endpoint('logsStream'), { withCredentials: true });
        liveLogSource.addEventListener('ready', () => {
            liveStreamConnected = true;
            setLiveStreamStatus('Canlı akış aktif', 'connected');
        });
        liveLogSource.addEventListener('log', event => {
            try { appendLiveLog(JSON.parse(event.data)); } catch (_) { setLiveStreamStatus('Canlı kayıt okunamadı', 'error'); }
        });
        liveLogSource.onerror = () => {
            liveStreamConnected = false;
            setLiveStreamStatus('Canlı akış yeniden bağlanıyor…', 'reconnecting');
            liveLogSource.close();
            if (!liveReconnectTimer) {
                liveReconnectTimer = window.setTimeout(() => {
                    liveReconnectTimer = null;
                    connectLiveLogStream();
                }, 3000);
            }
        };
    }

    async function refreshAll(force = false) {
        updateLastUpdated();
        const param = force ? '?refresh=true' : '';
        await Promise.all([loadHealthStatus(param), loadStats(param), loadAlertStatus(), loadTimeline(), loadLogs()]);
    }

    function toggleAutoRefresh() {
        const button = document.getElementById('auto-refresh-btn');
        const enabled = button?.dataset.enabled !== 'true';
        if (button) {
            button.dataset.enabled = String(enabled);
            button.setAttribute('aria-pressed', String(enabled));
            button.querySelector('span:last-child')?.replaceChildren(document.createTextNode(enabled ? 'Otomatik yenileme açık' : 'Otomatik yenileme kapalı'));
        }
        if (enabled) {
            refreshAll();
        }
    }

    function toggleSection(sectionName) {
        const section = document.querySelector(`[data-section="${sectionName}"]`);
        if (!section) return;
        section.classList.toggle('collapsed');
        const header = section.querySelector('.collapsible-header');
        if (header) header.setAttribute('aria-expanded', String(!section.classList.contains('collapsed')));
    }

    function initLogUpload() {
        const input = document.getElementById('log-upload-input');
        const dropzone = document.getElementById('log-upload-dropzone');
        const submit = document.getElementById('log-upload-submit');
        const reset = document.getElementById('log-upload-reset');
        const meta = document.getElementById('log-upload-meta');
        const status = document.getElementById('log-upload-status');
        if (!input || !dropzone || !submit || !reset || !meta || !status) return;
        let selectedFile = null;
        const setStatus = (message, state = 'info') => { status.textContent = message; status.dataset.state = state; };
        const selectFile = file => {
            selectedFile = file || null;
            const valid = selectedFile && /\.(log|txt|json|jsonl|csv)$/i.test(selectedFile.name) && selectedFile.size <= 10 * 1024 * 1024;
            if (!valid) {
                selectedFile = null;
                meta.textContent = file ? 'Desteklenmeyen dosya türü veya 10 MB üzeri dosya.' : (window.ECuzdanI18n && window.ECuzdanI18n['ui_auto_34474ae1b0ec'] || "Henüz dosya seçilmedi.");
                submit.disabled = true;
                reset.disabled = !file;
                setStatus(file ? 'Geçerli bir dosya seçin.' : '', 'error');
                return;
            }
            meta.textContent = `${selectedFile.name} · ${(selectedFile.size / 1024).toFixed(1)} KB`;
            submit.disabled = false;
            reset.disabled = false;
            setStatus('Analize hazır.', 'success');
        };
        input.addEventListener('change', () => selectFile(input.files[0]));
        ['dragenter', 'dragover'].forEach(name => dropzone.addEventListener(name, event => { event.preventDefault(); dropzone.classList.add('is-dragging'); }));
        ['dragleave', 'drop'].forEach(name => dropzone.addEventListener(name, event => { event.preventDefault(); dropzone.classList.remove('is-dragging'); }));
        dropzone.addEventListener('drop', event => selectFile(event.dataTransfer.files[0]));
        reset.addEventListener('click', () => { input.value = ''; selectedFile = null; meta.textContent = (window.ECuzdanI18n && window.ECuzdanI18n['ui_auto_34474ae1b0ec'] || "Henüz dosya seçilmedi."); submit.disabled = true; reset.disabled = true; setStatus(''); });
        submit.addEventListener('click', async () => {
            if (!selectedFile) return;
            submit.disabled = true;
            setStatus('Log analiz ediliyor…', 'loading');
            const body = new FormData();
            body.append('log_file', selectedFile);
            try {
                const payload = api()?.request
                    ? await api().request(endpoint('logsUpload'), { method: 'POST', body })
                    : await (await fetch(endpoint('logsUpload'), { method: 'POST', body, credentials: 'same-origin' })).json();
                const data = decodePayload('monitoringUpload', payload, monitoringDto('monitoringUpload'));
                loadedLogs = data.entries.map(normalizeEntry);
                renderLogEntries(loadedLogs);
                setStatus(`${formatNumber(data.count)} kayıt analiz edildi. Hassas alanlar maskelendi.`, 'success');
            } catch (error) {
                setStatus(error.message || 'Log yükleme başarısız.', 'error');
            } finally {
                submit.disabled = !selectedFile;
            }
        });
    }

    function initMonitoring() {
        const refreshButton = document.getElementById('refresh-btn');
        refreshButton?.addEventListener('click', () => refreshAll(true));
        document.getElementById('load-logs-btn')?.addEventListener('click', loadLogs);
        document.getElementById('clear-logs-btn')?.addEventListener('click', clearLogs);
        document.getElementById('download-logs-btn')?.addEventListener('click', downloadLogs);
        document.getElementById('auto-refresh-btn')?.addEventListener('click', toggleAutoRefresh);
        ['log-preset-select', 'log-file-select', 'log-level-select'].forEach(id => document.getElementById(id)?.addEventListener('change', loadLogs));
        ['log-search-input', 'log-request-id-input', 'log-trace-id-input'].forEach(id => document.getElementById(id)?.addEventListener('keydown', event => { if (event.key === 'Enter') loadLogs(); }));

        // Log Inspector Drawer handlers
        document.getElementById('drawer-close-btn')?.addEventListener('click', closeLogInspector);
        document.getElementById('log-inspector-backdrop')?.addEventListener('click', closeLogInspector);
        document.addEventListener('keydown', event => {
            if (event.key === 'Escape') closeLogInspector();
        });

        // Copy raw JSON from drawer
        document.getElementById('drawer-copy-json-btn')?.addEventListener('click', async () => {
            if (!activeInspectorEntry) return;
            const text = JSON.stringify(activeInspectorEntry, null, 2);
            try {
                await navigator.clipboard.writeText(text);
                const btn = document.getElementById('drawer-copy-json-btn');
                const span = btn?.querySelector('span');
                if (span) {
                    const orig = span.textContent;
                    span.textContent = 'Kopyalandı!';
                    window.setTimeout(() => { span.textContent = orig; }, 1800);
                }
            } catch (_) {
                const ta = document.createElement('textarea');
                ta.value = text;
                document.body.appendChild(ta);
                ta.select();
                document.execCommand('copy');
                document.body.removeChild(ta);
            }
        });

        // Filter by trace ID from drawer
        document.getElementById('drawer-filter-trace-btn')?.addEventListener('click', () => {
            if (!activeInspectorEntry?.trace_id) return;
            const traceInput = document.getElementById('log-trace-id-input');
            if (traceInput) {
                traceInput.value = activeInspectorEntry.trace_id;
                closeLogInspector();
                loadLogs();
            }
        });

        // Archive logs button handler
        document.getElementById('archive-logs-btn')?.addEventListener('click', async () => {
            if (!window.confirm('Tüm aktif log dosyaları arşivlenip (ZIP formatında sıkıştırılıp) sıfırlanacaktır. Bu işlemi onaylıyor musunuz?')) {
                return;
            }
            const btn = document.getElementById('archive-logs-btn');
            if (btn) btn.disabled = true;
            try {
                const csrfMeta = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
                const response = await fetch(endpoint('logsArchive'), {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Accept': 'application/json',
                        'X-CSRFToken': csrfMeta,
                        'X-CSRF-Token': csrfMeta,
                    }
                });
                const payload = await response.json().catch(() => ({}));
                if (!response.ok || !payload.success) {
                    throw new Error(payload.error || `HTTP ${response.status}`);
                }
                const data = payload.data || {};
                window.alert(`Loglar başarıyla arşivlendi:\nDosya: ${data.archive_file || 'Arşiv'}\nSıfırlanan Dosya Sayısı: ${data.archived_count || 0}`);
                refreshAll(true);
            } catch (err) {
                window.alert(`Log arşivleme hatası: ${err.message}`);
            } finally {
                if (btn) btn.disabled = false;
            }
        });

        refreshAll();
        refreshInterval = window.setInterval(() => {
            if (!liveStreamConnected) refreshAll();
            else Promise.all([loadHealthStatus(), loadStats(), loadAlertStatus(), loadTimeline()]);
        }, 30000);
        initLogUpload();
        connectLiveLogStream();
    }

    window.toggleSection = toggleSection;
    window.refreshMonitoring = refreshAll;
    window.addEventListener('beforeunload', () => {
        if (refreshInterval) window.clearInterval(refreshInterval);
        if (liveReconnectTimer) window.clearTimeout(liveReconnectTimer);
        if (liveLogSource) liveLogSource.close();
        if (logsRequestController) logsRequestController.abort();
        if (timelineChart) timelineChart.destroy();
    });

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initMonitoring, { once: true });
    else initMonitoring();
})();
