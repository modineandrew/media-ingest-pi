# Changelog - Version 2.0

## Summary

**Major Feature**: Multi-Destination Device Configuration

Devices can now have multiple transfer rules, each with its own destination, filters, and settings. This allows you to intelligently route different types of files from a single device to multiple locations.

## New Features

### 1. Multiple Transfer Rules per Device
- Each device can have unlimited transfer rules
- Each rule operates independently with its own settings
- Rules are processed in parallel when a device is detected

### 2. Advanced File Filtering
Three types of filters can be combined per rule:
- **File Types**: Filter by extension (`.jpg`, `.raw`, `.mp4`, etc.)
- **Source Path Patterns**: Filter by directory structure (`**/DCIM/**`, `**/PANO/**`)
- **Filename Patterns**: Filter by filename (`IMG_*`, `*_PANO_*`)

All filters use glob pattern matching and are combined with AND logic.

### 3. Tabbed Device Configuration UI
- Clean, intuitive tabbed interface in the web UI
- "Basic Info" tab for device-level settings
- Separate tab for each transfer rule
- Easy rule management: add, edit, delete
- Chip-style input for multi-value fields (file types, patterns)

### 4. Configuration Versioning
- Config files now include a version number
- Automatic migration system handles upgrades
- Backups created before migration

### 5. Enhanced Database Schema
- Transfer records now include `rule_id` and `rule_name`
- Better tracking of which rule processed which files

## Technical Changes

### Backend

**New Files:**
- `src/media_ingest/core/migration.py` - Configuration migration system

**Modified Files:**
- `src/media_ingest/core/config.py`
  - Added migration support
  - Added transfer rule CRUD methods
  - Version-aware config loading/saving
  
- `src/media_ingest/core/database.py`
  - Added `rule_id` and `rule_name` columns
  - Automatic schema migration
  
- `src/media_ingest/core/transfer.py`
  - Support for rule-specific transfers
  - Enhanced file filtering with path and filename patterns
  - V1 backwards compatibility in transfer logic
  
- `src/main.py`
  - Queue multiple transfers for devices with multiple rules
  - Pass rule information to database
  
- `src/media_ingest/web/server.py`
  - New API endpoints for transfer rule management
  - Enhanced device creation/update endpoints
  - Support for rule-specific manual triggers

**API Endpoints Added:**
- `GET /api/devices/<device_id>/transfer-rules` - List rules
- `POST /api/devices/<device_id>/transfer-rules` - Add rule
- `PUT /api/devices/<device_id>/transfer-rules/<rule_id>` - Update rule
- `DELETE /api/devices/<device_id>/transfer-rules/<rule_id>` - Delete rule

### Frontend

**Modified Files:**
- `templates/devices.html`
  - Complete redesign with tabbed interface
  - New CSS for tabs and chip inputs
  - Modal size increased for better UX
  
- `static/js/devices.js`
  - Complete rewrite for v2 support
  - Dynamic tab rendering
  - Chip input management
  - Rule CRUD operations
  - Enhanced validation

### Configuration

**Modified Files:**
- `config/devices.example.yaml` - Updated with v2 examples showing multiple rules
- `README.md` - Updated features and configuration documentation

**New Files:**
- `MIGRATION_v2.md` - Migration guide and documentation
- `CHANGELOG_v2.md` - This file

## Migration Details

### Automatic Migration Process

1. **Detection**: On startup, ConfigManager checks config version
2. **Backup**: Creates timestamped backup in `config/backups/`
3. **Migration**: Converts v1 format to v2:
   - Device-level settings → single transfer rule
   - Preserves all existing configuration
   - Adds new fields with sensible defaults
4. **Save**: Writes v2 config with version number

### V1 to V2 Transformation

**Before (V1):**
```yaml
devices:
  - name: "Camera"
    drop_location: "/mnt/nas/photos"
    file_types: [".jpg"]
    # ... other settings at device level
```

**After (V2):**
```yaml
version: 2
devices:
  - name: "Camera"
    transfer_rules:
      - name: "Camera"
        drop_location: "/mnt/nas/photos"
        file_types: [".jpg"]
        source_path_patterns: []
        filename_patterns: []
        # ... settings now at rule level
```

## Breaking Changes

⚠️ **Configuration Format**: V1 configuration files are no longer supported. Migration is automatic but irreversible without restoring backups.

⚠️ **API Changes**: Device create/update endpoints now expect `transfer_rules` array instead of flat settings.

## Backwards Compatibility

### What Still Works
- Migrated devices function identically to before (single rule)
- All existing features and settings preserved
- Database schema is backwards compatible (adds columns, doesn't remove)
- V1 configs are auto-migrated on first run

### What Doesn't Work
- Cannot use V1 config format after migration
- Old API format for device creation (automatically converted on save)

## Example Use Cases

### 1. Camera with Photo/Video Split
```yaml
- name: "Camera SD Card"
  transfer_rules:
    - name: "Photos"
      drop_location: "/mnt/nas/photos"
      file_types: [".jpg", ".raw", ".dng"]
    - name: "Videos"
      drop_location: "/mnt/nas/videos"
      file_types: [".mp4", ".mov"]
```

### 2. Drone with Path-Based Routing
```yaml
- name: "Drone"
  transfer_rules:
    - name: "Panoramas"
      drop_location: "/mnt/nas/photos/panos"
      source_path_patterns: ["**/PANO/**"]
      file_types: [".jpg", ".dng"]
    - name: "Regular Photos"
      drop_location: "/mnt/nas/photos/drone"
      source_path_patterns: ["**/DCIM/**"]
      filename_patterns: ["DJI_*"]
```

### 3. Multi-Camera Setup
```yaml
- name: "Main Camera"
  transfer_rules:
    - name: "RAW"
      drop_location: "/mnt/nas/photos/raw"
      file_types: [".cr2", ".nef"]
      preserve_structure: false
    - name: "JPEG"
      drop_location: "/mnt/nas/photos/jpeg"
      file_types: [".jpg"]
      preserve_structure: true
```

## Testing Recommendations

1. **Backup First**: Before upgrading, backup your `config/` directory
2. **Test Migration**: Verify your devices migrated correctly in the web UI
3. **Test Transfers**: Plug in a device and verify transfers work as expected
4. **Check Logs**: Review service logs for any migration warnings
5. **Verify Filters**: If using new filtering features, test with sample files

## Known Issues

None at this time.

## Upgrade Instructions

1. **Stop the service**:
   ```bash
   sudo systemctl stop media-ingest
   ```

2. **Backup configuration** (recommended):
   ```bash
   cp -r config config.backup.$(date +%Y%m%d)
   ```

3. **Pull latest code**:
   ```bash
   git pull
   ```

4. **Start the service**:
   ```bash
   sudo systemctl start media-ingest
   ```

5. **Check logs** for migration messages:
   ```bash
   sudo journalctl -u media-ingest -f
   ```

6. **Verify web UI**: Check that devices appear correctly with their transfer rules

## Support

- See `MIGRATION_v2.md` for detailed migration information
- Check `config/devices.example.yaml` for configuration examples
- Open GitHub issues for bugs or questions

