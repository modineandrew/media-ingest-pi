"""Configuration management for device profiles and global settings."""

import os
import yaml
import threading
from typing import Dict, List, Optional, Any
from pathlib import Path


class ConfigManager:
    """Manages loading and saving of configuration files."""
    
    def __init__(self, config_dir: str = None):
        """Initialize configuration manager.
        
        Args:
            config_dir: Path to configuration directory. Defaults to ../config relative to src.
        """
        if config_dir is None:
            # Default to config directory relative to project root
            src_dir = Path(__file__).parent.parent.parent
            config_dir = src_dir.parent / "config"
        
        self.config_dir = Path(config_dir)
        self.devices_file = self.config_dir / "devices.yaml"
        self.settings_file = self.config_dir / "settings.yaml"
        
        self._devices: List[Dict] = []
        self._settings: Dict = {}
        self._lock = threading.RLock()
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configurations
        self.load_all()
    
    def load_all(self):
        """Load all configuration files."""
        self.load_devices()
        self.load_settings()
    
    def load_devices(self) -> List[Dict]:
        """Load device profiles from YAML file.
        
        Returns:
            List of device profile dictionaries.
        """
        with self._lock:
            try:
                if self.devices_file.exists():
                    with open(self.devices_file, 'r') as f:
                        data = yaml.safe_load(f)
                        self._devices = data.get('devices', []) if data else []
                else:
                    self._devices = []
                    self.save_devices()  # Create empty file
            except Exception as e:
                print(f"Error loading devices: {e}")
                self._devices = []
            
            return self._devices.copy()
    
    def load_settings(self) -> Dict:
        """Load global settings from YAML file.
        
        Returns:
            Settings dictionary.
        """
        with self._lock:
            try:
                if self.settings_file.exists():
                    with open(self.settings_file, 'r') as f:
                        data = yaml.safe_load(f)
                        self._settings = data.get('settings', {}) if data else {}
                else:
                    # Create default settings
                    self._settings = self._get_default_settings()
                    self.save_settings()
            except Exception as e:
                print(f"Error loading settings: {e}")
                self._settings = self._get_default_settings()
            
            return self._settings.copy()
    
    def save_devices(self):
        """Save device profiles to YAML file."""
        with self._lock:
            try:
                with open(self.devices_file, 'w') as f:
                    yaml.safe_dump({'devices': self._devices}, f, default_flow_style=False)
            except Exception as e:
                print(f"Error saving devices: {e}")
    
    def save_settings(self):
        """Save global settings to YAML file."""
        with self._lock:
            try:
                with open(self.settings_file, 'w') as f:
                    yaml.safe_dump({'settings': self._settings}, f, default_flow_style=False)
            except Exception as e:
                print(f"Error saving settings: {e}")
    
    def get_devices(self) -> List[Dict]:
        """Get all device profiles.
        
        Returns:
            List of device profile dictionaries.
        """
        with self._lock:
            return self._devices.copy()
    
    def get_device(self, device_id: str) -> Optional[Dict]:
        """Get a specific device profile by ID.
        
        Args:
            device_id: Device unique identifier.
            
        Returns:
            Device profile dictionary or None if not found.
        """
        with self._lock:
            for device in self._devices:
                if device.get('id') == device_id:
                    return device.copy()
            return None
    
    def add_device(self, device: Dict) -> bool:
        """Add a new device profile.
        
        Args:
            device: Device profile dictionary.
            
        Returns:
            True if successful, False otherwise.
        """
        with self._lock:
            # Check if device with same ID already exists
            if any(d.get('id') == device.get('id') for d in self._devices):
                return False
            
            self._devices.append(device)
            self.save_devices()
            return True
    
    def update_device(self, device_id: str, updates: Dict) -> bool:
        """Update an existing device profile.
        
        Args:
            device_id: Device unique identifier.
            updates: Dictionary of fields to update.
            
        Returns:
            True if successful, False if device not found.
        """
        with self._lock:
            for i, device in enumerate(self._devices):
                if device.get('id') == device_id:
                    self._devices[i].update(updates)
                    self.save_devices()
                    return True
            return False
    
    def delete_device(self, device_id: str) -> bool:
        """Delete a device profile.
        
        Args:
            device_id: Device unique identifier.
            
        Returns:
            True if successful, False if device not found.
        """
        with self._lock:
            for i, device in enumerate(self._devices):
                if device.get('id') == device_id:
                    self._devices.pop(i)
                    self.save_devices()
                    return True
            return False
    
    def find_device_by_identifiers(self, device_info: Dict) -> Optional[Dict]:
        """Find a device profile that matches the given device information.
        
        Args:
            device_info: Dictionary with device properties (uuid, label, vendor, etc.)
            
        Returns:
            Matching device profile or None.
        """
        with self._lock:
            for device in self._devices:
                if not device.get('enabled', True):
                    continue
                
                identifiers = device.get('identifiers', {})
                
                # Check each identifier
                matched = False
                for key, value in identifiers.items():
                    device_value = device_info.get(key)
                    if device_value and str(device_value).lower() == str(value).lower():
                        matched = True
                        break
                
                if matched:
                    return device.copy()
            
            return None
    
    def get_settings(self) -> Dict:
        """Get global settings.
        
        Returns:
            Settings dictionary.
        """
        with self._lock:
            return self._settings.copy()
    
    def update_settings(self, updates: Dict):
        """Update global settings.
        
        Args:
            updates: Dictionary of settings to update (supports nested updates).
        """
        with self._lock:
            self._deep_update(self._settings, updates)
            self.save_settings()
    
    def _deep_update(self, target: Dict, updates: Dict):
        """Recursively update nested dictionary.
        
        Args:
            target: Target dictionary to update.
            updates: Updates to apply.
        """
        for key, value in updates.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def _get_default_settings(self) -> Dict:
        """Get default settings structure.
        
        Returns:
            Default settings dictionary.
        """
        return {
            'mqtt': {
                'enabled': False,
                'broker': 'localhost',
                'port': 1883,
                'username': '',
                'password': '',
                'base_topic': 'homeassistant/media_ingest'
            },
            'defaults': {
                'drop_location': '/tmp/media_ingest_drop',
                'temp_dir': '/tmp/media_ingest',
                'verify_checksums': True,
                'concurrent_transfers': 1
            },
            'web': {
                'port': 5000,
                'host': '0.0.0.0'
            }
        }

