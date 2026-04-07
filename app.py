import sys
import os
import json
import subprocess
import threading
import shutil

# ── Path setup ────────────────────────────────────────────────────────────────
APP_DIR  = os.path.dirname(os.path.abspath(__file__))
DEDRM_DIR = os.path.join(APP_DIR, "dedrm")
sys.path.insert(0, DEDRM_DIR)
sys.path.insert(0, APP_DIR)

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

# ── Settings ──────────────────────────────────────────────────────────────────
SETTINGS_DIR  = os.path.expanduser("~/Library/Application Support/KindleConverter")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")

def load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_settings(data):
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── First-run detection ───────────────────────────────────────────────────────
DEDRM_FILES = [
    "adobekey.py", "ineptepub.py", "ineptpdf.py",
    "utilities.py", "argv_utils.py", "zeroedzipinfo.py",
]
GITHUB_BASE = (
    "https://raw.githubusercontent.com/noDRM/DeDRM_tools/master/DeDRM_plugin"
)

def _deps_ok():
    try:
        try:
            import Cryptodome  # noqa: F401
        except ImportError:
            import Crypto  # noqa: F401
        import lxml  # noqa: F401
    except ImportError:
        return False
    return True

def _dedrm_ok():
    return all(os.path.exists(os.path.join(DEDRM_DIR, f)) for f in DEDRM_FILES)

NEEDS_SETUP = not _deps_ok() or not _dedrm_ok()


# ── Icon generation ───────────────────────────────────────────────────────────

def _generate_icon():
    """Draw a book icon PNG → convert to ICNS → install into the .app bundle."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return  # Pillow not yet installed — skip silently

    S = 1024
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Warm orange rounded background
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=224, fill="#E8682A")

    # Book dimensions
    bx, by  = int(S * 0.20), int(S * 0.17)
    bw, bh  = int(S * 0.60), int(S * 0.66)
    mid     = bx + bw // 2
    bend    = bx + bw

    # Left page (white) and right page (cream)
    d.rectangle([bx,    by, mid - 10, by + bh], fill="#FFFFFF")
    d.rectangle([mid + 10, by, bend, by + bh],  fill="#F0EDE8")
    # Spine
    d.rectangle([mid - 10, by, mid + 10, by + bh], fill="#B04A10")

    # Page lines
    for i in range(6):
        y = by + 70 + i * 85
        d.line([(bx + 45, y), (mid - 45, y)],   fill="#CCCCCC", width=9)
        d.line([(mid + 45, y), (bend - 45, y)],  fill="#BBBBBB", width=9)

    # Bottom shadow strip
    d.rectangle([bx, by + bh - 28, bend, by + bh], fill="#D0C8C0")

    png_path    = os.path.join(APP_DIR, "icon.png")
    icns_path   = os.path.join(APP_DIR, "icon.icns")
    iconset_dir = os.path.join(APP_DIR, "icon.iconset")

    img.save(png_path)

    # Build iconset with required sizes
    os.makedirs(iconset_dir, exist_ok=True)
    for sz, tag in [
        (16,  "16x16"), (32, "16x16@2x"),
        (32,  "32x32"), (64, "32x32@2x"),
        (128, "128x128"), (256, "128x128@2x"),
        (256, "256x256"), (512, "256x256@2x"),
        (512, "512x512"), (1024, "512x512@2x"),
    ]:
        subprocess.run(
            ["sips", "-z", str(sz), str(sz), png_path,
             "--out", os.path.join(iconset_dir, f"icon_{tag}.png")],
            capture_output=True,
        )

    subprocess.run(
        ["iconutil", "-c", "icns", iconset_dir, "-o", icns_path],
        capture_output=True,
    )

    # Install into the .app bundle that sits next to app.py
    bundle_res = os.path.join(APP_DIR, "KindleConverter.app", "Contents", "Resources")
    if os.path.isdir(os.path.dirname(bundle_res)):
        os.makedirs(bundle_res, exist_ok=True)
        shutil.copy2(icns_path, os.path.join(bundle_res, "AppIcon.icns"))

    # Clean up temporary iconset folder
    shutil.rmtree(iconset_dir, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════════════
#  First-run setup window
# ══════════════════════════════════════════════════════════════════════════════

class SetupWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kindle Converter – First-time Setup")
        self.resizable(False, False)
        self._build_ui()
        self.after(200, self._run_setup)

    def _build_ui(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Setting up Kindle Converter…",
                  font=("Helvetica", 15, "bold")).pack(pady=(0, 6))
        ttk.Label(frame, text="This only happens once.  Please wait.",
                  foreground="#555").pack(pady=(0, 12))
        self._bar = ttk.Progressbar(frame, mode="indeterminate", length=380)
        self._bar.pack(pady=(0, 10))
        self._bar.start(12)
        self._log = scrolledtext.ScrolledText(
            frame, width=52, height=10, state="disabled",
            font=("Menlo", 10), bg="#1e1e1e", fg="#d4d4d4")
        self._log.pack(pady=(0, 12))
        self._btn = ttk.Button(frame, text="Launch App",
                               command=self._relaunch, state="disabled")
        self._btn.pack()

    def _log_line(self, text):
        def _do():
            self._log.config(state="normal")
            self._log.insert("end", text + "\n")
            self._log.see("end")
            self._log.config(state="disabled")
        self.after(0, _do)

    def _run_setup(self):
        threading.Thread(target=self._setup_worker, daemon=True).start()

    def _setup_worker(self):
        ok = True

        for pkg in ("pycryptodome", "lxml", "Pillow"):
            self._log_line(f"Installing {pkg}…")
            r = subprocess.run([sys.executable, "-m", "pip", "install", pkg],
                               capture_output=True, text=True)
            if r.returncode == 0:
                self._log_line(f"  ✓ {pkg}")
            else:
                self._log_line(f"  ✗ {pkg} failed:\n{r.stderr.strip()}")
                ok = False

        self._log_line("Installing tkinterdnd2 (optional)…")
        subprocess.run([sys.executable, "-m", "pip", "install", "tkinterdnd2"],
                       capture_output=True)
        self._log_line("  ✓ drag-and-drop support")

        os.makedirs(DEDRM_DIR, exist_ok=True)
        open(os.path.join(DEDRM_DIR, "__init__.py"), "a").close()

        for fname in DEDRM_FILES:
            url  = f"{GITHUB_BASE}/{fname}"
            dest = os.path.join(DEDRM_DIR, fname)
            self._log_line(f"Downloading {fname}…")
            r = subprocess.run(["curl", "-fsSL", url, "-o", dest],
                               capture_output=True, text=True)
            if r.returncode == 0:
                self._log_line(f"  ✓ {fname}")
            else:
                self._log_line(f"  ✗ {fname}: {r.stderr.strip()}")
                ok = False

        self._log_line("Generating app icon…")
        _generate_icon()
        self._log_line("  ✓ icon")

        def _finish():
            self._bar.stop()
            self._bar.config(mode="determinate", value=100)
            if ok:
                self._log_line("\nSetup complete!  Click Launch App.")
                self._btn.config(state="normal")
            else:
                self._log_line(
                    "\nSome steps failed.  Check internet connection,\n"
                    "then quit and re-open the app to try again.")
        self.after(0, _finish)

    def _relaunch(self):
        self.destroy()
        os.execv(sys.executable, [sys.executable] + sys.argv)


# ══════════════════════════════════════════════════════════════════════════════
#  Settings dialog
# ══════════════════════════════════════════════════════════════════════════════

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings")
        self.resizable(False, False)
        self.grab_set()
        self._settings = load_settings()
        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Kindle Settings", font=("Helvetica", 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(frame, text="Kindle email:").grid(row=1, column=0, sticky="w", pady=4)
        self._email_var = tk.StringVar(value=self._settings.get("kindle_email", ""))
        ttk.Entry(frame, textvariable=self._email_var, width=36).grid(
            row=1, column=1, padx=(8, 0), pady=4)

        ttk.Label(frame, text="Kids library email\n(optional):",
                  justify="left").grid(row=2, column=0, sticky="w", pady=4)
        self._kids_var = tk.StringVar(value=self._settings.get("kindle_kids_email", ""))
        ttk.Entry(frame, textvariable=self._kids_var, width=36).grid(
            row=2, column=1, padx=(8, 0), pady=4)

        ttk.Label(frame,
                  text="Find your address at amazon.com → Manage Your Content\nand Devices → Preferences → Personal Document Settings",
                  foreground="#777", font=("Helvetica", 10), justify="left",
                  ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 12))

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, sticky="e")
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side="left")

    def _save(self):
        email = self._email_var.get().strip()
        if not email:
            messagebox.showerror("Missing email",
                                 "Please enter your Kindle email address.", parent=self)
            return
        self._settings["kindle_email"] = email
        kids = self._kids_var.get().strip()
        if kids:
            self._settings["kindle_kids_email"] = kids
        else:
            self._settings.pop("kindle_kids_email", None)
        save_settings(self._settings)
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  Main converter window
# ══════════════════════════════════════════════════════════════════════════════

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except Exception:
    HAS_DND = False

if not NEEDS_SETUP:
    from dedrm import adobekey
    from dedrm import ineptepub
    from dedrm import ineptpdf
    import traceback

_BaseApp = TkinterDnD.Tk if HAS_DND else tk.Tk

# Status colours
_CLR = {"idle": "#888888", "working": "#2979FF", "ok": "#2E7D32", "error": "#C62828"}


class ConverterApp(_BaseApp):

    _ADE_SEARCH_DIRS = [
        os.path.expanduser("~/Documents/My Digital Editions"),
        os.path.expanduser("~/My Digital Editions"),
        os.path.expanduser("~/Documents/Digital Editions"),
    ]

    def __init__(self):
        super().__init__()
        self.title("Kindle Converter")
        self.resizable(False, False)
        self._mde_before: set = set()
        self._busy = False
        self._build_ui()
        # Prompt for email on first launch
        settings = load_settings()
        if not settings.get("kindle_email"):
            self.after(300, self._open_settings)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.configure(bg="#F2F2F2")

        # ── Top bar (settings gear) ──
        top = tk.Frame(self, bg="#F2F2F2")
        top.pack(fill="x", padx=16, pady=(12, 0))
        tk.Button(
            top, text="⚙", font=("Helvetica", 16), bd=0,
            bg="#F2F2F2", activebackground="#F2F2F2", cursor="hand2",
            command=self._open_settings,
        ).pack(side="right")

        # ── Drop zone ──
        self._zone = tk.Frame(
            self, bg="#FFFFFF", width=400, height=220,
            highlightthickness=2, highlightbackground="#CCCCCC",
            cursor="hand2",
        )
        self._zone.pack(padx=24, pady=(4, 12))
        self._zone.pack_propagate(False)

        tk.Label(self._zone, text="📚", font=("Helvetica", 52),
                 bg="#FFFFFF").place(relx=0.5, rely=0.35, anchor="center")

        self._zone_lbl = tk.Label(
            self._zone,
            text="Drop library file here\n.acsm  ·  .epub  ·  .pdf",
            font=("Helvetica", 14), fg="#444444", bg="#FFFFFF", justify="center",
        )
        self._zone_lbl.place(relx=0.5, rely=0.68, anchor="center")

        tk.Label(self._zone, text="click to browse", font=("Helvetica", 11),
                 fg="#AAAAAA", bg="#FFFFFF").place(relx=0.5, rely=0.88, anchor="center")

        # Click anywhere in the zone → browse
        for w in (self._zone, self._zone_lbl):
            w.bind("<Button-1>", lambda _e: self._browse())

        # Drag-and-drop
        if HAS_DND:
            self._zone.drop_target_register(DND_FILES)
            self._zone.dnd_bind("<<Drop>>", self._on_drop)

        # ── Kids library toggle ──
        self._kids_var = tk.BooleanVar(value=False)
        self._kids_cb = ttk.Checkbutton(
            self, text="Send to Kids library",
            variable=self._kids_var,
        )
        self._kids_cb.pack(pady=(0, 4))
        self._refresh_kids_toggle()

        # ── Status bar ──
        self._status_var = tk.StringVar(value="Ready")
        self._status_lbl = tk.Label(
            self, textvariable=self._status_var,
            font=("Helvetica", 12), fg=_CLR["idle"],
            bg="#E5E5E5", anchor="center", pady=10,
        )
        self._status_lbl.pack(fill="x", padx=0, pady=(0, 0))

    def _refresh_kids_toggle(self):
        """Show the kids toggle only when a kids email is configured."""
        settings = load_settings()
        if settings.get("kindle_kids_email"):
            self._kids_cb.pack(pady=(0, 4))
        else:
            self._kids_cb.pack_forget()
            self._kids_var.set(False)

    def _open_settings(self):
        dlg = SettingsDialog(self)
        self.wait_window(dlg)
        self._refresh_kids_toggle()

    # ── Status helpers ────────────────────────────────────────────────────────

    def _set_status(self, text, kind="idle"):
        def _do():
            self._status_var.set(text)
            self._status_lbl.config(fg=_CLR[kind])
            shade = "#F8F8F8" if kind == "working" else "#FFFFFF"
            self._zone.config(bg=shade)
        self.after(0, _do)

    # ── File handling ─────────────────────────────────────────────────────────

    def _on_drop(self, event):
        files = [f for f in self.tk.splitlist(event.data)
                 if f.lower().endswith((".acsm", ".epub", ".pdf"))]
        if files:
            self._dispatch(files)

    def _browse(self):
        if self._busy:
            return
        initial = next((d for d in self._ADE_SEARCH_DIRS if os.path.isdir(d)),
                       os.path.expanduser("~"))
        files = filedialog.askopenfilenames(
            title="Select library file",
            filetypes=[("Library files", "*.acsm *.epub *.pdf"),
                       ("ACSM files", "*.acsm"),
                       ("EPUB files", "*.epub"),
                       ("PDF files", "*.pdf")],
            initialdir=initial,
        )
        if files:
            self._dispatch(list(files))

    def _dispatch(self, files):
        if self._busy:
            return
        settings = load_settings()
        if not settings.get("kindle_email"):
            self._set_status("Enter your Kindle email in Settings first", "error")
            self._open_settings()
            return
        acsm  = [f for f in files if f.lower().endswith(".acsm")]
        books = [f for f in files if f.lower().endswith((".epub", ".pdf"))]
        if acsm:
            self._open_acsm(acsm)
        elif books:
            self._start_conversion(books)

    # ── ACSM → ADE → watch ───────────────────────────────────────────────────

    def _open_acsm(self, acsm_files):
        import time
        self._busy = True
        self._mde_before = self._scan_mde()
        self._watch_start = time.time()
        for f in acsm_files:
            subprocess.run(["open", "-jg", f], capture_output=True)
        self._set_status("Downloading from library…", "working")
        threading.Thread(target=self._watch_for_download, daemon=True).start()

    def _scan_mde(self):
        found = set()
        for folder in self._ADE_SEARCH_DIRS:
            if os.path.isdir(folder):
                for root, _, names in os.walk(folder):
                    for n in names:
                        if n.lower().endswith((".epub", ".pdf")):
                            found.add(os.path.join(root, n))
        return found

    def _watch_for_download(self):
        import time
        deadline = time.time() + 300
        while time.time() < deadline:
            time.sleep(3)
            current = self._scan_mde()
            new = sorted(current - self._mde_before)
            if new:
                self._start_conversion(new)
                return
            # Book already existed — ADE updates its mtime when it opens it
            touched = sorted(
                f for f in (current & self._mde_before)
                if os.path.getmtime(f) >= self._watch_start
            )
            if touched:
                self._start_conversion(touched)
                return
        self._set_status("Download timed out — use Browse to select the file manually", "error")
        self._busy = False

    # ── Conversion ────────────────────────────────────────────────────────────

    def _start_conversion(self, files):
        self._busy = True
        threading.Thread(target=self._convert_worker,
                         args=(files,), daemon=True).start()

    def _convert_worker(self, files):
        # Check ADE key
        activation = os.path.expanduser(
            "~/Library/Application Support/Adobe/Digital Editions/activation.dat")
        if not os.path.exists(activation):
            self._set_status("Adobe Digital Editions not authorized — open ADE → Help → Authorize Computer", "error")
            self._busy = False
            return

        try:
            keys, _ = adobekey.adeptkeys()
        except Exception:
            self._set_status("Could not read Adobe key — try re-authorizing ADE", "error")
            self._busy = False
            return

        if not keys:
            self._set_status("No Adobe key found — open ADE and re-authorize", "error")
            self._busy = False
            return

        key = keys[0]
        output_dir = os.path.expanduser("~/Desktop")
        converted = []

        for inpath in files:
            self._set_status(f"Removing DRM…  {os.path.basename(inpath)}", "working")
            outpath = self._out_path(inpath, output_dir)
            try:
                if inpath.lower().endswith(".pdf"):
                    result = ineptpdf.decryptBook(key, inpath, outpath)
                else:
                    result = ineptepub.decryptBook(key, inpath, outpath)
            except Exception:
                self._set_status("Decryption error — see error.log for details", "error")
                self._busy = False
                return
            if result == 0:
                converted.append(outpath)
            elif result != 1:  # 1 = already DRM-free — treat as ok
                self._set_status("Decryption failed — wrong ADE account?", "error")
                self._busy = False
                return

        if not converted:
            converted = files  # all were already DRM-free

        settings = load_settings()
        use_kids  = self._kids_var.get() and settings.get("kindle_kids_email")
        target    = settings["kindle_kids_email"] if use_kids else settings["kindle_email"]

        self._set_status("Sending to Kindle…", "working")
        all_sent = True
        for fpath in converted:
            fname  = os.path.basename(fpath)
            script = f'''
tell application "Mail"
    set msg to make new outgoing message with properties {{¬
        subject:"{fname}", content:"", visible:false}}
    tell msg
        make new to recipient at end of to recipients ¬
            with properties {{address:"{target}"}}
        make new attachment with properties ¬
            {{file name:POSIX file "{fpath}"}} at after last paragraph
    end tell
    send msg
end tell
'''
            r = subprocess.run(["osascript", "-e", script],
                               capture_output=True, text=True)
            if r.returncode != 0:
                all_sent = False

        if all_sent:
            n = len(converted)
            self._set_status(
                f"✓  {'Book' if n == 1 else f'{n} books'} sent to Kindle!", "ok")
        else:
            self._set_status(
                "Converted but email failed — open Mail.app and add an account", "error")

        self._busy = False

    def _out_path(self, inpath, out_dir):
        stem, ext = os.path.splitext(os.path.basename(inpath))
        candidate = os.path.join(out_dir, f"{stem}_drm_free{ext}")
        n = 2
        while os.path.exists(candidate):
            candidate = os.path.join(out_dir, f"{stem}_drm_free_{n}{ext}")
            n += 1
        return candidate


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if NEEDS_SETUP:
        SetupWindow().mainloop()
    else:
        ConverterApp().mainloop()
