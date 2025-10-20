# Media Ingest Pi - Quick Start Guide

## 🚀 5-Minute Setup

### 1. Install Dependencies

```bash
cd /home/bscholer/media-ingest-pi
pip3 install -r requirements.txt
```

### 2. Configure Drop Location

Edit `config/settings.yaml`:

```bash
nano config/settings.yaml
```

Change the `drop_location` to where you want files copied:

```yaml
settings:
  defaults:
    drop_location: "/mnt/nas/incoming"  # Change this to your path
```

### 3. Start the Service

```bash
./run.sh
```

### 4. Open Web Interface

Open your browser and go to:

```
http://localhost:5000
```

Or from another computer:

```
http://<raspberry-pi-ip>:5000
```

### 5. Add Your First Device

1. Click **"Devices"** in the navigation
2. Click **"+ Add Device"**
3. Fill in the form:
   - **Name**: e.g., "My Camera SD Card"
   - **Drop Location**: e.g., `/mnt/nas/photos/camera`
   - **File Types**: e.g., `.jpg, .mp4, .raw`
   - **Identifiers**: Leave blank for now (we'll auto-detect)
   - Check **"Auto-ingest on detection"**
4. Click **"Save Device"**

### 6. Plug in a USB Device

1. Insert your USB drive or SD card
2. Go to the **Dashboard**
3. You should see it appear under **"Mounted Devices"**
4. Note the **Label** or **UUID** shown
5. Go back to **Devices** → **Edit** your device
6. Add the **Label** or **UUID** to the Identifiers section
7. Save

### 7. Test Auto-Ingest

1. Unplug the device
2. Plug it back in
3. Watch the **Dashboard** - transfer should start automatically!

## 📱 Device Identification

When you plug in a device, the system shows its properties:
- **UUID**: Unique ID (most reliable)
- **Label**: Drive name/label
- **Vendor**: Manufacturer name

Use these in your device profile to match the device.

## 🎯 Naming Patterns

Customize how files are renamed using these variables:

- `{date}` → `2025-10-19`
- `{datetime}` → `2025-10-19_14-30-00`
- `{device}` → `My-Camera`
- `{counter:04d}` → `0001, 0002, 0003...`
- `{original}` → Original filename
- `{ext}` → `.jpg`

**Example**: `{date}_{device}_{counter:04d}{ext}`
**Result**: `2025-10-19_My-Camera_0001.jpg`

## 🏠 Home Assistant Integration

### Enable MQTT

1. Go to **Settings**
2. Check **"Enable MQTT"**
3. Enter your MQTT broker details:
   - **Broker**: `homeassistant.local` (or your HA IP)
   - **Port**: `1883`
   - **Username**: Your MQTT username
   - **Password**: Your MQTT password
4. Click **"Save Settings"**
5. Restart the service

### Auto-Discovery

The service will automatically appear in Home Assistant with:
- **Sensors** for status and last transfer
- **Notifications** for device detection and transfer events

## 🔄 Run as System Service (Auto-start on Boot)

```bash
# Install service
sudo cp media-ingest.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable media-ingest
sudo systemctl start media-ingest

# Check status
sudo systemctl status media-ingest

# View live logs
sudo journalctl -u media-ingest -f
```

## 📊 Monitoring

### Web Interface
- **Dashboard**: See active transfers, mounted devices, statistics
- **History**: View all past transfers with details

### Command Line
```bash
# View logs
sudo journalctl -u media-ingest -f

# Check service status
sudo systemctl status media-ingest

# Restart service
sudo systemctl restart media-ingest
```

## 🐛 Troubleshooting

### Device not detected?
```bash
# Check if it's mounted
lsblk
mount | grep /media

# Add your user to plugdev group
sudo usermod -a -G plugdev $USER
# Log out and back in
```

### Can't access web interface?
```bash
# Check if service is running
sudo systemctl status media-ingest

# Check the configured port
cat config/settings.yaml | grep port

# Try accessing with IP instead of localhost
ip addr show
```

### Files not copying?
```bash
# Check drop location exists and is writable
ls -ld /mnt/nas/your-path

# Check disk space
df -h

# View error logs
sudo journalctl -u media-ingest -n 100
```

## 📚 Documentation

- **README.md** - Full feature documentation
- **INSTALL.md** - Detailed installation guide
- **PROJECT_SUMMARY.md** - Technical overview
- **media-ingest-pi.plan.md** - Original requirements

## 🎉 You're Ready!

Your Media Ingest Pi is now set up and ready to automatically transfer files from your USB drives and SD cards!

**Tips**:
- Start with one device and test thoroughly
- Use the Dashboard to monitor transfers
- Check the History page to see past transfers
- Enable MQTT for Home Assistant notifications
- Set up the systemd service for automatic startup

Enjoy your automated media workflow! 📸🎥

