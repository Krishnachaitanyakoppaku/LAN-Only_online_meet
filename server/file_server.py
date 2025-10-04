"""
File server for handling file uploads and downloads in the LAN Video Calling Application
"""

import os
import time
import threading
import hashlib
import uuid
from typing import Dict, List, Optional, Any, BinaryIO
from pathlib import Path
from shared.constants import *
from shared.utils import logger, file_manager, safe_filename, format_file_size
from shared.protocol import FileChunk, Message, MessageType


class FileTransfer:
    """Represents an active file transfer"""
    
    def __init__(self, file_id: str, filename: str, file_size: int, 
                 user_id: str, room_id: Optional[str] = None):
        self.file_id = file_id
        self.filename = filename
        self.file_size = file_size
        self.user_id = user_id
        self.room_id = room_id
        self.uploaded_chunks: Dict[int, bytes] = {}
        self.total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
        self.uploaded_size = 0
        self.start_time = time.time()
        self.is_complete = False
        self.file_path: Optional[str] = None
        self.checksum: Optional[str] = None
    
    def add_chunk(self, chunk_index: int, chunk_data: bytes) -> bool:
        """Add a chunk to the transfer"""
        if chunk_index in self.uploaded_chunks:
            return False  # Chunk already exists
        
        self.uploaded_chunks[chunk_index] = chunk_data
        self.uploaded_size += len(chunk_data)
        
        # Check if transfer is complete
        if len(self.uploaded_chunks) == self.total_chunks:
            self.is_complete = True
            return True
        
        return False
    
    def get_progress(self) -> float:
        """Get upload progress as percentage"""
        if self.total_chunks == 0:
            return 100.0
        return (len(self.uploaded_chunks) / self.total_chunks) * 100.0
    
    def assemble_file(self) -> bool:
        """Assemble the complete file from chunks"""
        try:
            # Create user directory
            user_dir = Path(UPLOAD_DIR) / self.user_id
            user_dir.mkdir(parents=True, exist_ok=True)
            
            # Create file path
            safe_filename_str = safe_filename(self.filename)
            self.file_path = str(user_dir / safe_filename_str)
            
            # Write file in correct order
            with open(self.file_path, 'wb') as f:
                for i in range(self.total_chunks):
                    if i in self.uploaded_chunks:
                        f.write(self.uploaded_chunks[i])
                    else:
                        logger.error(f"Missing chunk {i} for file {self.file_id}")
                        return False
            
            # Calculate checksum
            self.checksum = self._calculate_checksum()
            
            # Clean up chunks from memory
            self.uploaded_chunks.clear()
            
            logger.info(f"File assembled: {self.filename} ({format_file_size(self.file_size)})")
            return True
            
        except Exception as e:
            logger.error(f"Error assembling file {self.file_id}: {e}")
            return False
    
    def _calculate_checksum(self) -> str:
        """Calculate MD5 checksum of the file"""
        try:
            with open(self.file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Error calculating checksum: {e}")
            return ""


class FileServer:
    """Handles file uploads and downloads"""
    
    def __init__(self, user_manager, room_manager):
        self.user_manager = user_manager
        self.room_manager = room_manager
        self.active_transfers: Dict[str, FileTransfer] = {}
        self.completed_files: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        self.cleanup_thread = threading.Thread(target=self._cleanup_old_transfers, daemon=True)
        self.cleanup_thread.start()
        
        # Create upload directory
        Path(UPLOAD_DIR).mkdir(exist_ok=True)
    
    def start_file_upload(self, user_id: str, filename: str, file_size: int, 
                         room_id: Optional[str] = None) -> str:
        """Start a new file upload"""
        with self.lock:
            # Validate file size
            if file_size > MAX_FILE_SIZE:
                raise ValueError(f"File size exceeds maximum limit of {format_file_size(MAX_FILE_SIZE)}")
            
            # Check if user exists
            user = self.user_manager.get_user(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            
            # Create transfer object
            transfer = FileTransfer(
                file_id=file_id,
                filename=filename,
                file_size=file_size,
                user_id=user_id,
                room_id=room_id
            )
            
            self.active_transfers[file_id] = transfer
            
            logger.info(f"Started file upload: {filename} ({format_file_size(file_size)}) by {user.username}")
            
            return file_id
    
    def upload_chunk(self, file_id: str, chunk_index: int, chunk_data: bytes, 
                    checksum: str) -> bool:
        """Upload a file chunk"""
        with self.lock:
            transfer = self.active_transfers.get(file_id)
            if not transfer:
                return False
            
            # Verify chunk checksum
            if hashlib.md5(chunk_data).hexdigest() != checksum:
                logger.error(f"Checksum mismatch for chunk {chunk_index} of file {file_id}")
                return False
            
            # Add chunk
            is_complete = transfer.add_chunk(chunk_index, chunk_data)
            
            if is_complete:
                # Assemble file
                if transfer.assemble_file():
                    # Move to completed files
                    file_info = {
                        'file_id': file_id,
                        'filename': transfer.filename,
                        'file_size': transfer.file_size,
                        'user_id': transfer.user_id,
                        'room_id': transfer.room_id,
                        'file_path': transfer.file_path,
                        'checksum': transfer.checksum,
                        'upload_time': time.time(),
                        'upload_duration': time.time() - transfer.start_time
                    }
                    
                    self.completed_files[file_id] = file_info
                    
                    # Add to room shared files if applicable
                    if transfer.room_id:
                        self.room_manager.add_shared_file(transfer.room_id, file_info)
                    
                    # Remove from active transfers
                    del self.active_transfers[file_id]
                    
                    logger.info(f"File upload completed: {transfer.filename}")
                    return True
                else:
                    # Failed to assemble
                    del self.active_transfers[file_id]
                    return False
            
            return True
    
    def get_upload_progress(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get upload progress for a file"""
        with self.lock:
            transfer = self.active_transfers.get(file_id)
            if not transfer:
                return None
            
            return {
                'file_id': file_id,
                'filename': transfer.filename,
                'progress': transfer.get_progress(),
                'uploaded_size': transfer.uploaded_size,
                'total_size': transfer.file_size,
                'chunks_uploaded': len(transfer.uploaded_chunks),
                'total_chunks': transfer.total_chunks
            }
    
    def list_user_files(self, user_id: str) -> List[Dict[str, Any]]:
        """List files uploaded by a user"""
        with self.lock:
            user_files = []
            for file_info in self.completed_files.values():
                if file_info['user_id'] == user_id:
                    user_files.append({
                        'file_id': file_info['file_id'],
                        'filename': file_info['filename'],
                        'file_size': file_info['file_size'],
                        'upload_time': file_info['upload_time'],
                        'checksum': file_info['checksum']
                    })
            return user_files
    
    def list_room_files(self, room_id: str) -> List[Dict[str, Any]]:
        """List files shared in a room"""
        return self.room_manager.get_shared_files(room_id)
    
    def download_file(self, file_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Prepare file for download"""
        with self.lock:
            file_info = self.completed_files.get(file_id)
            if not file_info:
                return None
            
            # Check if user has access to the file
            if file_info['user_id'] != user_id:
                # Check if user is in the same room
                if file_info['room_id']:
                    user = self.user_manager.get_user(user_id)
                    if not user or user.room_id != file_info['room_id']:
                        return None
            
            # Check if file exists
            if not os.path.exists(file_info['file_path']):
                logger.error(f"File not found: {file_info['file_path']}")
                return None
            
            return {
                'file_id': file_id,
                'filename': file_info['filename'],
                'file_size': file_info['file_size'],
                'file_path': file_info['file_path'],
                'checksum': file_info['checksum']
            }
    
    def delete_file(self, file_id: str, user_id: str) -> bool:
        """Delete a file"""
        with self.lock:
            file_info = self.completed_files.get(file_id)
            if not file_info:
                return False
            
            # Check permissions (only owner can delete)
            if file_info['user_id'] != user_id:
                return False
            
            try:
                # Delete file from filesystem
                if os.path.exists(file_info['file_path']):
                    os.remove(file_info['file_path'])
                
                # Remove from completed files
                del self.completed_files[file_id]
                
                logger.info(f"File deleted: {file_info['filename']} by user {user_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error deleting file {file_id}: {e}")
                return False
    
    def get_file_chunk(self, file_path: str, chunk_index: int) -> Optional[bytes]:
        """Get a chunk of a file for download"""
        try:
            with open(file_path, 'rb') as f:
                f.seek(chunk_index * CHUNK_SIZE)
                chunk_data = f.read(CHUNK_SIZE)
                return chunk_data
        except Exception as e:
            logger.error(f"Error reading file chunk: {e}")
            return None
    
    def get_file_chunks_count(self, file_size: int) -> int:
        """Get total number of chunks for a file"""
        return (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
    
    def _cleanup_old_transfers(self):
        """Clean up old incomplete transfers"""
        while True:
            try:
                time.sleep(300)  # Check every 5 minutes
                current_time = time.time()
                
                with self.lock:
                    old_transfers = []
                    for file_id, transfer in self.active_transfers.items():
                        # Remove transfers older than 1 hour
                        if current_time - transfer.start_time > 3600:
                            old_transfers.append(file_id)
                    
                    for file_id in old_transfers:
                        transfer = self.active_transfers[file_id]
                        logger.info(f"Cleaning up old transfer: {transfer.filename}")
                        del self.active_transfers[file_id]
                        
            except Exception as e:
                logger.error(f"Error in transfer cleanup: {e}")
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get file server statistics"""
        with self.lock:
            total_files = len(self.completed_files)
            active_transfers = len(self.active_transfers)
            total_size = sum(f['file_size'] for f in self.completed_files.values())
            
            return {
                'total_files': total_files,
                'active_transfers': active_transfers,
                'total_storage_used': total_size,
                'total_storage_used_formatted': format_file_size(total_size)
            }
    
    def cancel_upload(self, file_id: str, user_id: str) -> bool:
        """Cancel an active upload"""
        with self.lock:
            transfer = self.active_transfers.get(file_id)
            if not transfer or transfer.user_id != user_id:
                return False
            
            # Remove from active transfers
            del self.active_transfers[file_id]
            
            logger.info(f"Upload cancelled: {transfer.filename} by user {user_id}")
            return True
