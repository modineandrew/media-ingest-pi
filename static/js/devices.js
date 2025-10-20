// Devices page JavaScript

let currentDeviceId = null;

// Initialize devices page
document.addEventListener('DOMContentLoaded', function() {
    loadDevices();
    
    // Check if we should create a device from detected device
    const createFromDevice = sessionStorage.getItem('createDeviceFrom');
    if (createFromDevice) {
        try {
            const deviceInfo = JSON.parse(createFromDevice);
            sessionStorage.removeItem('createDeviceFrom');
            showAddDeviceModalWithInfo(deviceInfo);
        } catch (error) {
            console.error('Error parsing device info:', error);
        }
    }
});

// Load all devices
async function loadDevices() {
    try {
        const data = await apiGet('/api/devices');
        const container = document.getElementById('devices-container');
        
        if (data.devices.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📱</div>
                    <p>No device profiles configured</p>
                    <button class="btn btn-primary mt-2" onclick="showAddDeviceModal()">Add Your First Device</button>
                </div>
            `;
            return;
        }
        
        container.innerHTML = `<div class="grid grid-2">` + 
            data.devices.map(device => `
                <div class="card">
                    <div class="flex flex-between flex-center mb-2">
                        <h3>${device.name}</h3>
                        <label class="toggle">
                            <input type="checkbox" ${device.enabled ? 'checked' : ''} 
                                   onchange="toggleDevice('${device.id}', this.checked)">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    
                    <div class="mb-2">
                        <small class="text-secondary">
                            <strong>Drop Location:</strong><br>
                            ${device.drop_location || 'Default'}
                        </small>
                    </div>
                    
                    <div class="mb-2">
                        <small class="text-secondary">
                            <strong>File Types:</strong><br>
                            ${(device.file_types || []).join(', ') || 'All files'}
                        </small>
                    </div>
                    
                    <div class="flex gap-1 mb-2">
                        ${device.auto_ingest ? '<span class="badge badge-info">Auto-ingest</span>' : ''}
                        ${device.delete_after ? '<span class="badge badge-warning">Delete after</span>' : ''}
                    </div>
                    
                    <div class="flex gap-1">
                        <button class="btn btn-sm btn-primary" onclick="editDevice('${device.id}')">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteDevice('${device.id}', '${device.name}')">Delete</button>
                    </div>
                </div>
            `).join('') + `</div>`;
    } catch (error) {
        console.error('Error loading devices:', error);
    }
}

// Show add device modal
function showAddDeviceModal() {
    currentDeviceId = null;
    document.getElementById('modal-title').textContent = 'Add Device';
    document.getElementById('device-form').reset();
    document.getElementById('device-id').value = '';
    document.getElementById('device-naming-pattern').value = '{date}_{device}_{counter:04d}{ext}';
    document.getElementById('device-modal').classList.add('active');
}

// Show add device modal with pre-filled info from detected device
function showAddDeviceModalWithInfo(deviceInfo) {
    currentDeviceId = null;
    document.getElementById('modal-title').textContent = 'Create Profile for Detected Device';
    document.getElementById('device-form').reset();
    document.getElementById('device-id').value = '';
    
    // Pre-fill with detected device info
    const suggestedName = deviceInfo.label || deviceInfo.vendor || 'New Device';
    document.getElementById('device-name').value = suggestedName;
    document.getElementById('device-naming-pattern').value = '{original}';
    
    // Set identifiers
    if (deviceInfo.uuid) {
        document.getElementById('device-uuid').value = deviceInfo.uuid;
    }
    if (deviceInfo.label) {
        document.getElementById('device-label').value = deviceInfo.label;
    }
    if (deviceInfo.vendor) {
        document.getElementById('device-vendor').value = deviceInfo.vendor;
    }
    
    // Default settings
    document.getElementById('device-auto-ingest').checked = true;
    document.getElementById('device-preserve-structure').checked = true;
    document.getElementById('device-delete-after').checked = false;
    document.getElementById('device-enabled').checked = true;
    
    // Open modal
    document.getElementById('device-modal').classList.add('active');
    
    // Show a helpful message
    showToast('Fill in the drop location and save to configure this device', 'info');
}

// Edit device
async function editDevice(deviceId) {
    try {
        const device = await apiGet(`/api/devices/${deviceId}`);
        
        currentDeviceId = deviceId;
        document.getElementById('modal-title').textContent = 'Edit Device';
        document.getElementById('device-id').value = device.id;
        document.getElementById('device-name').value = device.name;
        document.getElementById('device-drop-location').value = device.drop_location || '';
        document.getElementById('device-file-types').value = (device.file_types || []).join(', ');
        document.getElementById('device-naming-pattern').value = device.naming_pattern || '{date}_{device}_{counter:04d}{ext}';
        
        const identifiers = device.identifiers || {};
        document.getElementById('device-uuid').value = identifiers.uuid || '';
        document.getElementById('device-label').value = identifiers.label || '';
        document.getElementById('device-vendor').value = identifiers.vendor || '';
        
        document.getElementById('device-auto-ingest').checked = device.auto_ingest !== false;
        document.getElementById('device-preserve-structure').checked = device.preserve_structure !== false;
        document.getElementById('device-delete-after').checked = device.delete_after === true;
        document.getElementById('device-enabled').checked = device.enabled !== false;
        
        document.getElementById('device-modal').classList.add('active');
    } catch (error) {
        console.error('Error loading device:', error);
        showNotification('Error loading device', 'error');
    }
}

// Close device modal
function closeDeviceModal() {
    document.getElementById('device-modal').classList.remove('active');
    currentDeviceId = null;
}

// Save device
async function saveDevice(event) {
    event.preventDefault();
    
    const fileTypesStr = document.getElementById('device-file-types').value;
    const fileTypes = fileTypesStr ? fileTypesStr.split(',').map(s => s.trim()).filter(s => s) : [];
    
    const deviceData = {
        name: document.getElementById('device-name').value,
        drop_location: document.getElementById('device-drop-location').value,
        file_types: fileTypes,
        naming_pattern: document.getElementById('device-naming-pattern').value,
        identifiers: {
            uuid: document.getElementById('device-uuid').value || undefined,
            label: document.getElementById('device-label').value || undefined,
            vendor: document.getElementById('device-vendor').value || undefined
        },
        auto_ingest: document.getElementById('device-auto-ingest').checked,
        preserve_structure: document.getElementById('device-preserve-structure').checked,
        delete_after: document.getElementById('device-delete-after').checked,
        enabled: document.getElementById('device-enabled').checked
    };
    
    // Remove empty identifiers
    Object.keys(deviceData.identifiers).forEach(key => {
        if (!deviceData.identifiers[key]) {
            delete deviceData.identifiers[key];
        }
    });
    
    try {
        if (currentDeviceId) {
            // Update existing device
            await apiPut(`/api/devices/${currentDeviceId}`, deviceData);
            showNotification('Device updated successfully');
        } else {
            // Create new device
            await apiPost('/api/devices', deviceData);
            showNotification('Device created successfully');
        }
        
        closeDeviceModal();
        loadDevices();
    } catch (error) {
        console.error('Error saving device:', error);
        showNotification('Error saving device', 'error');
    }
}

// Toggle device enabled/disabled
async function toggleDevice(deviceId, enabled) {
    try {
        await apiPut(`/api/devices/${deviceId}`, { enabled });
    } catch (error) {
        console.error('Error toggling device:', error);
        showNotification('Error updating device', 'error');
        loadDevices();
    }
}

// Delete device
async function deleteDevice(deviceId, deviceName) {
    if (!confirm(`Are you sure you want to delete the device "${deviceName}"?`)) {
        return;
    }
    
    try {
        await apiDelete(`/api/devices/${deviceId}`);
        showNotification('Device deleted successfully');
        loadDevices();
    } catch (error) {
        console.error('Error deleting device:', error);
        showNotification('Error deleting device', 'error');
    }
}

// Close modal on background click
document.getElementById('device-modal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeDeviceModal();
    }
});

// Handle WebSocket device events
window.handleDeviceDetected = function(device) {
    const label = device.label || device.device_node || 'Unknown device';
    showToast(`Device detected: ${label}. Click "Create Profile" to configure it.`, 'info');
};

window.handleDeviceRemoved = function(device) {
    const label = device.label || device.device_node || 'Unknown device';
    showToast(`Device removed: ${label}`, 'info');
};

