/**
 * Incident History and Forensic Analysis logic.
 */

let activeModalIncidentId = null;
let incidentModalInstance = null;

async function fetchIncidents() {
    const sev = document.getElementById('filterSeverity').value;
    const stat = document.getElementById('filterStatus').value;

    try {
        const res = await fetch(`/api/incidents?severity=${encodeURIComponent(sev)}&status=${encodeURIComponent(stat)}`);
        if (!res.ok) return;
        const data = await res.json();

        const tbody = document.getElementById('incidentsTableBody');
        const countBadge = document.getElementById('incidentTotalCountBadge');
        const incidents = data.incidents || [];

        countBadge.textContent = `${incidents.length} Recorded`;
        if (incidents.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">No incidents match the selected filter criteria.</td></tr>';
            return;
        }

        tbody.innerHTML = incidents.map(inc => {
            const sevBadge = getSeverityBadge(inc.severity);
            let statusBadge = `<span class="badge bg-secondary">${inc.status}</span>`;
            if (inc.status === 'Open') statusBadge = '<span class="badge bg-danger-subtle text-danger">Open</span>';
            else if (inc.status === 'Under Investigation') statusBadge = '<span class="badge bg-warning-subtle text-warning">Investigating</span>';
            else if (inc.status === 'Mitigated') statusBadge = '<span class="badge bg-success-subtle text-success">Mitigated</span>';
            else if (inc.status === 'False Positive') statusBadge = '<span class="badge bg-secondary-subtle text-muted">False Positive</span>';

            return `
                <tr>
                    <td class="fw-bold font-monospace text-info">${inc.incident_id}</td>
                    <td class="text-muted small">${inc.timestamp}</td>
                    <td>${sevBadge}</td>
                    <td><span class="badge bg-dark border border-secondary">${inc.threat_score}/100</span></td>
                    <td><code>${inc.event_type}</code></td>
                    <td class="small text-truncate" style="max-width: 280px;" title="${inc.primary_reason}">
                        ${inc.primary_reason}
                    </td>
                    <td>${statusBadge}</td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-outline-info" onclick="openIncidentDetails('${inc.incident_id}')">
                            <i class="bi bi-eye"></i> Details
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (e) {
        console.warn('Error fetching incidents:', e);
    }
}

async function openIncidentDetails(incidentId) {
    activeModalIncidentId = incidentId;
    try {
        const res = await fetch(`/api/incidents/${incidentId}`);
        if (!res.ok) {
            showToast('Failed to load incident detail', 'error');
            return;
        }
        const data = await res.json();
        const inc = data.incident;

        document.getElementById('modalIncidentId').textContent = inc.incident_id;
        document.getElementById('modalSeverity').innerHTML = getSeverityBadge(inc.severity);
        document.getElementById('modalThreatScore').textContent = `${inc.threat_score}/100`;
        document.getElementById('modalEventType').textContent = inc.event_type;
        document.getElementById('modalStatus').textContent = inc.status;
        document.getElementById('modalPrimaryReason').textContent = inc.primary_reason;

        // Reasons list
        const reasonsList = document.getElementById('modalReasonsList');
        reasonsList.innerHTML = (inc.reasons || []).map(r => `<li>${r}</li>`).join('');

        // Formula breakdown
        const formulaEl = document.getElementById('modalFormula');
        const breakdown = inc.details ? inc.details.breakdown : null;
        if (breakdown && breakdown.formula_string) {
            formulaEl.textContent = breakdown.formula_string;
        } else {
            formulaEl.textContent = `Threat Score: ${inc.threat_score}/100 (Heuristic calculation logged)`;
        }

        // ML Vector
        const mlEl = document.getElementById('modalMLVector');
        const mlResult = inc.details ? inc.details.ml_result : null;
        if (mlResult && mlResult.enabled) {
            mlEl.textContent = JSON.stringify({
                prediction: mlResult.prediction,
                confidence: `${mlResult.confidence}%`,
                features_evaluated: mlResult.feature_vector,
                top_contributing_features: mlResult.top_features
            }, null, 2);
        } else {
            mlEl.textContent = 'ML telemetry disabled or benign heuristic evaluation only.';
        }

        if (!incidentModalInstance) {
            incidentModalInstance = new bootstrap.Modal(document.getElementById('incidentDetailModal'));
        }
        incidentModalInstance.show();

    } catch (e) {
        showToast('Error opening modal: ' + e.message, 'error');
    }
}

async function changeStatusFromModal(newStatus) {
    if (!activeModalIncidentId) return;
    try {
        const res = await fetch(`/api/incidents/${activeModalIncidentId}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Status updated to ${newStatus}`, 'success');
            document.getElementById('modalStatus').textContent = newStatus;
            fetchIncidents();
        }
    } catch (e) {
        showToast('Error updating status: ' + e.message, 'error');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    fetchIncidents();
});
