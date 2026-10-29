/**
 * Alerts Feed and Incident Response actions.
 */

async function emergencyStopSimulation() {
    try {
        const res = await fetch('/api/simulation/stop', { method: 'POST' });
        const data = await res.json();
        showToast('Containment executed: Simulation halted.', 'warn');
        refreshAlerts();
    } catch (e) {
        showToast('Error stopping simulation: ' + e.message, 'error');
    }
}

async function markIncidentStatus(incidentId, status) {
    try {
        const res = await fetch(`/api/incidents/${incidentId}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Incident ${incidentId} marked as ${status}.`, 'success');
            refreshAlerts();
        } else {
            showToast(data.error || 'Failed to update status', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function refreshAlerts() {
    try {
        const res = await fetch('/api/alerts?limit=25');
        if (!res.ok) return;
        const data = await res.json();

        const container = document.getElementById('alertsContainer');
        const countBadge = document.getElementById('alertsCountBadge');
        const alerts = data.alerts || [];

        countBadge.textContent = `${alerts.length} Alerts`;
        if (alerts.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="bi bi-shield-check text-success fs-1 d-block mb-2"></i>
                    No active threats detected. System operations are currently benign.
                </div>
            `;
            return;
        }

        container.innerHTML = alerts.map(al => {
            const fileName = (al.file_path || '').split(/[\\/]/).pop();
            const badge = getSeverityBadge(al.severity);
            const reasonsHtml = (al.reasons || []).map(r => `<li>${r}</li>`).join('');

            return `
                <div class="cyber-card p-3 border-start border-4 ${al.severity === 'CRITICAL' ? 'border-danger' : 'border-warning'}">
                    <div class="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-2">
                        <div class="d-flex align-items-center gap-2">
                            <span class="fw-bold text-white fs-6">${al.incident_id}</span>
                            ${badge}
                            <span class="badge bg-dark border border-secondary text-info">Score: ${al.threat_score}/100</span>
                        </div>
                        <div class="text-muted small">
                            <i class="bi bi-clock me-1"></i> ${al.timestamp}
                        </div>
                    </div>

                    <div class="fw-semibold text-warning-subtle mb-2">
                        <i class="bi bi-exclamation-octagon me-1"></i> ${al.primary_reason}
                    </div>

                    <div class="small text-muted mb-2">
                        <div class="fw-semibold text-light mb-1">Behavioral Detection Attribution:</div>
                        <ul class="mb-1 ps-3 text-secondary">
                            ${reasonsHtml}
                        </ul>
                    </div>

                    <div class="p-2 rounded bg-dark border border-secondary border-opacity-50 small mb-3">
                        <div class="text-muted mb-1"><strong>Mathematical Scoring Formulation:</strong></div>
                        <code class="text-info">${al.formula || 'Heuristic sum computed.'}</code>
                        ${al.ml_prediction ? `<div class="mt-1 text-muted"><strong>ML Classifier Verdict:</strong> <span class="text-light">${al.ml_prediction}</span></div>` : ''}
                    </div>

                    <div class="d-flex flex-wrap align-items-center justify-content-between gap-2 border-top border-secondary border-opacity-25 pt-2">
                        <div class="small text-muted text-truncate" style="max-width: 400px;">
                            Target: <span class="text-light font-monospace">${fileName}</span>
                        </div>

                        <div class="d-flex gap-2">
                            <button class="btn btn-sm btn-outline-warning" onclick="markIncidentStatus('${al.incident_id}', 'Under Investigation')">
                                <i class="bi bi-search me-1"></i> Investigate
                            </button>
                            <button class="btn btn-sm btn-outline-success" onclick="markIncidentStatus('${al.incident_id}', 'Mitigated')">
                                <i class="bi bi-check2-circle me-1"></i> Resolve / Mitigated
                            </button>
                            <button class="btn btn-sm btn-outline-secondary" onclick="markIncidentStatus('${al.incident_id}', 'False Positive')">
                                False Positive
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

    } catch (e) {
        console.warn('Alerts fetch error:', e);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    refreshAlerts();
    setInterval(refreshAlerts, 2000);
});
