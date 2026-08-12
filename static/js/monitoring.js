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
        console.log('[Monitoring] Document cookie:', document.cookie);
        const response = await fetch('/monitoring/api/health', {
            credentials: 'same-origin'
        });
        console.log('[Monitoring] Health status response:', response.status, response.statusText);
        console.log('[Monitoring] Response headers:', response.headers);
        if (!response.ok) {
            console.error('Health status API error:', response.status, response.statusText);
            console.error('Response text:', await response.text());
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
        const response = await fetch('/monitoring/api/stats', {
            credentials: 'same-origin'
        });
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
    try {
        console.log('[Monitoring] Loading logs');
        
        const fileSelect = document.getElementById('log-file-select');
        const levelSelect = document.getElementById('log-level-select');
        const presetSelect = document.getElementById('log-preset-select');
        const searchInput = document.getElementById('log-search-input');
        const linesInput = document.getElementById('log-lines-input');
        
        const file_type = fileSelect.value;
        let level_filter = levelSelect.value;
        const search_term = searchInput.value;
        const line_count = parseInt(linesInput.value) || 100;
        
        // Handle preset filters
        const preset = presetSelect.value;
        if (preset === 'errors_only') {
            level_filter = 'ERROR';
        } else if (preset === 'critical_only') {
            level_filter = 'CRITICAL';
        }
        
        // Build params
        const params = new URLSearchParams({
            file: file_type,
            lines: line_count
        });
        
        if (level_filter) params.append('level', level_filter);
        if (search_term) params.append('search', search_term);
        
        const response = await fetch(`/monitoring/api/logs?${params}`, {
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            console.error('Logs API error:', response.status, response.statusText);
            return;
        }
        
        const result = await response.json();
        console.log('[Monitoring] Logs data:', result);
        
        if (result.success && result.data) {
            renderLogs(result.data.logs);
            loadedLogs = result.data.logs;
        } else {
            console.error('Logs response error:', result.error);
        }
    } catch (error) {
        console.error('Logs yüklenemedi:', error);
    }
}

/**
 * Render logs to UI with syntax highlighting
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
        const highlightedMessage = highlightSyntax(message, logLevel);
        
        html += `
            <div class="log-entry ${levelClass}">
                <span class="log-timestamp">${timestamp}</span>
                <span class="log-level ${logLevel.toUpperCase()}">${logLevel.toUpperCase()}</span>
                <span class="log-message">${highlightedMessage}</span>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

/**
 * Apply syntax highlighting to log message
 */
function highlightSyntax(message, logLevel) {
    let highlighted = escapeHtml(message);
    
    // Highlight URLs
    highlighted = highlighted.replace(
        /(https?:\/\/[^\s]+)/g,
        '<span class="log-url">$1</span>'
    );
    
    // Highlight file paths
    highlighted = highlighted.replace(
        /([a-zA-Z]:\\[^\\/:*?"<>|]+(?:\\[^\\/:*?"<>|]+)*|\/[^\\/:*?"<>|]+(?:\/[^\\/:*?"<>|]+)*)/g,
        '<span class="log-path">$1</span>'
    );
    
    // Highlight numbers
    highlighted = highlighted.replace(
        /\b\d+\b/g,
        '<span class="log-number">$1</span>'
    );
    
    // Highlight function names (typical Python pattern)
    highlighted = highlighted.replace(
        /([a-zA-Z_][a-zA-Z0-9_]*)\(/g,
        '<span class="log-function">$1</span>('
    );
    
    // Highlight module paths
    highlighted = highlighted.replace(
        /([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)/g,
        '<span class="log-module">$1</span>'
    );
    
    // Highlight error codes
    highlighted = highlighted.replace(
        /\b(HTTP \d{3}|Error \d+|Code: \d+)\b/g,
        '<span class="log-error-code">$1</span>'
    );
    
    // Highlight common keywords
    const keywords = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'FROM', 'WHERE', 'AND', 'OR', 'NOT'];
    keywords.forEach(keyword => {
        const regex = new RegExp(`\\b${keyword}\\b`, 'g');
        highlighted = highlighted.replace(regex, `<span class="log-keyword">${keyword}</span>`);
    });
    
    return highlighted;
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
 * Download logs with format selection
 */
function downloadLogs() {
    if (loadedLogs.length === 0) {
        alert('İndirilecek log yok. Önce log yükleyin.');
        return;
    }
    
    // Ask user for format
    const format = prompt('İndirme formatını seçin:\n1. TXT (Metin)\n2. CSV (Excel uyumlu)\n3. JSON\n\nSayı girin (1, 2, veya 3):', '1');
    
    if (!format) return; // User cancelled
    
    const fileSelect = document.getElementById('log-file-select');
    const file = fileSelect ? fileSelect.value : 'logs';
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    let content, filename, mimeType;
    
    if (format === '2') {
        // CSV format
        filename = `logs_${file}_${timestamp}.csv`;
        mimeType = 'text/csv';
        content = convertLogsToCSV(loadedLogs);
    } else if (format === '3') {
        // JSON format
        filename = `logs_${file}_${timestamp}.json`;
        mimeType = 'application/json';
        content = convertLogsToJSON(loadedLogs);
    } else {
        // TXT format (default)
        filename = `logs_${file}_${timestamp}.txt`;
        mimeType = 'text/plain';
        content = loadedLogs.join('\n');
    }
    
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    console.log('[Monitoring] Logs downloaded as', format.toUpperCase());
}

/**
 * Convert logs to CSV format
 */
function convertLogsToCSV(logs) {
    const headers = ['Timestamp', 'Level', 'Message'];
    const rows = logs.map(log => {
        const level = extractLogLevel(log);
        const timestamp = extractTimestamp(log);
        const message = log.replace(level, '').replace(timestamp, '').trim();
        
        // Escape CSV special characters
        const escapeCSV = (text) => {
            if (text.includes(',') || text.includes('"') || text.includes('\n')) {
                return `"${text.replace(/"/g, '""')}"`;
            }
            return text;
        };
        
        return [escapeCSV(timestamp), escapeCSV(level), escapeCSV(message)].join(',');
    });
    
    return [headers.join(','), ...rows].join('\n');
}

/**
 * Convert logs to JSON format
 */
function convertLogsToJSON(logs) {
    const logObjects = logs.map(log => {
        const level = extractLogLevel(log);
        const timestamp = extractTimestamp(log);
        const message = log.replace(level, '').replace(timestamp, '').trim();
        
        return {
            timestamp: timestamp,
            level: level,
            message: message,
            raw: log
        };
    });
    
    return JSON.stringify(logObjects, null, 2);
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
 * Toggle collapsible section
 */
function toggleSection(sectionName) {
    const section = document.querySelector(`[data-section="${sectionName}"]`);
    if (section) {
        section.classList.toggle('collapsed');
        console.log('[Monitoring] Section toggled:', sectionName, section.classList.contains('collapsed') ? 'collapsed' : 'expanded');
    }
}

/**
 * Initialize monitoring dashboard
 */
function initMonitoring() {
    console.log('[Monitoring] Initializing dashboard...');
    
    // Load initial data immediately
    console.log('[Monitoring] Loading initial data...');
    refreshAll();
    
    // Start auto-refresh
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
    
    const presetSelect = document.getElementById('log-preset-select');
    if (presetSelect) {
        presetSelect.addEventListener('change', () => {
            console.log('[Monitoring] Preset changed:', presetSelect.value);
            loadLogs();
        });
        console.log('[Monitoring] Preset select listener attached');
    } else {
        console.error('[Monitoring] Preset select not found');
    }
    
    console.log('[Monitoring] Dashboard initialized successfully');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMonitoring);
} else {
    initMonitoring();
}
