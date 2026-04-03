import subprocess
import sys
import os
import ctypes
import tkinter as tk
from PIL import Image, ImageTk
from ctypes import wintypes
from io import BytesIO
from urllib.parse import urlparse

def install_dependencies():
    missing = []

    try:
        import PIL  # noqa: F401
    except ImportError:
        missing.append("Pillow")

    try:
        import requests  # noqa: F401
    except ImportError:
        missing.append("requests")

    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])

install_dependencies()

import requests


# --- CONFIGURACIÓN ---
TARGET_TITLE = "Equalizer APO 1.3.a2 Configuration Editor"
NEW_TITLE = "russo x nash los reyes del trap ⚔️"
BG_IMAGE_PATH = "https://github.com/nash-os/apo/blob/main/background.png"

OPACITY_FONDO = 0.1
OPACITY_APO = 130
OFFSET_X = 0
OFFSET_Y = -1

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
LWA_ALPHA = 0x2

user32 = ctypes.windll.user32


try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    user32.SetProcessDPIAware()


def is_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https")
    except Exception:
        return False


def load_image(source: str) -> Image.Image | None:
    try:
        if is_url(source):
            response = requests.get(source, timeout=15)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert("RGBA")

        if os.path.exists(source):
            return Image.open(source).convert("RGBA")

        print(f"No se encontró la imagen: {source}")
        return None
    except Exception as e:
        print(f"No se pudo cargar la imagen: {e}")
        return None


class AxiomaOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.config(bg="black")
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)

        self.canvas = tk.Canvas(self.root, bg="black", bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.bg_image = load_image(BG_IMAGE_PATH)
        self.tk_image = None
        self.image_id = None
        self.cached_size = (0, 0)
        self.apo_hwnd = None
        self.after_id = None
        self.running = True
        self.detected_once = False

        self.init_overlay()
        self.schedule_loop()
        self.root.mainloop()

    def find_window(self):
        hwnd = user32.FindWindowW(None, TARGET_TITLE)
        if not hwnd:
            hwnd = user32.FindWindowW(None, NEW_TITLE)
        return hwnd if hwnd and user32.IsWindow(hwnd) else None

    def apply_styles(self):
        hwnd = self.root.winfo_id()
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= WS_EX_LAYERED | WS_EX_TRANSPARENT
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        user32.SetLayeredWindowAttributes(hwnd, 0, int(OPACITY_FONDO * 255), LWA_ALPHA)

    def apply_transparency_apo(self, hwnd):
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED)
        user32.SetLayeredWindowAttributes(hwnd, 0, OPACITY_APO, LWA_ALPHA)

    def rename_window(self, hwnd):
        user32.SetWindowTextW(hwnd, NEW_TITLE)

    def get_client_rect(self, hwnd):
        rect = wintypes.RECT()
        user32.GetClientRect(hwnd, ctypes.byref(rect))
        point = wintypes.POINT(0, 0)
        user32.ClientToScreen(hwnd, ctypes.byref(point))
        return point.x, point.y, rect.right, rect.bottom

    def update_image(self, w, h):
        if not self.bg_image or w <= 0 or h <= 0:
            return

        if self.cached_size != (w, h):
            resized = self.bg_image.resize((w, h), Image.Resampling.LANCZOS)
            self.tk_image = ImageTk.PhotoImage(resized)

            if self.image_id:
                self.canvas.itemconfig(self.image_id, image=self.tk_image)
            else:
                self.image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

            self.cached_size = (w, h)

    def init_overlay(self):
        self.apply_styles()
        print("Script activo. Buscando Equalizer APO...")

    def schedule_loop(self):
        if self.running:
            self.after_id = self.root.after(10, self.loop)

    def shutdown(self):
        if not self.running:
            return

        self.running = False

        try:
            if self.after_id:
                self.root.after_cancel(self.after_id)
        except Exception:
            pass

        try:
            self.root.quit()
        except Exception:
            pass

        try:
            self.root.destroy()
        except Exception:
            pass

    def loop(self):
        if not self.running:
            return

        hwnd = self.find_window()

        if hwnd:
            self.detected_once = True

            if not self.root.winfo_viewable():
                print("Editor detectado. Aplicando efectos...")
                self.apo_hwnd = hwnd
                self.rename_window(hwnd)
                self.apply_transparency_apo(hwnd)
                self.root.deiconify()

            try:
                x, y, w, h = self.get_client_rect(hwnd)
                self.rename_window(hwnd)
                self.root.geometry(f"{w}x{h}+{x + OFFSET_X}+{y + OFFSET_Y}")
                self.update_image(w, h)
                self.root.lift()
            except Exception:
                pass
        else:
            if self.detected_once:
                print("Editor cerrado. Cerrando script...")
                self.shutdown()
                return

        self.schedule_loop()


if __name__ == "__main__":
    AxiomaOverlay()
