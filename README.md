# Media Ingest Pi

A Raspberry Pi service that automatically detects USB drives, SD cards, and other removable media, and copies files to configured network locations. Features a web interface for management and MQTT integration with Home Assistant.

## Features

- 🔌 **Auto-detection**: Automatically detect USB drives/SD cards when plugged in
- 📁 **Device Profiles**: Configure per-device settings (drop location, file types, naming patterns)
- 🌐 **Web Interface**: Modern web UI for management and monitoring
- 📊 **Real-time Progress**: Track transfers with live progress updates
- 🏠 **Home Assistant Integration**: MQTT notifications and discovery
- 🔄 **Smart Naming**: Template-based file naming with multiple variables
- ✅ **Checksum Verification**: Ensure file integrity with optional checksums
- 🗑️ **Optional Deletion**: Automatically delete source files after successful transfer

## Installation

### Requirements

- Raspberry Pi (any model with USB ports)
- Python 3.9 or higher
- Network storage location (NAS, SMB share, etc.)
- Optional: MQTT broker (e.g., Mosquitto, Home Assistant)

### Setup

1. Clone or copy this repository to your Raspberry Pi:
```bash
cd /home/bscholer
git clone <repository-url> media-ingest-pi
cd media-ingest-pi
```

2. Install Python dependencies:
```bash
pip3 install -r requirements.txt
```

3. Copy the example configuration:
```bash
cp config/settings.example.yaml config/settings.yaml
cp config/devices.example.yaml config/devices.yaml
```

4. Edit the configuration files:
```bash
nano config/settings.yaml
nano config/devices.yaml
```

5. Run the service:
```bash
python3 src/main.py
```

6. Access the web interface:
```
http://<raspberry-pi-ip>:5000
```

### Run as System Service

To run automatically on boot:

```bash
sudo cp media-ingest.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable media-ingest
sudo systemctl start media-ingest
```

## Configuration

### Device Profiles

Configure devices in `config/devices.yaml`:

```yaml
devices:
  - id: "uuid-1234"
    name: "Camera SD Card"
    identifiers:
      uuid: "ABCD-1234"
      label: "CAMERA_SD"
    auto_ingest: true
    drop_location: "/mnt/nas/photos/camera"
    file_types: [".jpg", ".jpeg", ".raw", ".dng"]
    naming_pattern: "{date}_{device}_{counter:04d}{ext}"
    delete_after: false
    enabled: true
```

### Global Settings

Configure global settings in `config/settings.yaml`:

```yaml
settings:
  mqtt:
    enabled: true
    broker: "homeassistant.local"
    port: 1883
    username: "mqtt_user"
    password: "mqtt_pass"
  defaults:
    drop_location: "/mnt/nas/incoming"
    temp_dir: "/tmp/media_ingest"
    verify_checksums: true
  web:
    port: 5000
    host: "0.0.0.0"
```

### Naming Pattern Variables

Use these variables in naming patterns:

- `{date}`: YYYY-MM-DD
- `{datetime}`: YYYY-MM-DD_HH-MM-SS
- `{device}`: Device name (sanitized)
- `{counter}` or `{counter:04d}`: Sequential number with padding
- `{original}`: Original filename without extension
- `{ext}`: File extension
- `{year}`, `{month}`, `{day}`: Individual date components
- `{uuid}`: Random UUID

Example: `{date}_{device}_{counter:04d}{ext}` → `2025-10-19_Camera-SD-Card_0001.jpg`

## Web Interface

- **Dashboard** (`/`): Active transfers, recent activity, device status
- **Devices** (`/devices`): Manage device profiles
- **Settings** (`/settings`): Configure MQTT and global settings
- **History** (`/history`): View transfer history

## MQTT Integration

When MQTT is enabled, the service publishes events to Home Assistant:

- Device detected
- Transfer started/progress/completed/failed
- Home Assistant auto-discovery

## Development

### Project Structure

```
media-ingest-pi/
├── src/
│   ├── main.py                 # Main entry point
│   └── media_ingest/
│       ├── core/               # Core services
│       │   ├── config.py       # Configuration management
│       │   ├── device_monitor.py  # USB device detection
│       │   ├── transfer.py     # File transfer logic
│       │   └── database.py     # Transfer history database
│       ├── mqtt/
│       │   └── client.py       # MQTT client
│       └── web/
│           ├── server.py       # Flask web server
│           └── api.py          # REST API endpoints
├── static/                     # Web UI assets
│   ├── css/
│   └── js/
├── templates/                  # HTML templates
├── config/                     # Configuration files
├── data/                       # Database and logs
└── requirements.txt
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or pull request.

