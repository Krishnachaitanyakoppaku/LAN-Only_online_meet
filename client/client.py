import socket
import threading
import os
import sys
import uuid
from tkinter import simpledialog
import pyaudio
import queue

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared import protocol
from client.gui_client import ClientGUI

class Client:
    def __init__(self, host='localhost'):
        self.host = host
        self.control_port = protocol.TCP_CONTROL_PORT
        self.file_port = protocol.TCP_FILE_PORT
        self.audio_port = protocol.UDP_AUDIO_STREAM_PORT
        self.control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.file_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.files = {}
        self.gui = None
        self.audio = pyaudio.PyAudio()
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.jitter_buffer = queue.Queue()

    def start(self):
        self.control_sock.connect((self.host, self.control_port))
        self.file_sock.connect((self.host, self.file_port))
        self.audio_sock.bind(('', 0)) # Bind to a random available port

        self.gui = ClientGUI(self)

        username = simpledialog.askstring("Username", "Enter your username:", parent=self.gui.root)
        if not username:
            return
        
        audio_port = self.audio_sock.getsockname()[1]
        register_message = protocol.create_message(protocol.REGISTER, {'username': username, 'audio_port': audio_port})
        self.control_sock.send(register_message)

        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()

        # send_audio_thread = threading.Thread(target=self.send_audio)
        # send_audio_thread.start()

        # receive_audio_thread = threading.Thread(target=self.receive_audio)
        # receive_audio_thread.start()

        self.gui.start()

    def send_audio(self):
        stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                                rate=self.RATE, input=True,
                                frames_per_buffer=self.CHUNK)
        while True:
            data = stream.read(self.CHUNK)
            self.audio_sock.sendto(data, (self.host, self.audio_port))

    def receive_audio(self):
        stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                                rate=self.RATE, output=True,
                                frames_per_buffer=self.CHUNK)
        while True:
            data, addr = self.audio_sock.recvfrom(self.CHUNK * 2)
            self.jitter_buffer.put(data)
            if self.jitter_buffer.qsize() > 10: # Basic jitter buffer
                stream.write(self.jitter_buffer.get())

    def send_chat_message(self, message):
        chat_message = protocol.create_message(protocol.CHAT, {'message': message})
        self.control_sock.send(chat_message)

    def upload_file(self, file_path):
        if not os.path.exists(file_path):
            self.gui.update_chat_log(f"[!] File not found: {file_path}")
            return

        file_size = os.path.getsize(file_path)
        file_id = str(uuid.uuid4())
        file_info = {
            'id': file_id,
            'filename': os.path.basename(file_path),
            'size': file_size
        }
        self.files[file_id] = file_info

        meta_message = protocol.create_message(protocol.FILE_META, file_info)
        self.file_sock.send(meta_message)

        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                self.file_sock.sendall(chunk)
        self.file_sock.sendall(b'EOF')
        self.gui.update_chat_log(f"[*] File {file_info['filename']} uploaded successfully.")

    def download_file(self, file_id, output_path):
        if file_id not in self.files:
            self.gui.update_chat_log(f"[!] File ID not found: {file_id}")
            return

        file_info = self.files[file_id]
        get_message = protocol.create_message(protocol.FILE_GET, {'id': file_id})
        self.file_sock.send(get_message)

        with open(output_path, 'wb') as f:
            total_received = 0
            while total_received < file_info['size']:
                chunk = self.file_sock.recv(4096)
                if not chunk:
                    break
                f.write(chunk)
                total_received += len(chunk)
                progress = (total_received / file_info['size']) * 100
                self.gui.update_chat_log(f"[*] Downloading {file_info['filename']}: {progress:.2f}%")
        self.gui.update_chat_log(f"\n[*] File {file_info['filename']} downloaded successfully.")

    def receive(self):
        while True:
            try:
                data = self.control_sock.recv(1024)
                if not data:
                    break
                
                message = protocol.parse_message(data)
                self.gui.queue.put(message)

            except Exception as e:
                self.gui.queue.put(f'[!] Error: {e}')
                break

if __name__ == '__main__':
    client = Client()
    client.start()
