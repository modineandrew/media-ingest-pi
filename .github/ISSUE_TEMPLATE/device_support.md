---
name: Device Support
about: Report device detection or compatibility issues
title: '[DEVICE] '
labels: device-support
assignees: ''
---

## Device Information
- **Device Type**: (e.g., USB drive, SD card, camera, phone)
- **Brand/Model**: (e.g., SanDisk Ultra 64GB)
- **Connection**: (e.g., USB 3.0, SD card reader)
- **Filesystem**: (e.g., exFAT, FAT32, NTFS)

## Issue Description
Describe the issue with this device:
- [ ] Device not detected at all
- [ ] Device detected but not mounting
- [ ] Device detected but wrong information shown
- [ ] Transfer fails with this device
- [ ] Other (please describe)

## Device Detection Output
Please provide output from:

```bash
# Plug in the device, then run:
lsblk
udevadm monitor
dmesg | tail -50
```

```
# Paste output here
```

## Configuration
```yaml
# Your device profile from config/devices.yaml
# Paste here if you have one
```

## Additional Information
- Does the device work on other computers/systems?
- Any special formatting or partitioning?
- Have you tried reformatting the device?

## Logs
```
# Relevant logs from Media Ingest Pi
# sudo journalctl -u media-ingest -n 100
```



