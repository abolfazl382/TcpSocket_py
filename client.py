import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import socket
import os


def client_upload(file_path, server_ip, server_port, status_callback):
    try:
        status_callback("Connecting to server for upload...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, server_port))
            s.sendall(b"UPLOAD\n")
            s.sendall(os.path.basename(file_path).encode() + b'\n')
            status_callback(f"Uploading {os.path.basename(file_path)}...")
            with open(file_path, 'rb') as f:
                while (chunk := f.read(4096)):
                    s.sendall(chunk)
            status_callback("Upload complete!")
    except Exception as e:
        status_callback(f"Upload failed: {e}")


def client_download(filename, server_ip, server_port, save_path, status_callback):
    try:
        status_callback("Connecting to server for download...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, server_port))
            s.sendall(b"DOWNLOAD\n")
            s.sendall(filename.encode() + b'\n')
            status_callback(f"Downloading {filename}...")

            with open(save_path, 'wb') as f:
                while True:
                    data = s.recv(4096)
                    if not data:
                        break
                    f.write(data)

            status_callback("Download complete!")
    except Exception as e:
        status_callback(f"Download failed: {e}")


class ClientApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TCP File Client")
        self.geometry("500x350")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.label_server_ip = ctk.CTkLabel(self, text="Server IP:")
        self.label_server_ip.pack(pady=(20, 5))
        self.entry_server_ip = ctk.CTkEntry(self)
        self.entry_server_ip.insert(0, "127.0.0.1")
        self.entry_server_ip.pack(padx=20, fill="x")

        self.label_server_port = ctk.CTkLabel(self, text="Server Port:")
        self.label_server_port.pack(pady=(10, 5))
        self.entry_server_port = ctk.CTkEntry(self)
        self.entry_server_port.insert(0, "9000")
        self.entry_server_port.pack(padx=20, fill="x")

        # Upload controls
        self.button_select_file = ctk.CTkButton(self, text="Select File to Upload", command=self.select_file)
        self.button_select_file.pack(pady=(20, 5))

        self.label_selected_file = ctk.CTkLabel(self, text="No file selected")
        self.label_selected_file.pack()

        self.button_upload = ctk.CTkButton(self, text="Upload", command=self.upload)
        self.button_upload.pack(pady=(10, 20))

        # Download controls
        self.label_download_file = ctk.CTkLabel(self, text="Filename to Download:")
        self.label_download_file.pack()
        self.entry_download_file = ctk.CTkEntry(self)
        self.entry_download_file.pack(padx=20, fill="x")

        self.button_download = ctk.CTkButton(self, text="Download", command=self.download)
        self.button_download.pack(pady=(10, 20))

        # Status
        self.label_status = ctk.CTkLabel(self, text="Status: Idle")
        self.label_status.pack(pady=10)

        self.selected_file_path = None

    def select_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.selected_file_path = file_path
            self.label_selected_file.configure(text=os.path.basename(file_path))
        else:
            self.label_selected_file.configure(text="No file selected")

    def update_status(self, msg):
        self.after(0, lambda: self.label_status.configure(text=f"Status: {msg}"))

    def upload(self):
        if not self.selected_file_path:
            messagebox.showwarning("No File", "Please select a file to upload.")
            return

        ip = self.entry_server_ip.get()
        port = self.entry_server_port.get()

        if not ip or not port:
            messagebox.showwarning("Input Error", "Please enter server IP and port.")
            return

        try:
            port = int(port)
        except ValueError:
            messagebox.showwarning("Input Error", "Port must be an integer.")
            return

        threading.Thread(target=client_upload, args=(self.selected_file_path, ip, port, self.update_status), daemon=True).start()

    def download(self):
        filename = self.entry_download_file.get()
        ip = self.entry_server_ip.get()
        port = self.entry_server_port.get()

        if not filename:
            messagebox.showwarning("Input Error", "Please enter filename to download.")
            return

        if not ip or not port:
            messagebox.showwarning("Input Error", "Please enter server IP and port.")
            return

        try:
            port = int(port)
        except ValueError:
            messagebox.showwarning("Input Error", "Port must be an integer.")
            return

        save_path = filedialog.asksaveasfilename(initialfile=filename)
        if not save_path:
            return

        threading.Thread(target=client_download, args=(filename, ip, port, save_path, self.update_status), daemon=True).start()


if __name__ == "__main__":
    app = ClientApp()
    app.mainloop()
