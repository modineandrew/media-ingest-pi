"""Flask web server with REST API and WebSocket support."""

import uuid
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import threading


class WebServer:
    """Flask web server with REST API."""
    
    def __init__(self, config_manager, database_manager, device_monitor, 
                 transfer_worker, mqtt_client, settings):
        """Initialize web server.
        
        Args:
            config_manager: Configuration manager instance.
            database_manager: Database manager instance.
            device_monitor: Device monitor instance.
            transfer_worker: Transfer worker instance.
            mqtt_client: MQTT client instance.
            settings: Global settings dictionary.
        """
        self.config_manager = config_manager
        self.database_manager = database_manager
        self.device_monitor = device_monitor
        self.transfer_worker = transfer_worker
        self.mqtt_client = mqtt_client
        self.settings = settings
        
        # Initialize Flask app
        self.app = Flask(
            __name__,
            template_folder=str(Path(__file__).parent.parent.parent.parent / "templates"),
            static_folder=str(Path(__file__).parent.parent.parent.parent / "static")
        )
        
        # Initialize SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Register routes
        self._register_routes()
        self._register_socketio_events()
        
        self._server_thread = None
    
    def _register_routes(self):
        """Register Flask routes."""
        
        # Main pages
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/devices')
        def devices_page():
            return render_template('devices.html')
        
        @self.app.route('/settings')
        def settings_page():
            return render_template('settings.html')
        
        @self.app.route('/history')
        def history_page():
            return render_template('history.html')
        
        # API: Devices
        @self.app.route('/api/devices', methods=['GET'])
        def get_devices():
            devices = self.config_manager.get_devices()
            return jsonify({'devices': devices})
        
        @self.app.route('/api/devices/<device_id>', methods=['GET'])
        def get_device(device_id):
            device = self.config_manager.get_device(device_id)
            if device:
                return jsonify(device)
            return jsonify({'error': 'Device not found'}), 404
        
        @self.app.route('/api/devices', methods=['POST'])
        def create_device():
            data = request.json
            
            # Generate ID if not provided
            if 'id' not in data:
                data['id'] = f"device_{uuid.uuid4().hex[:12]}"
            
            # Set defaults
            data.setdefault('enabled', True)
            data.setdefault('auto_ingest', True)
            data.setdefault('delete_after', False)
            data.setdefault('identifiers', {})
            
            success = self.config_manager.add_device(data)
            if success:
                # Rescan mounted devices to see if any match the new profile
                self.device_monitor.rescan_and_notify()
                return jsonify(data), 201
            return jsonify({'error': 'Device already exists'}), 400
        
        @self.app.route('/api/devices/<device_id>', methods=['PUT'])
        def update_device(device_id):
            data = request.json
            success = self.config_manager.update_device(device_id, data)
            if success:
                # If identifiers or enabled status changed, rescan devices
                if 'identifiers' in data or 'enabled' in data:
                    self.device_monitor.rescan_and_notify()
                return jsonify({'success': True})
            return jsonify({'error': 'Device not found'}), 404
        
        @self.app.route('/api/devices/<device_id>', methods=['DELETE'])
        def delete_device(device_id):
            success = self.config_manager.delete_device(device_id)
            if success:
                return jsonify({'success': True})
            return jsonify({'error': 'Device not found'}), 404
        
        # API: Settings
        @self.app.route('/api/settings', methods=['GET'])
        def get_settings():
            settings = self.config_manager.get_settings()
            return jsonify(settings)
        
        @self.app.route('/api/settings', methods=['PUT'])
        def update_settings():
            data = request.json
            self.config_manager.update_settings(data)
            
            # Reload MQTT if settings changed
            if 'mqtt' in data:
                self._reload_mqtt()
            
            return jsonify({'success': True})
        
        # API: Transfers
        @self.app.route('/api/transfers', methods=['GET'])
        def get_transfers():
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            device_id = request.args.get('device_id')
            status = request.args.get('status')
            
            transfers = self.database_manager.get_transfers(
                limit=limit,
                offset=offset,
                device_id=device_id,
                status=status
            )
            return jsonify({'transfers': transfers})
        
        @self.app.route('/api/transfers/<transfer_id>', methods=['GET'])
        def get_transfer(transfer_id):
            transfer = self.database_manager.get_transfer(transfer_id)
            if transfer:
                return jsonify(transfer)
            return jsonify({'error': 'Transfer not found'}), 404
        
        @self.app.route('/api/transfers/<transfer_id>/cancel', methods=['POST'])
        def cancel_transfer(transfer_id):
            success = self.transfer_worker.cancel_transfer(transfer_id)
            if success:
                return jsonify({'success': True, 'message': 'Transfer cancelled'})
            return jsonify({'error': 'Transfer not found or already completed'}), 404
        
        @self.app.route('/api/transfers/<transfer_id>', methods=['DELETE'])
        def delete_transfer(transfer_id):
            success = self.database_manager.delete_transfer(transfer_id)
            if success:
                return jsonify({'success': True})
            return jsonify({'error': 'Transfer not found'}), 404
        
        @self.app.route('/api/transfers/active', methods=['GET'])
        def get_active_transfers():
            transfers = self.transfer_worker.get_active_transfers()
            return jsonify({'transfers': transfers})
        
        @self.app.route('/api/transfers/recent', methods=['GET'])
        def get_recent_transfers():
            hours = request.args.get('hours', 24, type=int)
            transfers = self.database_manager.get_recent_transfers(hours=hours)
            return jsonify({'transfers': transfers})
        
        # API: Mounted devices
        @self.app.route('/api/mounted-devices', methods=['GET'])
        def get_mounted_devices():
            devices = self.device_monitor.get_mounted_devices()
            return jsonify({'devices': devices})
        
        # API: Manual trigger
        @self.app.route('/api/trigger-ingest', methods=['POST'])
        def trigger_ingest():
            data = request.json
            device_id = data.get('device_id')
            device_node = data.get('device_node')
            
            if not device_id or not device_node:
                return jsonify({'error': 'Missing device_id or device_node'}), 400
            
            # Get device profile
            device_profile = self.config_manager.get_device(device_id)
            if not device_profile:
                return jsonify({'error': 'Device profile not found'}), 404
            
            # Get device info
            device_info = self.device_monitor.get_device_by_node(device_node)
            if not device_info:
                return jsonify({'error': 'Device not mounted'}), 404
            
            # Queue transfer
            transfer_id = self.transfer_worker.queue_transfer(device_profile, device_info)
            
            return jsonify({'transfer_id': transfer_id, 'success': True})
        
        # API: Statistics
        @self.app.route('/api/statistics', methods=['GET'])
        def get_statistics():
            stats = self.database_manager.get_statistics()
            return jsonify(stats)
        
        # API: System info
        @self.app.route('/api/system-info', methods=['GET'])
        def get_system_info():
            import shutil
            
            # Get disk usage for drop location
            drop_location = self.settings.get('defaults', {}).get('drop_location', '/tmp')
            try:
                usage = shutil.disk_usage(drop_location)
                disk_info = {
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': int((usage.used / usage.total) * 100)
                }
            except:
                disk_info = None
            
            return jsonify({
                'mqtt_connected': self.mqtt_client.is_connected() if self.mqtt_client else False,
                'active_transfers': len(self.transfer_worker.get_active_transfers()),
                'mounted_devices': len(self.device_monitor.get_mounted_devices()),
                'disk_usage': disk_info
            })
    
    def _register_socketio_events(self):
        """Register SocketIO event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect():
            print(f"WebSocket client connected")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"WebSocket client disconnected")
    
    def emit_transfer_update(self, transfer_info):
        """Emit transfer update to all connected clients.
        
        Args:
            transfer_info: Transfer information dictionary.
        """
        self.socketio.emit('transfer_update', transfer_info)
    
    def emit_device_detected(self, device_info):
        """Emit device detected event to all connected clients.
        
        Args:
            device_info: Device information dictionary.
        """
        self.socketio.emit('device_detected', device_info)
    
    def emit_device_removed(self, device_info):
        """Emit device removed event to all connected clients.
        
        Args:
            device_info: Device information dictionary.
        """
        self.socketio.emit('device_removed', device_info)
    
    def _reload_mqtt(self):
        """Reload MQTT client with new settings."""
        if self.mqtt_client:
            self.mqtt_client.disconnect()
            # Re-initialize with new settings
            new_settings = self.config_manager.get_settings()
            self.mqtt_client.__init__(new_settings)
            self.mqtt_client.connect()
    
    def run(self, host=None, port=None, debug=False):
        """Run the web server.
        
        Args:
            host: Host to bind to.
            port: Port to bind to.
            debug: Enable debug mode.
        """
        if host is None:
            host = self.settings.get('web', {}).get('host', '0.0.0.0')
        if port is None:
            port = self.settings.get('web', {}).get('port', 5000)
        
        print(f"Starting web server on {host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
    
    def start_background(self):
        """Start web server in background thread."""
        if self._server_thread and self._server_thread.is_alive():
            return
        
        host = self.settings.get('web', {}).get('host', '0.0.0.0')
        port = self.settings.get('web', {}).get('port', 5000)
        
        self._server_thread = threading.Thread(
            target=lambda: self.socketio.run(
                self.app, 
                host=host, 
                port=port, 
                debug=False,
                allow_unsafe_werkzeug=True
            ),
            daemon=True
        )
        self._server_thread.start()
        print(f"Web server started in background on {host}:{port}")

