// Settings page JavaScript

// Initialize settings page
document.addEventListener('DOMContentLoaded', function() {
    loadSettings();
    loadSystemInfo();
    
    // Toggle MQTT settings visibility
    document.getElementById('mqtt-enabled').addEventListener('change', function() {
        document.getElementById('mqtt-settings').style.display = this.checked ? 'block' : 'none';
    });
    
    // Toggle LED settings visibility
    document.getElementById('led-enabled').addEventListener('change', function() {
        document.getElementById('led-settings').style.display = this.checked ? 'block' : 'none';
    });
    
    // Update brightness value display
    document.getElementById('led-brightness').addEventListener('input', function() {
        document.getElementById('led-brightness-value').textContent = this.value;
    });
    
    // Color preview updates
    const colorInputs = ['idle', 'progress', 'success', 'error'];
    colorInputs.forEach(color => {
        ['r', 'g', 'b'].forEach(channel => {
            const input = document.getElementById(`led-${color}-${channel}`);
            if (input) {
                input.addEventListener('input', function() {
                    updateColorPreview(color);
                });
            }
        });
    });
});

// Update color preview
function updateColorPreview(colorType) {
    const r = document.getElementById(`led-${colorType}-r`).value || 0;
    const g = document.getElementById(`led-${colorType}-g`).value || 0;
    const b = document.getElementById(`led-${colorType}-b`).value || 0;
    const preview = document.getElementById(`led-${colorType}-preview`);
    if (preview) {
        preview.style.background = `rgb(${r}, ${g}, ${b})`;
    }
}

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
        document.getElementById('web-port').value = web.port || 80;
        
        // LED settings
        const led = data.led || {};
        document.getElementById('led-enabled').checked = led.enabled || false;
        document.getElementById('led-pin').value = led.pin || 18;
        document.getElementById('led-count').value = led.led_count || 144;
        document.getElementById('led-brightness').value = led.brightness || 128;
        document.getElementById('led-brightness-value').textContent = led.brightness || 128;
        
        // LED colors
        const idleColor = led.idle_color || [0, 50, 255];
        document.getElementById('led-idle-r').value = idleColor[0];
        document.getElementById('led-idle-g').value = idleColor[1];
        document.getElementById('led-idle-b').value = idleColor[2];
        updateColorPreview('idle');
        
        const progressColor = led.progress_color || [0, 255, 0];
        document.getElementById('led-progress-r').value = progressColor[0];
        document.getElementById('led-progress-g').value = progressColor[1];
        document.getElementById('led-progress-b').value = progressColor[2];
        updateColorPreview('progress');
        
        const successColor = led.success_color || [0, 255, 0];
        document.getElementById('led-success-r').value = successColor[0];
        document.getElementById('led-success-g').value = successColor[1];
        document.getElementById('led-success-b').value = successColor[2];
        updateColorPreview('success');
        
        const errorColor = led.error_color || [255, 0, 0];
        document.getElementById('led-error-r').value = errorColor[0];
        document.getElementById('led-error-g').value = errorColor[1];
        document.getElementById('led-error-b').value = errorColor[2];
        updateColorPreview('error');
        
        // Toggle MQTT settings visibility
        document.getElementById('mqtt-settings').style.display = mqtt.enabled ? 'block' : 'none';
        
        // Toggle LED settings visibility
        document.getElementById('led-settings').style.display = led.enabled ? 'block' : 'none';
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
        },
        led: {
            enabled: document.getElementById('led-enabled').checked,
            pin: parseInt(document.getElementById('led-pin').value),
            led_count: parseInt(document.getElementById('led-count').value),
            brightness: parseInt(document.getElementById('led-brightness').value),
            idle_color: [
                parseInt(document.getElementById('led-idle-r').value),
                parseInt(document.getElementById('led-idle-g').value),
                parseInt(document.getElementById('led-idle-b').value)
            ],
            progress_color: [
                parseInt(document.getElementById('led-progress-r').value),
                parseInt(document.getElementById('led-progress-g').value),
                parseInt(document.getElementById('led-progress-b').value)
            ],
            success_color: [
                parseInt(document.getElementById('led-success-r').value),
                parseInt(document.getElementById('led-success-g').value),
                parseInt(document.getElementById('led-success-b').value)
            ],
            error_color: [
                parseInt(document.getElementById('led-error-r').value),
                parseInt(document.getElementById('led-error-g').value),
                parseInt(document.getElementById('led-error-b').value)
            ]
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

