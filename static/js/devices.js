// Devices page JavaScript - V2 with transfer rules support

let currentDeviceId = null;
let transferRules = [];  // Current editing transfer rules
let ruleCounter = 0;

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
            data.devices.map(device => {
                const rules = device.transfer_rules || [];
                const rulesText = rules.length > 0 
                    ? `${rules.length} transfer rule${rules.length !== 1 ? 's' : ''}`
                    : 'No transfer rules';
                
                return `
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
                            <strong>Transfer Rules:</strong><br>
                            ${rulesText}
                        </small>
                    </div>
                    
                    ${rules.length > 0 ? `
                        <div class="mb-2">
                            <small class="text-secondary">
                                ${rules.map(r => `• ${r.name}: ${r.drop_location || 'Not set'}`).slice(0, 2).join('<br>')}
                                ${rules.length > 2 ? `<br>• ... and ${rules.length - 2} more` : ''}
                            </small>
                        </div>
                    ` : ''}
                    
                    <div class="flex gap-1 mb-2">
                        ${device.auto_ingest ? '<span class="badge badge-info">Auto-ingest</span>' : ''}
                    </div>
                    
                    <div class="flex gap-1">
                        <button class="btn btn-sm btn-primary" onclick="editDevice('${device.id}')">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteDevice('${device.id}', '${device.name}')">Delete</button>
                    </div>
                </div>
                `;
            }).join('') + `</div>`;
    } catch (error) {
        console.error('Error loading devices:', error);
    }
}

// Show add device modal
function showAddDeviceModal() {
    currentDeviceId = null;
    transferRules = [];
    ruleCounter = 0;
    
    document.getElementById('modal-title').textContent = 'Add Device';
    document.getElementById('device-form').reset();
    document.getElementById('device-id').value = '';
    document.getElementById('device-auto-ingest').checked = true;
    document.getElementById('device-enabled').checked = true;
    
    // Add one default transfer rule
    addTransferRule();
    
    switchTab('basic');
    document.getElementById('device-modal').classList.add('active');
}

// Show add device modal with pre-filled info from detected device
function showAddDeviceModalWithInfo(deviceInfo) {
    currentDeviceId = null;
    transferRules = [];
    ruleCounter = 0;
    
    document.getElementById('modal-title').textContent = 'Create Profile for Detected Device';
    document.getElementById('device-form').reset();
    document.getElementById('device-id').value = '';
    
    // Pre-fill with detected device info
    const suggestedName = deviceInfo.label || deviceInfo.vendor || 'New Device';
    document.getElementById('device-name').value = suggestedName;
    
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
    document.getElementById('device-enabled').checked = true;
    
    // Add one default transfer rule
    addTransferRule();
    
    // Open modal
    switchTab('basic');
    document.getElementById('device-modal').classList.add('active');
    
    // Show a helpful message
    showToast('Fill in the transfer rules and save to configure this device', 'info');
}

// Edit device
async function editDevice(deviceId) {
    try {
        const device = await apiGet(`/api/devices/${deviceId}`);
        
        currentDeviceId = deviceId;
        transferRules = [];
        ruleCounter = 0;
        
        document.getElementById('modal-title').textContent = 'Edit Device';
        document.getElementById('device-id').value = device.id;
        document.getElementById('device-name').value = device.name;
        
        const identifiers = device.identifiers || {};
        document.getElementById('device-uuid').value = identifiers.uuid || '';
        document.getElementById('device-label').value = identifiers.label || '';
        document.getElementById('device-vendor').value = identifiers.vendor || '';
        
        document.getElementById('device-auto-ingest').checked = device.auto_ingest !== false;
        document.getElementById('device-enabled').checked = device.enabled !== false;
        
        // Load transfer rules
        const rules = device.transfer_rules || [];
        if (rules.length === 0) {
            // Add one default rule if none exist
            addTransferRule();
        } else {
            // Load existing rules
            rules.forEach(rule => {
                addTransferRule(rule);
            });
        }
        
        switchTab('basic');
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
    transferRules = [];
    ruleCounter = 0;
}

// Switch between tabs
function switchTab(tabName) {
    // Update tab headers
    document.querySelectorAll('.tab-header').forEach(header => {
        header.classList.remove('active');
        if (header.dataset.tab === tabName) {
            header.classList.add('active');
        }
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
        if (content.id === `tab-${tabName}`) {
            content.classList.add('active');
        }
    });
}

// Add a new transfer rule
function addTransferRule(existingRule = null) {
    const ruleId = existingRule ? existingRule.id : `rule_temp_${ruleCounter++}`;
    const ruleName = existingRule ? existingRule.name : `Rule ${transferRules.length + 1}`;
    
    const rule = existingRule || {
        id: ruleId,
        name: ruleName,
        drop_location: '',
        file_types: [],
        source_path_patterns: [],
        filename_patterns: [],
        naming_pattern: '{original}{ext}',
        preserve_structure: true,
        delete_after: false
    };
    
    transferRules.push(rule);
    renderTransferRules();
    
    // Switch to the new rule tab
    switchTab(ruleId);
}

// Render all transfer rules
function renderTransferRules() {
    const tabHeaders = document.getElementById('tab-headers');
    const rulesContainer = document.getElementById('transfer-rules-container');
    
    // Clear existing rule tabs (keep basic tab)
    const basicTab = tabHeaders.querySelector('[data-tab="basic"]');
    tabHeaders.innerHTML = '';
    tabHeaders.appendChild(basicTab);
    rulesContainer.innerHTML = '';
    
    // Add tabs for each rule
    transferRules.forEach((rule, index) => {
        // Add tab header
        const tabHeader = document.createElement('button');
        tabHeader.type = 'button';
        tabHeader.className = 'tab-header';
        tabHeader.dataset.tab = rule.id;
        tabHeader.textContent = rule.name || `Rule ${index + 1}`;
        tabHeader.onclick = () => switchTab(rule.id);
        tabHeaders.appendChild(tabHeader);
        
        // Add tab content
        const tabContent = createRuleTabContent(rule, index);
        rulesContainer.appendChild(tabContent);
    });
}

// Create tab content for a transfer rule
function createRuleTabContent(rule, index) {
    const div = document.createElement('div');
    div.className = 'tab-content';
    div.id = `tab-${rule.id}`;
    
    div.innerHTML = `
        <div class="form-group">
            <label class="form-label">Rule Name *</label>
            <input type="text" class="form-input rule-name" value="${rule.name || ''}" 
                   data-rule-index="${index}" oninput="updateRuleName(${index}, this.value)">
        </div>
        
        <div class="form-group">
            <label class="form-label">Drop Location *</label>
            <input type="text" class="form-input rule-drop-location" value="${rule.drop_location || ''}"
                   data-rule-index="${index}" placeholder="/mnt/nas/photos">
            <small class="text-secondary">Where files matching this rule will be saved</small>
        </div>
        
        <div class="form-group">
            <label class="form-label">File Types</label>
            <div class="chip-input-container" id="file-types-${index}" onclick="focusChipInput('file-types-${index}')">
                ${createChips(rule.file_types || [], 'file-types', index)}
                <input type="text" placeholder="e.g., .jpg, .mp4" 
                       onkeydown="handleChipInput(event, 'file-types', ${index})">
            </div>
            <small class="text-secondary">Press Enter after each extension. Leave empty or use * for all files</small>
        </div>
        
        <div class="form-group">
            <label class="form-label">Source Path Patterns (optional)</label>
            <div class="chip-input-container" id="source-patterns-${index}" onclick="focusChipInput('source-patterns-${index}')">
                ${createChips(rule.source_path_patterns || [], 'source-patterns', index)}
                <input type="text" placeholder="e.g., **/DCIM/**, **/PANO/**" 
                       onkeydown="handleChipInput(event, 'source-patterns', ${index})">
            </div>
            <small class="text-secondary">Only transfer files from paths matching these patterns (glob format)</small>
        </div>
        
        <div class="form-group">
            <label class="form-label">Filename Patterns (optional)</label>
            <div class="chip-input-container" id="filename-patterns-${index}" onclick="focusChipInput('filename-patterns-${index}')">
                ${createChips(rule.filename_patterns || [], 'filename-patterns', index)}
                <input type="text" placeholder="e.g., IMG_*, *_PANO_*" 
                       onkeydown="handleChipInput(event, 'filename-patterns', ${index})">
            </div>
            <small class="text-secondary">Only transfer files with names matching these patterns (glob format)</small>
        </div>
        
        <div class="form-group">
            <label class="form-label">Naming Pattern</label>
            <input type="text" class="form-input rule-naming-pattern" value="${rule.naming_pattern || '{original}{ext}'}"
                   data-rule-index="${index}">
            <small class="text-secondary">Variables: {date}, {datetime}, {device}, {counter:04d}, {original}, {ext}</small>
        </div>
        
        <div class="form-group">
            <label class="form-label">
                <input type="checkbox" class="form-checkbox rule-preserve-structure" 
                       data-rule-index="${index}" ${rule.preserve_structure !== false ? 'checked' : ''}>
                Preserve directory structure
            </label>
            <small class="text-secondary">Keep folder structure or flatten all files to destination</small>
        </div>
        
        <div class="form-group">
            <label class="form-label">
                <input type="checkbox" class="form-checkbox rule-delete-after" 
                       data-rule-index="${index}" ${rule.delete_after === true ? 'checked' : ''}>
                Delete source files after successful transfer
            </label>
        </div>
        
        ${transferRules.length > 1 ? `
            <button type="button" class="btn btn-sm btn-danger rule-delete-btn" onclick="deleteTransferRule(${index})">
                Delete This Rule
            </button>
        ` : ''}
    `;
    
    return div;
}

// Create HTML for chips
function createChips(items, type, ruleIndex) {
    return items.map(item => `
        <span class="chip">
            ${item}
            <span class="chip-remove" onclick="removeChip('${type}', ${ruleIndex}, '${item}')">×</span>
        </span>
    `).join('');
}

// Handle chip input (Enter key)
function handleChipInput(event, type, ruleIndex) {
    if (event.key === 'Enter') {
        event.preventDefault();
        const input = event.target;
        const value = input.value.trim();
        
        if (value) {
            // Add to rule data
            const fieldName = type === 'file-types' ? 'file_types' : 
                            type === 'source-patterns' ? 'source_path_patterns' : 'filename_patterns';
            
            if (!transferRules[ruleIndex][fieldName].includes(value)) {
                transferRules[ruleIndex][fieldName].push(value);
                
                // Re-render chips
                const container = document.getElementById(`${type}-${ruleIndex}`);
                const chips = createChips(transferRules[ruleIndex][fieldName], type, ruleIndex);
                container.innerHTML = chips + container.innerHTML.substring(container.innerHTML.lastIndexOf('<input'));
            }
            
            input.value = '';
        }
    }
}

// Remove a chip
function removeChip(type, ruleIndex, value) {
    const fieldName = type === 'file-types' ? 'file_types' : 
                    type === 'source-patterns' ? 'source_path_patterns' : 'filename_patterns';
    
    const index = transferRules[ruleIndex][fieldName].indexOf(value);
    if (index > -1) {
        transferRules[ruleIndex][fieldName].splice(index, 1);
        
        // Re-render chips
        const container = document.getElementById(`${type}-${ruleIndex}`);
        const chips = createChips(transferRules[ruleIndex][fieldName], type, ruleIndex);
        container.innerHTML = chips + container.innerHTML.substring(container.innerHTML.lastIndexOf('<input'));
    }
}

// Focus chip input
function focusChipInput(containerId) {
    const container = document.getElementById(containerId);
    const input = container.querySelector('input');
    if (input) input.focus();
}

// Update rule name
function updateRuleName(ruleIndex, newName) {
    transferRules[ruleIndex].name = newName;
    
    // Update tab header text
    const tabHeader = document.querySelector(`[data-tab="${transferRules[ruleIndex].id}"]`);
    if (tabHeader) {
        tabHeader.textContent = newName || `Rule ${ruleIndex + 1}`;
    }
}

// Delete a transfer rule
function deleteTransferRule(ruleIndex) {
    if (transferRules.length === 1) {
        showNotification('Cannot delete the last transfer rule. Device must have at least one rule.', 'error');
        return;
    }
    
    if (!confirm(`Delete transfer rule "${transferRules[ruleIndex].name}"?`)) {
        return;
    }
    
    transferRules.splice(ruleIndex, 1);
    renderTransferRules();
    switchTab('basic');
}

// Save device
async function saveDevice(event) {
    event.preventDefault();
    
    // Collect basic device data
    const deviceData = {
        name: document.getElementById('device-name').value,
        identifiers: {
            uuid: document.getElementById('device-uuid').value || undefined,
            label: document.getElementById('device-label').value || undefined,
            vendor: document.getElementById('device-vendor').value || undefined
        },
        auto_ingest: document.getElementById('device-auto-ingest').checked,
        enabled: document.getElementById('device-enabled').checked,
        transfer_rules: []
    };
    
    // Remove empty identifiers
    Object.keys(deviceData.identifiers).forEach(key => {
        if (!deviceData.identifiers[key]) {
            delete deviceData.identifiers[key];
        }
    });
    
    // Collect transfer rules from form
    transferRules.forEach((rule, index) => {
        const ruleData = {
            id: rule.id,
            name: document.querySelector(`.rule-name[data-rule-index="${index}"]`).value,
            drop_location: document.querySelector(`.rule-drop-location[data-rule-index="${index}"]`).value,
            file_types: rule.file_types || [],
            source_path_patterns: rule.source_path_patterns || [],
            filename_patterns: rule.filename_patterns || [],
            naming_pattern: document.querySelector(`.rule-naming-pattern[data-rule-index="${index}"]`).value,
            preserve_structure: document.querySelector(`.rule-preserve-structure[data-rule-index="${index}"]`).checked,
            delete_after: document.querySelector(`.rule-delete-after[data-rule-index="${index}"]`).checked
        };
        
        deviceData.transfer_rules.push(ruleData);
    });
    
    // Validate at least one rule
    if (deviceData.transfer_rules.length === 0) {
        showNotification('Device must have at least one transfer rule', 'error');
        return;
    }
    
    // Validate each rule has required fields
    for (const rule of deviceData.transfer_rules) {
        if (!rule.name) {
            showNotification('All transfer rules must have a name', 'error');
            return;
        }
        if (!rule.drop_location) {
            showNotification(`Transfer rule "${rule.name}" must have a drop location`, 'error');
            return;
        }
    }
    
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
