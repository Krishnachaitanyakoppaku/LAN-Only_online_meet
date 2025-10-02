import tkinter as tk
from tkinter import filedialog, simpledialog
import threading
import os
import queue

class ClientGUI:
    def __init__(self, client):
        self.client = client
        self.root = tk.Tk()
        self.root.title("Chat Client")
        self.queue = queue.Queue()

        self.chat_log = tk.Text(self.root, state='disabled')
        self.chat_log.pack(padx=10, pady=10)

        self.message_entry = tk.Entry(self.root, width=50)
        self.message_entry.pack(side=tk.LEFT, padx=10)

        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.LEFT)

        self.upload_button = tk.Button(self.root, text="Upload", command=self.upload_file)
        self.upload_button.pack(side=tk.RIGHT, padx=10)

        self.files_listbox = tk.Listbox(self.root)
        self.files_listbox.pack(pady=10)

        self.download_button = tk.Button(self.root, text="Download", command=self.download_file)
        self.download_button.pack()

        self.client.gui = self

    def start(self):
        self.process_queue()
        self.root.mainloop()

    def process_queue(self):
        try:
            message = self.queue.get_nowait()
            if isinstance(message, dict):
                if message['type'] == 'CHAT':
                    self.update_chat_log(f"{message['payload']['username']}: {message['payload']['message']}")
                elif message['type'] == 'FILE_META':
                    file_info = message['payload']
                    self.client.files[file_info['id']] = file_info
                    self.update_files_list(file_info)
                    self.update_chat_log(f"\n[!] New file available: {file_info['filename']} (ID: {file_info['id']})")
            else:
                self.update_chat_log(message)
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def send_message(self):
        message = self.message_entry.get()
        self.message_entry.delete(0, tk.END)
        self.client.send_chat_message(message)

    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.client.upload_file(file_path)

    def download_file(self):
        selected_file_index = self.files_listbox.curselection()
        if selected_file_index:
            file_id = self.files_listbox.get(selected_file_index).split(' (')[1][:-1]
            output_path = filedialog.asksaveasfilename()
            if output_path:
                self.client.download_file(file_id, output_path)

    def update_chat_log(self, message):
        self.chat_log.config(state='normal')
        self.chat_log.insert(tk.END, message + '\n')
        self.chat_log.config(state='disabled')

    def update_files_list(self, file_info):
        self.files_listbox.insert(tk.END, f"{file_info['filename']} ({file_info['id']})")

if __name__ == '__main__':
    # This part is for testing the GUI independently.
    # You will need to integrate it with your client logic.
    class MockClient:
        def send_chat_message(self, message):
            print(f"Sending chat message: {message}")

        def upload_file(self, file_path):
            print(f"Uploading file: {file_path}")

        def download_file(self, file_id, output_path):
            print(f"Downloading file {file_id} to {output_path}")

    client = MockClient()
    gui = ClientGUI(client)
    gui.start()
