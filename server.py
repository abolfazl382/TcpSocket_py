import customtkinter as ctk
from tkinter import messagebox
import threading
import socket
import os

SERVER_HOST = '0.0.0.0'


def handle_client_connection(client_socket, base_dir, status_callback):
    try:
        # Receive command
        command = b''
        while not command.endswith(b'\n'):
            chunk = client_socket.recv(1)
            if not chunk:
                status_callback("Connection closed prematurely")
                client_socket.close()
                return
            command += chunk
        command = command.decode().strip()
        status_callback(f"Received command: {command}")

        if command == "UPLOAD":
            # Receive filename
            filename_bytes = b''
            while not filename_bytes.endswith(b'\n'):
                chunk = client_socket.recv(1)
                if not chunk:
                    status_callback("Connection closed while receiving filename")
                    client_socket.close()
                    return
                filename_bytes += chunk
            filename = filename_bytes.decode().strip()
            status_callback(f"Receiving file: {filename}")

            filepath = os.path.join(base_dir, os.path.basename(filename))
            with open(filepath, 'wb') as f:
                while True:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    f.write(data)

            status_callback(f"File '{filename}' saved successfully.")

        elif command == "DOWNLOAD":
            # Receive filename
            filename_bytes = b''
            while not filename_bytes.endswith(b'\n'):
                chunk = client_socket.recv(1)
                if not chunk:
                    status_callback("Connection closed while receiving filename")
                    client_socket.close()
                    return
                filename_bytes += chunk
            filename = filename_bytes.decode().strip()
            filepath = os.path.join(base_dir, os.path.basename(filename))
            status_callback(f"Client requested file: {filename}")

            if not os.path.isfile(filepath):
                status_callback(f"File '{filename}' not found.")
                client_socket.close()
                return

            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    client_socket.sendall(chunk)
            status_callback(f"File '{filename}' sent successfully.")

        else:
            status_callback(f"Unknown command: {command}")

    except Exception as e:
        status_callback(f"Server error: {e}")

    finally:
        client_socket.close()


def start_server(base_dir, status_callback, host=SERVER_HOST, port=9000):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    status_callback(f"Server listening on {host}:{port} ...")

    while True:
        client_sock, addr = server_socket.accept()
        status_callback(f"Accepted connection from {addr}")
        client_thread = threading.Thread(target=handle_client_connection, args=(client_sock, base_dir, status_callback), daemon=True)
        client_thread.start()


class ServerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TCP File Server")
        self.geometry("500x300")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.label_dir = ctk.CTkLabel(self, text="Directory to store files:")
        self.label_dir.pack(pady=(20, 5))

        self.entry_dir = ctk.CTkEntry(self)
        self.entry_dir.insert(0, os.getcwd())
        self.entry_dir.pack(padx=20, fill="x")

        self.label_port = ctk.CTkLabel(self, text="Port to listen on:")
        self.label_port.pack(pady=(10, 5))

        self.entry_port = ctk.CTkEntry(self)
        self.entry_port.insert(0, "9000")
        self.entry_port.pack(padx=20, fill="x")

        self.button_start = ctk.CTkButton(self, text="Start Server", command=self.start_server_thread)
        self.button_start.pack(pady=20)

        self.label_status = ctk.CTkLabel(self, text="Status: Not running")
        self.label_status.pack(pady=10)

        self.server_thread = None

    def start_server_thread(self):
        base_dir = self.entry_dir.get()
        if not os.path.isdir(base_dir):
            messagebox.showerror("Error", "Directory does not exist.")
            return

        try:
            port = int(self.entry_port.get())
        except ValueError:
            messagebox.showerror("Error", "Port must be an integer.")
            return

        if self.server_thread and self.server_thread.is_alive():
            messagebox.showinfo("Info", "Server already running.")
            return

        self.server_thread = threading.Thread(target=start_server, args=(base_dir, self.update_status, SERVER_HOST, port), daemon=True)
        self.server_thread.start()
        self.update_status(f"Server started, storing files in: {base_dir}")

    def update_status(self, msg):
        self.after(0, lambda: self.label_status.configure(text=f"Status: {msg}"))


if __name__ == "__main__":
    app = ServerApp()
    app.mainloop()
