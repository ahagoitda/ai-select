#!/usr/bin/env python3
"""
MyAISelect - Lightweight personal AI Screen Selector for any Windows desktop.

Features (MVP):
- Global hotkey capture with clean overlay
- Fast region selection (multi-monitor)
- Local history with thumbnails
- One-click "continue in Google Lens (Chrome)" 
- Optional AI cutout (rembg)
- Optional OCR (easyocr or pytesseract)

Run:
  python ai_select.py

Hotkey inside script: Ctrl + Shift + A (may need admin for global hotkeys).
Better: Use PowerToys Keyboard Manager to bind a key to this script with --capture flag.

Created for personal use because the official Samsung Smart Select became too slow/heavy.
"""

import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
import webbrowser

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:
    print("tkinter is required (usually comes with Python).")
    sys.exit(1)

try:
    from PIL import Image, ImageTk, ImageDraw
    import mss
    import pyperclip
    import pystray
except ImportError as e:
    print("Missing core dependencies. Run in the project folder:")
    print("  pip install -r requirements.txt")
    print(f"Error: {e}")
    sys.exit(1)

# Optional advanced AI
try:
    from rembg import remove as rembg_remove
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False

try:
    import easyocr
    HAS_EASYOCR = True
    _easyocr_reader = None
except ImportError:
    HAS_EASYOCR = False

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

# Paths
BASE_DIR = Path(__file__).parent.resolve()
HISTORY_DIR = BASE_DIR / "history"
ASSETS_DIR = BASE_DIR / "assets"
HISTORY_DIR.mkdir(exist_ok=True)

# Config
HOTKEY = "ctrl+shift+a"
MAX_THUMB_SIZE = (180, 120)
SUPPORTED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}


class SelectionOverlay:
    """Fullscreen semi-transparent overlay for region selection."""
    def __init__(self, on_capture_callback):
        self.on_capture = on_capture_callback
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")
        self.root.attributes("-alpha", 0.25)  # dark overlay

        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Crosshair cursor
        self.root.config(cursor="crosshair")

        self.start_x = self.start_y = None
        self.rect = None
        self.rect_coords = None

        # Bindings
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Escape>", lambda e: self.cancel())

        # Instructions label
        self.label = tk.Label(
            self.root,
            text="Drag to select region  •  ESC to cancel",
            bg="black", fg="white", font=("Segoe UI", 14)
        )
        self.label.place(relx=0.5, rely=0.02, anchor="n")

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="#00ff9f", width=2
        )

    def on_drag(self, event):
        if self.rect and self.start_x is not None:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        if self.start_x is None:
            self.cancel()
            return

        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)

        # Minimum size guard
        if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
            self.cancel()
            return

        self.rect_coords = (x1, y1, x2, y2)
        self.root.withdraw()  # hide overlay fast
        self.root.after(50, self._do_capture)

    def _do_capture(self):
        if not self.rect_coords:
            self.cancel()
            return

        x1, y1, x2, y2 = self.rect_coords

        try:
            with mss.mss() as sct:
                # mss uses (left, top, width, height)
                monitor = {
                    "left": x1,
                    "top": y1,
                    "width": x2 - x1,
                    "height": y2 - y1,
                }
                img = sct.grab(monitor)
                pil_img = Image.frombytes("RGB", img.size, img.rgb)
        except Exception as e:
            messagebox.showerror("Capture Error", str(e))
            self.cancel()
            return

        self.root.destroy()
        self.on_capture(pil_img)

    def cancel(self):
        self.root.destroy()

    def run(self):
        self.root.mainloop()


class ResultWindow:
    """Shows captured image + optional cutout + OCR + action buttons."""
    def __init__(self, original_img: Image.Image, timestamp: str):
        self.original = original_img
        self.timestamp = timestamp
        self.cutout = None
        self.ocr_text = ""

        self.win = tk.Toplevel()
        self.win.title(f"MyAISelect - {timestamp}")
        self.win.geometry("900x620")
        self.win.minsize(700, 500)

        # Main layout
        main = ttk.Frame(self.win, padding=8)
        main.pack(fill=tk.BOTH, expand=True)

        # Left: Original
        left = ttk.LabelFrame(main, text="Original Capture", padding=4)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))

        self.orig_label = ttk.Label(left)
        self.orig_label.pack(expand=True)
        self._show_image(self.orig_label, self.original)

        # Right: Cutout + OCR
        right = ttk.Frame(main)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        cut_frame = ttk.LabelFrame(right, text="AI Cutout (if available)", padding=4)
        cut_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        self.cut_label = ttk.Label(cut_frame)
        self.cut_label.pack(expand=True)

        text_frame = ttk.LabelFrame(right, text="Extracted Text (OCR)", padding=4)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.text_box = tk.Text(text_frame, height=8, wrap=tk.WORD)
        self.text_box.pack(fill=tk.BOTH, expand=True)

        # Buttons
        btns = ttk.Frame(self.win, padding=6)
        btns.pack(fill=tk.X)

        ttk.Button(btns, text="🔍 Search in Google Lens (Chrome)",
                   command=self.open_google_lens).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="📋 Copy Image",
                   command=self.copy_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="📄 Copy Text",
                   command=self.copy_text).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="💾 Save to History",
                   command=self.save_to_history).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Close", command=self.win.destroy).pack(side=tk.RIGHT, padx=2)

        # Start async processing for cutout + OCR
        threading.Thread(target=self._process_ai, daemon=True).start()

    def _show_image(self, label, img: Image.Image, max_size=(420, 380)):
        img = img.copy()
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        tkimg = ImageTk.PhotoImage(img)
        label.configure(image=tkimg)
        label.image = tkimg  # keep reference

    def _process_ai(self):
        # Cutout
        if HAS_REMBG:
            try:
                cut = rembg_remove(self.original)
                self.cutout = cut
                self.win.after(0, lambda: self._show_image(self.cut_label, cut))
            except Exception as e:
                print("rembg failed:", e)

        # OCR
        text = ""
        if HAS_EASYOCR:
            global _easyocr_reader
            try:
                if _easyocr_reader is None:
                    _easyocr_reader = easyocr.Reader(['ko', 'en'], gpu=False, verbose=False)
                results = _easyocr_reader.readtext(self.original)
                text = "\n".join([r[1] for r in results])
            except Exception as e:
                text = f"[easyocr error] {e}"
        elif HAS_TESSERACT:
            try:
                text = pytesseract.image_to_string(self.original, lang='kor+eng')
            except Exception as e:
                text = f"[tesseract error] {e}"
        else:
            text = "OCR not installed.\nSee README.md for easyocr or tesseract setup."

        self.ocr_text = text
        self.win.after(0, lambda: self._update_text(text))

    def _update_text(self, text):
        self.text_box.delete("1.0", tk.END)
        self.text_box.insert("1.0", text)

    def open_google_lens(self):
        # Best practical experience: open Lens + open the saved image folder/file
        img_path = self._ensure_saved()
        try:
            webbrowser.open("https://lens.google.com")
            # Give Lens a moment then open the folder so user can drag the image
            time.sleep(0.8)
            os.startfile(str(img_path.parent))
            # Also copy full path to clipboard as backup
            pyperclip.copy(str(img_path))
        except Exception as e:
            messagebox.showinfo("Google Lens", f"Opened browser.\nManually drag the image from:\n{img_path}\n\n{e}")

    def copy_image(self):
        try:
            # Pillow on Windows can put image on clipboard via win32
            # Fallback: save temp and tell user
            temp = HISTORY_DIR / f"_temp_{int(time.time())}.png"
            self.original.save(temp, "PNG")
            pyperclip.copy(str(temp))
            messagebox.showinfo("Copied", "Image path copied to clipboard.\nYou can also drag the file from the history folder.")
        except Exception as e:
            messagebox.showerror("Copy failed", str(e))

    def copy_text(self):
        if self.ocr_text:
            pyperclip.copy(self.ocr_text)
            messagebox.showinfo("Copied", "Text copied to clipboard.")
        else:
            messagebox.showinfo("Text", "No text extracted yet.")

    def _ensure_saved(self) -> Path:
        """Make sure the image exists in history and return the path."""
        path = HISTORY_DIR / f"{self.timestamp}.png"
        if not path.exists():
            self.original.save(path, "PNG")
            self._make_thumb(path)
        return path

    def save_to_history(self):
        path = self._ensure_saved()
        messagebox.showinfo("Saved", f"Saved to:\n{path}")

    def _make_thumb(self, path: Path):
        try:
            thumb_path = path.with_suffix(".thumb.jpg")
            img = Image.open(path)
            img.thumbnail(MAX_THUMB_SIZE, Image.Resampling.LANCZOS)
            img.convert("RGB").save(thumb_path, "JPEG", quality=85)
        except Exception:
            pass


class MyAISelectApp:
    def __init__(self):
        self.tray_icon = None
        self.running = True

    def start_capture(self):
        """Entry point for hotkey or tray menu."""
        overlay = SelectionOverlay(on_capture_callback=self._on_captured)
        overlay.run()

    def _on_captured(self, pil_img: Image.Image):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Save immediately
        save_path = HISTORY_DIR / f"{ts}.png"
        pil_img.save(save_path, "PNG")
        self._make_thumb(save_path)

        # Show result window
        ResultWindow(pil_img, ts)

    def _make_thumb(self, path: Path):
        try:
            thumb = path.with_suffix(".thumb.jpg")
            img = Image.open(path)
            img.thumbnail(MAX_THUMB_SIZE, Image.Resampling.LANCZOS)
            img.convert("RGB").save(thumb, "JPEG", quality=80)
        except Exception:
            pass

    def open_history(self):
        """Simple history browser."""
        win = tk.Toplevel()
        win.title("MyAISelect History")
        win.geometry("820x520")

        canvas = tk.Canvas(win)
        scroll = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        frame = ttk.Frame(canvas)

        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        images = sorted(HISTORY_DIR.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)

        if not images:
            ttk.Label(frame, text="No captures yet. Use the hotkey!").pack(padx=20, pady=20)
            return

        row = 0
        for img_path in images[:30]:  # limit
            thumb_path = img_path.with_suffix(".thumb.jpg")
            if not thumb_path.exists():
                try:
                    im = Image.open(img_path)
                    im.thumbnail(MAX_THUMB_SIZE, Image.Resampling.LANCZOS)
                    im.convert("RGB").save(thumb_path, "JPEG", quality=80)
                except Exception:
                    continue

            try:
                thumb = Image.open(thumb_path)
                tkthumb = ImageTk.PhotoImage(thumb)
            except Exception:
                continue

            lbl = ttk.Label(frame, image=tkthumb, text=img_path.stem, compound="top")
            lbl.image = tkthumb
            lbl.grid(row=row // 4, column=row % 4, padx=6, pady=6)

            # Click to re-open result
            def open_result(p=img_path, ts=img_path.stem):
                try:
                    im = Image.open(p)
                    ResultWindow(im, ts)
                except Exception as e:
                    messagebox.showerror("Error", str(e))

            lbl.bind("<Button-1>", lambda e, p=img_path, ts=img_path.stem: open_result(p, ts))
            row += 1

        frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def create_tray(self):
        def on_capture(icon, item):
            self.start_capture()

        def on_history(icon, item):
            self.open_history()

        def on_quit(icon, item):
            self.running = False
            icon.stop()

        # Simple icon (you can replace with a real png in assets/)
        icon_img = Image.new("RGB", (64, 64), color=(30, 30, 40))
        draw = ImageDraw.Draw(icon_img)
        draw.rectangle([8, 8, 56, 56], outline=(0, 200, 150), width=3)
        draw.line([20, 20, 44, 44], fill=(0, 220, 180), width=2)

        menu = pystray.Menu(
            pystray.MenuItem("New Capture", on_capture, default=True),
            pystray.MenuItem("History", on_history),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", on_quit)
        )

        self.tray_icon = pystray.Icon("MyAISelect", icon_img, "MyAISelect", menu)
        self.tray_icon.run()

    def run(self, capture_immediately=False):
        if capture_immediately:
            threading.Thread(target=self.start_capture, daemon=True).start()

        # Try to register hotkey (best effort)
        try:
            import keyboard
            keyboard.add_hotkey(HOTKEY, self.start_capture)
            print(f"Global hotkey registered: {HOTKEY}")
        except Exception as e:
            print(f"Could not register global hotkey ({e}). Use tray or PowerToys instead.")

        print("MyAISelect running. Right-click tray icon or use hotkey.")
        self.create_tray()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true", help="Immediately start a capture")
    args = parser.parse_args()

    app = MyAISelectApp()
    app.run(capture_immediately=args.capture)


if __name__ == "__main__":
    main()