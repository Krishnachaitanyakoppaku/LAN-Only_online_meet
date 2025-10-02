import socket
import threading
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared import protocol
from server.gui_server import ServerGUI

class Server:
    def __init__(self, host='0.0.0.0'):
        self.host = host
        self.control_port = protocol.TCP_CONTROL_PORT
        self.file_port = protocol.TCP_FILE_PORT
        self.clients = {}
        self.files = {}
        self.control_sock = None
        self.file_sock = None
        self.gui = None
        self.listening = False

    def start_listening(self):
        self.control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.file_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.control_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.file_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.control_sock.bind((self.host, self.control_port))
        self.file_sock.bind((self.host, self.file_port))
        os.makedirs("session_files", exist_ok=True)

        self.control_sock.listen(5)
        self.file_sock.listen(5)
        self.listening = True
        self.gui.update_log(f'[*] Listening for control connections on {self.host}:{self.control_port}')
        self.gui.update_log(f'[*] Listening for file connections on {self.host}:{self.file_port}')

        control_thread = threading.Thread(target=self.handle_control_connections)
        control_thread.start()

        file_thread = threading.Thread(target=self.handle_file_connections)
        file_thread.start()

    def stop_listening(self):
        self.listening = False
        self.control_sock.close()
        self.file_sock.close()
        self.gui.update_log("[*] Server stopped.")

    def handle_control_connections(self):
        while self.listening:
            try:
                client, address = self.control_sock.accept()
                self.gui.update_log(f'[*] Accepted control connection from {address[0]}:{address[1]}')
                threading.Thread(target=self.handle_client, args=(client,)).start()
            except OSError:
                break

    def handle_file_connections(self):
        while self.listening:
            try:
                client, address = self.file_sock.accept()
                self.gui.update_log(f'[*] Accepted file connection from {address[0]}:{address[1]}')
                threading.Thread(target=self.handle_file_client, args=(client,)).start()
            except OSError:
                break

    def handle_client(self, client_socket):
        username = None
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                message = protocol.parse_message(data)
                
                if message['type'] == protocol.REGISTER:
                    username = message['payload']['username']
                    self.clients[client_socket] = username
                    join_notification = protocol.create_message(protocol.CHAT, {
                        'username': 'Server',
                        'message': f'{username} has joined the chat.'
                    })
                    self.broadcast(join_notification)
                    self.gui.update_log(f"[*] {username} has joined the chat.")
                
                elif message['type'] == protocol.CHAT:
                    chat_message = protocol.create_message(protocol.CHAT, {
                        'username': self.clients[client_socket],
                        'message': message['payload']['message']
                    })
                    self.broadcast(chat_message)

            except Exception as e:
                self.gui.update_log(f'[!] Error: {e}')
                break
        
        if username:
            del self.clients[client_socket]
            leave_notification = protocol.create_message(protocol.CHAT, {
                'username': 'Server',
                'message': f'{username} has left the chat.'
            })
            self.broadcast(leave_notification)
            self.gui.update_log(f"[*] {username} has left the chat.")

        client_socket.close()

    def handle_file_client(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break

                message = protocol.parse_message(data)

                if message['type'] == protocol.FILE_META:
                    file_info = message['payload']
                    self.files[file_info['id']] = file_info
                    file_notification = protocol.create_message(protocol.FILE_META, file_info)
                    self.broadcast(file_notification)
                    self.gui.update_log(f"[*] New file available: {file_info['filename']}")

                    with open(os.path.join("session_files", file_info['filename']), 'wb') as f:
                        while True:
                            chunk_data = client_socket.recv(4096)
                            if not chunk_data:
                                break
                            f.write(chunk_data)
                            received_size += len(chunk_data)
                    self.gui.update_log(f"[*] File {file_info['filename']} received successfully.")

                elif message['type'] == protocol.FILE_GET:
                    file_id = message['payload']['id']
                    if file_id in self.files:
                        file_info = self.files[file_id]
                        file_path = os.path.join("session_files", file_info['filename'])
                        with open(file_path, 'rb') as f:
                            while True:
                                chunk = f.read(4096)
                                if not chunk:
                                    break
                                client_socket.sendall(chunk)
                        client_socket.sendall(b'EOF')
                        self.gui.update_log(f"[*] Sent {file_info['filename']} to a client.")

            except Exception as e:
                self.gui.update_log(f'[!] Error: {e}')
                break
        client_socket.close()

    def broadcast(self, message):
        for client in self.clients:
            try:
                client.send(message)
            except:
                client.close()
                del self.clients[client]

if __name__ == '__main__':
    server = Server()
    gui = ServerGUI(server)
    gui.start()
