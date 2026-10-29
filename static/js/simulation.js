/**
 * Simulation Control and Terminal Telemetry logic.
 */

let lastLogCount = 0;

function updateSpeedLabel(val) {
    document.getElementById('speedValueLabel').textContent = `${parseFloat(val).toFixed(1)}x`;
}

function clearTerminalView() {
    document.getElementById('simulationTerminal').innerHTML = '<div class="term-line-info">[TERMINAL CLEARED]</div>';
    lastLogCount = 0;
}

// Start simulation
async function startSimulation() {
    const profileRadio = document.querySelector('input[name="simProfile"]:checked');
    const profile = profileRadio ? profileRadio.value : 'benign';
    const speed = document.getElementById('speedSlider').value;

    try {
        const res = await fetch('/api/simulation/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile, speed })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'error');
        }
    } catch (e) {
        showToast('Failed to start simulation: ' + e.message, 'error');
    }
}

// Pause simulation
async function pauseSimulation() {
    try {
        const res = await fetch('/api/simulation/pause', { method: 'POST' });
        const data = await res.json();
        if (data.success) showToast(data.message, 'warn');
        else showToast(data.message, 'error');
    } catch (e) {
        showToast(e.message, 'error');
    }
}

// Resume simulation
async function resumeSimulation() {
    try {
        const res = await fetch('/api/simulation/resume', { method: 'POST' });
        const data = await res.json();
        if (data.success) showToast(data.message, 'success');
        else showToast(data.message, 'error');
    } catch (e) {
        showToast(e.message, 'error');
    }
}

// Stop simulation
async function stopSimulation() {
    try {
        const res = await fetch('/api/simulation/stop', { method: 'POST' });
        const data = await res.json();
        if (data.success) showToast(data.message, 'warn');
        else showToast(data.message, 'error');
    } catch (e) {
        showToast(e.message, 'error');
    }
}

// Reset sandbox
async function resetSimulation() {
    if (!confirm('This will wipe all dummy files inside demo_data/sandbox/ and reset the simulator. Proceed?')) {
        return;
    }
    try {
        const res = await fetch('/api/simulation/reset', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            clearTerminalView();
        } else {
            showToast(data.message, 'error');
        }
    } catch (e) {
        showToast(e.message, 'error');
    }
}

// Poll simulation status
async function pollSimulationStatus() {
    try {
        const res = await fetch('/api/simulation/status');
        if (!res.ok) return;
        const status = await res.json();

        // 1. State badge
        const badge = document.getElementById('simStateBadge');
        if (badge) {
            badge.textContent = status.state;
            if (status.state === 'RUNNING') badge.className = 'badge bg-success';
            else if (status.state === 'PAUSED') badge.className = 'badge bg-warning text-dark';
            else if (status.state === 'STOPPED') badge.className = 'badge bg-danger';
            else badge.className = 'badge bg-secondary';
        }

        // 2. Control buttons state
        const btnStart = document.getElementById('btnStart');
        const btnPause = document.getElementById('btnPause');
        const btnResume = document.getElementById('btnResume');
        const btnStop = document.getElementById('btnStop');

        if (status.state === 'RUNNING') {
            btnStart.disabled = true;
            btnPause.disabled = false;
            btnPause.classList.remove('d-none');
            btnResume.classList.add('d-none');
            btnStop.disabled = false;
        } else if (status.state === 'PAUSED') {
            btnStart.disabled = true;
            btnPause.classList.add('d-none');
            btnResume.classList.remove('d-none');
            btnStop.disabled = false;
        } else {
            btnStart.disabled = false;
            btnPause.disabled = true;
            btnPause.classList.remove('d-none');
            btnResume.classList.add('d-none');
            btnStop.disabled = true;
        }

        // 3. Progress bar
        const progressBar = document.getElementById('simProgressBar');
        const progressText = document.getElementById('progressText');
        const currentStepText = document.getElementById('currentStepText');
        const totalStepsText = document.getElementById('totalStepsText');

        if (progressBar) progressBar.style.width = `${status.progress_percent || 0}%`;
        if (progressText) progressText.textContent = `${status.progress_percent || 0}%`;
        if (currentStepText) currentStepText.textContent = status.current_step || 0;
        if (totalStepsText) totalStepsText.textContent = status.total_steps || 0;

        // 4. Update Terminal Feed
        const term = document.getElementById('simulationTerminal');
        if (term && status.logs && status.logs.length > lastLogCount) {
            const newEntries = status.logs.slice(lastLogCount);
            newEntries.forEach(log => {
                const line = document.createElement('div');
                const lvl = (log.level || 'INFO').toLowerCase();
                line.className = `term-line-${lvl}`;
                line.textContent = `[${log.timestamp}] [${log.level}] ${log.message}`;
                term.appendChild(line);
            });
            term.scrollTop = term.scrollHeight;
            lastLogCount = status.logs.length;
        }

        // 5. Update Sandbox Files
        const fileTable = document.getElementById('sandboxFilesTableBody');
        const countBadge = document.getElementById('sandboxFileCountBadge');
        if (fileTable && status.files_in_sandbox) {
            countBadge.textContent = `${status.files_in_sandbox.length} Files`;
            if (status.files_in_sandbox.length === 0) {
                fileTable.innerHTML = '<tr><td colspan="3" class="text-center text-muted py-3">Sandbox directory is currently empty.</td></tr>';
            } else {
                fileTable.innerHTML = status.files_in_sandbox.map(fname => {
                    const ext = fname.includes('.') ? '.' + fname.split('.').pop() : 'none';
                    let classBadge = '<span class="badge bg-success-subtle text-success">Benign Document</span>';
                    const suspicious = ['.locked', '.crypto', '.crypted', '.enc', '.dark', '.vault'];
                    if (suspicious.some(s => fname.endsWith(s))) {
                        classBadge = '<span class="badge badge-critical">Simulated Locked File</span>';
                    } else if (fname.includes('RESTORE') || fname.includes('README')) {
                        classBadge = '<span class="badge badge-high">Simulated Ransom Note</span>';
                    }

                    return `
                        <tr>
                            <td class="text-light fw-semibold">${fname}</td>
                            <td><code>${ext}</code></td>
                            <td>${classBadge}</td>
                        </tr>
                    `;
                }).join('');
            }
        }

    } catch (e) {
        console.warn('Simulation poll error:', e);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    pollSimulationStatus();
    setInterval(pollSimulationStatus, 1000);
});
