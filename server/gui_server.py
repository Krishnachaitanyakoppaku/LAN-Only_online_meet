import tkinter as tk

class ServerGUI:
    def __init__(self, server):
        self.server = server
        self.root = tk.Tk()
        self.root.title("Chat Server")

        self.log = tk.Text(self.root, state='disabled')
        self.log.pack(padx=10, pady=10)

        self.start_button = tk.Button(self.root, text="Start Server", command=self.start_server)
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = tk.Button(self.root, text="Stop Server", command=self.stop_server, state='disabled')
        self.stop_button.pack(side=tk.RIGHT, padx=10)

        self.server.gui = self

    def start(self):
        self.root.mainloop()

    def start_server(self):
        self.server.start_listening()
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')

    def stop_server(self):
        self.server.stop_listening()
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')

    def update_log(self, message):
        self.log.config(state='normal')
        self.log.insert(tk.END, message + '\n')
        self.log.config(state='disabled')

if __name__ == '__main__':
    class MockServer:
        def start_listening(self):
            print("Server started")
        def stop_listening(self):
            print("Server stopped")

    server = MockServer()
    gui = ServerGUI(server)
    gui.start()
