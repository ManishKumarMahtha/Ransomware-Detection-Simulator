/**
 * Dashboard Chart.js and Polling Logic for Ransomware Detection Simulator.
 */

let timelineChart = null;
let doughnutChart = null;

// Initialize Chart.js instances
function initCharts() {
    // 1. Threat Timeline Line Chart
    const ctxTimeline = document.getElementById('threatTimelineChart').getContext('2d');
    timelineChart = new Chart(ctxTimeline, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Threat Score (0-100)',
                data: [],
                borderColor: '#38bdf8',
                backgroundColor: 'rgba(56, 189, 248, 0.15)',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 3,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    grid: { color: 'rgba(30, 41, 59, 0.5)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8', maxRotation: 0 }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });

    // 2. Severity Doughnut Chart
    const ctxDoughnut = document.getElementById('severityDoughnutChart').getContext('2d');
    doughnutChart = new Chart(ctxDoughnut, {
        type: 'doughnut',
        data: {
            labels: ['Low', 'Medium', 'High', 'Critical'],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: ['#10b981', '#f59e0b', '#f97316', '#ef4444'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// Fetch stats and update UI elements
async function fetchDashboardData() {
    try {
        const res = await fetch('/api/dashboard/stats');
        if (!res.ok) return;
        const data = await res.json();

        // Update KPIs
        document.getElementById('kpiMonitoredFiles').textContent = data.total_monitored_files || 0;
        document.getElementById('kpiSafeActivities').textContent = data.safe_activities || 0;
        document.getElementById('kpiSuspiciousActivities').textContent = data.suspicious_activities || 0;
        document.getElementById('kpiThreatsDetected').textContent = data.threats_detected || 0;

        // Health indicators
        const hlthWatchdog = document.getElementById('healthWatchdog');
        if (hlthWatchdog) {
            hlthWatchdog.textContent = data.monitoring_active ? 'ACTIVE' : 'IDLE';
            hlthWatchdog.className = data.monitoring_active ? 'badge bg-success-subtle text-success' : 'badge bg-secondary-subtle text-muted';
        }

        const hlthML = document.getElementById('healthML');
        if (hlthML) {
            hlthML.textContent = data.ml_available ? 'ONLINE' : 'UNAVAILABLE';
            hlthML.className = data.ml_available ? 'badge bg-success-subtle text-success' : 'badge bg-warning-subtle text-warning';
        }

        // Critical threat banner
        const critBanner = document.getElementById('criticalThreatBanner');
        if (critBanner) {
            const hasCritical = (data.severity_distribution && data.severity_distribution.CRITICAL > 0);
            if (hasCritical && data.recent_incidents && data.recent_incidents.length > 0) {
                const latest = data.recent_incidents[0];
                if (latest.severity === 'CRITICAL' && latest.status === 'Open') {
                    critBanner.classList.remove('d-none');
                    critBanner.classList.add('d-flex');
                    document.getElementById('bannerThreatReason').textContent = latest.primary_reason;
                } else {
                    critBanner.classList.add('d-none');
                    critBanner.classList.remove('d-flex');
                }
            } else {
                critBanner.classList.add('d-none');
                critBanner.classList.remove('d-flex');
            }
        }

        // Update Doughnut Chart
        if (doughnutChart && data.severity_distribution) {
            doughnutChart.data.datasets[0].data = [
                data.severity_distribution.LOW || 0,
                data.severity_distribution.MEDIUM || 0,
                data.severity_distribution.HIGH || 0,
                data.severity_distribution.CRITICAL || 0
            ];
            doughnutChart.update();
        }

        // Update Timeline Chart
        if (timelineChart && data.timeline) {
            const labels = data.timeline.map(t => {
                const parts = (t.timestamp || '').split(' ');
                return parts[1] || t.timestamp;
            });
            const scores = data.timeline.map(t => t.threat_score);

            timelineChart.data.labels = labels;
            timelineChart.data.datasets[0].data = scores;
            timelineChart.update();
        }

        // Update Recent Events Table
        const tbody = document.getElementById('recentEventsTableBody');
        if (tbody && data.recent_events) {
            if (data.recent_events.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Awaiting simulation or file events...</td></tr>';
            } else {
                tbody.innerHTML = data.recent_events.map(ev => {
                    const score = ev.threat_score || 0;
                    const fileName = (ev.file_path || '').split(/[\\/]/).pop();
                    let scoreBadge = `<span class="badge bg-secondary">${score}/100</span>`;
                    if (score >= 80) scoreBadge = `<span class="badge badge-critical">${score}/100</span>`;
                    else if (score >= 60) scoreBadge = `<span class="badge badge-high">${score}/100</span>`;
                    else if (score >= 30) scoreBadge = `<span class="badge badge-medium">${score}/100</span>`;
                    else scoreBadge = `<span class="badge badge-low">${score}/100</span>`;

                    const flagBadge = ev.is_flagged ?
                        '<span class="badge bg-danger-subtle text-danger"><i class="bi bi-shield-x me-1"></i>Flagged</span>' :
                        '<span class="badge bg-success-subtle text-success"><i class="bi bi-shield-check me-1"></i>Safe</span>';

                    return `
                        <tr>
                            <td class="text-muted small">${ev.timestamp}</td>
                            <td><span class="badge bg-dark border border-secondary">${ev.event_type}</span></td>
                            <td class="fw-semibold text-light">${fileName}</td>
                            <td>${scoreBadge}</td>
                            <td>${flagBadge}</td>
                        </tr>
                    `;
                }).join('');
            }
        }

    } catch (e) {
        console.warn('Dashboard fetch error:', e);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    fetchDashboardData();
    setInterval(fetchDashboardData, 2000);
});
