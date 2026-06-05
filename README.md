# MyAISelect - Custom Lightweight AI Screen Select (Desktop Edition)

Samsung Smart Select (AISelect) became too heavy and slow on my machines (especially non-Galaxy-Book desktops). This is a **personal, lightweight replacement** that focuses on speed + the features I actually use:

- Fast region capture (global hotkey)
- AI-powered cutout / object selection (optional via rembg)
- OCR / text recognition (optional, Korean supported)
- One-click "continue search in Google Lens (Chrome)" instead of locked-in Bing
- Local history of captures with thumbnails
- No 500MB+ bloat, no always-on heavy service, no Samsung hardware requirement

Works great on any modern Windows 10/11 desktop or laptop.

## Current Status (MVP)
- Core capture with nice overlay selection works out of the box.
- History saving + quick "Search in Google Lens via Chrome".
- Optional advanced AI (cutout + OCR) via pip extras.
- Very fast startup and low memory compared to the original.

## Setup (5-10 minutes)

1. Make sure you have Python 3.10+ installed (python.org or Microsoft Store).

2. Open PowerShell / Terminal in this folder and run:

```powershell
cd C:\Users\ahago\MyAISelect
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. (Recommended for best experience) Install PowerToys from Microsoft Store / GitHub.
   - Use Keyboard Manager to bind a hotkey (e.g. `Ctrl + Shift + A`) to run:
     `C:\Users\ahago\MyAISelect\.venv\Scripts\python.exe C:\Users\ahago\MyAISelect\ai_select.py --capture`

   Or just run the script once — it registers an internal hotkey (Ctrl+Shift+A). May require running as admin for global hotkeys in some cases.

4. Optional but awesome AI features:

   **For real AI Cutout (background removal / object selection):**
   ```powershell
   pip install rembg
   ```
   First run will download a small model (~50-100MB). Works on CPU, surprisingly good for photos and UI elements.

   **For OCR (text extraction, including Korean):**
   - Easiest good option: `pip install easyocr`
     (First run downloads ~200MB Korean+English model, then works offline.)
   - Alternative (lighter runtime): Install Tesseract OCR + Korean data, then `pip install pytesseract`.

5. Run it:
   ```powershell
   .\ .venv\Scripts\Activate.ps1
   python ai_select.py
   ```

   A tray icon should appear. Use the hotkey or right-click tray → "New Capture".

## How to Use
- Press your hotkey (default Ctrl+Shift+A inside the running script).
- Drag to select any region on any monitor.
- Release mouse → capture happens instantly.
- Result window opens with:
  - Original capture
  - Cutout version (if rembg installed)
  - Extracted text (if OCR installed)
  - Big buttons: **Search in Google Lens (Chrome)**, Copy, Save, etc.
- All captures are saved in the `history/` folder with timestamps + thumbnails.

## Making it Feel Like Circle to Search
- Bind a comfortable global hotkey via PowerToys.
- The flow is: Hotkey → drag select → immediately see results + one more click/hotkey to open full Google Lens in Chrome (much snappier and more powerful than the old in-app Bing view).
- For pure speed, you can run the script minimized to tray.

## Customization Ideas (future)
- Add local on-device vision models via ONNX (same ones Samsung uses are heavy).
- Better freehand lasso selection.
- Auto-translate extracted text.
- Cloud fallback options.
- Dark theme + always-on-top result window.
- Sync history across machines (OneDrive the `history` folder).

## Why this is better for a non-Samsung desktop
- Starts in <1s.
- No mandatory heavy background service.
- You control the search backend (Google Lens / Chrome by default).
- Easy to modify (pure Python).
- If it breaks or you don't like it: just delete the folder. No Store app to reset.

## Troubleshooting
- Hotkey not working: Run PowerShell as Administrator, or use PowerToys Keyboard Manager instead of the built-in one.
- "No module named rembg": just `pip install rembg` in the venv.
- Capture is black/blank: some games or protected windows block normal capture (expected limitation).

Made for personal use on my own machines. Reinstalling the original Samsung version is always one Microsoft Store click away if needed.

Enjoy the speed! 🚀
