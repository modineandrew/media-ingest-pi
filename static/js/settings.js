// Settings page JavaScript

// Initialize settings page
document.addEventListener('DOMContentLoaded', function() {
    loadSettings();
    loadSystemInfo();
    
    // Toggle MQTT settings visibility
    document.getElementById('mqtt-enabled').addEventListener('change', function() {
        document.getElementById('mqtt-settings').style.display = this.checked ? 'block' : 'none';
    });
});

// Load settings
async function loadSettings() {
    try {
        const data = await apiGet('/api/settings');
        
        // MQTT settings
        const mqtt = data.mqtt || {};
        document.getElementById('mqtt-enabled').checked = mqtt.enabled || false;
        document.getElementById('mqtt-broker').value = mqtt.broker || '';
        document.getElementById('mqtt-port').value = mqtt.port || 1883;
        document.getElementById('mqtt-username').value = mqtt.username || '';
        document.getElementById('mqtt-password').value = mqtt.password || '';
        document.getElementById('mqtt-base-topic').value = mqtt.base_topic || 'homeassistant/media_ingest';
        
        // Default settings
        const defaults = data.defaults || {};
        document.getElementById('default-drop-location').value = defaults.drop_location || '';
        document.getElementById('default-temp-dir').value = defaults.temp_dir || '';
        document.getElementById('default-verify-checksums').checked = defaults.verify_checksums !== false;
        document.getElementById('default-concurrent-transfers').value = defaults.concurrent_transfers || 1;
        
        // Web settings
        const web = data.web || {};
        document.getElementById('web-host').value = web.host || '0.0.0.0';
        document.getElementById('web-port').value = web.port || 5000;
        
        // Toggle MQTT settings visibility
        document.getElementById('mqtt-settings').style.display = mqtt.enabled ? 'block' : 'none';
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

// Load system info
async function loadSystemInfo() {
    try {
        const data = await apiGet('/api/system-info');
        
        // MQTT status
        const mqttStatus = document.getElementById('mqtt-status');
        if (data.mqtt_connected) {
            mqttStatus.textContent = 'Connected';
            mqttStatus.className = 'badge badge-success';
        } else {
            mqttStatus.textContent = 'Disconnected';
            mqttStatus.className = 'badge badge-danger';
        }
        
        // Disk usage
        if (data.disk_usage) {
            const usage = data.disk_usage;
            document.getElementById('disk-usage').textContent = 
                `${formatBytes(usage.used)} / ${formatBytes(usage.total)} (${usage.percent}%)`;
        } else {
            document.getElementById('disk-usage').textContent = 'N/A';
        }
    } catch (error) {
        console.error('Error loading system info:', error);
    }
}

// Save settings
async function saveSettings(event) {
    event.preventDefault();
    
    const settingsData = {
        mqtt: {
            enabled: document.getElementById('mqtt-enabled').checked,
            broker: document.getElementById('mqtt-broker').value,
            port: parseInt(document.getElementById('mqtt-port').value),
            username: document.getElementById('mqtt-username').value,
            password: document.getElementById('mqtt-password').value,
            base_topic: document.getElementById('mqtt-base-topic').value
        },
        defaults: {
            drop_location: document.getElementById('default-drop-location').value,
            temp_dir: document.getElementById('default-temp-dir').value,
            verify_checksums: document.getElementById('default-verify-checksums').checked,
            concurrent_transfers: parseInt(document.getElementById('default-concurrent-transfers').value)
        },
        web: {
            host: document.getElementById('web-host').value,
            port: parseInt(document.getElementById('web-port').value)
        }
    };
    
    try {
        await apiPut('/api/settings', settingsData);
        showNotification('Settings saved successfully! Some changes may require a restart.');
        
        // Reload system info after a delay
        setTimeout(loadSystemInfo, 2000);
    } catch (error) {
        console.error('Error saving settings:', error);
        showNotification('Error saving settings', 'error');
    }
}

