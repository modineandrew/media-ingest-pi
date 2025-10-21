# Migration to Configuration V2

## What Changed?

Version 2 introduces **multi-destination support** for devices. Each device can now have multiple transfer rules, allowing you to send different types of files to different locations from a single SD card or USB drive.

### Key Features

- **Multiple Transfer Rules per Device**: Configure separate destinations for photos, videos, panoramas, etc.
- **Advanced Filtering**: Filter files by:
  - File types (`.jpg`, `.raw`, `.mp4`, etc.)
  - Source path patterns (`**/DCIM/**`, `**/PANO/**`)
  - Filename patterns (`IMG_*`, `*_PANO_*`)
- **Rule-Specific Settings**: Each rule has its own:
  - Drop location
  - Naming pattern
  - Preserve structure setting
  - Delete after setting

### Example Use Case

**Camera SD Card** with one device profile but three transfer rules:
1. **RAW Photos** → `/mnt/nas/photos/camera/raw` (only `.dng`, `.cr2` files)
2. **JPEG Photos** → `/mnt/nas/photos/camera/jpeg` (only `.jpg` files)
3. **Videos** → `/mnt/nas/videos/camera` (only `.mp4`, `.mov` files)

## Automatic Migration

The migration happens automatically on first launch after upgrading:

1. **Backup Created**: Your existing `devices.yaml` is backed up to `config/backups/devices.yaml.v1.backup.TIMESTAMP`
2. **Migration Applied**: Each device is converted to v2 format:
   - Old device-level settings become a single transfer rule named "Default Transfer" or the device name
   - All existing settings are preserved
3. **Version Tagged**: Config files are marked as version 2

### Before Migration (v1)
```yaml
devices:
  - id: device_123
    name: "Camera SD"
    drop_location: /mnt/nas/photos
    file_types: [.jpg, .raw]
    naming_pattern: "{original}"
    # ...
```

### After Migration (v2)
```yaml
version: 2
devices:
  - id: device_123
    name: "Camera SD"
    transfer_rules:
      - id: rule_abc123
        name: "Camera SD"  # Uses device name
        drop_location: /mnt/nas/photos
        file_types: [.jpg, .raw]
        source_path_patterns: []
        filename_patterns: []
        naming_pattern: "{original}"
        preserve_structure: true
        delete_after: false
```

## Using the New Features

### Web Interface

1. **Open Devices Page**: Navigate to the Devices section
2. **Edit a Device**: Click "Edit" on any device
3. **Tabbed Interface**: You'll see:
   - **Basic Info** tab: Device name, identifiers, auto-ingest settings
   - **Rule 1, Rule 2, etc.** tabs: One tab per transfer rule
4. **Add Rules**: Click "+ Add Transfer Rule" to create additional rules
5. **Configure Each Rule**:
   - Give it a descriptive name
   - Set the drop location
   - Add file types (press Enter after each)
   - Optionally add path patterns and filename patterns
   - Configure naming and deletion settings
6. **Delete Rules**: Use the "Delete This Rule" button (must keep at least one)

### Advanced Filtering Examples

**Separate panoramas from regular photos:**
```yaml
- name: "Panoramas"
  source_path_patterns: ["**/PANO/**", "**/Panorama/**"]
  
- name: "Regular Photos"
  source_path_patterns: ["**/DCIM/**"]
  filename_patterns: ["DJI_*"]  # Only drone files starting with DJI_
```

**Different destinations by file type:**
```yaml
- name: "RAW Photos"
  file_types: [".raw", ".dng", ".cr2"]
  drop_location: "/mnt/nas/photos/raw"
  
- name: "JPEGs"
  file_types: [".jpg", ".jpeg"]
  drop_location: "/mnt/nas/photos/jpeg"
```

## Backwards Compatibility

**None.** This is a breaking change that requires migration. The old v1 format is no longer supported after migration.

However:
- Migration is automatic and safe (creates backups)
- Existing devices continue to work with their settings converted to a single rule
- You can add more rules to migrated devices at any time

## Rollback

If you need to rollback:

1. Stop the service:
   ```bash
   sudo systemctl stop media-ingest
   ```

2. Restore the backup:
   ```bash
   cp config/backups/devices.yaml.v1.backup.TIMESTAMP config/devices.yaml
   cp config/backups/settings.yaml.v1.backup.TIMESTAMP config/settings.yaml
   ```

3. Checkout the previous version of the code

4. Restart the service

## Need Help?

- Check `config/devices.example.yaml` for complete examples
- Review the logs for migration status
- Open an issue on GitHub if you encounter problems

