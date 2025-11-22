import os
import string
import ctypes

class SDCardConnection:
    def __init__(self):
        self.devices = []
        self.selected_device = None
        self.sd_connected = False
        self.files = []

    def list_devices(self):
        """Lista os dispositivos de armazenamento conectados"""

        kernel32 = ctypes.windll.kernel32
        for letter in string.ascii_uppercase:
            path = f"{letter}:/"
            if os.path.exists(path):
                volume_name = ctypes.create_unicode_buffer(1024)
                try:
                    kernel32.GetVolumeInformationW(ctypes.c_wchar_p(path), volume_name, ctypes.sizeof(volume_name),None,None,None,None,0)
                    name = volume_name.value if volume_name.value else "No name"
                except Exception:
                    name = "Unknown"

                self.devices.append({"name": name, "path": path})

        return self.devices

    def automatic_connection(self, label="FLIGHT-DATA"):
        """Seleciona o dispositivo SD a ser usado"""
        self.list_devices()

        for device in self.devices:
            if device["name"].upper() == label.upper():
                self.selected_device = device["path"]
                self.list_files()
                self.sd_connected = True
                print(f"[debug] auto connect ok -> SD card '{label}' found at {self.selected_device}")
                return True

        print(f"[debug] auto connect fail -> SD card '{label}' not found.")
        return False

    def list_files(self, extension=".TXT"):
        """
        Lista todos os arquivos presentes no cartão SD.
        """
        if not self.selected_device:
            print("[debug] error -> No SD card selected.")
            return []

        self.files = []
        try:
            for f in os.listdir(self.selected_device):
                if f.upper().endswith(extension.upper()):
                    self.files.append(f)
            if self.files:
                print(f"[debug] -> Files found on SD card: {self.files}")
            else:
                print("[debug] -> No files found on SD card.")
        except Exception as e:
            print(f"[debug] error -> Unable to list files: {e}")

        return self.files

    def load_file(self, filename):
        """
        Lê o conteúdo de um arquivo no SD card e retorna as linhas.
        """
        if not self.selected_device:
            print("[debug] error -> No SD card selected.")
            return False

        file_path = os.path.join(self.selected_device, filename)
        if not os.path.exists(file_path):
            print(f"[debug] error -> File '{filename}' not found on SD card.")
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            print(f"[debug] -> File '{filename}' loaded, {len(lines)} lines read.")
            return lines
        except Exception as e:
            print(f"[debug] error -> Unable to read file '{filename}': {e}")
            return False