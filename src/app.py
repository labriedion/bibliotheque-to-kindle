import sys
import os
import json
import subprocess
import threading
import traceback
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# ── Platform ──────────────────────────────────────────────────────────────────
IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform == "win32"

# ── Paths ─────────────────────────────────────────────────────────────────────
APP_DIR = os.path.dirname(os.path.abspath(__file__))

if IS_WIN:
    SETTINGS_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                                "BibliothequeToKindle")
else:
    SETTINGS_DIR = os.path.expanduser(
        "~/Library/Application Support/BibliothequeToKindle")

if getattr(sys, "frozen", False):
    DEDRM_DIR = os.path.join(sys._MEIPASS, "dedrm")  # bundled by PyInstaller
else:
    DEDRM_DIR = os.path.join(APP_DIR, "dedrm")

sys.path.insert(0, DEDRM_DIR)
sys.path.insert(0, APP_DIR)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ── Settings ──────────────────────────────────────────────────────────────────
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")
LOANS_FILE    = os.path.join(SETTINGS_DIR, "loans.json")
ERROR_LOG     = os.path.join(SETTINGS_DIR, "error.log")

DEFAULT_OUTPUT_DIR = os.path.expanduser("~/Desktop")

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


# ── Loan tracking ─────────────────────────────────────────────────────────────

def load_loans():
    try:
        with open(LOANS_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_loans(loans):
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    with open(LOANS_FILE, "w") as f:
        json.dump(loans, f, indent=2)

def expired_loans():
    """Return loans that have expired and haven't been confirmed deleted."""
    now = datetime.now(timezone.utc)
    result = []
    for loan in load_loans():
        if loan.get("confirmed_deleted"):
            continue
        expiry_str = loan.get("expiry")
        if not expiry_str:
            continue
        try:
            expiry = datetime.fromisoformat(expiry_str)
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            if expiry < now:
                result.append(loan)
        except ValueError:
            pass
    return result

def confirm_loans_deleted(loans_to_confirm):
    all_loans = load_loans()
    titles = {l["title"] for l in loans_to_confirm}
    for loan in all_loans:
        if loan.get("title") in titles:
            loan["confirmed_deleted"] = True
    save_loans(all_loans)

def add_loan(title, expiry_str, local_path):
    loans = load_loans()
    loans.append({
        "title": title,
        "expiry": expiry_str,
        "local_path": local_path,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "confirmed_deleted": False,
    })
    save_loans(loans)


# ── ACSM parsing ──────────────────────────────────────────────────────────────

def _parse_acsm(path):
    """Return (expiry_iso, is_loan) or (None, False)."""
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        ns      = "http://ns.adobe.com/adept"
        is_loan = root.get("fulfillmentType") == "loan"
        expiry  = root.find(f"{{{ns}}}expiry") or root.find("expiry")
        return (expiry.text if expiry is not None else None), is_loan
    except Exception:
        return None, False


# ── Kindle library URL ────────────────────────────────────────────────────────

def _kindle_library_url():
    domain = load_settings().get("amazon_domain", "amazon.ca")
    return f"https://www.{domain}/hz/mycd/myx#/home/content/pdocs/dateDsc/"


# ── ADE paths ─────────────────────────────────────────────────────────────────

def _ade_activation_path():
    if IS_WIN:
        return os.path.join(os.environ.get("APPDATA", ""),
                            "Adobe", "Digital Editions", "activation.dat")
    return os.path.expanduser(
        "~/Library/Application Support/Adobe/Digital Editions/activation.dat")

_ADE_SEARCH_DIRS = (
    [
        os.path.expanduser("~/Documents/My Digital Editions"),
        os.path.expanduser("~/My Digital Editions"),
    ] if IS_WIN else [
        os.path.expanduser("~/Documents/My Digital Editions"),
        os.path.expanduser("~/My Digital Editions"),
        os.path.expanduser("~/Documents/Digital Editions"),
    ]
)


# ── File / URL helpers ────────────────────────────────────────────────────────

def _open_file(path):
    if IS_MAC:
        subprocess.run(["open", "-jg", path], capture_output=True)
    else:
        os.startfile(path)

def _open_url(url):
    if IS_MAC:
        subprocess.run(["open", url], capture_output=True)
    else:
        os.startfile(url)

def _reveal_in_finder(path):
    """Reveal a file or folder in Finder (macOS) or Explorer (Windows)."""
    if IS_MAC:
        subprocess.run(["open", "-R", path], capture_output=True)
    else:
        subprocess.run(["explorer", "/select,", path], capture_output=True)


# ── Email sending ─────────────────────────────────────────────────────────────

def send_file_to_kindle(fpath, target_email):
    """Open the mail client with the file attached and Kindle address pre-filled."""
    if IS_MAC:
        return _send_via_mail_app(fpath, target_email)
    else:
        return _send_via_mapi(fpath, target_email)

def _send_via_mail_app(fpath, target_email):
    def _esc(s):
        return s.replace("\\", "\\\\").replace('"', '\\"')

    script = f'''
tell application "Mail"
    set msg to make new outgoing message with properties {{¬
        subject:"{_esc(os.path.basename(fpath))}", content:"", visible:true}}
    tell msg
        make new to recipient at end of to recipients ¬
            with properties {{address:"{_esc(target_email)}"}}
        make new attachment with properties ¬
            {{file name:POSIX file "{_esc(fpath)}"}} at after last paragraph
    end tell
    activate
end tell
'''
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return r.returncode == 0

def _send_via_mapi(fpath, target_email):
    """Open the default Windows mail client via Simple MAPI.
    Compatible with Outlook, Thunderbird, Windows Mail, and any MAPI client.
    No credentials required — user just clicks Send.
    """
    import ctypes

    MAPI_DIALOG   = 0x8
    MAPI_LOGON_UI = 0x1
    MAPI_TO       = 1

    class MapiRecipDesc(ctypes.Structure):
        _fields_ = [
            ("ulReserved",   ctypes.c_ulong),
            ("ulRecipClass", ctypes.c_ulong),
            ("lpszName",     ctypes.c_char_p),
            ("lpszAddress",  ctypes.c_char_p),
            ("ulEIDSize",    ctypes.c_ulong),
            ("lpEntryID",    ctypes.c_void_p),
        ]

    class MapiFileDesc(ctypes.Structure):
        _fields_ = [
            ("ulReserved",   ctypes.c_ulong),
            ("flFlags",      ctypes.c_ulong),
            ("nPosition",    ctypes.c_ulong),
            ("lpszPathName", ctypes.c_char_p),
            ("lpszFileName", ctypes.c_char_p),
            ("lpFileType",   ctypes.c_void_p),
        ]

    class MapiMessage(ctypes.Structure):
        _fields_ = [
            ("ulReserved",         ctypes.c_ulong),
            ("lpszSubject",        ctypes.c_char_p),
            ("lpszNoteText",       ctypes.c_char_p),
            ("lpszMessageType",    ctypes.c_char_p),
            ("lpszDateReceived",   ctypes.c_char_p),
            ("lpszConversationID", ctypes.c_char_p),
            ("flFlags",            ctypes.c_ulong),
            ("lpOriginator",       ctypes.c_void_p),
            ("nRecipCount",        ctypes.c_ulong),
            ("lpRecips",           ctypes.POINTER(MapiRecipDesc)),
            ("nFileCount",         ctypes.c_ulong),
            ("lpFiles",            ctypes.POINTER(MapiFileDesc)),
        ]

    recip = MapiRecipDesc(
        ulRecipClass = MAPI_TO,
        lpszName     = target_email.encode(),
        lpszAddress  = f"SMTP:{target_email}".encode(),
    )

    attachment = MapiFileDesc(
        lpszPathName = fpath.encode(),
        lpszFileName = os.path.basename(fpath).encode(),
        nPosition    = 0xFFFFFFFF,  # no inline position
    )

    msg = MapiMessage(
        lpszSubject = os.path.basename(fpath).encode(),
        nRecipCount = 1,
        lpRecips    = ctypes.pointer(recip),
        nFileCount  = 1,
        lpFiles     = ctypes.pointer(attachment),
    )

    try:
        mapi   = ctypes.windll.MAPI32
        result = mapi.MAPISendMail(0, 0, ctypes.byref(msg),
                                   MAPI_DIALOG | MAPI_LOGON_UI, 0)
        return result == 0
    except Exception:
        return False


# ── DeDRM check ───────────────────────────────────────────────────────────────

_DEDRM_FILES = [
    "adobekey.py", "ineptepub.py", "ineptpdf.py",
    "utilities.py", "argv_utils.py", "zeroedzipinfo.py",
]

def _dedrm_ok():
    return all(os.path.exists(os.path.join(DEDRM_DIR, f)) for f in _DEDRM_FILES)

# Lazy imports — surfaces missing-file errors as status messages, not crashes
_dedrm_imported = False
adobekey = ineptepub = ineptpdf = None

def _ensure_dedrm():
    global _dedrm_imported, adobekey, ineptepub, ineptpdf
    if _dedrm_imported:
        return True
    try:
        from dedrm import adobekey as _ak
        from dedrm import ineptepub as _ep
        from dedrm import ineptpdf as _pd
        adobekey  = _ak
        ineptepub = _ep
        ineptpdf  = _pd
        _dedrm_imported = True
        return True
    except Exception:
        return False


# ── Icon generation (macOS build step only) ───────────────────────────────────

def _generate_icon():
    if not IS_MAC:
        return
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return

    S = 1024
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=224, fill="#E8682A")

    bx, by = int(S * 0.20), int(S * 0.17)
    bw, bh = int(S * 0.60), int(S * 0.66)
    mid    = bx + bw // 2
    bend   = bx + bw

    d.rectangle([bx,       by, mid - 10, by + bh], fill="#FFFFFF")
    d.rectangle([mid + 10, by, bend,     by + bh], fill="#F0EDE8")
    d.rectangle([mid - 10, by, mid + 10, by + bh], fill="#B04A10")

    for i in range(6):
        y = by + 70 + i * 85
        d.line([(bx + 45, y),  (mid - 45, y)],  fill="#CCCCCC", width=9)
        d.line([(mid + 45, y), (bend - 45, y)],  fill="#BBBBBB", width=9)

    d.rectangle([bx, by + bh - 28, bend, by + bh], fill="#D0C8C0")

    png_path    = os.path.join(APP_DIR, "icon.png")
    icns_path   = os.path.join(APP_DIR, "icon.icns")
    iconset_dir = os.path.join(APP_DIR, "icon.iconset")

    img.save(png_path)
    os.makedirs(iconset_dir, exist_ok=True)

    for sz, tag in [
        (16,  "16x16"),   (32,   "16x16@2x"),
        (32,  "32x32"),   (64,   "32x32@2x"),
        (128, "128x128"), (256,  "128x128@2x"),
        (256, "256x256"), (512,  "256x256@2x"),
        (512, "512x512"), (1024, "512x512@2x"),
    ]:
        subprocess.run(
            ["sips", "-z", str(sz), str(sz), png_path,
             "--out", os.path.join(iconset_dir, f"icon_{tag}.png")],
            capture_output=True)

    subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", icns_path],
                   capture_output=True)

    bundle_res = os.path.join(APP_DIR, "Bibliothèque to Kindle.app",
                              "Contents", "Resources")
    if os.path.isdir(os.path.dirname(bundle_res)):
        os.makedirs(bundle_res, exist_ok=True)
        shutil.copy2(icns_path, os.path.join(bundle_res, "AppIcon.icns"))

    shutil.rmtree(iconset_dir, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════════════
#  Settings dialog
# ══════════════════════════════════════════════════════════════════════════════

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings / Paramètres")
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._settings = load_settings()
        self._build_ui()
        self._toggle_kindle_fields()

    def _on_close(self):
        self.grab_release()
        self.destroy()
        self.master.focus_force()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        # ── Kindle ──
        ttk.Label(frame, text="Kindle", font=("Helvetica", 13, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        # "send_to_kindle" is True by default; derived from inverted legacy "save_only"
        default_send = not self._settings.get("save_only", not self._settings.get("send_to_kindle", True))
        self._save_only_var = tk.BooleanVar(value=self._settings.get("send_to_kindle", default_send))
        ttk.Checkbutton(frame,
                        text="Send to Kindle / Envoyer au Kindle",
                        variable=self._save_only_var,
                        command=self._toggle_kindle_fields,
                        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))

        self._email_lbl = ttk.Label(frame, text="Address / Adresse :")
        self._email_lbl.grid(row=2, column=0, sticky="w", pady=4)
        self._email_var = tk.StringVar(value=self._settings.get("kindle_email", ""))
        self._email_entry = tk.Entry(
            frame, textvariable=self._email_var, width=36, bg="white",
            fg="#000000", disabledforeground="#AAAAAA")
        self._email_entry.grid(row=2, column=1, columnspan=2, padx=(8, 0), pady=4)

        self._email_link_lbl = tk.Label(
            frame,
            text="Find your address / Trouvez votre adresse",
            foreground="#2979FF", font=("Helvetica", 10))
        self._email_link_lbl.grid(row=3, column=0, columnspan=3, sticky="w", pady=(0, 4))
        self._email_link_lbl.bind("<Button-1>", lambda _e: _open_url(self._personal_docs_url()))

        # ── Output folder ──
        ttk.Separator(frame, orient="horizontal").grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=(10, 14))

        ttk.Label(frame, text="Output / Sortie", font=("Helvetica", 13, "bold")).grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(0, 10))

        ttk.Label(frame, text="Output folder\nDossier de sortie :").grid(
            row=6, column=0, sticky="w", pady=4)
        self._output_var = tk.StringVar(
            value=self._settings.get("output_dir", DEFAULT_OUTPUT_DIR))
        ttk.Entry(frame, textvariable=self._output_var, width=28).grid(
            row=6, column=1, padx=(8, 0), pady=4, sticky="ew")
        ttk.Button(frame, text="…", width=3,
                   command=self._browse_output).grid(row=6, column=2, padx=(4, 0))

        self._open_folder_lbl = tk.Label(
            frame, text="Open folder / Ouvrir le dossier",
            foreground="#2979FF", font=("Helvetica", 10))
        self._open_folder_lbl.grid(row=7, column=0, columnspan=3, sticky="w", pady=(0, 4))
        self._open_folder_lbl.bind("<Button-1>", lambda _e: self._open_output_folder())

        # ── Amazon domain ──
        ttk.Separator(frame, orient="horizontal").grid(
            row=8, column=0, columnspan=3, sticky="ew", pady=(10, 14))

        ttk.Label(frame, text="Amazon", font=("Helvetica", 13, "bold")).grid(
            row=9, column=0, columnspan=3, sticky="w", pady=(0, 10))

        ttk.Label(frame, text="Amazon domain\nDomaine Amazon :").grid(
            row=10, column=0, sticky="w", pady=4)
        self._domain_var = tk.StringVar(
            value=self._settings.get("amazon_domain", "amazon.ca"))
        ttk.Entry(frame, textvariable=self._domain_var, width=20).grid(
            row=10, column=1, padx=(8, 0), pady=4, sticky="w")

        ttk.Label(frame, text="Kindle library link\nBibliothèque Kindle :").grid(
            row=11, column=0, sticky="w", pady=4)
        self._url_lbl = tk.Label(frame, text="", foreground="#2979FF",
                                 font=("Helvetica", 10),
                                 justify="left", wraplength=220)
        self._url_lbl.grid(row=11, column=1, columnspan=2, padx=(8, 0), pady=4, sticky="w")
        self._url_lbl.bind("<Button-1>", lambda _e: _open_url(_kindle_library_url()))
        self._domain_var.trace_add("write", lambda *_: self._refresh_url())
        self._refresh_url()

        # ── Buttons ──
        ttk.Separator(frame, orient="horizontal").grid(
            row=20, column=0, columnspan=3, sticky="ew", pady=(14, 14))
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=21, column=0, columnspan=3, sticky="e")
        ttk.Button(btn_frame, text="Cancel / Annuler", command=self._on_close).pack(
            side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="Save / Enregistrer", command=self._save).pack(side="left")

    def _browse_output(self):
        current = self._output_var.get()
        initial = current if os.path.isdir(current) else DEFAULT_OUTPUT_DIR
        folder = filedialog.askdirectory(
            title="Select output folder / Choisir le dossier de sortie",
            initialdir=initial)
        if folder:
            self._output_var.set(folder)

    def _open_output_folder(self):
        folder = self._output_var.get() or DEFAULT_OUTPUT_DIR
        if os.path.isdir(folder):
            _open_file(folder)
        else:
            messagebox.showinfo(
                "Folder not found / Dossier introuvable",
                f"The folder does not exist yet:\n{folder}\n\n"
                "Le dossier n'existe pas encore.",
                parent=self)

    def _personal_docs_url(self):
        domain = self._domain_var.get().strip() or "amazon.ca"
        return f"https://www.{domain}/hz/mycd/myx#/home/settings/pdocs"

    def _refresh_url(self):
        domain = self._domain_var.get().strip() or "amazon.ca"
        self._url_lbl.config(
            text=f"https://www.{domain}/hz/mycd/myx#/home/content/pdocs/dateDsc/")

    def _toggle_kindle_fields(self):
        sending = self._save_only_var.get()  # var is "send_to_kindle"
        grey    = "#AAAAAA"
        self._email_entry.config(
            state="normal" if sending else "disabled",
            bg="white" if sending else "#D8D8D8",
            fg="#000000",
            disabledforeground="#AAAAAA")
        self._email_lbl.config(foreground="" if sending else grey)
        self._email_link_lbl.config(foreground="#2979FF" if sending else grey)

    def _save(self):
        send_to_kindle = self._save_only_var.get()  # var is "send_to_kindle"
        email          = self._email_var.get().strip()
        if send_to_kindle and not email:
            messagebox.showerror(
                "Missing address / Adresse manquante",
                "Please enter your Kindle address, or uncheck 'Send to Kindle'.\n"
                "Veuillez entrer votre adresse Kindle, ou décocher 'Envoyer au Kindle'.",
                parent=self)
            return
        self._settings["kindle_email"]   = email
        self._settings["amazon_domain"]  = self._domain_var.get().strip() or "amazon.ca"
        self._settings["output_dir"]     = self._output_var.get().strip() or DEFAULT_OUTPUT_DIR
        self._settings["send_to_kindle"] = send_to_kindle
        self._settings.pop("save_only", None)  # remove legacy key
        save_settings(self._settings)
        self._on_close()


# ══════════════════════════════════════════════════════════════════════════════
#  Expired loans dialog
# ══════════════════════════════════════════════════════════════════════════════

class ExpiredLoansDialog(tk.Toplevel):
    """Shows expired loans and optionally fires a callback when the user responds."""

    def __init__(self, parent, loans, on_done=None):
        super().__init__(parent)
        self.title("Expired Loans / Prêts expirés")
        self.resizable(False, False)
        self._loans   = loans
        self._on_done = on_done   # callable(confirmed: bool) or None
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.focus_force()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame,
                  text="Please delete these expired loans from your Kindle\n"
                       "library before borrowing a new book.\n\n"
                       "Veuillez supprimer ces prêts expirés de votre\n"
                       "bibliothèque Kindle avant d'emprunter un nouveau livre.",
                  font=("Helvetica", 12), justify="left",
                  ).pack(anchor="w", pady=(0, 12))

        box = tk.Frame(frame, bg="#F8F8F8", bd=1, relief="solid")
        box.pack(fill="x", pady=(0, 12))
        for loan in self._loans:
            expiry = loan.get("expiry", "")[:10]
            tk.Label(box, text=f"  {loan['title']}  —  expired / expiré le {expiry}",
                     bg="#F8F8F8", fg="#1A1A1A", anchor="w", font=("Helvetica", 11), pady=5,
                     ).pack(fill="x")

        url  = _kindle_library_url()
        link = tk.Label(frame, text=url, foreground="#2979FF",
                        font=("Helvetica", 11))
        link.pack(anchor="w", pady=(0, 16))
        link.bind("<Button-1>", lambda _e: _open_url(url))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(anchor="e")
        ttk.Button(btn_frame, text="Cancel / Annuler", command=self._cancel).pack(
            side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="I've deleted them / Je les ai supprimés",
                   command=self._confirm).pack(side="left")

    def _confirm(self):
        confirm_loans_deleted(self._loans)
        self.destroy()
        if self._on_done:
            self._on_done(True)

    def _cancel(self):
        self.destroy()
        if self._on_done:
            self._on_done(False)


# ══════════════════════════════════════════════════════════════════════════════
#  Main window
# ══════════════════════════════════════════════════════════════════════════════

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except Exception:
    HAS_DND = False

_CLR = {"idle": "#888888", "working": "#2979FF", "ok": "#2E7D32", "error": "#C62828"}


class ConverterApp(tk.Tk):

    def __init__(self):
        super().__init__()
        if HAS_DND:
            try:
                TkinterDnD._require(self)
            except Exception:
                pass
        self.title("Bibliothèque to Kindle")
        self.resizable(False, False)
        self._mde_before: set  = set()
        self._pending_expiry   = None   # (expiry_str, title) | None
        self._busy             = False
        self._last_output_dir  = None   # for the reveal button
        self._build_ui()
        self.focus_force()
        if IS_MAC:
            self._activate_on_mac()

    def _activate_on_mac(self):
        """Call NSApp.activateIgnoringOtherApps via the ObjC runtime so clicks
        register immediately without needing a title-bar click first."""
        try:
            import ctypes, ctypes.util
            objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
            objc.objc_getClass.restype   = ctypes.c_void_p
            objc.sel_registerName.restype = ctypes.c_void_p
            objc.objc_msgSend.restype    = ctypes.c_void_p
            objc.objc_msgSend.argtypes   = [ctypes.c_void_p, ctypes.c_void_p,
                                             ctypes.c_bool]
            NSApp = ctypes.c_void_p(objc.objc_msgSend(
                ctypes.c_void_p(objc.objc_getClass(b"NSApplication")),
                ctypes.c_void_p(objc.sel_registerName(b"sharedApplication")),
                False))
            objc.objc_msgSend(NSApp, ctypes.c_void_p(
                objc.sel_registerName(b"activateIgnoringOtherApps:")), True)
        except Exception:
            pass
        if not _dedrm_ok():
            messagebox.showerror(
                "Setup required / Configuration requise",
                "DeDRM files are missing. Please run:\n\n"
                "    ./setup.sh\n\n"
                "then restart the app.\n\n"
                "Les fichiers DeDRM sont manquants. Veuillez exécuter :\n\n"
                "    ./setup.sh\n\n"
                "puis redémarrez l'application.")
        elif load_settings().get("send_to_kindle") and not load_settings().get("kindle_email"):
            self._set_status(
                "Click ⚙ to enter your Kindle address / "
                "Cliquez ⚙ pour entrer votre adresse Kindle", "idle")
        # Check for expired loans at startup so the dialog never interrupts a drop
        self.after(400, self._check_expired_loans_on_boot)

    def _check_expired_loans_on_boot(self):
        loans = expired_loans()
        if loans:
            ExpiredLoansDialog(self, loans)
        self.focus_force()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.configure(bg="#F2F2F2")

        top = tk.Frame(self, bg="#F2F2F2")
        top.pack(fill="x", padx=16, pady=(12, 0))
        gear_btn = tk.Button(
            top, text="⚙  Settings", font=("Helvetica", 13),
            bg="#E0E0E0", activebackground="#C8C8C8",
            fg="#333333", activeforeground="#000000",
            relief="flat", bd=0, padx=12, pady=6,
            cursor="pointinghand",
            command=self._open_settings)
        gear_btn.pack(side="right")

        self._zone = tk.Frame(self, bg="#FFFFFF", width=400, height=220,
                              highlightthickness=2, highlightbackground="#CCCCCC",
                              cursor="pointinghand")
        self._zone.pack(padx=24, pady=(4, 12))
        self._zone.pack_propagate(False)

        self._zone_icon = tk.Label(self._zone, text="📚", font=("Helvetica", 52),
                                   bg="#FFFFFF", cursor="pointinghand")
        self._zone_icon.place(relx=0.5, rely=0.30, anchor="center")

        self._zone_lbl = tk.Label(
            self._zone,
            text="Drop your file here / Déposez votre fichier ici\n.acsm  ·  .epub  ·  .pdf",
            font=("Helvetica", 13), fg="#444444", bg="#FFFFFF", justify="center",
            cursor="pointinghand")
        self._zone_lbl.place(relx=0.5, rely=0.62, anchor="center")

        self._zone_hint = tk.Label(self._zone,
                 text="click to browse / cliquez pour parcourir",
                 font=("Helvetica", 11), fg="#AAAAAA", bg="#FFFFFF",
                 cursor="pointinghand")
        self._zone_hint.place(relx=0.5, rely=0.82, anchor="center")

        for w in (self._zone, self._zone_lbl, self._zone_icon, self._zone_hint):
            w.bind("<Button-1>", lambda _e: self._browse())
            w.bind("<Enter>", lambda _e: self._zone.config(highlightbackground="#888888"))
            w.bind("<Leave>", lambda _e: self._zone.config(highlightbackground="#CCCCCC"))

        if HAS_DND:
            self._zone.drop_target_register(DND_FILES)
            self._zone.dnd_bind("<<Drop>>", self._on_drop)

        status_frame = tk.Frame(self, bg="#E5E5E5")
        status_frame.pack(fill="x")

        self._status_var = tk.StringVar(value="Ready / Prêt")
        self._status_lbl = tk.Label(
            status_frame, textvariable=self._status_var,
            font=("Helvetica", 12), fg=_CLR["idle"],
            bg="#E5E5E5", anchor="center", pady=8)
        self._status_lbl.pack(side="left", fill="x", expand=True)

        self._reveal_btn = tk.Button(
            status_frame, text="📂", font=("Helvetica", 14), bd=0,
            bg="#E5E5E5", activebackground="#E5E5E5",
            command=self._reveal_output)
        # hidden until a conversion succeeds

    def _open_settings(self):
        SettingsDialog(self)

    # ── Status bar ────────────────────────────────────────────────────────────

    def _set_status(self, text, kind="idle", show_reveal=False):
        def _do():
            self._status_var.set(text)
            self._status_lbl.config(fg=_CLR[kind])
            self._zone.config(bg="#F8F8F8" if kind == "working" else "#FFFFFF")
            if show_reveal:
                self._reveal_btn.pack(side="right", padx=(0, 6))
            else:
                self._reveal_btn.pack_forget()
        self.after(0, _do)

    def _reveal_output(self):
        if self._last_output_dir and os.path.isdir(self._last_output_dir):
            _reveal_in_finder(self._last_output_dir)

    # ── File handling ─────────────────────────────────────────────────────────

    def _on_drop(self, event):
        if self._busy:
            return
        files = [f for f in self.tk.splitlist(event.data)
                 if f.lower().endswith((".acsm", ".epub", ".pdf"))]
        if files:
            self.after(300, lambda: self._dispatch(files))

    def _browse(self):
        if self._busy:
            return
        initial = next((d for d in _ADE_SEARCH_DIRS if os.path.isdir(d)),
                       os.path.expanduser("~"))
        files = filedialog.askopenfilenames(
            title="Select a file / Sélectionner un fichier",
            filetypes=[("Library files / Fichiers de bibliothèque", "*.acsm *.epub *.pdf"),
                       ("ACSM files", "*.acsm"),
                       ("EPUB files", "*.epub"),
                       ("PDF files", "*.pdf")],
            initialdir=initial)
        if files:
            self._dispatch(list(files))

    def _dispatch(self, files):
        if self._busy:
            return
        settings = load_settings()
        if settings.get("send_to_kindle") and not settings.get("kindle_email"):
            self._set_status(
                "Configure your Kindle address in Settings / Configurez votre adresse Kindle",
                "error")
            self._open_settings()
            return
        loans = expired_loans()
        if loans:
            ExpiredLoansDialog(self, loans,
                               on_done=lambda ok: self._do_dispatch(files) if ok else None)
            return
        self._do_dispatch(files)

    def _do_dispatch(self, files):
        acsm  = [f for f in files if f.lower().endswith(".acsm")]
        books = [f for f in files if f.lower().endswith((".epub", ".pdf"))]
        if acsm:
            self._open_acsm(acsm)
        elif books:
            self._pending_expiry = None
            self._start_conversion(books)

    # ── ACSM → ADE → watch ───────────────────────────────────────────────────

    def _open_acsm(self, acsm_files):
        import time
        self._busy           = True
        self._pending_expiry = None
        for path in acsm_files:
            expiry_str, is_loan = _parse_acsm(path)
            if is_loan and expiry_str:
                title = os.path.splitext(os.path.basename(path))[0]
                self._pending_expiry = (expiry_str, title)
                break
        self._mde_before  = self._scan_mde()
        self._watch_start = time.time()
        for f in acsm_files:
            _open_file(f)
        self._set_status(
            "Downloading from library… / Téléchargement depuis la bibliothèque…",
            "working")
        threading.Thread(target=self._watch_for_download, daemon=True).start()

    def _scan_mde(self):
        found = set()
        for folder in _ADE_SEARCH_DIRS:
            if os.path.isdir(folder):
                for root, _, names in os.walk(folder):
                    for n in names:
                        if n.lower().endswith((".epub", ".pdf")):
                            found.add(os.path.join(root, n))
        return found

    def _watch_for_download(self):
        import time
        deadline = time.time() + 300  # 5-minute timeout
        while time.time() < deadline:
            time.sleep(3)
            current = self._scan_mde()
            new     = sorted(current - self._mde_before)
            if new:
                self._start_conversion(new)
                return
            # Book already existed — ADE updated its modification time
            touched = sorted(
                f for f in (current & self._mde_before)
                if os.path.getmtime(f) >= self._watch_start)
            if touched:
                self._start_conversion(touched)
                return
        self._set_status(
            "Timed out — use Browse to select the file manually / "
            "Délai dépassé — utilisez Parcourir pour sélectionner le fichier",
            "error")
        self._busy = False

    # ── Conversion ────────────────────────────────────────────────────────────

    def _start_conversion(self, files):
        self._busy = True
        threading.Thread(target=self._convert_worker,
                         args=(files,), daemon=True).start()

    def _convert_worker(self, files):
        try:
            self._convert_worker_inner(files)
        except Exception as exc:
            self._log_error(exc)
            self._set_status(
                "Unexpected error — see error.log for details / "
                "Erreur inattendue — voir error.log pour les détails",
                "error")
        finally:
            self._busy = False

    def _convert_worker_inner(self, files):
        if not _ensure_dedrm():
            self._set_status(
                "DeDRM missing — run setup.sh and restart / "
                "DeDRM manquant — exécutez setup.sh et redémarrez",
                "error")
            self._busy = False
            return

        if not os.path.exists(_ade_activation_path()):
            self._set_status(
                "Adobe Digital Editions not authorised — open ADE → Help → Authorize Computer / "
                "ADE non autorisé — ouvrez ADE → Aide → Autoriser l'ordinateur",
                "error")
            self._busy = False
            return

        try:
            keys, _ = adobekey.adeptkeys()
        except Exception as exc:
            self._log_error(exc)
            self._set_status(
                "Cannot read Adobe key — try re-authorising ADE / "
                "Impossible de lire la clé Adobe — réautorisez ADE",
                "error")
            self._busy = False
            return

        if not keys:
            self._set_status(
                "No Adobe key found — open ADE and re-authorise / "
                "Aucune clé Adobe — ouvrez ADE et réautorisez",
                "error")
            self._busy = False
            return

        key        = keys[0]
        settings   = load_settings()
        output_dir = settings.get("output_dir") or DEFAULT_OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)

        converted = []
        drm_free  = []

        for inpath in files:
            self._set_status(
                f"Removing DRM… / Suppression du DRM…  {os.path.basename(inpath)}",
                "working")
            outpath = self._out_path(inpath, output_dir)
            try:
                result = (ineptpdf.decryptBook(key, inpath, outpath)
                          if inpath.lower().endswith(".pdf")
                          else ineptepub.decryptBook(key, inpath, outpath))
            except ineptpdf.PDFEncryptionError as exc:
                if "not encrypted" in str(exc).lower():
                    result = 1  # treat as DRM-free
                else:
                    self._log_error(exc)
                    self._set_status(
                        f"Decryption error — see error.log for details / "
                        f"Erreur de déchiffrement — voir error.log pour les détails",
                        "error")
                    self._busy = False
                    return
            except Exception as exc:
                self._log_error(exc)
                self._set_status(
                    f"Decryption error — see error.log for details / "
                    f"Erreur de déchiffrement — voir error.log pour les détails",
                    "error")
                self._busy = False
                return

            if result == 0:
                converted.append(outpath)
            elif result == 1:
                drm_free.append(inpath)   # already DRM-free, send the original
            else:
                self._set_status(
                    "Decryption failed — wrong ADE account? / "
                    "Déchiffrement échoué — mauvais compte ADE ?",
                    "error")
                self._busy = False
                return

        to_send = converted + drm_free
        self._last_output_dir = output_dir

        n        = len(to_send)
        label    = "Book saved" if n == 1 else f"{n} books saved"
        label_fr = "Livre sauvegardé" if n == 1 else f"{n} livres sauvegardés"

        if not settings.get("send_to_kindle"):
            self._set_status(f"✓  {label} / {label_fr}", "ok", show_reveal=True)
            self._busy = False
            return

        target = settings.get("kindle_email", "")
        if not target:
            self._set_status(
                "Kindle address not configured — open Settings / "
                "Adresse Kindle non configurée — ouvrez les Paramètres",
                "error", show_reveal=bool(converted))
            self._busy = False
            return

        self._set_status("Sending to Kindle… / Envoi vers Kindle…", "working")
        all_sent = all(send_file_to_kindle(f, target) for f in to_send)

        label    = "Book sent" if n == 1 else f"{n} books sent"
        label_fr = "Livre envoyé" if n == 1 else f"{n} livres envoyés"

        if all_sent:
            if self._pending_expiry:
                expiry_str, title = self._pending_expiry
                add_loan(title, expiry_str, converted[0] if converted else "")
                self._pending_expiry = None
                self._set_status(
                    f"✓  {label} / {label_fr} — "
                    f"loan expires / prêt expire le {expiry_str[:10]}",
                    "ok", show_reveal=True)
            else:
                self._set_status(
                    f"✓  {label} / {label_fr} to Kindle!",
                    "ok", show_reveal=True)
        else:
            self._set_status(
                "Converted but email failed — open Mail and add an account / "
                "Converti mais l'envoi a échoué — ouvrez Mail et ajoutez un compte",
                "error", show_reveal=bool(converted))

        self._busy = False

    @staticmethod
    def _out_path(inpath, out_dir):
        stem, ext = os.path.splitext(os.path.basename(inpath))
        candidate = os.path.join(out_dir, f"{stem}{ext}")
        n = 2
        while os.path.exists(candidate):
            candidate = os.path.join(out_dir, f"{stem}_{n}{ext}")
            n += 1
        return candidate

    @staticmethod
    def _log_error(exc):
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(ERROR_LOG, "a") as f:
            f.write(f"\n{'='*60}\n{datetime.now().isoformat()}\n")
            traceback.print_exc(file=f)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ConverterApp().mainloop()
