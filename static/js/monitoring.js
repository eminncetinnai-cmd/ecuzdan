/**
 * Monitoring Dashboard JavaScript
 * Handles health status, stats, and log viewer functionality
 */

let refreshInterval = null;
let logAutoRefreshInterval = null;
let loadedLogs = [];

/**
 * Update last updated timestamp
 */
function updateLastUpdated() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('tr-TR', { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
    });
    const lastUpdatedEl = document.getElementById('last-updated');
    if (lastUpdatedEl) {
        lastUpdatedEl.textContent = timeStr;
    }
}

/**
 * Load health status from API
 */
async function loadHealthStatus() {
    try {
        console.log('[Monitoring] Fetching health status from /monitoring/api/health');
        const response = await fetch('/monitoring/api/health');
        console.log('[Monitoring] Health status response:', response.status, response.statusText);
        if (!response.ok) {
            console.error('Health status API error:', response.status, response.statusText);
            return;
        }
        const result = await response.json();
        console.log('[Monitoring] Health status data:', result);
        
        if (result.success && result.data) {
            renderHealthStatus(result.data);
        } else {
            console.error('Health status response error:', result.error);
        }
    } catch (error) {
        console.error('Health status yüklenemedi:', error);
    }
}

/**
 * Render health status to UI
 */
function renderHealthStatus(health) {
    const statusEl = document.getElementById('health-status');
    const componentsEl = document.getElementById('health-components');
    
    if (!statusEl || !componentsEl) return;
    
    // Overall status
    const statusColors = {
        'healthy': 'bg-green-100 text-green-800',
        'degraded': 'bg-yellow-100 text-yellow-800',
        'critical': 'bg-red-100 text-red-800'
    };
    
    const statusIcons = {
        'healthy': '✓',
        'degraded': '⚠',
        'critical': '✕'
    };
    
    statusEl.className = `health-status ${statusColors[health.status] || statusColors['healthy']}`;
    statusEl.innerHTML = `
        <span class="status-indicator"></span>
        <span class="font-semibold">${statusIcons[health.status] || ''} Sistem Durumu: ${health.status.toUpperCase()}</span>
    `;
    
    // Components
    componentsEl.innerHTML = '';
    for (const [component, status] of Object.entries(health.components)) {
        const componentNames = {
            'database': 'Veritabanı',
            'logs': 'Log Dosyaları',
            'disk_space': 'Disk Alanı'
        };
        
        const componentEl = document.createElement('div');
        componentEl.className = 'component-item';
        componentEl.innerHTML = `
            <div class="component-status-dot ${status}"></div>
            <span class="text-sm">${componentNames[component] || component}: ${status.toUpperCase()}</span>
        `;
        componentsEl.appendChild(componentEl);
    }
    
    // Disk usage info
    if (health.disk_usage) {
        const diskEl = document.getElementById('disk-usage-info');
        if (diskEl) {
            diskEl.innerHTML = `
                <div class="text-sm text-slate-600">
                    <span class="font-medium">Disk:</span> 
                    ${health.disk_usage.used_gb.toFixed(1)} GB / ${health.disk_usage.total_gb.toFixed(1)} GB
                    (${health.disk_usage.free_percent.toFixed(1)}% boş)
                </div>
            `;
        }
    }
}

/**
 * Load stats from API
 */
async function loadStats() {
    try {
        console.log('[Monitoring] Fetching stats from /monitoring/api/stats');
        const response = await fetch('/monitoring/api/stats');
        console.log('[Monitoring] Stats response:', response.status, response.statusText);
        if (!response.ok) {
            console.error('Stats API error:', response.status, response.statusText);
            return;
        }
        const result = await response.json();
        console.log('[Monitoring] Stats data:', result);
        
        if (result.success && result.data) {
            renderStats(result.data);
        } else {
            console.error('Stats response error:', result.error);
        }
    } catch (error) {
        console.error('İstatistikler yüklenemedi:', error);
    }
}

/**
 * Render stats to UI
 */
function renderStats(stats) {
    // Update stat cards
    const statElements = {
        'total-logs': stats.total_logs,
        'error-count': stats.error_count,
        'warning-count': stats.warning_count,
        'critical-count': stats.critical_count,
        'security-count': stats.security_count
    };
    
    for (const [id, value] of Object.entries(statElements)) {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = value.toLocaleString();
        }
    }
    
    // Log file sizes
    if (stats.log_files) {
        const logFilesEl = document.getElementById('log-files-info');
        if (logFilesEl) {
            let html = '<div class="text-sm text-slate-600">';
            for (const [file, info] of Object.entries(stats.log_files)) {
                if (info.exists) {
                    html += `<div>${file}: ${info.size_mb.toFixed(2)} MB</div>`;
                }
            }
            html += '</div>';
            logFilesEl.innerHTML = html;
        }
    }
}

/**
 * Load logs from API
 */
async function loadLogs() {
    const fileSelect = document.getElementById('log-file-select');
    const levelSelect = document.getElementById('log-level-select');
    const searchInput = document.getElementById('log-search-input');
    const linesInput = document.getElementById('log-lines-input');
    
    if (!fileSelect) return;
    
    const file = fileSelect.value;
    const level = levelSelect ? levelSelect.value : '';
    const search = searchInput ? searchInput.value : '';
    const lines = linesInput ? parseInt(linesInput.value) : 100;
    
    try {
        const params = new URLSearchParams({
            file: file,
            lines: lines.toString()
        });
        
        if (level) params.append('level', level);
        if (search) params.append('search', search);
        
        const response = await fetch(`/monitoring/api/logs?${params}`);
        const result = await response.json();
        
        if (result.success && result.data) {
            loadedLogs = result.data.logs || [];
            renderLogs(loadedLogs);
        }
    } catch (error) {
        console.error('Log yüklenemedi:', error);
    }
}

/**
 * Render logs to UI
 */
function renderLogs(logs) {
    const container = document.getElementById('log-container');
    if (!container) return;
    
    if (logs.length === 0) {
        container.innerHTML = '<div class="text-center text-slate-400 py-8">Log bulunamadı</div>';
        return;
    }
    
    let html = '';
    for (const log of logs) {
        const logLevel = extractLogLevel(log);
        const timestamp = extractTimestamp(log);
        const message = log.replace(logLevel, '').replace(timestamp, '').trim();
        
        const levelClass = logLevel.toLowerCase();
        
        html += `
            <div class="log-entry ${levelClass}">
                <span class="log-timestamp">${timestamp}</span>
                <span class="log-level ${logLevel.toUpperCase()}">${logLevel.toUpperCase()}</span>
                <span class="log-message">${escapeHtml(message)}</span>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

/**
 * Extract log level from log line
 */
function extractLogLevel(log) {
    const levels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'];
    for (const level of levels) {
        if (log.includes(level)) {
            return level;
        }
    }
    return 'INFO';
}

/**
 * Extract timestamp from log line
 */
function extractTimestamp(log) {
    const match = log.match(/\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/);
    return match ? match[0] : '';
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Clear logs display
 */
function clearLogs() {
    const container = document.getElementById('log-container');
    if (container) {
        container.innerHTML = '<div class="text-center text-slate-400 py-8">Log temizlendi</div>';
    }
    loadedLogs = [];
}

/**
 * Download logs as text file
 */
function downloadLogs() {
    if (loadedLogs.length === 0) {
        alert('İndirilecek log yok. Önce log yükleyin.');
        return;
    }
    
    const fileSelect = document.getElementById('log-file-select');
    const file = fileSelect ? fileSelect.value : 'logs';
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `logs_${file}_${timestamp}.txt`;
    
    const content = loadedLogs.join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Toggle auto-refresh for logs
 */
function toggleAutoRefresh() {
    const btn = document.getElementById('auto-refresh-btn');
    
    if (logAutoRefreshInterval) {
        clearInterval(logAutoRefreshInterval);
        logAutoRefreshInterval = null;
        if (btn) {
            btn.textContent = 'Otomatik Yenileme: KAPALI';
            btn.classList.remove('bg-green-600');
            btn.classList.add('bg-blue-600');
        }
    } else {
        loadLogs();
        logAutoRefreshInterval = setInterval(loadLogs, 10000); // 10 seconds
        if (btn) {
            btn.textContent = 'Otomatik Yenileme: AÇIK';
            btn.classList.remove('bg-blue-600');
            btn.classList.add('bg-green-600');
        }
    }
}

/**
 * Refresh all data
 */
async function refreshAll() {
    updateLastUpdated();
    await Promise.all([
        loadHealthStatus(),
        loadStats()
    ]);
}

/**
 * Start auto-refresh
 */
function startAutoRefresh() {
    refreshAll();
    refreshInterval = setInterval(refreshAll, 30000); // 30 seconds
}

/**
 * Stop auto-refresh
 */
function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
    if (logAutoRefreshInterval) {
        clearInterval(logAutoRefreshInterval);
        logAutoRefreshInterval = null;
    }
}

/**
 * Initialize monitoring dashboard
 */
function initMonitoring() {
    console.log('[Monitoring] Initializing dashboard...');
    
    // Load initial data
    console.log('[Monitoring] Starting auto-refresh...');
    startAutoRefresh();
    
    // Setup event listeners
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshAll);
        console.log('[Monitoring] Refresh button listener attached');
    } else {
        console.error('[Monitoring] Refresh button not found');
    }
    
    const loadLogsBtn = document.getElementById('load-logs-btn');
    if (loadLogsBtn) {
        loadLogsBtn.addEventListener('click', loadLogs);
        console.log('[Monitoring] Load logs button listener attached');
    } else {
        console.error('[Monitoring] Load logs button not found');
    }
    
    const clearLogsBtn = document.getElementById('clear-logs-btn');
    if (clearLogsBtn) {
        clearLogsBtn.addEventListener('click', clearLogs);
        console.log('[Monitoring] Clear logs button listener attached');
    } else {
        console.error('[Monitoring] Clear logs button not found');
    }
    
    const downloadLogsBtn = document.getElementById('download-logs-btn');
    if (downloadLogsBtn) {
        downloadLogsBtn.addEventListener('click', downloadLogs);
        console.log('[Monitoring] Download logs button listener attached');
    } else {
        console.error('[Monitoring] Download logs button not found');
    }
    
    const autoRefreshBtn = document.getElementById('auto-refresh-btn');
    if (autoRefreshBtn) {
        autoRefreshBtn.addEventListener('click', toggleAutoRefresh);
        console.log('[Monitoring] Auto refresh button listener attached');
    } else {
        console.error('[Monitoring] Auto refresh button not found');
    }
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', stopAutoRefresh);
    console.log('[Monitoring] Dashboard initialization complete');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMonitoring);
} else {
    initMonitoring();
}
