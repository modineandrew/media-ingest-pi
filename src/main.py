#!/usr/bin/env python3
"""Media Ingest Pi - Main Service Entry Point."""

import sys
import signal
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from media_ingest.core.config import ConfigManager
from media_ingest.core.database import DatabaseManager
from media_ingest.core.device_monitor import DeviceMonitor
from media_ingest.core.transfer import FileTransferWorker
from media_ingest.mqtt.client import MQTTClient
from media_ingest.web.server import WebServer


class MediaIngestService:
    """Main service coordinator for Media Ingest Pi."""
    
    def __init__(self):
        """Initialize the service."""
        print("=" * 60)
        print("Media Ingest Pi - Starting...")
        print("=" * 60)
        
        # Initialize components
        print("Initializing configuration manager...")
        self.config_manager = ConfigManager()
        
        print("Initializing database...")
        self.database_manager = DatabaseManager()
        
        # Get settings
        self.settings = self.config_manager.get_settings()
        
        print("Initializing MQTT client...")
        self.mqtt_client = MQTTClient(self.settings)
        
        print("Initializing transfer worker...")
        self.transfer_worker = FileTransferWorker(
            self.settings,
            progress_callback=self._on_transfer_progress
        )
        
        print("Initializing device monitor...")
        self.device_monitor = DeviceMonitor(
            on_device_added=self._on_device_added,
            on_device_removed=self._on_device_removed
        )
        
        print("Initializing web server...")
        self.web_server = WebServer(
            self.config_manager,
            self.database_manager,
            self.device_monitor,
            self.transfer_worker,
            self.mqtt_client,
            self.settings
        )
        
        self._running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def start(self):
        """Start all services."""
        print("\nStarting services...")
        
        # Start MQTT client
        if self.mqtt_client.enabled:
            print("Connecting to MQTT broker...")
            self.mqtt_client.connect()
            time.sleep(1)  # Give it a moment to connect
            
            if self.mqtt_client.is_connected():
                print("✓ MQTT connected")
                self.mqtt_client.publish_status('online')
            else:
                print("✗ MQTT connection failed (continuing anyway)")
        else:
            print("MQTT disabled")
        
        # Start transfer worker
        print("Starting transfer worker...")
        self.transfer_worker.start()
        print("✓ Transfer worker started")
        
        # Start device monitor
        print("Starting device monitor...")
        self.device_monitor.start()
        print("✓ Device monitor started")
        
        # Start web server
        print("Starting web server...")
        web_host = self.settings.get('web', {}).get('host', '0.0.0.0')
        web_port = self.settings.get('web', {}).get('port', 5000)
        print(f"✓ Web server started on http://{web_host}:{web_port}")
        
        print("\n" + "=" * 60)
        print("Media Ingest Pi is running!")
        print("=" * 60)
        print(f"Web Interface: http://{web_host}:{web_port}")
        print("Press Ctrl+C to stop")
        print("=" * 60 + "\n")
        
        self._running = True
        
        # Run web server (blocking)
        try:
            self.web_server.run()
        except KeyboardInterrupt:
            pass
    
    def stop(self):
        """Stop all services."""
        if not self._running:
            return
        
        print("\n\nShutting down services...")
        self._running = False
        
        # Publish offline status
        if self.mqtt_client and self.mqtt_client.is_connected():
            print("Publishing offline status...")
            self.mqtt_client.publish_status('offline')
        
        # Stop device monitor
        print("Stopping device monitor...")
        self.device_monitor.stop()
        
        # Stop transfer worker
        print("Stopping transfer worker...")
        self.transfer_worker.stop()
        
        # Disconnect MQTT
        if self.mqtt_client:
            print("Disconnecting MQTT...")
            self.mqtt_client.disconnect()
        
        print("Shutdown complete. Goodbye!")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals.
        
        Args:
            signum: Signal number.
            frame: Current stack frame.
        """
        print(f"\nReceived signal {signum}")
        self.stop()
        sys.exit(0)
    
    def _on_device_added(self, device_info: dict):
        """Handle device added event.
        
        Args:
            device_info: Device information dictionary.
        """
        device_label = device_info.get('label') or device_info.get('device_node')
        print(f"\n📱 Device detected: {device_label}")
        print(f"   Mount point: {device_info.get('mount_point')}")
        print(f"   UUID: {device_info.get('uuid')}")
        print(f"   Vendor: {device_info.get('vendor')}")
        print(f"   Size: {device_info.get('size_bytes', 0) / (1024**3):.1f} GB")
        
        # Find matching device profile
        device_profile = self.config_manager.find_device_by_identifiers(device_info)
        
        if device_profile:
            print(f"   ✓ Matched profile: {device_profile['name']}")
            print(f"   Drop location: {device_profile.get('drop_location')}")
            print(f"   Auto-ingest: {device_profile.get('auto_ingest', False)}")
            
            # Emit to web clients
            self.web_server.emit_device_detected(device_info)
            
            # Publish to MQTT
            if self.mqtt_client and self.mqtt_client.is_connected():
                self.mqtt_client.publish_device_detected(
                    device_profile['id'],
                    device_profile['name'],
                    device_profile.get('auto_ingest', False)
                )
            
            # Auto-ingest if enabled
            if device_profile.get('auto_ingest', False):
                print(f"   → Auto-ingest enabled - queueing transfer...")
                try:
                    transfer_id = self.transfer_worker.queue_transfer(device_profile, device_info)
                    
                    # Create database record
                    self.database_manager.create_transfer({
                        'transfer_id': transfer_id,
                        'device_id': device_profile['id'],
                        'device_name': device_profile['name'],
                        'status': 'queued',
                        'source_path': device_info.get('mount_point', ''),
                        'drop_location': device_profile.get('drop_location', '')
                    })
                    print(f"   ✓ Transfer queued: {transfer_id}")
                except Exception as e:
                    print(f"   ✗ Error queuing transfer: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"   ⊘ Auto-ingest disabled - manual trigger required")
        else:
            print(f"   ⚠ No matching profile found - please create a profile for this device")
            
            # Still emit to web clients
            self.web_server.emit_device_detected(device_info)
    
    def _on_device_removed(self, device_info: dict):
        """Handle device removed event.
        
        Args:
            device_info: Device information dictionary.
        """
        print(f"\n📱 Device removed: {device_info.get('label') or device_info.get('device_node')}")
        
        # Emit to web clients
        self.web_server.emit_device_removed(device_info)
    
    def _on_transfer_progress(self, transfer_info: dict):
        """Handle transfer progress update.
        
        Args:
            transfer_info: Transfer information dictionary.
        """
        transfer_id = transfer_info['transfer_id']
        status = transfer_info['status']
        
        # Update database
        db_updates = {
            'status': status,
            'files_transferred': transfer_info.get('files_transferred', 0),
            'files_failed': transfer_info.get('files_failed', 0),
            'files_skipped': transfer_info.get('files_skipped', 0),
            'bytes_transferred': transfer_info.get('bytes_transferred', 0)
        }
        
        if status == 'completed':
            db_updates['completed_at'] = transfer_info.get('completed_at')
            db_updates['duration_seconds'] = transfer_info.get('duration_seconds')
        elif status == 'failed':
            db_updates['error_message'] = transfer_info.get('error')
        
        self.database_manager.update_transfer(transfer_id, db_updates)
        
        # Emit to web clients
        self.web_server.emit_transfer_update(transfer_info)
        
        # Publish to MQTT
        if not self.mqtt_client or not self.mqtt_client.is_connected():
            return
        
        if status == 'in_progress':
            # Only publish progress every 10 files to avoid spam
            files_completed = transfer_info.get('files_transferred', 0)
            if files_completed % 10 == 0 or files_completed == transfer_info.get('total_files', 0):
                self.mqtt_client.publish_transfer_progress(transfer_info)
        elif status == 'completed':
            print(f"✓ Transfer {transfer_id} completed successfully")
            self.mqtt_client.publish_transfer_completed(transfer_info)
        elif status == 'failed':
            print(f"✗ Transfer {transfer_id} failed: {transfer_info.get('error')}")
            self.mqtt_client.publish_transfer_failed(transfer_info)


def main():
    """Main entry point."""
    service = MediaIngestService()
    
    try:
        service.start()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        service.stop()
        sys.exit(1)


if __name__ == '__main__':
    main()

