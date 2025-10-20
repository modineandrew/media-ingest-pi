"""Database manager for transfer history and state persistence."""

import sqlite3
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any


class DatabaseManager:
    """Manages SQLite database for transfer history."""
    
    def __init__(self, db_path: str = None):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file. Defaults to data/history.db.
        """
        if db_path is None:
            # Default to data directory relative to project root
            src_dir = Path(__file__).parent.parent.parent
            data_dir = src_dir.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "history.db"
        
        self.db_path = str(db_path)
        self._lock = threading.RLock()
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create transfers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transfer_id TEXT UNIQUE NOT NULL,
                    device_id TEXT NOT NULL,
                    device_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    total_files INTEGER DEFAULT 0,
                    files_transferred INTEGER DEFAULT 0,
                    files_failed INTEGER DEFAULT 0,
                    total_size_bytes INTEGER DEFAULT 0,
                    bytes_transferred INTEGER DEFAULT 0,
                    duration_seconds REAL,
                    source_path TEXT,
                    drop_location TEXT,
                    error_message TEXT,
                    metadata TEXT
                )
            ''')
            
            # Create transfer_files table for detailed file tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transfer_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transfer_id TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    destination_file TEXT,
                    status TEXT NOT NULL,
                    size_bytes INTEGER,
                    checksum TEXT,
                    error_message TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (transfer_id) REFERENCES transfers(transfer_id)
                )
            ''')
            
            # Migration: Add files_skipped column if it doesn't exist
            cursor.execute("PRAGMA table_info(transfers)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'files_skipped' not in columns:
                cursor.execute('ALTER TABLE transfers ADD COLUMN files_skipped INTEGER DEFAULT 0')
                print("Added files_skipped column to transfers table")
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transfers_device ON transfers(device_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transfers_status ON transfers(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transfers_started ON transfers(started_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transfer_files_transfer ON transfer_files(transfer_id)')
            
            conn.commit()
            conn.close()
    
    def _get_connection(self):
        """Get a new database connection.
        
        Returns:
            SQLite connection object.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_transfer(self, transfer_data: Dict) -> str:
        """Create a new transfer record.
        
        Args:
            transfer_data: Dictionary with transfer information.
            
        Returns:
            Transfer ID.
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            transfer_id = transfer_data['transfer_id']
            metadata = json.dumps(transfer_data.get('metadata', {}))
            
            cursor.execute('''
                INSERT INTO transfers (
                    transfer_id, device_id, device_name, status, started_at,
                    source_path, drop_location, total_files, total_size_bytes, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                transfer_id,
                transfer_data['device_id'],
                transfer_data['device_name'],
                transfer_data.get('status', 'started'),
                transfer_data.get('started_at', datetime.now().isoformat()),
                transfer_data.get('source_path', ''),
                transfer_data.get('drop_location', ''),
                transfer_data.get('total_files', 0),
                transfer_data.get('total_size_bytes', 0),
                metadata
            ))
            
            conn.commit()
            conn.close()
            
            return transfer_id
    
    def update_transfer(self, transfer_id: str, updates: Dict):
        """Update an existing transfer record.
        
        Args:
            transfer_id: Transfer unique identifier.
            updates: Dictionary of fields to update.
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Build dynamic UPDATE query
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key == 'metadata':
                    value = json.dumps(value)
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            values.append(transfer_id)
            
            query = f"UPDATE transfers SET {', '.join(set_clauses)} WHERE transfer_id = ?"
            cursor.execute(query, values)
            
            conn.commit()
            conn.close()
    
    def delete_transfer(self, transfer_id: str) -> bool:
        """Delete a transfer record.
        
        Args:
            transfer_id: Transfer unique identifier.
            
        Returns:
            True if deleted, False if not found.
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Delete transfer files first
            cursor.execute('DELETE FROM transfer_files WHERE transfer_id = ?', (transfer_id,))
            
            # Delete transfer record
            cursor.execute('DELETE FROM transfers WHERE transfer_id = ?', (transfer_id,))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return deleted
    
    def get_transfer(self, transfer_id: str) -> Optional[Dict]:
        """Get a specific transfer record.
        
        Args:
            transfer_id: Transfer unique identifier.
            
        Returns:
            Transfer dictionary or None if not found.
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM transfers WHERE transfer_id = ?', (transfer_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return self._row_to_dict(row)
            return None
    
    def get_transfers(self, limit: int = 100, offset: int = 0, 
                      device_id: str = None, status: str = None) -> List[Dict]:
        """Get transfer records with optional filters.
        
        Args:
            limit: Maximum number of records to return.
            offset: Number of records to skip.
            device_id: Filter by device ID.
            status: Filter by status.
            
        Returns:
            List of transfer dictionaries.
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = 'SELECT * FROM transfers WHERE 1=1'
            params = []
            
            if device_id:
                query += ' AND device_id = ?'
                params.append(device_id)
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            query += ' ORDER BY started_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            return [self._row_to_dict(row) for row in rows]
    
    def get_active_transfers(self) -> List[Dict]:
        """Get all active (in-progress) transfers.
        
        Returns:
            List of active transfer dictionaries.
        """
        return self.get_transfers(status='in_progress', limit=1000)
    
    def get_recent_transfers(self, hours: int = 24, limit: int = 50) -> List[Dict]:
        """Get recent transfers within the specified time window.
        
        Args:
            hours: Number of hours to look back.
            limit: Maximum number of records.
            
        Returns:
            List of transfer dictionaries.
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cutoff = datetime.now() - timedelta(hours=hours)
            cutoff_str = cutoff.isoformat()
            
            cursor.execute('''
                SELECT * FROM transfers 
                WHERE started_at >= ? 
                ORDER BY started_at DESC 
                LIMIT ?
            ''', (cutoff_str, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_dict(row) for row in rows]
    
    def add_transfer_file(self, file_data: Dict):
        """Add a file record to a transfer.
        
        Args:
            file_data: Dictionary with file information.
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO transfer_files (
                    transfer_id, source_file, destination_file, status,
                    size_bytes, checksum, error_message, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_data['transfer_id'],
                file_data['source_file'],
                file_data.get('destination_file', ''),
                file_data['status'],
                file_data.get('size_bytes', 0),
                file_data.get('checksum', ''),
                file_data.get('error_message', ''),
                file_data.get('timestamp', datetime.now().isoformat())
            ))
            
            conn.commit()
            conn.close()
    
    def get_transfer_files(self, transfer_id: str) -> List[Dict]:
        """Get all file records for a transfer.
        
        Args:
            transfer_id: Transfer unique identifier.
            
        Returns:
            List of file dictionaries.
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM transfer_files 
                WHERE transfer_id = ? 
                ORDER BY timestamp
            ''', (transfer_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_dict(row) for row in rows]
    
    def get_statistics(self) -> Dict:
        """Get overall transfer statistics.
        
        Returns:
            Dictionary with statistics.
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Total transfers
            cursor.execute('SELECT COUNT(*) as count FROM transfers')
            total_transfers = cursor.fetchone()['count']
            
            # Successful transfers
            cursor.execute("SELECT COUNT(*) as count FROM transfers WHERE status = 'completed'")
            successful_transfers = cursor.fetchone()['count']
            
            # Failed transfers
            cursor.execute("SELECT COUNT(*) as count FROM transfers WHERE status = 'failed'")
            failed_transfers = cursor.fetchone()['count']
            
            # Total files transferred
            cursor.execute('SELECT SUM(files_transferred) as total FROM transfers')
            total_files = cursor.fetchone()['total'] or 0
            
            # Total bytes transferred
            cursor.execute('SELECT SUM(bytes_transferred) as total FROM transfers')
            total_bytes = cursor.fetchone()['total'] or 0
            
            conn.close()
            
            return {
                'total_transfers': total_transfers,
                'successful_transfers': successful_transfers,
                'failed_transfers': failed_transfers,
                'total_files_transferred': total_files,
                'total_bytes_transferred': total_bytes
            }
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Convert SQLite row to dictionary.
        
        Args:
            row: SQLite row object.
            
        Returns:
            Dictionary representation.
        """
        d = dict(row)
        
        # Parse JSON metadata if present
        if 'metadata' in d and d['metadata']:
            try:
                d['metadata'] = json.loads(d['metadata'])
            except:
                d['metadata'] = {}
        
        return d
    
    def cleanup_old_records(self, days: int = 90):
        """Delete transfer records older than specified days.
        
        Args:
            days: Number of days to retain.
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cutoff = datetime.now().replace(microsecond=0)
            cutoff = cutoff.replace(day=cutoff.day - days)
            cutoff_str = cutoff.isoformat()
            
            # Delete old transfer files first (foreign key)
            cursor.execute('''
                DELETE FROM transfer_files 
                WHERE transfer_id IN (
                    SELECT transfer_id FROM transfers WHERE started_at < ?
                )
            ''', (cutoff_str,))
            
            # Delete old transfers
            cursor.execute('DELETE FROM transfers WHERE started_at < ?', (cutoff_str,))
            
            conn.commit()
            conn.close()

