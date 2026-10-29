/**
 * File Monitoring JavaScript module.
 */

let defaultSandboxPath = '';

// Validate path asynchronously
async function validatePathInput(path) {
    const feedback = document.getElementById('pathValidationFeedback');
    if (!path.trim()) {
        feedback.textContent = 'Path cannot be empty.';
        feedback.className = 'small mt-1 text-danger';
        return false;
    }

    try {
        const res = await fetch('/api/monitoring/validate-path', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ directory_path: path })
        });
        const data = await res.json();
        if (data.is_valid) {
            feedback.innerHTML = '<span class="text-success"><i class="bi bi-check-circle me-1"></i>Path verified & safe for monitoring.</span>';
            return true;
        } else {
            feedback.innerHTML = `<span class="text-danger"><i class="bi bi-x-circle me-1"></i>${data.message}</span>`;
            return false;
        }
    } catch (e) {
        feedback.textContent = 'Validation error: ' + e.message;
        feedback.className = 'small mt-1 text-warning';
        return false;
    }
}

function useDefaultSandboxPath() {
    if (defaultSandboxPath) {
        document.getElementById('monitoredPathInput').value = defaultSandboxPath;
        validatePathInput(defaultSandboxPath);
    }
}

// Start monitoring
async function startMonitoring() {
    const path = document.getElementById('monitoredPathInput').value.trim();
    try {
        const res = await fetch('/api/monitoring/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ directory_path: path })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'error');
        }
    } catch (e) {
        showToast('Error starting monitor: ' + e.message, 'error');
    }
}

// Stop monitoring
async function stopMonitoring() {
    try {
        const res = await fetch('/api/monitoring/stop', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'warn');
        } else {
            showToast(data.message, 'error');
        }
    } catch (e) {
        showToast('Error stopping monitor: ' + e.message, 'error');
    }
}

// Poll monitoring telemetry
async function pollMonitoringStatus() {
    try {
        const res = await fetch('/api/monitoring/status');
        if (!res.ok) return;
        const data = await res.json();

        defaultSandboxPath = data.default_sandbox_path || '';
        const input = document.getElementById('monitoredPathInput');
        if (!input.value && defaultSandboxPath) {
            input.value = defaultSandboxPath;
            validatePathInput(defaultSandboxPath);
        }

        // Status badge
        const badge = document.getElementById('monitorStatusBadge');
        const btnStart = document.getElementById('btnStartMonitor');
        const btnStop = document.getElementById('btnStopMonitor');

        if (data.is_monitoring) {
            badge.textContent = 'ACTIVE MONITORING';
            badge.className = 'badge bg-success';
            btnStart.disabled = true;
            btnStop.disabled = false;
        } else {
            badge.textContent = 'INACTIVE';
            badge.className = 'badge bg-secondary';
            btnStart.disabled = false;
            btnStop.disabled = true;
        }

        document.getElementById('monitorEventCount').textContent = data.event_count || 0;
        document.getElementById('monitorUptime').textContent = `${data.uptime_seconds || 0}s`;
        document.getElementById('activeMonitoredPathDisplay').textContent = data.is_monitoring ? data.monitored_path : 'None (Stopped)';

        // Events Table
        const tbody = document.getElementById('monitorEventsTableBody');
        if (tbody && data.recent_events) {
            if (data.recent_events.length === 0) {
                if (data.is_monitoring) {
                    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-info py-4"><span class="spinner-border spinner-border-sm me-2"></span>Observer active: Listening for file operations...</td></tr>';
                }
            } else {
                tbody.innerHTML = data.recent_events.slice().reverse().map(ev => {
                    let typeBadge = `<span class="badge bg-secondary">${ev.event_type}</span>`;
                    if (ev.event_type === 'CREATE') typeBadge = '<span class="badge bg-primary">CREATE</span>';
                    else if (ev.event_type === 'MODIFY') typeBadge = '<span class="badge bg-warning text-dark">MODIFY</span>';
                    else if (ev.event_type === 'RENAME') typeBadge = '<span class="badge bg-info text-dark">RENAME</span>';
                    else if (ev.event_type === 'DELETE') typeBadge = '<span class="badge bg-danger">DELETE</span>';

                    const details = ev.old_name ? `From: <code class="text-muted">${ev.old_name}</code>` : `<code class="text-muted">${ev.path}</code>`;

                    return `
                        <tr>
                            <td class="text-muted small">${ev.timestamp}</td>
                            <td>${typeBadge}</td>
                            <td class="fw-semibold text-light">${ev.file_name}</td>
                            <td class="small text-truncate" style="max-width: 250px;">${details}</td>
                        </tr>
                    `;
                }).join('');
            }
        }
    } catch (e) {
        console.warn('Monitoring poll error:', e);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('monitoredPathInput');
    if (input) {
        input.addEventListener('input', (e) => validatePathInput(e.target.value));
    }
    pollMonitoringStatus();
    setInterval(pollMonitoringStatus, 1500);
});
