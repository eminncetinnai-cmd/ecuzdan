/**
 * E-CÜZDAN v15.0 - Charts JavaScript
 * Chart.js configurations and helper functions
 */

// Chart Colors
export const CHART_COLORS = {
    green: '#10b981',
    greenLight: '#34d399',
    red: '#ef4444',
    redLight: '#f87171',
    blue: '#3b82f6',
    blueLight: '#60a5fa',
    indigo: '#6366f1',
    indigoLight: '#818cf8',
    amber: '#f59e0b',
    amberLight: '#fbbf24',
    purple: '#8b5cf6',
    purpleLight: '#a78bfa',
    slate: '#64748b',
    slateLight: '#94a3b8'
};

// Default Chart Options
export const DEFAULT_CHART_OPTIONS = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: false
        },
        tooltip: {
            backgroundColor: 'rgba(255,255,255,0.97)',  /* beyaz tooltip bg */
            titleColor: '#0f172a',   /* #0f172a / white → 19.05:1 ✅ WCAG AAA */
            bodyColor: '#334155',    /* #334155 / white → 10.1:1 ✅ WCAG AAA */
            borderColor: '#e2e8f0',
            borderWidth: 1,
            titleFont: { size: 12, weight: 'bold' },
            bodyFont: { size: 13 },
            padding: 14,
            cornerRadius: 8,
            displayColors: true
        }
    },
    scales: {
        x: {
            grid: { display: false },
            ticks: { 
                font: { size: 10, weight: '600' }, 
                color: '#334155'  /* #334155 / white bg → 10.1:1 ✅ WCAG AAA */
            }
        },
        y: {
            grid: { 
                color: '#e2e8f0',  /* hafif gri grid — beyaz bg üzeri */
                drawBorder: false 
            },
            ticks: {
                font: { size: 10, weight: '600' },
                color: '#334155'  /* #334155 / white bg → 10.1:1 ✅ WCAG AAA */
            }
        }
    }
};

// Bar Chart Options
export const BAR_CHART_OPTIONS = {
    ...DEFAULT_CHART_OPTIONS,
    plugins: {
        ...DEFAULT_CHART_OPTIONS.plugins,
        legend: {
            display: true,
            position: 'top',
            labels: {
                font: { size: 10, weight: 'bold' },
                color: '#1e293b',  /* #1e293b / white bg → 14.2:1 ✅ WCAG AAA */
                usePointStyle: true,
                padding: 15
            }
        }
    }
};

// Line Chart Options
export const LINE_CHART_OPTIONS = {
    ...DEFAULT_CHART_OPTIONS,
    plugins: {
        ...DEFAULT_CHART_OPTIONS.plugins,
        legend: {
            display: true,
            position: 'top',
            labels: {
                font: { size: 10, weight: 'bold' },
                color: '#1e293b',  /* #1e293b / white bg → 14.2:1 ✅ WCAG AAA */
                usePointStyle: true,
                padding: 15
            }
        }
    },
    elements: {
        line: {
            tension: 0.4,
            borderWidth: 2
        },
        point: {
            radius: 4,
            hoverRadius: 6
        }
    }
};

// Doughnut Chart Options
export const DOUGHNUT_CHART_OPTIONS = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '70%',
    plugins: {
        legend: {
            position: 'bottom',
            labels: {
                boxWidth: 12,
                font: { size: 10, weight: 'bold' },
                color: '#1e293b',  /* #1e293b / white bg → 14.2:1 ✅ WCAG AAA */
                padding: 15,
                usePointStyle: true
            }
        },
        tooltip: {
            backgroundColor: 'rgba(255,255,255,0.97)',  /* beyaz tooltip */
            titleColor: '#0f172a',  /* 19.05:1 ✅ WCAG AAA */
            bodyColor: '#334155',   /* 10.1:1 ✅ WCAG AAA */
            borderColor: '#e2e8f0',
            borderWidth: 1,
            titleFont: { size: 12, weight: 'bold' },
            bodyFont: { size: 13 },
            padding: 14,
            cornerRadius: 8
        }
    }
};

// Create Bar Chart
export function createBarChart(ctx, data, options = {}) {
    return new Chart(ctx, {
        type: 'bar',
        data: data,
        options: { ...BAR_CHART_OPTIONS, ...options }
    });
}

// Create Line Chart
export function createLineChart(ctx, data, options = {}) {
    return new Chart(ctx, {
        type: 'line',
        data: data,
        options: { ...LINE_CHART_OPTIONS, ...options }
    });
}

// Create Doughnut Chart
export function createDoughnutChart(ctx, data, options = {}) {
    return new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: { ...DOUGHNUT_CHART_OPTIONS, ...options }
    });
}

// Create Pie Chart
export function createPieChart(ctx, data, options = {}) {
    return new Chart(ctx, {
        type: 'pie',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        font: { size: 10, weight: 'bold' },
                        padding: 15,
                        usePointStyle: true
                    }
                }
            }
        }
    });
}

// Create Area Chart (Line with fill)
export function createAreaChart(ctx, data, options = {}) {
    const areaData = {
        ...data,
        datasets: data.datasets.map(dataset => ({
            ...dataset,
            fill: true,
            backgroundColor: dataset.backgroundColor || 'rgba(99, 102, 241, 0.1)'
        }))
    };
    
    return new Chart(ctx, {
        type: 'line',
        data: areaData,
        options: { ...LINE_CHART_OPTIONS, ...options }
    });
}

// Create Multi-Line Chart
export function createMultiLineChart(ctx, data, options = {}) {
    return new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            ...LINE_CHART_OPTIONS,
            interaction: {
                mode: 'index',
                intersect: false
            }
        }
    });
}

// Create Stacked Bar Chart
export function createStackedBarChart(ctx, data, options = {}) {
    return new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            ...BAR_CHART_OPTIONS,
            scales: {
                x: {
                    ...BAR_CHART_OPTIONS.scales.x,
                    stacked: true
                },
                y: {
                    ...BAR_CHART_OPTIONS.scales.y,
                    stacked: true
                }
            }
        }
    });
}

// Format Chart Labels (Money)
export function formatMoneyLabel(value) {
    var val = value;
    if (typeof value === 'string') {
        val = parseFloat(value);
        if (isNaN(val)) val = 0;
    }
    return new Intl.NumberFormat('tr-TR', {
        style: 'currency',
        currency: 'TRY',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(val);
}

// Format Chart Labels (Percentage)
export function formatPercentLabel(value) {
    return value + '%';
}

// Destroy Chart
export function destroyChart(chart) {
    if (chart) {
        chart.destroy();
    }
}

// Update Chart Data
export function updateChartData(chart, newData) {
    if (chart) {
        chart.data = newData;
        chart.update();
    }
}

// Export for global access
window.ECuzdanCharts = {
    CHART_COLORS,
    DEFAULT_CHART_OPTIONS,
    BAR_CHART_OPTIONS,
    LINE_CHART_OPTIONS,
    DOUGHNUT_CHART_OPTIONS,
    createBarChart,
    createLineChart,
    createDoughnutChart,
    createPieChart,
    createAreaChart,
    createMultiLineChart,
    createStackedBarChart,
    formatMoneyLabel,
    formatPercentLabel,
    destroyChart,
    updateChartData
};
