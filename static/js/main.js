/**
 * Global JavaScript helper functions for Ransomware Detection Simulator.
 */

// Toast notification helper
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;

    const bgClass = {
        'success': 'bg-success text-white',
        'error': 'bg-danger text-white',
        'warn': 'bg-warning text-dark',
        'info': 'bg-info text-dark'
    }[type] || 'bg-primary text-white';

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center ${bgClass} border-0 shadow-lg`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body fw-semibold">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toastEl);
    const bsToast = new bootstrap.Toast(toastEl, { delay: 4000 });
    bsToast.show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

// Format severity badges
function getSeverityBadge(severity) {
    const s = (severity || 'LOW').toUpperCase();
    const map = {
        'LOW': '<span class="badge badge-low px-2 py-1"><i class="bi bi-shield-check me-1"></i>LOW</span>',
        'MEDIUM': '<span class="badge badge-medium px-2 py-1"><i class="bi bi-shield-exclamation me-1"></i>MEDIUM</span>',
        'HIGH': '<span class="badge badge-high px-2 py-1"><i class="bi bi-exclamation-triangle me-1"></i>HIGH</span>',
        'CRITICAL': '<span class="badge badge-critical px-2 py-1"><i class="bi bi-radioactive me-1"></i>CRITICAL</span>'
    };
    return map[s] || `<span class="badge bg-secondary">${s}</span>`;
}

// Global quick status updater for header badges
async function refreshGlobalSystemPills() {
    try {
        const res = await fetch('/api/dashboard/stats');
        if (!res.ok) return;
        const data = await res.json();

        // Update active monitor badge
        const monPill = document.getElementById('globalMonitorStatus');
        if (monPill) {
            if (data.monitoring_active) {
                monPill.innerHTML = '<span class="status-indicator online me-1"></span> Live Monitor Active';
                monPill.className = 'badge bg-success-subtle text-success border border-success';
            } else {
                monPill.innerHTML = '<span class="status-indicator offline me-1"></span> Monitor Inactive';
                monPill.className = 'badge bg-secondary-subtle text-muted border border-secondary';
            }
        }

        // Update simulation status badge
        const simPill = document.getElementById('globalSimulatorStatus');
        if (simPill) {
            const state = data.simulator_state || 'IDLE';
            if (state === 'RUNNING') {
                simPill.innerHTML = '<span class="status-indicator alert me-1"></span> Sim Active';
                simPill.className = 'badge bg-warning-subtle text-warning border border-warning';
            } else if (state === 'PAUSED') {
                simPill.innerHTML = '<span class="status-indicator busy me-1"></span> Sim Paused';
                simPill.className = 'badge bg-info-subtle text-info border border-info';
            } else {
                simPill.innerHTML = '<span class="status-indicator offline me-1"></span> Sim Idle';
                simPill.className = 'badge bg-secondary-subtle text-muted border border-secondary';
            }
        }
    } catch (e) {
        console.warn('Status poll warning:', e);
    }
}

// Start polling for top navbar status
document.addEventListener('DOMContentLoaded', () => {
    refreshGlobalSystemPills();
    setInterval(refreshGlobalSystemPills, 3000);
});
