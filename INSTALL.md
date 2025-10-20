# Media Ingest Pi - Installation Guide

## Prerequisites

- Raspberry Pi (any model with USB ports)
- Raspberry Pi OS (Debian-based Linux)
- Python 3.9 or higher
- Network storage location (NAS, SMB share, or local directory)
- Optional: MQTT broker (e.g., Mosquitto, Home Assistant)

## Step-by-Step Installation

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

### 2. Install Python Dependencies

Navigate to the project directory and install requirements:

```bash
cd /home/bscholer/media-ingest-pi
pip3 install -r requirements.txt
```

Or install system-wide with sudo:

```bash
sudo pip3 install -r requirements.txt
```

### 3. Configure Network Storage

Mount your network storage (if using NAS):

```bash
# Example for SMB/CIFS share
sudo apt install -y cifs-utils
sudo mkdir -p /mnt/nas
```

Add to `/etc/fstab` for automatic mounting:

```
//192.168.1.100/photos /mnt/nas cifs credentials=/home/pi/.smbcredentials,uid=1000,gid=1000 0 0
```

Create credentials file at `/home/pi/.smbcredentials`:

```
username=your_username
password=your_password
```

```bash
sudo chmod 600 /home/pi/.smbcredentials
sudo mount -a
```

### 4. Configure the Application

Edit the configuration files:

```bash
nano config/settings.yaml
```

Update the settings:
- Set your MQTT broker details (if using)
- Configure default drop location (e.g., `/mnt/nas/incoming`)
- Adjust other settings as needed

### 5. Test the Application

Run the application manually first to test:

```bash
./run.sh
```

Or:

```bash
python3 src/main.py
```

Access the web interface at: `http://<raspberry-pi-ip>:5000`

Press `Ctrl+C` to stop.

### 6. Configure Device Profiles

1. Open the web interface in your browser
2. Go to the "Devices" page
3. Click "Add Device"
4. Fill in the device details:
   - **Name**: Friendly name (e.g., "Camera SD Card")
   - **Drop Location**: Where to copy files (e.g., `/mnt/nas/photos/camera`)
   - **File Types**: Extensions to copy (e.g., `.jpg, .mp4, .raw`)
   - **Naming Pattern**: How to rename files (default: `{date}_{device}_{counter:04d}{ext}`)
   - **Identifiers**: UUID, label, or vendor to match the device
   - **Auto-ingest**: Enable to start automatically when device is detected
   - **Delete after**: Enable to delete source files after successful copy

### 7. Install as System Service

To run automatically on boot:

```bash
# Copy service file
sudo cp media-ingest.service /etc/systemd/system/

# Edit service file if your username is not 'pi'
sudo nano /etc/systemd/system/media-ingest.service
# Change User=pi to your username

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable media-ingest

# Start the service
sudo systemctl start media-ingest

# Check status
sudo systemctl status media-ingest

# View logs
sudo journalctl -u media-ingest -f
```

### 8. Configure udev Permissions (if needed)

If the service can't detect devices, add your user to the plugdev group:

```bash
sudo usermod -a -G plugdev $USER
```

Log out and back in for changes to take effect.

## Usage

### Web Interface

Access the web interface at: `http://<raspberry-pi-ip>:5000`

**Dashboard**: View active transfers, mounted devices, and recent activity
**Devices**: Manage device profiles
**History**: View transfer history
**Settings**: Configure MQTT and global settings

### Manual Operation

1. Plug in a USB drive or SD card
2. If a matching device profile exists with auto-ingest enabled, transfer starts automatically
3. Otherwise, go to the Dashboard and click "Start" next to the detected device

### Command Line

```bash
# Start service
./run.sh

# Or with Python directly
python3 src/main.py

# Install as system service (auto-start on boot)
sudo systemctl enable media-ingest
sudo systemctl start media-ingest

# View logs
sudo journalctl -u media-ingest -f

# Stop service
sudo systemctl stop media-ingest

# Restart service
sudo systemctl restart media-ingest
```

## MQTT Integration with Home Assistant

If you have Home Assistant with MQTT:

1. Configure MQTT settings in the Settings page or `config/settings.yaml`
2. Enable MQTT
3. Restart the service
4. The service will auto-discover in Home Assistant
5. You'll see sensors for:
   - Media Ingest Status
   - Last Transfer
6. You'll receive notifications for:
   - Device detected
   - Transfer started/completed/failed
   - Progress updates

## Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u media-ingest -n 50

# Check Python dependencies
pip3 list | grep -E "flask|pyudev|paho-mqtt|pyyaml"

# Test manually
python3 src/main.py
```

### Devices not detected

```bash
# Check if devices are mounted
lsblk
mount | grep /media

# Check udev permissions
groups  # Should include 'plugdev'

# Test device detection manually
python3 -c "import pyudev; ctx = pyudev.Context(); print(list(ctx.list_devices(subsystem='block')))"
```

### Web interface not accessible

```bash
# Check if service is running
sudo systemctl status media-ingest

# Check firewall (if enabled)
sudo ufw allow 5000

# Try different port in config/settings.yaml
```

### Files not copying

```bash
# Check drop location permissions
ls -ld /mnt/nas/target-directory
# Should be writable by your user

# Check disk space
df -h

# Check logs for errors
sudo journalctl -u media-ingest -f
```

## Updating

To update the application:

```bash
# Pull latest changes (if using git)
git pull

# Restart service
sudo systemctl restart media-ingest
```

## Uninstalling

```bash
# Stop and disable service
sudo systemctl stop media-ingest
sudo systemctl disable media-ingest

# Remove service file
sudo rm /etc/systemd/system/media-ingest.service
sudo systemctl daemon-reload

# Remove application directory
rm -rf /home/bscholer/media-ingest-pi

# Optionally uninstall Python packages
pip3 uninstall flask flask-socketio paho-mqtt pyudev pyyaml
```

## Support

For issues, questions, or contributions, please refer to the project documentation.

