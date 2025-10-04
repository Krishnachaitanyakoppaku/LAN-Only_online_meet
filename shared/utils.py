"""
Utility functions for the LAN Video Calling Application
"""

import os
import sys
import time
import hashlib
import threading
import queue
from typing import Any, Callable, Optional, List, Dict
from pathlib import Path


def get_local_ip() -> str:
    """Get local IP address"""
    import socket
    try:
        # Connect to a remote server to get local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception:
        return "127.0.0.1"


def get_available_port(start_port: int = 8000, end_port: int = 9000) -> int:
    """Find an available port in the given range"""
    import socket
    
    for port in range(start_port, end_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No available ports in range {start_port}-{end_port}")


def create_directory(path: str) -> None:
    """Create directory if it doesn't exist"""
    Path(path).mkdir(parents=True, exist_ok=True)


def get_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Error calculating file hash: {e}")
        return ""


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def format_duration(seconds: float) -> str:
    """Format duration in human readable format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def get_timestamp() -> str:
    """Get formatted timestamp"""
    return time.strftime("%Y-%m-%d %H:%M:%S")


def safe_filename(filename: str) -> str:
    """Convert filename to safe format"""
    import re
    # Remove or replace invalid characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(safe_name) > 255:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:255-len(ext)] + ext
    return safe_name


class ThreadSafeQueue:
    """Thread-safe queue wrapper"""
    
    def __init__(self, maxsize: int = 0):
        self._queue = queue.Queue(maxsize=maxsize)
        self._lock = threading.Lock()
    
    def put(self, item: Any, block: bool = True, timeout: Optional[float] = None) -> None:
        """Put item in queue"""
        self._queue.put(item, block=block, timeout=timeout)
    
    def get(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """Get item from queue"""
        return self._queue.get(block=block, timeout=timeout)
    
    def empty(self) -> bool:
        """Check if queue is empty"""
        return self._queue.empty()
    
    def size(self) -> int:
        """Get queue size"""
        return self._queue.qsize()
    
    def clear(self) -> None:
        """Clear queue"""
        with self._lock:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break


class RateLimiter:
    """Rate limiter for controlling message frequency"""
    
    def __init__(self, max_requests: int, time_window: float):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.lock = threading.Lock()
    
    def is_allowed(self) -> bool:
        """Check if request is allowed"""
        with self.lock:
            now = time.time()
            # Remove old requests
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.time_window]
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False


class ConnectionManager:
    """Manage network connections"""
    
    def __init__(self):
        self.connections: Dict[str, Any] = {}
        self.lock = threading.Lock()
    
    def add_connection(self, connection_id: str, connection: Any) -> None:
        """Add a connection"""
        with self.lock:
            self.connections[connection_id] = connection
    
    def remove_connection(self, connection_id: str) -> None:
        """Remove a connection"""
        with self.lock:
            if connection_id in self.connections:
                del self.connections[connection_id]
    
    def get_connection(self, connection_id: str) -> Optional[Any]:
        """Get a connection"""
        with self.lock:
            return self.connections.get(connection_id)
    
    def get_all_connections(self) -> Dict[str, Any]:
        """Get all connections"""
        with self.lock:
            return self.connections.copy()
    
    def broadcast(self, message: Any, exclude: Optional[str] = None) -> None:
        """Broadcast message to all connections"""
        with self.lock:
            for conn_id, connection in self.connections.items():
                if exclude and conn_id == exclude:
                    continue
                try:
                    if hasattr(connection, 'send'):
                        connection.send(message)
                except Exception as e:
                    print(f"Error broadcasting to {conn_id}: {e}")


class FileManager:
    """Manage file operations"""
    
    def __init__(self, base_dir: str = "files"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.upload_dir = self.base_dir / "uploads"
        self.download_dir = self.base_dir / "downloads"
        self.upload_dir.mkdir(exist_ok=True)
        self.download_dir.mkdir(exist_ok=True)
    
    def save_file(self, file_data: bytes, filename: str, user_id: str) -> str:
        """Save uploaded file"""
        safe_filename_str = safe_filename(filename)
        user_dir = self.upload_dir / user_id
        user_dir.mkdir(exist_ok=True)
        
        file_path = user_dir / safe_filename_str
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        return str(file_path)
    
    def get_file(self, file_path: str) -> Optional[bytes]:
        """Get file data"""
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file"""
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            return False
    
    def list_user_files(self, user_id: str) -> List[Dict[str, Any]]:
        """List files for a user"""
        user_dir = self.upload_dir / user_id
        if not user_dir.exists():
            return []
        
        files = []
        for file_path in user_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    'filename': file_path.name,
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                    'path': str(file_path)
                })
        
        return files


class Logger:
    """Simple logger for the application"""
    
    def __init__(self, log_file: str = "app.log"):
        self.log_file = log_file
        self.lock = threading.Lock()
    
    def log(self, level: str, message: str) -> None:
        """Log a message"""
        timestamp = get_timestamp()
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        with self.lock:
            try:
                with open(self.log_file, 'a') as f:
                    f.write(log_entry)
            except Exception as e:
                print(f"Error writing to log: {e}")
        
        # Also print to console
        print(f"[{level}] {message}")
    
    def info(self, message: str) -> None:
        """Log info message"""
        self.log("INFO", message)
    
    def warning(self, message: str) -> None:
        """Log warning message"""
        self.log("WARNING", message)
    
    def error(self, message: str) -> None:
        """Log error message"""
        self.log("ERROR", message)
    
    def debug(self, message: str) -> None:
        """Log debug message"""
        self.log("DEBUG", message)


# Global instances
logger = Logger()
file_manager = FileManager()
connection_manager = ConnectionManager()
