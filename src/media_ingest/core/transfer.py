"""File transfer worker with progress tracking and checksum verification."""

import os
import shutil
import hashlib
import threading
import queue
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed


class FileTransferWorker:
    """Handles file transfer operations with progress tracking."""
    
    def __init__(self, settings: Dict, progress_callback: Callable = None):
        """Initialize file transfer worker.
        
        Args:
            settings: Global settings dictionary.
            progress_callback: Callback for progress updates.
        """
        self.settings = settings
        self.progress_callback = progress_callback
        
        self._transfer_queue = queue.Queue()
        self._active_transfers: Dict[str, Dict] = {}
        self._workers: List[threading.Thread] = []
        self._running = False
        self._lock = threading.RLock()
        
        # Ensure temp and drop directories exist
        temp_dir = settings.get('defaults', {}).get('temp_dir', '/tmp/media_ingest')
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        
        drop_location = settings.get('defaults', {}).get('drop_location', '/tmp/media_ingest_drop')
        Path(drop_location).mkdir(parents=True, exist_ok=True)
    
    def start(self, num_workers: int = None):
        """Start transfer worker threads.
        
        Args:
            num_workers: Number of concurrent transfer workers. Defaults to setting.
        """
        if self._running:
            return
        
        if num_workers is None:
            num_workers = self.settings.get('defaults', {}).get('concurrent_transfers', 1)
        
        self._running = True
        
        for i in range(num_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True, name=f"TransferWorker-{i}")
            worker.start()
            self._workers.append(worker)
        
        print(f"Started {num_workers} transfer worker(s)")
    
    def stop(self):
        """Stop all transfer workers."""
        self._running = False
        
        # Wait for workers to finish
        for worker in self._workers:
            worker.join(timeout=5)
        
        self._workers.clear()
        print("Transfer workers stopped")
    
    def queue_transfer(self, device_profile: Dict, device_info: Dict, 
                       transfer_id: str = None) -> str:
        """Queue a new transfer job.
        
        Args:
            device_profile: Device configuration profile.
            device_info: Device hardware information.
            transfer_id: Optional transfer ID (generated if not provided).
            
        Returns:
            Transfer ID.
        """
        if transfer_id is None:
            transfer_id = f"transfer_{uuid.uuid4().hex[:12]}"
        
        transfer_job = {
            'transfer_id': transfer_id,
            'device_profile': device_profile,
            'device_info': device_info,
            'status': 'queued',
            'queued_at': datetime.now().isoformat()
        }
        
        self._transfer_queue.put(transfer_job)
        print(f"Transfer queued: {transfer_id} for device {device_profile['name']}")
        
        return transfer_id
    
    def cancel_transfer(self, transfer_id: str) -> bool:
        """Cancel an active transfer.
        
        Args:
            transfer_id: Transfer ID to cancel.
            
        Returns:
            True if cancelled, False if not found or already completed.
        """
        with self._lock:
            if transfer_id in self._active_transfers:
                self._active_transfers[transfer_id]['cancelled'] = True
                print(f"Transfer {transfer_id} marked for cancellation")
                return True
            return False
    
    def _worker_loop(self):
        """Main worker loop for processing transfers."""
        while self._running:
            try:
                # Get next transfer job (with timeout to check _running periodically)
                transfer_job = self._transfer_queue.get(timeout=1)
                
                # Process the transfer
                self._process_transfer(transfer_job)
                
                self._transfer_queue.task_done()
            
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker error: {e}")
    
    def _process_transfer(self, transfer_job: Dict):
        """Process a single transfer job.
        
        Args:
            transfer_job: Transfer job dictionary.
        """
        transfer_id = transfer_job['transfer_id']
        device_profile = transfer_job['device_profile']
        device_info = transfer_job['device_info']
        
        # Mark as active
        start_time = datetime.now()
        with self._lock:
            self._active_transfers[transfer_id] = {
                'transfer_id': transfer_id,
                'device_id': device_profile['id'],
                'device_name': device_profile['name'],
                'status': 'in_progress',
                'started_at': start_time.isoformat(),
                'start_timestamp': start_time.timestamp(),
                'total_files': 0,
                'files_transferred': 0,
                'files_failed': 0,
                'files_skipped': 0,
                'total_size_bytes': 0,
                'bytes_transferred': 0,
                'transfer_speed_mbps': 0,
                'current_file': '',
                'error': None
            }
        
        try:
            # Prepare drop location first (needed for scanning)
            drop_location = device_profile.get('drop_location') or \
                          self.settings.get('defaults', {}).get('drop_location')
            drop_path = Path(drop_location)
            preserve_structure = device_profile.get('preserve_structure', True)
            
            # Scan for files to transfer (excluding files that already exist)
            source_path = device_info['mount_point']
            print(f"Scanning for files in {source_path}...")
            file_list = self._scan_files(
                source_path, 
                device_profile.get('file_types', []),
                drop_path,
                preserve_structure
            )
            print(f"Found {len(file_list)} files to transfer")
            
            if not file_list:
                print(f"No files found for transfer {transfer_id}")
                self._update_transfer_status(transfer_id, 'completed', 
                                            error='No matching files found')
                return
            
            # Update total counts
            total_files = len(file_list)
            total_size = sum(f['size'] for f in file_list)
            
            self._update_transfer_status(transfer_id, 'in_progress',
                                        total_files=total_files,
                                        total_size_bytes=total_size)
            drop_path.mkdir(parents=True, exist_ok=True)
            
            # Transfer files with multithreading
            naming_pattern = device_profile.get('naming_pattern', '{original}{ext}')
            preserve_structure = device_profile.get('preserve_structure', True)
            
            # Get thread pool size from settings (default to 4 concurrent copies)
            max_workers = self.settings.get('defaults', {}).get('concurrent_transfers', 4)
            print(f"Starting transfer with {max_workers} concurrent threads...")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all file copy tasks
                future_to_file = {}
                for idx, file_info in enumerate(file_list, start=1):
                    # Check if transfer was cancelled
                    with self._lock:
                        if not self._running or self._active_transfers.get(transfer_id, {}).get('cancelled', False):
                            print(f"Transfer {transfer_id} cancelled")
                            self._update_transfer_status(transfer_id, 'cancelled')
                            break
                    
                    # Submit file copy task to thread pool
                    future = executor.submit(
                        self._copy_single_file,
                        transfer_id,
                        file_info,
                        drop_path,
                        preserve_structure,
                        naming_pattern,
                        idx,
                        device_profile
                    )
                    future_to_file[future] = file_info
                
                # Process completed file copies as they finish
                for future in as_completed(future_to_file):
                    # Check if transfer was cancelled
                    with self._lock:
                        if not self._running or self._active_transfers.get(transfer_id, {}).get('cancelled', False):
                            print(f"Transfer {transfer_id} cancelled")
                            self._update_transfer_status(transfer_id, 'cancelled')
                            # Cancel remaining futures
                            for f in future_to_file:
                                f.cancel()
                            break
                    
                    file_info = future_to_file[future]
                    try:
                        result = future.result()
                        # Result is already handled in _copy_single_file
                    except Exception as e:
                        print(f"Error in thread pool for {file_info['name']}: {e}")
                        with self._lock:
                            self._active_transfers[transfer_id]['files_failed'] += 1
                
            
            # Mark as completed
            with self._lock:
                transfer = self._active_transfers[transfer_id]
                duration = (datetime.now() - datetime.fromisoformat(transfer['started_at'])).total_seconds()
                transfer['status'] = 'completed'
                transfer['completed_at'] = datetime.now().isoformat()
                transfer['duration_seconds'] = duration
                
                # Calculate final average speed
                if duration > 0:
                    bytes_per_second = transfer['bytes_transferred'] / duration
                    transfer['transfer_speed_mbps'] = round(bytes_per_second / (1024 * 1024), 2)
            
            self._send_progress_update(transfer_id)
            
            transferred_mb = transfer['bytes_transferred'] / (1024 * 1024)
            speed = transfer.get('transfer_speed_mbps', 0)
            skipped = transfer.get('files_skipped', 0)
            print(f"Transfer {transfer_id} completed:")
            print(f"  ✓ Transferred: {transfer['files_transferred']}/{transfer['total_files']} files ({transferred_mb:.1f} MB @ {speed} MB/s)")
            print(f"  ✗ Failed: {transfer['files_failed']}")
            if skipped > 0:
                print(f"  ⊙ Skipped: {skipped} (deleted during transfer)")
        
        except Exception as e:
            print(f"Transfer {transfer_id} failed: {e}")
            self._update_transfer_status(transfer_id, 'failed', error=str(e))
            self._send_progress_update(transfer_id)
        
        finally:
            # Remove from active after a delay to allow final status reads
            threading.Timer(5.0, lambda: self._remove_active_transfer(transfer_id)).start()
    
    def _scan_files(self, source_path: str, file_types: List[str], drop_path: Path = None, preserve_structure: bool = True) -> List[Dict]:
        """Scan source directory for matching files that need to be transferred.
        
        Args:
            source_path: Source directory path.
            file_types: List of file extensions to include (e.g., ['.jpg', '.mp4']). Use ['*'] for all files.
            drop_path: Destination directory path (for checking if files already exist).
            preserve_structure: Whether directory structure is preserved.
            
        Returns:
            List of file information dictionaries (excluding files that already exist).
        """
        files = []
        skipped_count = 0
        source = Path(source_path)
        print(f"  File types filter: {file_types if file_types else 'ALL'}")
        
        # Handle wildcard - '*' means all files
        if not file_types or '*' in file_types:
            extensions = None  # No filter, include all files
            print(f"  Including all file types")
        else:
            # Normalize extensions
            extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                         for ext in file_types]
            print(f"  Including extensions: {extensions}")
        
        for root, dirs, filenames in os.walk(source):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in filenames:
                file_path = Path(root) / filename
                
                # Skip hidden files and system files
                if filename.startswith('.'):
                    continue
                
                # Check extension filter
                if extensions and file_path.suffix.lower() not in extensions:
                    continue
                
                try:
                    stat = file_path.stat()
                    # Calculate relative path from source
                    relative_path = file_path.relative_to(source)
                    
                    # Check if file already exists at destination with same size
                    if drop_path:
                        if preserve_structure:
                            dest_file = drop_path / relative_path
                        else:
                            dest_file = drop_path / filename
                        
                        if dest_file.exists():
                            try:
                                dest_size = dest_file.stat().st_size
                                if dest_size == stat.st_size:
                                    # File already exists with same size - skip it
                                    skipped_count += 1
                                    continue
                            except Exception:
                                # If we can't check, include the file
                                pass
                    
                    files.append({
                        'path': str(file_path),
                        'name': filename,
                        'relative_path': str(relative_path),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime)
                    })
                except Exception as e:
                    print(f"Error scanning file {file_path}: {e}")
        
        if skipped_count > 0:
            print(f"  Skipped {skipped_count} files (already exist with same size)")
        
        return files
    
    def _copy_single_file(self, transfer_id: str, file_info: Dict, drop_path: Path, 
                          preserve_structure: bool, naming_pattern: str, counter: int, 
                          device_profile: Dict) -> bool:
        """Copy a single file (called by thread pool).
        
        Args:
            transfer_id: Transfer ID.
            file_info: File information dictionary.
            drop_path: Destination base path.
            preserve_structure: Whether to preserve directory structure.
            naming_pattern: File naming pattern.
            counter: File counter for naming.
            device_profile: Device profile configuration.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Check if source file still exists
            source_file = Path(file_info['path'])
            if not source_file.exists():
                # File was deleted
                with self._lock:
                    self._active_transfers[transfer_id]['files_skipped'] += 1
                return False
            
            # Determine destination path
            if preserve_structure and 'relative_path' in file_info:
                # Preserve directory structure
                dest_path = drop_path / file_info['relative_path']
                dest_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                # Flat structure with custom naming
                dest_name = self._generate_filename(
                    naming_pattern,
                    file_info,
                    device_profile,
                    counter
                )
                dest_path = drop_path / dest_name
            
            # Ensure unique filename
            dest_path = self._ensure_unique_path(dest_path)
            
            # Update current file
            self._update_transfer_status(transfer_id, 'in_progress',
                                        current_file=file_info['name'])
            
            # Copy file
            verify_checksum = self.settings.get('defaults', {}).get('verify_checksums', True)
            success = self._copy_file(str(source_file), str(dest_path), verify_checksum)
            
            if success:
                # Update progress
                with self._lock:
                    transfer = self._active_transfers[transfer_id]
                    transfer['files_transferred'] += 1
                    transfer['bytes_transferred'] += file_info['size']
                    
                    # Calculate transfer speed (MB/s)
                    elapsed = datetime.now().timestamp() - transfer['start_timestamp']
                    if elapsed > 0:
                        bytes_per_second = transfer['bytes_transferred'] / elapsed
                        transfer['transfer_speed_mbps'] = round(bytes_per_second / (1024 * 1024), 2)
                
                # Send progress update
                self._send_progress_update(transfer_id)
                
                # Delete source file if configured
                if device_profile.get('delete_after', False):
                    try:
                        os.remove(file_info['path'])
                    except Exception as e:
                        print(f"Error deleting source file: {e}")
                
                return True
            else:
                with self._lock:
                    self._active_transfers[transfer_id]['files_failed'] += 1
                self._send_progress_update(transfer_id)
                return False
                
        except FileNotFoundError:
            # File disappeared during copy
            with self._lock:
                self._active_transfers[transfer_id]['files_skipped'] += 1
            return False
        except Exception as e:
            print(f"Error copying {file_info['name']}: {e}")
            with self._lock:
                self._active_transfers[transfer_id]['files_failed'] += 1
            self._send_progress_update(transfer_id)
            return False
    
    def _copy_file(self, source: str, destination: str, verify_checksum: bool = True) -> bool:
        """Copy a file with optional checksum verification.
        
        Args:
            source: Source file path.
            destination: Destination file path.
            verify_checksum: Whether to verify with checksum.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Verify source exists
            if not os.path.exists(source):
                return False
            
            # Copy file
            shutil.copy2(source, destination)
            
            # Verify with checksum if enabled
            if verify_checksum:
                source_hash = self._calculate_checksum(source)
                dest_hash = self._calculate_checksum(destination)
                
                if source_hash != dest_hash:
                    print(f"⚠ Checksum mismatch: {os.path.basename(destination)}")
                    os.remove(destination)
                    return False
            
            return True
        
        except FileNotFoundError as e:
            # File disappeared during copy - skip silently
            return False
        except PermissionError as e:
            print(f"✗ Permission denied: {os.path.basename(source)}")
            return False
        except Exception as e:
            print(f"✗ Copy error ({type(e).__name__}): {os.path.basename(source)} - {e}")
            return False
    
    def _calculate_checksum(self, file_path: str, algorithm: str = 'md5') -> str:
        """Calculate checksum for a file.
        
        Args:
            file_path: Path to file.
            algorithm: Hash algorithm (md5, sha1, sha256).
            
        Returns:
            Hexadecimal hash string.
        """
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    def _generate_filename(self, pattern: str, file_info: Dict, 
                          device_profile: Dict, counter: int) -> str:
        """Generate filename from naming pattern.
        
        Args:
            pattern: Naming pattern with variables.
            file_info: File information dictionary.
            device_profile: Device profile dictionary.
            counter: Sequential counter.
            
        Returns:
            Generated filename.
        """
        now = datetime.now()
        file_path = Path(file_info['name'])
        
        # Sanitize device name for filename
        device_name = re.sub(r'[^\w\-]', '-', device_profile['name'])
        
        # Build replacement dictionary
        replacements = {
            'date': now.strftime('%Y-%m-%d'),
            'datetime': now.strftime('%Y-%m-%d_%H-%M-%S'),
            'device': device_name,
            'counter': str(counter),
            'original': file_path.stem,
            'ext': file_path.suffix,
            'year': now.strftime('%Y'),
            'month': now.strftime('%m'),
            'day': now.strftime('%d'),
            'uuid': uuid.uuid4().hex[:8]
        }
        
        # Replace variables
        result = pattern
        for key, value in replacements.items():
            # Handle formatted counters like {counter:04d}
            result = re.sub(rf'\{{{key}:0(\d+)d\}}', 
                          lambda m: value.zfill(int(m.group(1))), result)
            # Handle simple variables
            result = result.replace(f'{{{key}}}', value)
        
        return result
    
    def _ensure_unique_path(self, path: Path) -> Path:
        """Ensure path is unique by appending number if needed.
        
        Args:
            path: Desired file path.
            
        Returns:
            Unique file path.
        """
        if not path.exists():
            return path
        
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        counter = 1
        
        while True:
            new_path = parent / f"{stem}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1
    
    def _update_transfer_status(self, transfer_id: str, status: str, **kwargs):
        """Update transfer status.
        
        Args:
            transfer_id: Transfer ID.
            status: New status.
            **kwargs: Additional fields to update.
        """
        with self._lock:
            if transfer_id in self._active_transfers:
                transfer = self._active_transfers[transfer_id]
                transfer['status'] = status
                transfer.update(kwargs)
    
    def _send_progress_update(self, transfer_id: str):
        """Send progress update via callback.
        
        Args:
            transfer_id: Transfer ID.
        """
        if not self.progress_callback:
            return
        
        with self._lock:
            if transfer_id in self._active_transfers:
                transfer = self._active_transfers[transfer_id].copy()
        
        try:
            self.progress_callback(transfer)
        except Exception as e:
            print(f"Error in progress callback: {e}")
    
    def _remove_active_transfer(self, transfer_id: str):
        """Remove transfer from active list.
        
        Args:
            transfer_id: Transfer ID.
        """
        with self._lock:
            self._active_transfers.pop(transfer_id, None)
    
    def get_active_transfers(self) -> List[Dict]:
        """Get list of active transfers.
        
        Returns:
            List of transfer status dictionaries.
        """
        with self._lock:
            return list(self._active_transfers.values())
    
    def get_transfer_status(self, transfer_id: str) -> Optional[Dict]:
        """Get status of a specific transfer.
        
        Args:
            transfer_id: Transfer ID.
            
        Returns:
            Transfer status dictionary or None.
        """
        with self._lock:
            return self._active_transfers.get(transfer_id)

