"""
File client for handling file uploads and downloads in the LAN Video Calling Application
"""

import os
import time
import hashlib
import threading
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from shared.constants import *
from shared.protocol import Message, MessageType, FileChunk
from shared.utils import logger, format_file_size, safe_filename


class FileTransfer:
    """Represents a file transfer operation"""
    
    def __init__(self, file_id: str, filename: str, file_size: int, 
                 transfer_type: str = "upload"):
        self.file_id = file_id
        self.filename = filename
        self.file_size = file_size
        self.transfer_type = transfer_type  # "upload" or "download"
        self.progress = 0.0
        self.bytes_transferred = 0
        self.chunks_transferred = 0
        self.total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
        self.start_time = time.time()
        self.is_complete = False
        self.is_cancelled = False
        self.error_message: Optional[str] = None
    
    def update_progress(self, bytes_transferred: int, chunks_transferred: int):
        """Update transfer progress"""
        self.bytes_transferred = bytes_transferred
        self.chunks_transferred = chunks_transferred
        self.progress = (chunks_transferred / self.total_chunks) * 100.0 if self.total_chunks > 0 else 0.0
    
    def get_transfer_speed(self) -> float:
        """Get transfer speed in bytes per second"""
        elapsed = time.time() - self.start_time
        return self.bytes_transferred / elapsed if elapsed > 0 else 0.0
    
    def get_eta(self) -> float:
        """Get estimated time to completion in seconds"""
        speed = self.get_transfer_speed()
        if speed > 0:
            remaining_bytes = self.file_size - self.bytes_transferred
            return remaining_bytes / speed
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'file_id': self.file_id,
            'filename': self.filename,
            'file_size': self.file_size,
            'transfer_type': self.transfer_type,
            'progress': self.progress,
            'bytes_transferred': self.bytes_transferred,
            'chunks_transferred': self.chunks_transferred,
            'total_chunks': self.total_chunks,
            'transfer_speed': self.get_transfer_speed(),
            'eta': self.get_eta(),
            'is_complete': self.is_complete,
            'is_cancelled': self.is_cancelled,
            'error_message': self.error_message
        }


class FileClient:
    """Handles file upload and download operations"""
    
    def __init__(self, main_client):
        self.main_client = main_client
        
        # Active transfers
        self.active_transfers: Dict[str, FileTransfer] = {}
        self.transfer_lock = threading.RLock()
        
        # Callbacks
        self.transfer_callbacks: Dict[str, Callable] = {}
        
        # Statistics
        self.files_uploaded = 0
        self.files_downloaded = 0
        self.total_bytes_uploaded = 0
        self.total_bytes_downloaded = 0
        self.start_time = time.time()
    
    def upload_file(self, file_path: str, room_id: str = None) -> bool:
        """Upload a file to the server"""
        if not self.main_client.is_authenticated:
            logger.warning("Cannot upload file: not authenticated")
            return False
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False
            
            # Get file info
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            
            # Check file size limit
            if file_size > MAX_FILE_SIZE:
                logger.error(f"File size exceeds limit: {format_file_size(file_size)}")
                return False
            
            # Generate file ID
            import uuid
            file_id = str(uuid.uuid4())
            
            # Create transfer object
            transfer = FileTransfer(file_id, filename, file_size, "upload")
            
            with self.transfer_lock:
                self.active_transfers[file_id] = transfer
            
            # Start upload thread
            upload_thread = threading.Thread(
                target=self._upload_file_thread,
                args=(file_id, file_path, room_id),
                daemon=True
            )
            upload_thread.start()
            
            logger.info(f"Started upload: {filename} ({format_file_size(file_size)})")
            return True
            
        except Exception as e:
            logger.error(f"Error starting file upload: {e}")
            return False
    
    def _upload_file_thread(self, file_id: str, file_path: str, room_id: str = None):
        """Upload file in background thread"""
        try:
            with self.transfer_lock:
                transfer = self.active_transfers.get(file_id)
                if not transfer:
                    return
            
            # Send upload start message
            message = Message(
                msg_type=MessageType.FILE_UPLOAD_START,
                data={
                    'filename': transfer.filename,
                    'file_size': transfer.file_size,
                    'room_id': room_id or self.main_client.current_room_id
                },
                sender=self.main_client.user_id
            )
            
            if not self.main_client.send_message(message):
                self._set_transfer_error(file_id, "Failed to send upload start message")
                return
            
            # Read and send file in chunks
            with open(file_path, 'rb') as f:
                chunk_index = 0
                bytes_transferred = 0
                
                while True:
                    chunk_data = f.read(CHUNK_SIZE)
                    if not chunk_data:
                        break
                    
                    # Calculate checksum
                    checksum = hashlib.md5(chunk_data).hexdigest()
                    
                    # Create chunk message
                    chunk_msg = Message(
                        msg_type=MessageType.FILE_UPLOAD_CHUNK,
                        data={
                            'file_id': file_id,
                            'chunk_index': chunk_index,
                            'chunk_data': chunk_data.hex(),  # Convert to hex string
                            'checksum': checksum
                        },
                        sender=self.main_client.user_id
                    )
                    
                    # Send chunk
                    if not self.main_client.send_message(chunk_msg):
                        self._set_transfer_error(file_id, "Failed to send chunk")
                        return
                    
                    # Update progress
                    bytes_transferred += len(chunk_data)
                    chunk_index += 1
                    
                    with self.transfer_lock:
                        if file_id in self.active_transfers:
                            self.active_transfers[file_id].update_progress(bytes_transferred, chunk_index)
                            
                            # Call progress callback
                            if 'on_upload_progress' in self.transfer_callbacks:
                                self.transfer_callbacks['on_upload_progress'](self.active_transfers[file_id])
                    
                    # Small delay to prevent overwhelming the server
                    time.sleep(0.01)
            
            # Mark transfer as complete
            with self.transfer_lock:
                if file_id in self.active_transfers:
                    self.active_transfers[file_id].is_complete = True
                    self.files_uploaded += 1
                    self.total_bytes_uploaded += transfer.file_size
                    
                    # Call completion callback
                    if 'on_upload_complete' in self.transfer_callbacks:
                        self.transfer_callbacks['on_upload_complete'](transfer)
            
            logger.info(f"Upload completed: {transfer.filename}")
            
        except Exception as e:
            logger.error(f"Error in upload thread: {e}")
            self._set_transfer_error(file_id, str(e))
    
    def download_file(self, file_id: str, save_path: str) -> bool:
        """Download a file from the server"""
        if not self.main_client.is_authenticated:
            logger.warning("Cannot download file: not authenticated")
            return False
        
        try:
            # Send download request
            message = Message(
                msg_type=MessageType.FILE_DOWNLOAD_REQUEST,
                data={'file_id': file_id},
                sender=self.main_client.user_id
            )
            
            if not self.main_client.send_message(message):
                logger.error("Failed to send download request")
                return False
            
            # Create transfer object (will be updated when we get file info)
            transfer = FileTransfer(file_id, "unknown", 0, "download")
            
            with self.transfer_lock:
                self.active_transfers[file_id] = transfer
            
            logger.info(f"Download requested: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting file download: {e}")
            return False
    
    def handle_download_info(self, file_info: Dict[str, Any]):
        """Handle download file info from server"""
        try:
            file_id = file_info['file_id']
            filename = file_info['filename']
            file_size = file_info['file_size']
            file_path = file_info['file_path']
            
            with self.transfer_lock:
                if file_id in self.active_transfers:
                    transfer = self.active_transfers[file_id]
                    transfer.filename = filename
                    transfer.file_size = file_size
                    transfer.total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
            
            # Start download thread
            download_thread = threading.Thread(
                target=self._download_file_thread,
                args=(file_id, filename, file_size, file_path),
                daemon=True
            )
            download_thread.start()
            
        except Exception as e:
            logger.error(f"Error handling download info: {e}")
    
    def _download_file_thread(self, file_id: str, filename: str, file_size: int, file_path: str):
        """Download file in background thread"""
        try:
            # Create save directory
            save_dir = Path(file_path).parent
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Download file in chunks
            with open(file_path, 'wb') as f:
                chunk_index = 0
                bytes_downloaded = 0
                
                while bytes_downloaded < file_size:
                    # Request chunk
                    chunk_msg = Message(
                        msg_type=MessageType.FILE_DOWNLOAD_CHUNK,
                        data={
                            'file_id': file_id,
                            'chunk_index': chunk_index
                        },
                        sender=self.main_client.user_id
                    )
                    
                    if not self.main_client.send_message(chunk_msg):
                        self._set_transfer_error(file_id, "Failed to request chunk")
                        return
                    
                    # Wait for chunk response (simplified - in real implementation, 
                    # you'd need proper message handling)
                    time.sleep(0.1)  # Placeholder
                    
                    # Update progress
                    chunk_size = min(CHUNK_SIZE, file_size - bytes_downloaded)
                    bytes_downloaded += chunk_size
                    chunk_index += 1
                    
                    with self.transfer_lock:
                        if file_id in self.active_transfers:
                            self.active_transfers[file_id].update_progress(bytes_downloaded, chunk_index)
                            
                            # Call progress callback
                            if 'on_download_progress' in self.transfer_callbacks:
                                self.transfer_callbacks['on_download_progress'](self.active_transfers[file_id])
            
            # Mark transfer as complete
            with self.transfer_lock:
                if file_id in self.active_transfers:
                    self.active_transfers[file_id].is_complete = True
                    self.files_downloaded += 1
                    self.total_bytes_downloaded += file_size
                    
                    # Call completion callback
                    if 'on_download_complete' in self.transfer_callbacks:
                        self.transfer_callbacks['on_download_complete'](self.active_transfers[file_id])
            
            logger.info(f"Download completed: {filename}")
            
        except Exception as e:
            logger.error(f"Error in download thread: {e}")
            self._set_transfer_error(file_id, str(e))
    
    def cancel_transfer(self, file_id: str) -> bool:
        """Cancel an active transfer"""
        with self.transfer_lock:
            if file_id in self.active_transfers:
                transfer = self.active_transfers[file_id]
                transfer.is_cancelled = True
                
                # Send cancel message to server
                cancel_msg = Message(
                    msg_type=MessageType.FILE_DELETE,
                    data={'file_id': file_id},
                    sender=self.main_client.user_id
                )
                self.main_client.send_message(cancel_msg)
                
                logger.info(f"Transfer cancelled: {transfer.filename}")
                return True
        
        return False
    
    def _set_transfer_error(self, file_id: str, error_message: str):
        """Set transfer error"""
        with self.transfer_lock:
            if file_id in self.active_transfers:
                self.active_transfers[file_id].error_message = error_message
                
                # Call error callback
                if 'on_transfer_error' in self.transfer_callbacks:
                    self.transfer_callbacks['on_transfer_error'](self.active_transfers[file_id])
    
    def get_active_transfers(self) -> List[FileTransfer]:
        """Get list of active transfers"""
        with self.transfer_lock:
            return list(self.active_transfers.values())
    
    def get_transfer(self, file_id: str) -> Optional[FileTransfer]:
        """Get transfer by ID"""
        with self.transfer_lock:
            return self.active_transfers.get(file_id)
    
    def remove_completed_transfer(self, file_id: str):
        """Remove completed transfer from active list"""
        with self.transfer_lock:
            if file_id in self.active_transfers:
                transfer = self.active_transfers[file_id]
                if transfer.is_complete or transfer.is_cancelled:
                    del self.active_transfers[file_id]
    
    def set_transfer_callback(self, event: str, callback: Callable):
        """Set transfer callback"""
        self.transfer_callbacks[event] = callback
    
    def get_file_stats(self) -> Dict[str, Any]:
        """Get file transfer statistics"""
        uptime = time.time() - self.start_time
        
        return {
            'files_uploaded': self.files_uploaded,
            'files_downloaded': self.files_downloaded,
            'total_bytes_uploaded': self.total_bytes_uploaded,
            'total_bytes_downloaded': self.total_bytes_downloaded,
            'total_bytes_uploaded_formatted': format_file_size(self.total_bytes_uploaded),
            'total_bytes_downloaded_formatted': format_file_size(self.total_bytes_downloaded),
            'active_transfers': len(self.active_transfers),
            'uptime': uptime,
            'upload_speed': self.total_bytes_uploaded / uptime if uptime > 0 else 0,
            'download_speed': self.total_bytes_downloaded / uptime if uptime > 0 else 0
        }
