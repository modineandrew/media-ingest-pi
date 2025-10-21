"""Configuration migration system for handling version upgrades."""

import os
import yaml
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class ConfigMigration:
    """Handles migration of configuration files between versions."""
    
    # Current supported version
    CURRENT_VERSION = 2
    
    def __init__(self, config_dir: Path):
        """Initialize configuration migration.
        
        Args:
            config_dir: Path to configuration directory.
        """
        self.config_dir = Path(config_dir)
        self.backup_dir = self.config_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def get_config_version(self, config_data: Dict, config_type: str) -> int:
        """Get version number from config data.
        
        Args:
            config_data: Configuration dictionary.
            config_type: Type of config ('devices' or 'settings').
            
        Returns:
            Version number (defaults to 1 if not specified).
        """
        if config_data is None:
            return 1
        
        # Check for version field at root level
        if 'version' in config_data:
            return config_data['version']
        
        # If no version field, assume v1
        return 1
    
    def needs_migration(self, config_data: Dict, config_type: str) -> bool:
        """Check if config needs migration.
        
        Args:
            config_data: Configuration dictionary.
            config_type: Type of config ('devices' or 'settings').
            
        Returns:
            True if migration needed, False otherwise.
        """
        current_version = self.get_config_version(config_data, config_type)
        return current_version < self.CURRENT_VERSION
    
    def backup_config(self, config_file: Path, version: int):
        """Create backup of configuration file.
        
        Args:
            config_file: Path to config file.
            version: Version number for backup naming.
        """
        if not config_file.exists():
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{config_file.name}.v{version}.backup.{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(config_file, backup_path)
        print(f"✓ Backed up config to: {backup_path}")
    
    def migrate_devices(self, devices_data: Dict) -> Dict:
        """Migrate devices configuration to latest version.
        
        Args:
            devices_data: Current devices configuration.
            
        Returns:
            Migrated devices configuration.
        """
        if devices_data is None:
            devices_data = {'devices': []}
        
        current_version = self.get_config_version(devices_data, 'devices')
        
        print(f"Migrating devices config from v{current_version} to v{self.CURRENT_VERSION}")
        
        # Apply migrations in sequence
        if current_version < 2:
            devices_data = self._migrate_devices_v1_to_v2(devices_data)
        
        return devices_data
    
    def migrate_settings(self, settings_data: Dict) -> Dict:
        """Migrate settings configuration to latest version.
        
        Args:
            settings_data: Current settings configuration.
            
        Returns:
            Migrated settings configuration.
        """
        if settings_data is None:
            settings_data = {'settings': {}}
        
        current_version = self.get_config_version(settings_data, 'settings')
        
        print(f"Migrating settings config from v{current_version} to v{self.CURRENT_VERSION}")
        
        # Apply migrations in sequence
        if current_version < 2:
            settings_data = self._migrate_settings_v1_to_v2(settings_data)
        
        return settings_data
    
    def _migrate_devices_v1_to_v2(self, devices_data: Dict) -> Dict:
        """Migrate devices from v1 to v2 format.
        
        Changes:
        - Add version field
        - Convert single drop_location to transfer_rules array
        - Preserve all existing settings in the rule
        
        Args:
            devices_data: v1 devices configuration.
            
        Returns:
            v2 devices configuration.
        """
        devices = devices_data.get('devices', [])
        migrated_devices = []
        
        for device in devices:
            # Create new device structure
            migrated_device = {
                'id': device.get('id', f"device_{uuid.uuid4().hex[:12]}"),
                'name': device.get('name', 'Unnamed Device'),
                'identifiers': device.get('identifiers', {}),
                'auto_ingest': device.get('auto_ingest', True),
                'enabled': device.get('enabled', True),
                'transfer_rules': []
            }
            
            # Convert old flat settings to a single transfer rule
            rule = {
                'id': f"rule_{uuid.uuid4().hex[:12]}",
                'name': device.get('name', 'Default Transfer'),
                'drop_location': device.get('drop_location', ''),
                'file_types': device.get('file_types', []),
                'source_path_patterns': [],  # New field, empty for v1 devices
                'filename_patterns': [],  # New field, empty for v1 devices
                'naming_pattern': device.get('naming_pattern', '{original}{ext}'),
                'preserve_structure': device.get('preserve_structure', True),
                'delete_after': device.get('delete_after', False)
            }
            
            migrated_device['transfer_rules'].append(rule)
            migrated_devices.append(migrated_device)
            
            print(f"  ✓ Migrated device: {migrated_device['name']}")
        
        return {
            'version': 2,
            'devices': migrated_devices
        }
    
    def _migrate_settings_v1_to_v2(self, settings_data: Dict) -> Dict:
        """Migrate settings from v1 to v2 format.
        
        Changes:
        - Add version field
        - Preserve all existing settings
        
        Args:
            settings_data: v1 settings configuration.
            
        Returns:
            v2 settings configuration.
        """
        # Settings structure doesn't change in v2, just add version
        return {
            'version': 2,
            'settings': settings_data.get('settings', {})
        }

