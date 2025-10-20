"""MQTT client for Home Assistant integration."""

import json
import threading
from typing import Dict, Optional
import paho.mqtt.client as mqtt


class MQTTClient:
    """MQTT client for publishing events to Home Assistant."""
    
    def __init__(self, settings: Dict):
        """Initialize MQTT client.
        
        Args:
            settings: MQTT settings dictionary.
        """
        self.settings = settings
        self.mqtt_config = settings.get('mqtt', {})
        self.enabled = self.mqtt_config.get('enabled', False)
        
        # Initialize connection state (needs to be set before early return)
        self._connected = False
        self._lock = threading.RLock()
        
        if not self.enabled:
            self.client = None
            return
        
        self.base_topic = self.mqtt_config.get('base_topic', 'homeassistant/media_ingest')
        self.client = mqtt.Client(client_id="media_ingest_pi")
        
        # Set credentials if provided
        username = self.mqtt_config.get('username')
        password = self.mqtt_config.get('password')
        if username and password:
            self.client.username_pw_set(username, password)
        
        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
    
    def connect(self):
        """Connect to MQTT broker."""
        if not self.enabled or not self.client:
            return
        
        try:
            broker = self.mqtt_config.get('broker', 'localhost')
            port = self.mqtt_config.get('port', 1883)
            
            print(f"Connecting to MQTT broker at {broker}:{port}...")
            self.client.connect(broker, port, keepalive=60)
            self.client.loop_start()
        
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        if not self.enabled or not self.client:
            return
        
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self._connected = False
            print("Disconnected from MQTT broker")
        except Exception as e:
            print(f"Error disconnecting from MQTT broker: {e}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker.
        
        Args:
            client: MQTT client instance.
            userdata: User data.
            flags: Response flags.
            rc: Connection result code.
        """
        if rc == 0:
            self._connected = True
            print("Connected to MQTT broker")
            
            # Publish Home Assistant discovery messages
            self._publish_discovery()
        else:
            print(f"Failed to connect to MQTT broker, return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker.
        
        Args:
            client: MQTT client instance.
            userdata: User data.
            rc: Disconnection result code.
        """
        self._connected = False
        print("Disconnected from MQTT broker")
    
    def is_connected(self) -> bool:
        """Check if connected to broker.
        
        Returns:
            True if connected, False otherwise.
        """
        return self._connected
    
    def publish_device_detected(self, device_id: str, device_name: str, auto_ingest: bool):
        """Publish device detected event.
        
        Args:
            device_id: Device unique identifier.
            device_name: Device name.
            auto_ingest: Whether auto-ingest is enabled.
        """
        if not self.enabled or not self._connected:
            return
        
        topic = f"{self.base_topic}/device/detected"
        payload = {
            "device_id": device_id,
            "device_name": device_name,
            "timestamp": self._get_timestamp(),
            "auto_ingest": auto_ingest
        }
        
        self._publish(topic, payload)
    
    def publish_transfer_started(self, transfer_info: Dict):
        """Publish transfer started event.
        
        Args:
            transfer_info: Transfer information dictionary.
        """
        if not self.enabled or not self._connected:
            return
        
        topic = f"{self.base_topic}/transfer/started"
        payload = {
            "device_id": transfer_info.get('device_id'),
            "device_name": transfer_info.get('device_name'),
            "total_files": transfer_info.get('total_files', 0),
            "total_size_mb": round(transfer_info.get('total_size_bytes', 0) / (1024 * 1024), 2),
            "timestamp": transfer_info.get('started_at', self._get_timestamp())
        }
        
        self._publish(topic, payload)
    
    def publish_transfer_progress(self, transfer_info: Dict):
        """Publish transfer progress event.
        
        Args:
            transfer_info: Transfer information dictionary.
        """
        if not self.enabled or not self._connected:
            return
        
        total_files = transfer_info.get('total_files', 1)
        files_completed = transfer_info.get('files_transferred', 0)
        percent_complete = int((files_completed / total_files) * 100) if total_files > 0 else 0
        
        topic = f"{self.base_topic}/transfer/progress"
        payload = {
            "device_id": transfer_info.get('device_id'),
            "files_completed": files_completed,
            "files_total": total_files,
            "percent_complete": percent_complete,
            "current_file": transfer_info.get('current_file', '')
        }
        
        self._publish(topic, payload)
    
    def publish_transfer_completed(self, transfer_info: Dict):
        """Publish transfer completed event.
        
        Args:
            transfer_info: Transfer information dictionary.
        """
        if not self.enabled or not self._connected:
            return
        
        topic = f"{self.base_topic}/transfer/completed"
        payload = {
            "device_id": transfer_info.get('device_id'),
            "device_name": transfer_info.get('device_name'),
            "files_transferred": transfer_info.get('files_transferred', 0),
            "files_failed": transfer_info.get('files_failed', 0),
            "duration_seconds": transfer_info.get('duration_seconds', 0),
            "timestamp": transfer_info.get('completed_at', self._get_timestamp())
        }
        
        self._publish(topic, payload)
    
    def publish_transfer_failed(self, transfer_info: Dict):
        """Publish transfer failed event.
        
        Args:
            transfer_info: Transfer information dictionary.
        """
        if not self.enabled or not self._connected:
            return
        
        topic = f"{self.base_topic}/transfer/failed"
        payload = {
            "device_id": transfer_info.get('device_id'),
            "device_name": transfer_info.get('device_name'),
            "error": transfer_info.get('error', 'Unknown error'),
            "files_completed": transfer_info.get('files_transferred', 0),
            "files_failed": transfer_info.get('files_failed', 0),
            "timestamp": self._get_timestamp()
        }
        
        self._publish(topic, payload)
    
    def publish_status(self, status: str):
        """Publish service status.
        
        Args:
            status: Status string (e.g., 'online', 'offline').
        """
        if not self.enabled or not self._connected:
            return
        
        topic = f"{self.base_topic}/status"
        payload = {
            "status": status,
            "timestamp": self._get_timestamp()
        }
        
        self._publish(topic, payload)
    
    def _publish_discovery(self):
        """Publish Home Assistant MQTT discovery messages."""
        if not self.enabled or not self._connected:
            return
        
        # Publish sensor discovery for service status
        topic = "homeassistant/sensor/media_ingest/status/config"
        payload = {
            "name": "Media Ingest Status",
            "state_topic": f"{self.base_topic}/status",
            "value_template": "{{ value_json.status }}",
            "unique_id": "media_ingest_status",
            "device": {
                "identifiers": ["media_ingest_pi"],
                "name": "Media Ingest Pi",
                "model": "Raspberry Pi Media Ingest",
                "manufacturer": "Custom"
            }
        }
        
        self._publish(topic, payload, retain=True)
        
        # Publish last transfer sensor
        topic = "homeassistant/sensor/media_ingest/last_transfer/config"
        payload = {
            "name": "Media Ingest Last Transfer",
            "state_topic": f"{self.base_topic}/transfer/completed",
            "value_template": "{{ value_json.device_name }}",
            "json_attributes_topic": f"{self.base_topic}/transfer/completed",
            "unique_id": "media_ingest_last_transfer",
            "device": {
                "identifiers": ["media_ingest_pi"],
                "name": "Media Ingest Pi",
                "model": "Raspberry Pi Media Ingest",
                "manufacturer": "Custom"
            }
        }
        
        self._publish(topic, payload, retain=True)
        
        print("Published Home Assistant discovery messages")
    
    def _publish(self, topic: str, payload: Dict, retain: bool = False):
        """Publish message to MQTT broker.
        
        Args:
            topic: MQTT topic.
            payload: Message payload dictionary.
            retain: Whether to retain the message.
        """
        if not self.enabled or not self.client:
            return
        
        try:
            payload_json = json.dumps(payload)
            result = self.client.publish(topic, payload_json, qos=1, retain=retain)
            
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                print(f"Failed to publish to {topic}: {result.rc}")
        
        except Exception as e:
            print(f"Error publishing to MQTT: {e}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            ISO formatted timestamp string.
        """
        from datetime import datetime
        return datetime.now().isoformat()

