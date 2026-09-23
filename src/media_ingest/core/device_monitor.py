"""Device monitoring service for USB drives and SD cards using pyudev."""

import pyudev
import threading
import time
import os
from pathlib import Path
from typing import Callable, Dict, Optional, List


class DeviceMonitor:
    """Monitors USB and SD card device events."""
    
    def __init__(self, on_device_added: Callable = None, on_device_removed: Callable = None):
        """Initialize device monitor.
        
        Args:
            on_device_added: Callback function when device is added.
            on_device_removed: Callback function when device is removed.
        """
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        # Monitor block devices (both disks and partitions for USB/SD cards)
        self.monitor.filter_by(subsystem='block')
        
        self.on_device_added = on_device_added
        self.on_device_removed = on_device_removed
        
        self._running = False
        self._thread = None
        self._mounted_devices: Dict[str, Dict] = {}
        self._lock = threading.RLock()
    
    def start(self):
        """Start monitoring for device events."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print("Device monitor started")
    
    def stop(self):
        """Stop monitoring for device events."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("Device monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        observer = pyudev.MonitorObserver(self.monitor, callback=self._handle_device_event)
        observer.start()
        
        # Also scan for already connected devices
        self._scan_existing_devices()
        
        while self._running:
            time.sleep(1)
        
        observer.stop()
    
    def _scan_existing_devices(self):
        """Scan for devices that are already connected."""
        # Scan all block devices (disks and partitions)
        for device in self.context.list_devices(subsystem='block'):
            device_info = self._get_device_info(device)
            if device_info and device_info.get('mount_point'):
                with self._lock:
                    self._mounted_devices[device_info['device_node']] = device_info
                
                if self.on_device_added:
                    try:
                        self.on_device_added(device_info)
                    except Exception as e:
                        print(f"Error in device_added callback: {e}")
    
    def _handle_device_event(self, device: pyudev.Device):
        """Handle udev device events.
        
        Args:
            device: udev device object.
        """

        action = device.action

        if action == 'add':
            # Wait a moment for the device to be mounted
            time.sleep(2)
            device_info = self._get_device_info(device)
            
            if device_info and device_info.get('mount_point'):
                with self._lock:
                    self._mounted_devices[device_info['device_node']] = device_info
                
                print(f"Device added: {device_info['device_node']} mounted at {device_info['mount_point']}")
                
                if self.on_device_added:
                    try:
                        self.on_device_added(device_info)
                    except Exception as e:
                        print(f"Error in device_added callback: {e}")
        
        elif action == 'remove':
            device_node = device.device_node
            
            with self._lock:
                device_info = self._mounted_devices.pop(device_node, None)
            
            if device_info:
                print(f"Device removed: {device_node}")
                
                if self.on_device_removed:
                    try:
                        self.on_device_removed(device_info)
                    except Exception as e:
                        print(f"Error in device_removed callback: {e}")
    
    def _get_device_info(self, device: pyudev.Device) -> Optional[Dict]:
        """Extract device information.
        
        Args:
            device: udev device object.
            
        Returns:
            Dictionary with device information or None if not a removable device.
        """
        try:
            # Check if it's a removable device
            # For partitions, find parent disk; for whole disks, use the device itself
            parent = device.find_parent('block')
            if not parent:
                # This is a top-level disk device (no parent)
                parent = device
            
            # Check if device is removable
            try:
                removable = parent.attributes.asstring('removable')
                if removable != '1':
                    return None
            except:
                # If we can't read removable attribute, skip this device
                return None
            
            # Get device info
            device_node = device.device_node
            if not device_node:
                return None
            
            # Get mount point
            mount_point = self._get_mount_point(device_node)
            if not mount_point:
                return None
            
            # Get UUID and label
            uuid = device.get('ID_FS_UUID', '')
            label = device.get('ID_FS_LABEL', '')
            
            # Get vendor and model from parent (or device itself if it's the disk)
            vendor = parent.get('ID_VENDOR', '')
            model = parent.get('ID_MODEL', '')
            
            # Get size
            size_bytes = 0
            try:
                size_str = device.attributes.asstring('size')
                if size_str:
                    # Size is in 512-byte sectors
                    size_bytes = int(size_str) * 512
            except:
                pass
            
            return {
                'device_node': device_node,
                'mount_point': mount_point,
                'uuid': uuid,
                'label': label,
                'vendor': vendor,
                'model': model,
                'size_bytes': size_bytes,
                'filesystem': device.get('ID_FS_TYPE', ''),
            }
        
        except Exception as e:
            print(f"Error getting device info: {e}")
            return None
    
    def _get_mount_point(self, device_node: str) -> Optional[str]:
        """Get mount point for a device node.
        
        Args:
            device_node: Device node path (e.g., /dev/sda1).
            
        Returns:
            Mount point path or None if not mounted.
        """
        try:
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2 and parts[0] == device_node:
                        return parts[1]
        except Exception as e:
            print(f"Error reading mounts: {e}")
        
        return None
    
    def get_mounted_devices(self) -> List[Dict]:
        """Get list of currently mounted devices.
        
        Returns:
            List of device information dictionaries.
        """
        with self._lock:
            return list(self._mounted_devices.values())
    
    def get_device_by_node(self, device_node: str) -> Optional[Dict]:
        """Get device information by device node.
        
        Args:
            device_node: Device node path.
            
        Returns:
            Device information dictionary or None.
        """
        with self._lock:
            return self._mounted_devices.get(device_node)
    
    def refresh_devices(self):
        """Refresh the list of mounted devices."""
        self._scan_existing_devices()
    
    def rescan_and_notify(self):
        """Rescan devices and notify callbacks for all mounted devices.
        
        This is useful when device profiles are added/updated and we want to
        re-check if any currently mounted devices now match a profile.
        """
        with self._lock:
            devices = list(self._mounted_devices.values())
        
        print(f"Rescanning {len(devices)} mounted device(s)...")
        for device_info in devices:
            if self.on_device_added:
                try:
                    self.on_device_added(device_info)
                except Exception as e:
                    print(f"Error in device_added callback during rescan: {e}")

