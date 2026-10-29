/**
 * Settings and AI Diagnostics JavaScript logic.
 */

async function loadSettings() {
    try {
        const res = await fetch('/api/settings');
        if (!res.ok) return;
        const cfg = await res.json();

        document.getElementById('cfgBurstWindow').value = cfg.burst_window_seconds || 5.0;
        document.getElementById('cfgRenameThreshold').value = cfg.rename_threshold || 4;
        document.getElementById('cfgModThreshold').value = cfg.modification_threshold || 6;
        document.getElementById('cfgVelocityThreshold').value = cfg.total_event_threshold || 10;

        document.getElementById('cfgRenameWeight').value = cfg.rename_weight || 35.0;
        document.getElementById('cfgExtWeight').value = cfg.extension_weight || 40.0;
        document.getElementById('cfgBurstWeight').value = cfg.burst_weight || 25.0;

        const exts = Array.isArray(cfg.suspicious_extensions) ? cfg.suspicious_extensions.join(', ') : (cfg.suspicious_extensions || '');
        document.getElementById('cfgSuspiciousExts').value = exts;

        document.getElementById('cfgMLEnabled').checked = !!cfg.ml_enabled;
        document.getElementById('cfgAutoMitigate').checked = !!cfg.auto_mitigate_on_critical;

        // ML Diagnostics
        if (cfg.ml_model_status) {
            document.getElementById('mlSampleCount').textContent = cfg.ml_model_status.sample_count || '1,500';
            const fList = document.getElementById('mlFeatureImportanceList');
            const imps = cfg.ml_model_status.feature_importances || {};
            fList.innerHTML = Object.entries(imps).map(([feat, pct]) => `
                <div>
                    <div class="d-flex justify-content-between text-muted mb-1">
                        <code>${feat}</code>
                        <span class="text-info fw-bold">${pct}%</span>
                    </div>
                    <div class="progress" style="height: 6px; background-color: #0b1120;">
                        <div class="progress-bar bg-info" style="width: ${pct}%"></div>
                    </div>
                </div>
            `).join('');
        }
    } catch (e) {
        console.warn('Error loading settings:', e);
    }
}

async function saveSettings(e) {
    e.preventDefault();
    const payload = {
        burst_window_seconds: parseFloat(document.getElementById('cfgBurstWindow').value),
        rename_threshold: parseInt(document.getElementById('cfgRenameThreshold').value),
        modification_threshold: parseInt(document.getElementById('cfgModThreshold').value),
        total_event_threshold: parseInt(document.getElementById('cfgVelocityThreshold').value),
        rename_weight: parseFloat(document.getElementById('cfgRenameWeight').value),
        extension_weight: parseFloat(document.getElementById('cfgExtWeight').value),
        burst_weight: parseFloat(document.getElementById('cfgBurstWeight').value),
        suspicious_extensions: document.getElementById('cfgSuspiciousExts').value,
        ml_enabled: document.getElementById('cfgMLEnabled').checked,
        auto_mitigate_on_critical: document.getElementById('cfgAutoMitigate').checked
    };

    try {
        const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
        } else {
            showToast(data.error || 'Failed to save settings', 'error');
        }
    } catch (err) {
        showToast('Error saving settings: ' + err.message, 'error');
    }
}

async function resetToDefaults() {
    if (!confirm('Reset all detection parameters to faculty demonstration defaults?')) return;
    try {
        const res = await fetch('/api/settings/reset', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            loadSettings();
        }
    } catch (err) {
        showToast('Error: ' + err.message, 'error');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
});
