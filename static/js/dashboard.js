// Dashboard page JavaScript

let refreshInterval = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
    
    // Refresh every 5 seconds
    refreshInterval = setInterval(loadDashboard, 5000);
});

// Load all dashboard data
async function loadDashboard() {
    await Promise.all([
        loadSystemInfo(),
        loadStatistics(),
        loadActiveTransfers(),
        loadMountedDevices(),
        loadRecentTransfers()
    ]);
}

// Load system info
async function loadSystemInfo() {
    try {
        const data = await apiGet('/api/system-info');
        
        document.getElementById('stat-active-transfers').textContent = data.active_transfers;
        document.getElementById('stat-mounted-devices').textContent = data.mounted_devices;
    } catch (error) {
        console.error('Error loading system info:', error);
    }
}

// Load statistics
async function loadStatistics() {
    try {
        const data = await apiGet('/api/statistics');
        
        document.getElementById('stat-total-transfers').textContent = data.total_transfers;
        document.getElementById('stat-files-transferred').textContent = 
            data.total_files_transferred.toLocaleString();
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Load active transfers
async function loadActiveTransfers() {
    try {
        const data = await apiGet('/api/transfers/active');
        const container = document.getElementById('active-transfers-container');
        
        if (data.transfers.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">⏳</div>
                    <p>No active transfers</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = data.transfers.map(transfer => {
            const percentComplete = transfer.total_files > 0 ? (transfer.files_transferred / transfer.total_files * 100) : 0;
            const totalSizeMB = (transfer.total_size_bytes / (1024 * 1024)).toFixed(1);
            const transferredMB = (transfer.bytes_transferred / (1024 * 1024)).toFixed(1);
            const speed = transfer.transfer_speed_mbps || 0;
            
            return `
                <div class="card mb-2">
                    <div class="flex flex-between flex-center mb-1">
                        <strong>${transfer.device_name}</strong>
                        <div class="flex gap-1">
                            ${getStatusBadge(transfer.status)}
                            <button class="btn btn-sm btn-danger" onclick="cancelTransfer('${transfer.transfer_id}')" title="Cancel transfer">✕</button>
                        </div>
                    </div>
                    <div class="flex flex-between mb-1">
                        <small>${transfer.files_transferred} / ${transfer.total_files} files</small>
                        <small>${transferredMB} / ${totalSizeMB} MB ${speed > 0 ? `(${speed} MB/s)` : ''}</small>
                    </div>
                    <div class="progress">
                        <div class="progress-bar" style="width: ${percentComplete}%"></div>
                    </div>
                    <div class="flex flex-between mt-1">
                        <small class="text-secondary">${transfer.current_file || 'Processing...'}</small>
                        <div class="flex gap-1">
                            ${transfer.files_failed > 0 ? `<small class="text-danger">${transfer.files_failed} failed</small>` : ''}
                            ${transfer.files_skipped > 0 ? `<small class="text-warning">${transfer.files_skipped} deleted</small>` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading active transfers:', error);
    }
}

// Load mounted devices
async function loadMountedDevices() {
    try {
        const data = await apiGet('/api/mounted-devices');
        const devicesData = await apiGet('/api/devices');
        const container = document.getElementById('mounted-devices-container');
        
        if (data.devices.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">💾</div>
                    <p>No devices mounted</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = data.devices.map(device => {
            // Backend provides the matched profile (single source of truth)
            const profile = device.matched_profile;
            
            return `
                <div class="card mb-2">
                    <div class="flex flex-between flex-center">
                        <div class="flex-grow">
                            <div class="flex flex-center gap-2 mb-1">
                                <strong>${device.label || device.device_node}</strong>
                                ${profile ? `
                                    <span class="badge badge-success">✓ Configured</span>
                                    ${profile.auto_ingest ? '<span class="badge badge-info">Auto-ingest</span>' : ''}
                                ` : '<span class="badge badge-warning">⚠ Unconfigured</span>'}
                            </div>
                            <small class="text-secondary">
                                ${device.vendor || 'Unknown'} ${device.model ? '- ' + device.model : ''} - ${formatBytes(device.size_bytes)}
                            </small>
                            ${device.uuid ? `<br><small class="text-secondary">UUID: ${device.uuid}</small>` : ''}
                        </div>
                        <div class="flex gap-1">
                            ${profile ? `
                                ${!profile.auto_ingest ? 
                                    `<button class="btn btn-sm btn-primary" onclick="triggerIngest('${profile.id}', '${device.device_node}')">Start Transfer</button>` : 
                                    ''
                                }
                            ` : `
                                <button class="btn btn-sm btn-success" onclick="createProfileFromDevice(${JSON.stringify(device).replace(/"/g, '&quot;')})">
                                    + Create Profile
                                </button>
                            `}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading mounted devices:', error);
        document.getElementById('mounted-devices-container').innerHTML = 
            '<div class="empty-state"><p>Error loading devices</p></div>';
    }
}

// Load recent transfers
async function loadRecentTransfers() {
    try {
        const data = await apiGet('/api/transfers/recent?hours=24');
        const tbody = document.getElementById('recent-transfers-body');
        
        if (data.transfers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">No recent transfers</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.transfers.map(transfer => `
            <tr>
                <td>${transfer.device_name}</td>
                <td>${getStatusBadge(transfer.status)}</td>
                <td>${transfer.files_transferred} / ${transfer.total_files}</td>
                <td>${formatRelativeTime(transfer.started_at)}</td>
                <td>${formatDuration(transfer.duration_seconds)}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading recent transfers:', error);
    }
}

// Refresh mounted devices
function refreshMountedDevices() {
    loadMountedDevices();
}

// Trigger manual ingest
async function triggerIngest(deviceId, deviceNode) {
    try {
        const data = await apiPost('/api/trigger-ingest', {
            device_id: deviceId,
            device_node: deviceNode
        });
        
        showNotification('Transfer started!');
        setTimeout(loadDashboard, 1000);
    } catch (error) {
        console.error('Error triggering ingest:', error);
        showNotification('Error starting transfer', 'error');
    }
}

// Cancel a transfer
async function cancelTransfer(transferId) {
    if (!confirm('Are you sure you want to cancel this transfer?')) {
        return;
    }
    
    try {
        await apiPost(`/api/transfers/${transferId}/cancel`, {});
        showToast('Transfer cancelled', 'success');
        setTimeout(loadDashboard, 500);
    } catch (error) {
        console.error('Error cancelling transfer:', error);
        showToast('Error cancelling transfer', 'error');
    }
}

// Handle WebSocket transfer updates
window.handleTransferUpdate = function(transfer) {
    loadActiveTransfers();
    loadSystemInfo();
};

// Create profile from detected device
function createProfileFromDevice(device) {
    // Store device info in sessionStorage for the devices page to pick up
    sessionStorage.setItem('createDeviceFrom', JSON.stringify(device));
    // Navigate to devices page
    window.location.href = '/devices';
}

// Handle WebSocket device events
window.handleDeviceDetected = function(device) {
    loadMountedDevices();
    loadSystemInfo();
    showToast(`Device detected: ${device.label || device.device_node}`, 'info');
};

window.handleDeviceRemoved = function(device) {
    loadMountedDevices();
    loadSystemInfo();
    showToast(`Device removed: ${device.label || device.device_node}`, 'info');
};

