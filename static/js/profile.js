/* ==========================================================================
   E-Cüzdan — Investor Profile & Radar Chart (static/js/profile.js)
   Clean, User-Friendly, EAFGS Standard Colors
   ========================================================================== */

let radarChartInstance = null;

function initRadarChart() {
    const canvas = document.getElementById('radarChart');
    if (!canvas || !window.profileChartData) return;

    if (typeof Chart === 'undefined') {
        let retryCount = 0;
        const retryInterval = setInterval(() => {
            retryCount++;
            if (typeof Chart !== 'undefined') {
                clearInterval(retryInterval);
                initRadarChart();
            } else if (retryCount >= 50) {
                clearInterval(retryInterval);
                console.warn('[Profile] Chart.js is not loaded');
            }
        }, 100);
        return;
    }

    if (radarChartInstance) {
        radarChartInstance.destroy();
    }

    const ctx = canvas.getContext('2d');
    
    const isDark = document.documentElement.classList.contains('dark');
    const gridColor = isDark ? 'rgba(148, 163, 184, 0.18)' : 'rgba(148, 163, 184, 0.28)';
    const textColor = isDark ? '#94a3b8' : '#475569';
    const primaryColor = '#6366f1';
    const primaryBg = 'rgba(99, 102, 241, 0.2)';
    const whiteColor = '#ffffff';

    const data = window.profileChartData;
    
    radarChartInstance = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: data.labels || [
                'Finansal Okuryazarlık',
                'Risk Kapasitesi',
                'Risk Toleransı',
                'Davranışsal Finans',
                'Yatırım Deneyimi'
            ],
            datasets: [{
                label: data.label || 'Risk Profili',
                data: data.scores || [0, 0, 0, 0, 0],
                backgroundColor: primaryBg,
                borderColor: primaryColor,
                borderWidth: 2,
                pointBackgroundColor: primaryColor,
                pointBorderColor: whiteColor,
                pointHoverBackgroundColor: whiteColor,
                pointHoverBorderColor: primaryColor
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20,
                        color: textColor,
                        backdropColor: 'transparent',
                        font: { size: 10, weight: '600' }
                    },
                    grid: {
                        color: gridColor
                    },
                    angleLines: {
                        color: gridColor
                    },
                    pointLabels: {
                        color: textColor,
                        font: { size: 11, weight: '700' }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

let profileHistorySortState = { column: null, ascending: true };

function sortProfileHistory(headerEl, column) {
    const table = document.getElementById('profileHistoryTable');
    if (!table) return;
    const tbody = table.querySelector('tbody');
    if (!tbody) return;

    const rows = Array.from(tbody.querySelectorAll('tr'));
    if (!rows.length) return;

    if (profileHistorySortState.column === column) {
        profileHistorySortState.ascending = !profileHistorySortState.ascending;
    } else {
        profileHistorySortState.column = column;
        profileHistorySortState.ascending = true;
    }

    const isAsc = profileHistorySortState.ascending;

    // Update header indicators
    table.querySelectorAll('th .sort-indicator').forEach(ind => {
        ind.textContent = '⇅';
    });
    if (headerEl) {
        const currentInd = headerEl.querySelector('.sort-indicator');
        if (currentInd) currentInd.textContent = isAsc ? '↑' : '↓';
    }

    rows.sort((a, b) => {
        let valA, valB;
        if (column === 'date') {
            valA = a.getAttribute('data-date') || '';
            valB = b.getAttribute('data-date') || '';
            return isAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
        } else if (column === 'risk') {
            valA = a.getAttribute('data-risk') || '';
            valB = b.getAttribute('data-risk') || '';
            return isAsc ? valA.localeCompare(valB, 'tr') : valB.localeCompare(valA, 'tr');
        } else if (column === 'confidence') {
            valA = parseFloat(a.getAttribute('data-confidence')) || 0;
            valB = parseFloat(b.getAttribute('data-confidence')) || 0;
            return isAsc ? valA - valB : valB - valA;
        } else if (column === 'status') {
            valA = parseInt(a.getAttribute('data-status')) || 0;
            valB = parseInt(b.getAttribute('data-status')) || 0;
            return isAsc ? valA - valB : valB - valA;
        }
        return 0;
    });

    rows.forEach(row => tbody.appendChild(row));
}
window.sortProfileHistory = sortProfileHistory;

function initScoreBars() {
    document.querySelectorAll('.profile-score-fill[data-width]').forEach(bar => {
        const w = bar.getAttribute('data-width');
        if (w !== null && (!bar.style.width || bar.style.width === '0%')) {
            bar.style.width = Math.min(100, Math.max(0, parseFloat(w) || 0)) + '%';
        }
    });
}
window.initScoreBars = initScoreBars;

function initProfilePage() {
    initRadarChart();
    initScoreBars();
}

document.addEventListener('DOMContentLoaded', initProfilePage);
window.addEventListener('ecuzdan:theme-changed', initProfilePage);
