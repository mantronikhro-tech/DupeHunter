#!/usr/bin/env python3
import os
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from datetime import datetime
import getpass
import platform
import string
import hashlib
from collections import defaultdict
from typing import Optional, List, Tuple, Set, Dict
import base64
import io
import json

# ---------------------------------------------------------------------------
# Config – Theme-Einstellung speichern/laden
# ---------------------------------------------------------------------------
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".dupehunter_config.json")

def config_laden() -> dict:
    """Lädt gespeicherte Einstellungen. Gibt dict mit Defaults zurück."""
    defaults = {"theme": 0, "geometry": "1500x900", "lang": detect_language()}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            idx = int(data.get("theme", 0))
            if idx not in (0, 1, 2):
                idx = 0
            lang = data.get("lang", detect_language())
            if lang not in LANGUAGES:
                lang = "en"
            return {
                "theme":    idx,
                "geometry": data.get("geometry", defaults["geometry"]),
                "lang":     lang,
            }
    except Exception:
        return defaults

def config_speichern(theme_idx: int, geometry: str = "", lang: str = ""):
    """Speichert Theme, Fenstergröße/-position und Sprache."""
    try:
        data: dict = {"theme": theme_idx}
        if geometry:
            data["geometry"] = geometry
        if lang:
            data["lang"] = lang
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Pillow-Check – einmalig beim Start
# ---------------------------------------------------------------------------
try:
    from PIL import Image, ImageTk  # pip install pillow
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False

def check_pillow_and_notify(root: tk.Tk):
    """Zeigt einen freundlichen Hinweis wenn Pillow fehlt."""
    if PILLOW_OK:
        return

    win = tk.Toplevel(root)
    win.title(T("pillow_title"))
    win.resizable(False, False)
    win.geometry("480x300")
    win.configure(bg="#1E1E1E")
    win.grab_set()

    win.update_idletasks()
    x = root.winfo_x() + root.winfo_width()  // 2 - 240
    y = root.winfo_y() + root.winfo_height() // 2 - 115
    win.geometry(f"480x300+{x}+{y}")

    tk.Label(win, text=T("pillow_head"),
             font=("Segoe UI" if platform.system() == "Windows"
                   else "Helvetica", 13, "bold"),
             bg="#1E1E1E", fg="#FFD60A").pack(pady=(22, 6))

    tk.Label(win,
             text=T("pillow_body").replace("\\n", "\n"),
             font=("Segoe UI" if platform.system() == "Windows"
                   else "Helvetica", 11),
             bg="#1E1E1E", fg="#D4D4D4",
             justify=tk.CENTER).pack()

    # Befehl als kopierbares Label
    cmd = "pip install pillow"
    cmd_lbl = tk.Label(win, text=cmd,
                        font=("Courier New", 11, "bold"),
                        bg="#2D2D2D", fg="#4EC9B0",
                        padx=12, pady=6, cursor="hand2")
    cmd_lbl.pack(pady=(8, 0))

    # Klick kopiert den Befehl in die Zwischenablage
    def copy_cmd(e=None):
        root.clipboard_clear()
        root.clipboard_append(cmd)
        cmd_lbl.config(text="✅ Kopiert!")
        win.after(1500, lambda: cmd_lbl.config(text=cmd))

    cmd_lbl.bind("<Button-1>", copy_cmd)

    tk.Label(win, text="(Klick zum Kopieren)",
             font=("Segoe UI" if platform.system() == "Windows"
                   else "Helvetica", 9),
             bg="#1E1E1E", fg="#858585").pack(pady=(2, 0))

    tk.Button(win, text="Verstanden",
              font=("Segoe UI" if platform.system() == "Windows"
                    else "Helvetica", 11, "bold"),
              relief="flat", bg="#007AFF", fg="white",
              padx=20, pady=6, cursor="hand2",
              activebackground="#007AFF", activeforeground="white",
              command=win.destroy).pack(pady=(10, 0))

# ---------------------------------------------------------------------------
# App-Icon (eingebettet als Base64-PNG, 80x80)
# ---------------------------------------------------------------------------
ICON_B64 = (
    "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"
)


# ---------------------------------------------------------------------------
# Mehrsprachigkeit  (i18n)
# ---------------------------------------------------------------------------
# Neue Sprache hinzufügen:
#   1. Neues Dict mit allen Keys unten anlegen
#   2. Dict in LANGUAGES eintragen
#   3. Fertig – kein weiterer Code nötig
# ---------------------------------------------------------------------------

LANGUAGES: Dict[str, Dict[str, str]] = {
    "de": {
        # Sidebar Tooltips
        "tt_scan":          "System-Scan starten",
        "tt_folder":        "Ordner auswählen & scannen",
        "tt_export":        "Ergebnisse als CSV exportieren",
        "tt_pause":         "Scan pausieren / fortsetzen",
        "tt_stop":          "Scan abbrechen",
        "tt_info":          "Über DupeHunter",
        "tt_hash":          "Schnell-Hash: vergleicht Anfang + Ende jeder Datei – sehr zuverlässig, kein vollständiger Dateivergleich",
        "tt_dupe":          "Nur Duplikate anzeigen (Name-basiert)",
        "tt_mb":            "Dateien kleiner als dieser Wert werden ausgeblendet. Standard: 45 MB – filtert kleine System- und Hilfsdateien heraus.",
        # Chip Tooltips
        "chip_all":         "Alle Dateitypen anzeigen",
        "chip_cross":       "Dateien die auf beiden Systemen laufen",
        "chip_installer":   "Native Installer für dieses System",
        "chip_game":        "Spiele-Dateien (Steam, Epic, etc.)",
        "chip_program":     "Erkannte Programm-Dateien",
        "chip_document":    "PDF-Dokumente ab 1 MB",
        "chip_unknown":     "Nicht klassifizierte Dateien",
        # Chip Labels
        "chip_all_lbl":     "Alle",
        # Statuszeile
        "status_ready":     "Bereit zum Scannen",
        "status_scanning":  "🔍 Scanne: {folder}…",
        "status_done":      "✅ Fertig: {count} Funde | {gb:.2f} GB",
        "status_stopped":   "⏹ Abgebrochen",
        "status_paused":    "⏸ PAUSIERT",
        "status_no_files":  "Scan beendet: Keine Dateien gefunden.",
        "status_no_files_mb": "Scan beendet: Keine Dateien gefunden  –  Tipp: MB-Regler steht auf {mb} MB, evtl. reduzieren?",
        "status_hashing":   "🔬 Hash {i}/{total}: {name}",
        "status_hash_done_none": "🔬 Hash-Check abgeschlossen: Keine identischen Dateien gefunden.",
        "status_hash_done": "🔴 Schnell-Hash: {groups} Duplikat-Gruppe(n) – {count} sehr wahrscheinlich identische Dateien",
        "status_removed":   "🗑 {count} Eintrag/Einträge entfernt  –  ↩ Rückgängig per Rechtsklick",
        "status_restored":  "↩ Wiederhergestellt: {name}",
        "status_undo_empty":"Nichts zum Rückgängigmachen.",
        # Dupe Labels
        "dupe_none":        "✅ Keine Hash-Dupes",
        "dupe_count":       "🔴 {groups} Hash-Gruppen ({count} Dateien)",
        "dupe_btn":         "⚠️ Nur Duplikate",
        # Buttons
        "btn_hash":         "🔬 Hash-Check",
        "btn_hashing":      "🔬 Hashing…",
        "btn_close":        "Schließen",
        "btn_pause":        "⏸",
        "btn_resume":       "▶",
        # Min-Größe
        "min_size":         "Min. Größe:",
        # Treeview Spalten
        "col_name":         "Name",
        "col_size":         "Größe",
        "col_type":         "Typ",
        "col_date":         "Datum",
        "col_path":         "Pfad",
        # Kontextmenü
        "ctx_open":         "📂 Ordner öffnen",
        "ctx_copy":         "📋 Pfad kopieren",
        "ctx_remove":       "🗑 Aus Liste entfernen",
        "ctx_undo":         "↩ Entfernen rückgängig",
        # Dialoge
        "dlg_hash_title":   "Hash-Check",
        "dlg_hash_noscan":  "Bitte zuerst einen Scan durchführen.",
        "dlg_export_empty": "Keine Daten zum Exportieren.",
        "dlg_export_ok":    "{count} Einträge gespeichert!",
        "dlg_export_filter":"Filter aktiv: {filter}",
        "dlg_export_err":   "Speichern fehlgeschlagen: {error}",
        "dlg_export_title": "Export erfolgreich",
        "dlg_export_etitle":"Fehler",
        # Info-Dialog
        "info_title":       "Über DupeHunter",
        "info_desc":        "Scannt Datenträger nach Installationsdateien,\nerkennt Duplikate per Name und Hash-Prüfung.\nLäuft auf Windows & Linux  |  Python 3.8+",
        "info_github":      "Neueste Version auf GitHub:",
        # Pillow-Dialog
        "pillow_title":     "Hinweis – Optionales Paket fehlt",
        "pillow_head":      "📦 Pillow nicht installiert",
        "pillow_body":      "Das Icon im Info-Dialog wird ohne Pillow\nnicht angezeigt. Alles andere funktioniert normal.\n\nInstallation (einmalig im Terminal):",
        "pillow_copied":    "✅ Kopiert!",
        # Typen
        "type_cross":       "🔀 Cross-Plattform",
        "type_installer":   "📦 Installer",
        "type_game":        "🎮 Spiel",
        "type_program":     "⚙️ Programm",
        "type_document":    "📄 Dokument",
        "type_unknown":     "❓ Unbekannt",
        "type_copy":        " 📂 (Kopie)",
        "type_version":     " 🔄 (Version)",
        # Export CSV Header
        "csv_header":       "Name;Größe;Typ;Datum;Pfad;Hash-Duplikat",
        "csv_hash_yes":     "JA",
        # Sprach-Anzeige
        "lang_label":       "🇩🇪",
    },
    "en": {
        "tt_scan":          "Start system scan",
        "tt_folder":        "Select folder & scan",
        "tt_export":        "Export results as CSV",
        "tt_pause":         "Pause / resume scan",
        "tt_stop":          "Stop scan",
        "tt_info":          "About DupeHunter",
        "tt_hash":          "Quick-hash: compares start + end of each file – very reliable, not a full file comparison",
        "tt_dupe":          "Show duplicates only (name-based)",
        "tt_mb":            "Files smaller than this value are hidden. Default: 45 MB – filters out small system and helper files.",
        "chip_all":         "Show all file types",
        "chip_cross":       "Files that run on both systems",
        "chip_installer":   "Native installers for this system",
        "chip_game":        "Game files (Steam, Epic, etc.)",
        "chip_program":     "Detected program files",
        "chip_document":    "PDF documents from 1 MB",
        "chip_unknown":     "Unclassified files",
        "chip_all_lbl":     "All",
        "status_ready":     "Ready to scan",
        "status_scanning":  "🔍 Scanning: {folder}…",
        "status_done":      "✅ Done: {count} found | {gb:.2f} GB",
        "status_stopped":   "⏹ Stopped",
        "status_paused":    "⏸ PAUSED",
        "status_no_files":  "Scan complete: No files found.",
        "status_no_files_mb": "Scan complete: No files found  –  Tip: MB slider is at {mb} MB, try reducing it?",
        "status_hashing":   "🔬 Hash {i}/{total}: {name}",
        "status_hash_done_none": "🔬 Hash-check complete: No identical files found.",
        "status_hash_done": "🔴 Quick-hash: {groups} duplicate group(s) – {count} very likely identical files",
        "status_removed":   "🗑 {count} item(s) removed  –  ↩ Undo via right-click",
        "status_restored":  "↩ Restored: {name}",
        "status_undo_empty":"Nothing to undo.",
        "dupe_none":        "✅ No hash dupes",
        "dupe_count":       "🔴 {groups} hash groups ({count} files)",
        "dupe_btn":         "⚠️ Dupes only",
        "btn_hash":         "🔬 Hash-Check",
        "btn_hashing":      "🔬 Hashing…",
        "btn_close":        "Close",
        "btn_pause":        "⏸",
        "btn_resume":       "▶",
        "min_size":         "Min. size:",
        "col_name":         "Name",
        "col_size":         "Size",
        "col_type":         "Type",
        "col_date":         "Date",
        "col_path":         "Path",
        "ctx_open":         "📂 Open folder",
        "ctx_copy":         "📋 Copy path",
        "ctx_remove":       "🗑 Remove from list",
        "ctx_undo":         "↩ Undo remove",
        "dlg_hash_title":   "Hash-Check",
        "dlg_hash_noscan":  "Please run a scan first.",
        "dlg_export_empty": "No data to export.",
        "dlg_export_ok":    "{count} entries saved!",
        "dlg_export_filter":"Filter active: {filter}",
        "dlg_export_err":   "Save failed: {error}",
        "dlg_export_title": "Export successful",
        "dlg_export_etitle":"Error",
        "info_title":       "About DupeHunter",
        "info_desc":        "Scans drives for installation files,\ndetects duplicates by name and hash.\nRuns on Windows & Linux  |  Python 3.8+",
        "info_github":      "Latest version on GitHub:",
        "pillow_title":     "Notice – Optional package missing",
        "pillow_head":      "📦 Pillow not installed",
        "pillow_body":      "The icon in the info dialog requires Pillow.\nEverything else works normally.\n\nInstall it once in your terminal:",
        "pillow_copied":    "✅ Copied!",
        "type_cross":       "🔀 Cross-Platform",
        "type_installer":   "📦 Installer",
        "type_game":        "🎮 Game",
        "type_program":     "⚙️ Program",
        "type_document":    "📄 Document",
        "type_unknown":     "❓ Unknown",
        "type_copy":        " 📂 (Copy)",
        "type_version":     " 🔄 (Version)",
        "csv_header":       "Name;Size;Type;Date;Path;Hash-Duplicate",
        "csv_hash_yes":     "YES",
        "lang_label":       "🇬🇧",
    },
}

# Verfügbare Sprachen in Reihenfolge für den Umschalter
LANG_ORDER = ["de", "en"]

def detect_language() -> str:
    """Erkennt die Systemsprache. Fallback: Englisch."""
    try:
        import locale
        # Python 3.15+ kompatibel: getlocale() statt getdefaultlocale()
        lang = locale.getlocale()[0] or ""
        if not lang:
            # Fallback über Umgebungsvariablen (Windows)
            import os
            lang = os.environ.get("LANG", os.environ.get("LANGUAGE", ""))
        if lang.startswith("de"):
            return "de"
        return "en"
    except Exception:
        return "en"

# Aktive Sprache – wird beim Start gesetzt, kann per Klick gewechselt werden
_current_lang: str = "de"   # wird in config_laden() überschrieben

def T(key: str, **kwargs) -> str:
    """Übersetzung abrufen. Unbekannte Keys geben den Key selbst zurück."""
    text = LANGUAGES.get(_current_lang, LANGUAGES["en"]).get(key, key)
    return text.format(**kwargs) if kwargs else text

def set_language(lang: str):
    global _current_lang
    if lang in LANGUAGES:
        _current_lang = lang

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------
VERSION = "6.0"
SYSTEM  = platform.system()

SPIELE_KEYWORDS   = ["steam", "epic games", "gog games", "origin", "ubisoft",
                     "games", "spiele", "riot games", "blizzard", "ea sports",
                     "GOG Galaxy", "gog galaxy", "battle.net", "battlenet",
                     "rockstar games", "bethesda"]
SPIELE_DATEINAMEN = ["setup", "install", "launcher", "update", "patch",
                     "game", "play", "steam_api", "unins"]

PROGRAMM_KEYWORDS = ["appdata", "locallow", "adobe", "office", "google",
                     "microsoft", "common files", "program files", "metatrader",
                     "programme", "applications", "opt", "usr/local",
                     "jetbrains", "visual studio", "anaconda", "python",
                     "nodejs", "java", "jdk", "jre"]

# Dateinamen-Muster die auf Installer hindeuten (unabhängig vom Pfad)
INSTALLER_MUSTER  = ["setup", "install", "installer", "einrichten",
                     "instalar", "installa"]

STOP_WORDS        = {"chipset", "driver", "unins", "vc_redist", "dxsetup",
                     "helper", "ndp", "redist", "redistributable",
                     "directx", "dotnet", "windowsdesktop"}

SCAN_EXT_UNIVERSAL = {".exe", ".deb", ".appimage", ".run", ".msi",
                      ".zip", ".rar", ".iso", ".pkg", ".pdf"}
COMPOUND_EXT       = {".tar.gz"}

PDF_MIN_MB = 1    # PDFs ab 1 MB – filtert leere Formulare & Web-PDFs heraus

NATIVE_EXT = {
    "Windows": {".exe", ".msi"},
    "Linux":   {".exe", ".deb", ".appimage", ".run"},
}
FOREIGN_EXT   = {".exe", ".deb", ".appimage", ".run", ".msi"} - NATIVE_EXT.get(SYSTEM, set())
INSTALLER_EXT = NATIVE_EXT.get(SYSTEM, set()) - {".exe"}

IGNORE_COMMON = {"temp", "download", "update", "driver", "$recycle.bin"}
IGNORE_LINUX  = {"trash", ".trash", "x86", "x64", "intel", "geforce", "msi",
                 "programdata", "win-x64"}
IGNORE_WIN    = {"windows", "system32", "system volume information",
                 "$windows.~ws", "recovery", "windowsapps", "programdata",
                 "intel", "geforce", "msi", "win-x64",
                 "packages", "localcache", "winsxs", "servicing",
                 "installer", "softwaredistribution"}
ORDNER_IGNORE = IGNORE_COMMON | (IGNORE_WIN if SYSTEM == "Windows" else IGNORE_LINUX)

MIN_GROESSE_MB = 45
BATCH_SIZE     = 50
HASH_CHUNK     = 65536   # 64 KB Blöcke für schnelles Hashing

# ---------------------------------------------------------------------------
# Theme-Definitionen
# ---------------------------------------------------------------------------
THEMES = {
    0: {
        "name":          "☀️ Light",
        "bg":            "#F5F5F7",
        "fg":            "#1D1D1F",
        "tree_bg":       "#FFFFFF",
        "tree_odd":      "#FBFBFD",
        "tree_even":     "#FFFFFF",
        "tree_heading":  "#E5E5E7",
        "entry_bg":      "#FFFFFF",
        "entry_border":  "#D2D2D7",
        "btn_folder":    "#E5E5E7",
        "btn_folder_fg": "#1D1D1F",
        "textgray":      "#86868B",
        "blue":          "#007AFF",
        "red":           "#FF5F56",
        "yellow":        "#FFBD2E",
        "green":         "#27AE60",
        "gray":          "#D2D2D7",
        "darkgray":      "#4A4A4A",
        "slider_trough": "#D2D2D7",
        "dupe_fg":       "#E07000",
        "dupe_bg":       "#FFF3E0",
        "hash_dupe_fg":  "#C0392B",
        "hash_dupe_bg":  "#FDECEA",
    },
    1: {
        "name":          "🌑 Dark",
        "bg":            "#1E1E1E",
        "fg":            "#D4D4D4",
        "tree_bg":       "#252526",
        "tree_odd":      "#2D2D2D",
        "tree_even":     "#252526",
        "tree_heading":  "#333333",
        "entry_bg":      "#3C3C3C",
        "entry_border":  "#555555",
        "btn_folder":    "#3C3C3C",
        "btn_folder_fg": "#D4D4D4",
        "textgray":      "#858585",
        "blue":          "#4FC3F7",
        "red":           "#F44747",
        "yellow":        "#FFBD2E",
        "green":         "#4EC9B0",
        "gray":          "#3C3C3C",
        "darkgray":      "#666666",
        "slider_trough": "#3C3C3C",
        "dupe_fg":       "#FF8C00",
        "dupe_bg":       "#2D2200",
        "hash_dupe_fg":  "#FF6B6B",
        "hash_dupe_bg":  "#2D0F0F",
    },
    2: {
        "name":          "🍎 macOS",
        "bg":            "#1C1C1E",
        "fg":            "#F2F2F7",
        "tree_bg":       "#2C2C2E",
        "tree_odd":      "#3A3A3C",
        "tree_even":     "#2C2C2E",
        "tree_heading":  "#3A3A3C",
        "entry_bg":      "#3A3A3C",
        "entry_border":  "#48484A",
        "btn_folder":    "#3A3A3C",
        "btn_folder_fg": "#F2F2F7",
        "textgray":      "#8E8E93",
        "blue":          "#0A84FF",
        "red":           "#FF453A",
        "yellow":        "#FFD60A",
        "green":         "#30D158",
        "gray":          "#48484A",
        "darkgray":      "#636366",
        "slider_trough": "#48484A",
        "dupe_fg":       "#FF9933",
        "dupe_bg":       "#2A1A00",
        "hash_dupe_fg":  "#FF6B6B",
        "hash_dupe_bg":  "#2D0F0F",
    },
}

ACCENT = {
    "installer":     "#8B5CF6",
    "crossplatform": "#06B6D4",
    "kopie":         "#FF9500",
    "version":       "#5AC8FA",
}

# Plattformübergreifende Schriftart
FONT_DEFAULT = ("Segoe UI" if SYSTEM == "Windows" else "Helvetica", 11)
FONT_BOLD    = ("Segoe UI" if SYSTEM == "Windows" else "Helvetica", 11, "bold")
FONT_SMALL   = ("Segoe UI" if SYSTEM == "Windows" else "Helvetica", 10)
FONT_ITALIC  = ("Segoe UI" if SYSTEM == "Windows" else "Helvetica", 11, "italic")
FONT_TINY    = ("Segoe UI" if SYSTEM == "Windows" else "Helvetica", 9)

THEME_LABELS = ["☀️ Light", "🌑 Dark", "🍎 macOS"]


# ---------------------------------------------------------------------------
# Pfad-Logik
# ---------------------------------------------------------------------------
def get_start_paths() -> List[str]:
    paths = []
    if SYSTEM == "Windows":
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                paths.append(drive)
    else:
        user_name = getpass.getuser()
        paths.append(os.path.expanduser("~"))
        for p in [f"/media/{user_name}", "/mnt"]:
            if os.path.exists(p):
                paths.append(p)
    return paths


def get_file_ext(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".tar.gz"):
        return ".tar.gz"
    return os.path.splitext(lower)[1]


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------
def hash_datei(pfad: str) -> Optional[str]:
    """
    Berechnet einen schnellen MD5-Hash aus:
      - den ersten 64 KB
      - den letzten 64 KB
      - der Dateigröße
    Das reicht für praktisch alle Installer/Archive um echte Duplikate
    sicher zu erkennen, ohne die komplette Datei lesen zu müssen.
    """
    try:
        groesse = os.path.getsize(pfad)
        h = hashlib.md5()
        h.update(str(groesse).encode())
        with open(pfad, "rb") as f:
            h.update(f.read(HASH_CHUNK))          # Anfang
            if groesse > HASH_CHUNK * 2:
                f.seek(-HASH_CHUNK, 2)
                h.update(f.read(HASH_CHUNK))       # Ende
        return h.hexdigest()
    except OSError:
        return None


# ---------------------------------------------------------------------------
# Duplikat-Erkennung
# ---------------------------------------------------------------------------
def berechne_name_duplikate(fundliste: List[Tuple]) -> Set[str]:
    """
    Schnelle Vorprüfung: Dateinamen, die in mehr als einem Ordner vorkommen.
    """
    name_zu_ordner: Dict[str, Set[str]] = defaultdict(set)
    for name, _, _, _, ordner in fundliste:
        name_zu_ordner[name].add(ordner)
    return {name for name, ordner in name_zu_ordner.items() if len(ordner) > 1}


def berechne_hash_duplikate(fundliste: List[Tuple],
                             status_cb=None) -> Dict[str, List[str]]:
    """
    Hash-basierte Prüfung aller Dateien in fundliste.
    Gibt ein Dict {hash: [pfad1, pfad2, ...]} zurück – nur Einträge mit > 1 Pfad.
    status_cb(text) wird aufgerufen um den Fortschritt zu melden.
    """
    hash_zu_pfade: Dict[str, List[str]] = defaultdict(list)
    total = len(fundliste)
    for i, (name, _, _, _, ordner) in enumerate(fundliste):
        voller_pfad = os.path.join(ordner, name)
        if status_cb:
            status_cb(T("status_hashing", i=i+1, total=total, name=name))
        h = hash_datei(voller_pfad)
        if h:
            hash_zu_pfade[h].append(voller_pfad)
    return {h: pfade for h, pfade in hash_zu_pfade.items() if len(pfade) > 1}


# ---------------------------------------------------------------------------
# Tooltip-Hilfsklasse
# ---------------------------------------------------------------------------
class Tooltip:
    """Zeigt einen kleinen Hinweistext wenn man über ein Widget hovert."""

    def __init__(self, widget: tk.Widget, text: str):
        self._widget  = widget
        self._text    = text
        self._tip_win: Optional[tk.Toplevel] = None
        widget.bind("<Enter>",  self._show)
        widget.bind("<Leave>",  self._hide)
        widget.bind("<Button>", self._hide)

    def _show(self, event=None):
        if self._tip_win:
            return
        x = self._widget.winfo_rootx() + self._widget.winfo_width() + 6
        y = self._widget.winfo_rooty() + self._widget.winfo_height() // 2 - 10

        self._tip_win = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)   # kein Fensterrahmen
        tw.wm_geometry(f"+{x}+{y}")
        tw.wm_attributes("-topmost", True)

        lbl = tk.Label(tw, text=self._text,
                        font=(FONT_SMALL[0], FONT_SMALL[1]),
                        bg="#1D1D1F", fg="#F5F5F7",
                        relief="flat", padx=10, pady=5)
        lbl.pack()

    def _hide(self, event=None):
        if self._tip_win:
            self._tip_win.destroy()
            self._tip_win = None


# ---------------------------------------------------------------------------
# Haupt-App
# ---------------------------------------------------------------------------
class DupeHunterApp:
    def __init__(self, root: tk.Tk):
        self.root         = root
        self.root.title(f"DupeHunter  v{VERSION}")
        self.root.geometry("1500x900")
        self.root.minsize(900, 600)

        self.alle_fundstuecke: List[Tuple] = []
        self.scan_aktiv      = False
        self.pausiert        = False
        self.pause_condition = threading.Condition()
        self._scan_lock      = threading.Lock()   # verhindert Doppelstart
        self._pending_batch: List[Tuple] = []

        # Hash-Ergebnis: set von vollen Pfaden, die echte Duplikate sind
        self._hash_dupe_pfade: Set[str] = set()
        self._hash_laeuft = False

        # Performance: Cache für Duplikat-Berechnung
        self._name_dupes_cache: Set[str] = set()
        self._cache_dirty       = True   # True = neu berechnen nötig

        # Performance: Schnellsuche für Kopie/Version-Erkennung im Scan
        self._gesehene_namen: Dict[str, int] = {}  # name → groesse_mb

        # Undo-Stack für "Aus Liste entfernen"
        self._undo_stack: List[Tuple] = []   # Liste entfernter Einträge

        self._nur_dupes   = tk.BooleanVar(value=False)
        self._hash_modus  = tk.BooleanVar(value=False)   

        cfg = config_laden()
        set_language(cfg["lang"])
        self._theme_idx  = tk.IntVar(value=cfg["theme"])
        self._t          = THEMES[0]
        self._sort_col   : Optional[str]  = None
        self._sort_rev   : bool           = False

        self._build_styles()
        self._build_ui()
        # Fenstergröße/-position wiederherstellen
        try:
            self.root.geometry(cfg["geometry"])
        except Exception:
            self.root.geometry("1500x900")
        self._theme_idx.set(cfg["theme"])
        self._apply_theme(cfg["theme"])
        # Fenstergröße beim Schließen speichern
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------
    def _build_styles(self):
        self._style = ttk.Style()
        self._style.theme_use("clam")

    def _refresh_styles(self, t: dict):
        self._style.configure(
            "Treeview",
            background=t["tree_bg"], fieldbackground=t["tree_bg"],
            foreground=t["fg"], rowheight=30, font=FONT_DEFAULT)
        self._style.configure(
            "Treeview.Heading",
            font=FONT_BOLD,
            background=t["tree_heading"], foreground=t["fg"], relief="flat")
        self._style.map("Treeview", background=[("selected", t["blue"])])
        self._style.configure(
            "TCombobox",
            fieldbackground=t["entry_bg"], background=t["entry_bg"],
            foreground=t["fg"], selectbackground=t["blue"],
            selectforeground="white")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        # DPI-Awareness für Windows
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        # ── Haupt-Layout: Sidebar links + Content rechts ──────────────
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # ── Sidebar ───────────────────────────────────────────────────
        self.sidebar = tk.Frame(self.main_frame, width=56)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        self.btn_scan = tk.Button(
            self.sidebar, text="🔍",
            font=(FONT_DEFAULT[0], 16), relief="flat",
            cursor="hand2", bd=0, pady=14,
            command=lambda: self.start_scan("auto"))
        self.btn_scan.pack(fill=tk.X, pady=(14, 2))

        self.btn_folder = tk.Button(
            self.sidebar, text="📁",
            font=(FONT_DEFAULT[0], 16), relief="flat",
            cursor="hand2", bd=0, pady=10,
            command=lambda: self.start_scan("manual"))
        self.btn_folder.pack(fill=tk.X, pady=2)

        self.btn_export = tk.Button(
            self.sidebar, text="💾",
            font=(FONT_DEFAULT[0], 16), relief="flat",
            cursor="hand2", bd=0, pady=10,
            command=self.export_liste)
        self.btn_export.pack(fill=tk.X, pady=2)

        tk.Frame(self.sidebar, height=1).pack(fill=tk.X, padx=8, pady=10)

        self.btn_pause = tk.Button(
            self.sidebar, text="⏸",
            font=(FONT_DEFAULT[0], 14), relief="flat",
            cursor="hand2", bd=0, pady=8,
            state=tk.DISABLED,
            command=self.toggle_pause)
        self.btn_pause.pack(fill=tk.X, pady=2)

        self.btn_stop = tk.Button(
            self.sidebar, text="⏹",
            font=(FONT_DEFAULT[0], 14), relief="flat",
            cursor="hand2", bd=0, pady=8,
            state=tk.DISABLED,
            command=self.stop_scan)
        self.btn_stop.pack(fill=tk.X, pady=2)

        self.btn_info = tk.Button(
            self.sidebar, text="ℹ️",
            font=(FONT_DEFAULT[0], 14), relief="flat",
            cursor="hand2", bd=0, pady=8,
            command=self._show_info)
        self.btn_info.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 8))

        # Sprach-Umschalter (🇩🇪 / 🇬🇧)
        self.btn_lang = tk.Button(
            self.sidebar, text=T("lang_label"),
            font=(FONT_DEFAULT[0], 13), relief="flat",
            cursor="hand2", bd=0, pady=6,
            command=self._toggle_language)
        self.btn_lang.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 2))
        Tooltip(self.btn_lang, "Sprache wechseln / Switch language")

        # Tooltips für Sidebar-Icons
        Tooltip(self.btn_scan,   T("tt_scan"))
        Tooltip(self.btn_folder, T("tt_folder"))
        Tooltip(self.btn_export, T("tt_export"))
        Tooltip(self.btn_pause,  T("tt_pause"))
        Tooltip(self.btn_stop,   T("tt_stop"))
        Tooltip(self.btn_info,   T("tt_info"))

        # Theme-Punkte (●●●) unten in Sidebar
        self.theme_frame = tk.Frame(self.sidebar)
        self.theme_frame.pack(side=tk.BOTTOM, pady=(0, 6))
        self._theme_dots = []
        _theme_names = ["☀️ Light", "🌑 Dark", "🍎 macOS"]
        for i in range(3):
            dot = tk.Label(self.theme_frame, text="●",
                           font=(FONT_DEFAULT[0], 11),
                           cursor="hand2")
            dot.pack()
            dot.bind("<Button-1>", lambda e, idx=i: self._set_theme(idx))
            Tooltip(dot, f"Theme: {_theme_names[i]}")
            self._theme_dots.append(dot)

        # Trennlinie Sidebar / Content
        self.sidebar_sep = tk.Frame(self.main_frame, width=1)
        self.sidebar_sep.pack(side=tk.LEFT, fill=tk.Y)

        # ── Content-Bereich ───────────────────────────────────────────
        self.content = tk.Frame(self.main_frame)
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ── Topbar: Suche + Chips + Version ──────────────────────────
        self.topbar = tk.Frame(self.content, pady=10, padx=14)
        self.topbar.pack(fill=tk.X)

        self.such_frame = tk.Frame(self.topbar, padx=10, pady=6)
        self.such_frame.pack(side=tk.LEFT, padx=(0, 10))
        self._such_icon = tk.Label(self.such_frame, text="🔎",
                                    font=(FONT_DEFAULT[0], 12))
        self._such_icon.pack(side=tk.LEFT)
        self.such_entry = tk.Entry(self.such_frame, font=FONT_DEFAULT,
                                    relief="flat", highlightthickness=0,
                                    width=28, bd=0)
        self.such_entry.pack(side=tk.LEFT, padx=(6, 0), ipady=1)
        self.such_entry.bind("<KeyRelease>", self.filter_tabelle)

        # Typ-Filter als Chips
        self.chip_frame = tk.Frame(self.topbar)
        self.chip_frame.pack(side=tk.LEFT, padx=4)
        self._chip_values = [
            (T("chip_all_lbl"), "Alle",              T("chip_all")),
            ("🔀",  T("type_cross"),                 T("chip_cross")),
            ("📦",  T("type_installer"),             T("chip_installer")),
            ("🎮",  T("type_game"),                  T("chip_game")),
            ("⚙️", T("type_program"),               T("chip_program")),
            ("📄",  T("type_document"),              T("chip_document")),
            ("❓",  T("type_unknown"),               T("chip_unknown")),
        ]
        self._chip_buttons = []
        self.typ_var = tk.StringVar(value="Alle")
        for label, value, tip in self._chip_values:
            btn = tk.Button(
                self.chip_frame, text=label,
                font=FONT_SMALL, relief="flat",
                padx=10, pady=4, cursor="hand2", bd=0,
                command=lambda v=value: self._set_chip(v))
            btn.pack(side=tk.LEFT, padx=2)
            Tooltip(btn, tip)
            self._chip_buttons.append((btn, value, tip))

        os_label = "🪟 Windows" if SYSTEM == "Windows" else "🐧 Linux"
        self.lbl_version = tk.Label(self.topbar,
                                     text=f"{os_label}  v{VERSION}",
                                     font=FONT_SMALL)
        self.lbl_version.pack(side=tk.RIGHT, padx=(0, 8))

        # ── Statuszeile ───────────────────────────────────────────────
        self.statusbar = tk.Frame(self.content, pady=6, padx=14)
        self.statusbar.pack(fill=tk.X)

        self.status_label = tk.Label(self.statusbar,
                                      text=T("status_ready"),
                                      font=FONT_SMALL)
        self.status_label.pack(side=tk.LEFT)

        self.lbl_dupe_count = tk.Label(self.statusbar, text="",
                                        font=FONT_SMALL)
        self.lbl_dupe_count.pack(side=tk.LEFT, padx=(12, 0))

        # Hash-Check + Dupe-Filter rechts
        self.btn_dupe_filter = tk.Button(
            self.statusbar, text=T("dupe_btn"),
            font=FONT_SMALL, relief="flat",
            padx=10, pady=3, cursor="hand2", bd=0,
            command=self._toggle_dupe_filter)
        self.btn_dupe_filter.pack(side=tk.RIGHT, padx=(4, 0))
        Tooltip(self.btn_dupe_filter, T("tt_dupe"))

        self.btn_hash = tk.Button(
            self.statusbar, text=T("btn_hash"),
            font=FONT_SMALL, relief="flat",
            padx=10, pady=3, cursor="hand2", bd=0,
            command=self._start_hash_check)
        self.btn_hash.pack(side=tk.RIGHT, padx=(4, 0))
        Tooltip(self.btn_hash, T("tt_hash"))

        # Min-MB Slider
        self.mb_frame = tk.Frame(self.statusbar)
        self.mb_frame.pack(side=tk.RIGHT, padx=(0, 14))
        self._mb_label_prefix = tk.Label(self.mb_frame, text=T("min_size"),
                                          font=FONT_SMALL, cursor="hand2")
        self._mb_label_prefix.pack(side=tk.LEFT)
        Tooltip(self._mb_label_prefix,
                T("tt_mb"))
        self.min_mb_var   = tk.IntVar(value=MIN_GROESSE_MB)
        self.min_mb_label = tk.Label(self.mb_frame,
                                      text=f"{MIN_GROESSE_MB} MB",
                                      font=FONT_SMALL, width=7)
        self.min_mb_label.pack(side=tk.LEFT)
        self.mb_slider = tk.Scale(
            self.mb_frame, from_=0, to=2000, orient=tk.HORIZONTAL,
            variable=self.min_mb_var, showvalue=False,
            highlightthickness=0, length=130, bd=0,
            command=self._on_mb_slider)
        self.mb_slider.pack(side=tk.LEFT)
        Tooltip(self.mb_slider,
                T("tt_mb"))

        # Trennlinie
        self.top_sep = tk.Frame(self.content, height=1)
        self.top_sep.pack(fill=tk.X)

        # ── Treeview ─────────────────────────────────────────────────
        self.tree_frame = tk.Frame(self.content)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)

        cols = (T("col_name"), T("col_size"), T("col_type"), T("col_date"), T("col_path"))
        self.liste = ttk.Treeview(self.tree_frame, columns=cols,
                                   show="headings", selectmode="extended")

        self.liste.tag_configure("kopie",         foreground=ACCENT["kopie"])
        self.liste.tag_configure("version",       foreground=ACCENT["version"])
        self.liste.tag_configure("installer",     foreground=ACCENT["installer"])
        self.liste.tag_configure("crossplatform", foreground=ACCENT["crossplatform"])
        self.liste.tag_configure("duplikat",
                                  foreground=THEMES[0]["dupe_fg"],
                                  background=THEMES[0]["dupe_bg"])
        self.liste.tag_configure("hash_duplikat",
                                  foreground=THEMES[0]["hash_dupe_fg"],
                                  background=THEMES[0]["hash_dupe_bg"])

        widths = {T("col_name"): 300, T("col_size"): 100, T("col_type"): 190, T("col_date"): 110, T("col_path"): 700}
        for c in cols:
            self.liste.heading(c, text=c,
                                command=lambda _c=c: self.sort_column(_c, False))
            self.liste.column(c, width=widths[c], minwidth=60,
                               stretch=(c == "Pfad"))

        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical",
                             command=self.liste.yview)
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal",
                             command=self.liste.xview)
        self.liste.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.liste.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree_frame.rowconfigure(0, weight=1)
        self.tree_frame.columnconfigure(0, weight=1)

        # Kontextmenü
        self.ctx_menu = tk.Menu(self.root, tearoff=0)
        self.ctx_menu.add_command(label=T("ctx_open"),
                                   command=self._ctx_open_folder)
        self.ctx_menu.add_command(label=T("ctx_copy"),
                                   command=self._ctx_copy_path)
        self.ctx_menu.add_separator()
        self.ctx_menu.add_command(label=T("ctx_remove"),
                                   command=self._ctx_remove)
        self.ctx_menu.add_command(label=T("ctx_undo"),
                                   command=self._ctx_undo_remove)

        self.liste.bind("<Double-1>", self._open_folder_event)
        self.liste.bind("<Button-3>", self._show_context_menu)

        # Widget-Gruppen für Theme
        self._bg_widgets = [self.root, self.main_frame, self.sidebar,
                             self.content, self.topbar, self.chip_frame,
                             self.statusbar, self.mb_frame, self.tree_frame,
                             self.theme_frame, self.such_frame]
        self._fg_labels  = [self.lbl_version, self.min_mb_label,
                             self.status_label, self.lbl_dupe_count]


    # ------------------------------------------------------------------
    # Info-Dialog
    # ------------------------------------------------------------------
    def _show_info(self):
        import webbrowser
        t    = self._t
        win  = tk.Toplevel(self.root)
        win.title(T("info_title"))
        win.resizable(False, False)
        win.configure(bg=t["bg"])

        # Fenster zentrieren
        win.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width()  // 2 - 280
        y = self.root.winfo_y() + self.root.winfo_height() // 2 - 150
        win.geometry(f"560x390+{x}+{y}")

        # Icon anzeigen
        if PILLOW_OK:
            try:
                img_data = base64.b64decode(ICON_B64)
                img = Image.open(io.BytesIO(img_data))
                photo = ImageTk.PhotoImage(img)
                lbl_icon = tk.Label(win, image=photo, bg=t["bg"])
                lbl_icon.image = photo  # Referenz halten
                lbl_icon.pack(pady=(18, 4))
            except Exception:
                tk.Label(win, text="🔍", font=(FONT_BOLD[0], 32),
                         bg=t["bg"], fg=t["blue"]).pack(pady=(18, 4))
        else:
            tk.Label(win, text="🔍", font=(FONT_BOLD[0], 32),
                     bg=t["bg"], fg=t["blue"]).pack(pady=(18, 4))

        tk.Label(win, text="DupeHunter",
                 font=(*FONT_BOLD[:2], "bold"), bg=t["bg"],
                 fg=t["fg"]).pack(pady=(0, 2))

        tk.Label(win, text=f"Version {VERSION}",
                 font=FONT_DEFAULT, bg=t["bg"],
                 fg=t["textgray"]).pack()

        tk.Frame(win, bg=t["gray"], height=1).pack(
            fill=tk.X, padx=30, pady=14)

        desc = T("info_desc")
        tk.Label(win, text=desc, font=FONT_DEFAULT,
                 bg=t["bg"], fg=t["fg"],
                 justify=tk.CENTER).pack(pady=(0, 14))

        tk.Frame(win, bg=t["gray"], height=1).pack(
            fill=tk.X, padx=30, pady=(0, 10))

        github_url = "https://github.com/mantronikhro-tech/DupeHunter"

        tk.Label(win, text=T("info_github"),
                 font=FONT_SMALL, bg=t["bg"],
                 fg=t["textgray"]).pack()

        lbl_link = tk.Label(win,
                             text=github_url,
                             font=FONT_SMALL, bg=t["bg"],
                             fg=t["blue"], cursor="hand2")
        lbl_link.pack()
        lbl_link.bind("<Button-1>",
                       lambda e: webbrowser.open(github_url))

        tk.Button(win, text=T("btn_close"),
                  font=FONT_DEFAULT, relief="flat",
                  bg=t["blue"], fg="white",
                  padx=20, pady=6, cursor="hand2",
                  activebackground=t["blue"], activeforeground="white",
                  command=win.destroy).pack(pady=(16, 0))
    # ------------------------------------------------------------------
    # Hash-Check
    # ------------------------------------------------------------------
    def _start_hash_check(self):
        if not self.alle_fundstuecke:
            messagebox.showinfo(T("dlg_hash_title"), T("dlg_hash_noscan"))
            return
        if self._hash_laeuft or self.scan_aktiv:
            return

        self._hash_laeuft = True
        self._hash_dupe_pfade.clear()
        self.btn_hash.config(state=tk.DISABLED, text=T("btn_hashing"))

        def run():
            def status_cb(text):
                self.root.after(0, self.status_label.config,
                                 {"text": text, "fg": self._t["blue"]})

            ergebnis = berechne_hash_duplikate(self.alle_fundstuecke, status_cb)
            # Alle Pfade, die echte Duplikate sind, sammeln
            for pfade in ergebnis.values():
                for p in pfade:
                    self._hash_dupe_pfade.add(p)

            self.root.after(0, self._finish_hash_check, len(ergebnis))

        threading.Thread(target=run, daemon=True).start()

    def _finish_hash_check(self, dupe_gruppen: int):
        self._hash_laeuft = False
        self.btn_hash.config(state=tk.NORMAL, text=T("btn_hash"))
        self._reapply_dupe_tags()

        if dupe_gruppen == 0:
            self.status_label.config(
                text=T("status_hash_done_none"),
                fg=self._t["green"])
            self.lbl_dupe_count.config(text=T("dupe_none"),
                                        fg=self._t["green"])
        else:
            anzahl = len(self._hash_dupe_pfade)
            self.status_label.config(
                text=T("status_hash_done", groups=dupe_gruppen, count=anzahl),
                fg=self._t["hash_dupe_fg"])
            self.lbl_dupe_count.config(
                text=T("dupe_count", groups=dupe_gruppen, count=anzahl),
                fg=self._t["hash_dupe_fg"])
            # Automatisch nur Hash-Duplikate anzeigen
            self._nur_dupes.set(True)
            self._refresh_dupe_btn()
            self.filter_tabelle()

    # ------------------------------------------------------------------
    # Duplikat-Filter Toggle
    # ------------------------------------------------------------------
    def _toggle_dupe_filter(self):
        self._nur_dupes.set(not self._nur_dupes.get())
        self._refresh_dupe_btn()
        self.filter_tabelle()

    def _refresh_dupe_btn(self):
        t = self._t
        if self._nur_dupes.get():
            self.btn_dupe_filter.config(
                bg=t["dupe_fg"], fg="white",
                activebackground=t["dupe_fg"], activeforeground="white")
        else:
            self.btn_dupe_filter.config(
                bg=t["btn_folder"], fg=t["btn_folder_fg"],
                activebackground=t["btn_folder"],
                activeforeground=t["btn_folder_fg"])

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------
    def _on_close(self):
        """Fenstergröße/-position und Sprache speichern."""
        try:
            geo = self.root.winfo_geometry()
            config_speichern(self._theme_idx.get(), geo, _current_lang)
        except Exception:
            pass
        self.root.destroy()

    def _toggle_language(self):
        """Wechselt zur nächsten Sprache in LANG_ORDER."""
        idx  = LANG_ORDER.index(_current_lang)
        next_lang = LANG_ORDER[(idx + 1) % len(LANG_ORDER)]
        set_language(next_lang)
        config_speichern(self._theme_idx.get(),
                         self.root.winfo_geometry(), next_lang)
        self._rebuild_ui_texts()

    def _rebuild_ui_texts(self):
        """Aktualisiert alle UI-Texte nach einem Sprachwechsel."""
        # Sidebar Tooltips neu setzen
        for tip in getattr(self, "_all_tooltips", []):
            tip.destroy_if_exists()

        # Buttons
        self.btn_lang.config(text=T("lang_label"))
        self.btn_dupe_filter.config(text=T("dupe_btn"))
        self.btn_hash.config(text=T("btn_hash"))
        self._mb_label_prefix.config(text=T("min_size"))
        self.status_label.config(text=T("status_ready"))

        # Chips neu aufbauen
        for btn, _, _ in self._chip_buttons:
            btn.destroy()
        self._chip_buttons.clear()

        new_chip_values = [
            (T("chip_all_lbl"), "Alle",              T("chip_all")),
            ("🔀",  T("type_cross"),                 T("chip_cross")),
            ("📦",  T("type_installer"),             T("chip_installer")),
            ("🎮",  T("type_game"),                  T("chip_game")),
            ("⚙️", T("type_program"),               T("chip_program")),
            ("📄",  T("type_document"),              T("chip_document")),
            ("❓",  T("type_unknown"),               T("chip_unknown")),
        ]
        self._chip_values = new_chip_values
        t = self._t
        for label, value, tip in new_chip_values:
            btn = tk.Button(
                self.chip_frame, text=label,
                font=FONT_SMALL, relief="flat",
                padx=10, pady=4, cursor="hand2", bd=0,
                command=lambda v=value: self._set_chip(v))
            btn.pack(side=tk.LEFT, padx=2)
            Tooltip(btn, tip)
            self._chip_buttons.append((btn, value, tip))

        # Kontextmenü
        self.ctx_menu.entryconfig(0, label=T("ctx_open"))
        self.ctx_menu.entryconfig(1, label=T("ctx_copy"))
        self.ctx_menu.entryconfig(3, label=T("ctx_remove"))
        self.ctx_menu.entryconfig(4, label=T("ctx_undo"))

        # Treeview-Spalten umbenennen
        col_map = {
            0: T("col_name"), 1: T("col_size"), 2: T("col_type"),
            3: T("col_date"), 4: T("col_path")
        }
        for i, col in enumerate(self.liste["columns"]):
            self.liste.heading(col, text=col_map[i])

        # Theme neu anwenden um alle Farben zu refreshen
        self._apply_theme(self._theme_idx.get())

        # Tabelle mit neuen Typ-Strings neu aufbauen
        if self.alle_fundstuecke:
            self.filter_tabelle()

    def _set_theme(self, idx: int):
        self._theme_idx.set(idx)
        self._apply_theme(idx)
        config_speichern(idx, self.root.winfo_geometry(), _current_lang)

    def _apply_theme(self, idx: int):
        t       = THEMES[idx]
        self._t = t
        self._refresh_styles(t)

        for w in self._bg_widgets:
            w.config(bg=t["bg"])
        for w in self._fg_labels:
            w.config(bg=t["bg"], fg=t["textgray"])

        self.status_label.config(fg=t["textgray"])
        self.sidebar_sep.config(bg=t["gray"])
        self.top_sep.config(bg=t["gray"])
        self.such_frame.config(bg=t["entry_bg"],
                                highlightbackground=t["entry_border"],
                                highlightthickness=1)
        self._such_icon.config(bg=t["entry_bg"], fg=t["textgray"])

        # Sidebar-Buttons: Icon-Stil
        for btn in [self.btn_scan, self.btn_folder, self.btn_export,
                    self.btn_pause, self.btn_stop, self.btn_info]:
            btn.config(bg=t["bg"], fg=t["fg"],
                       activebackground=t["btn_folder"],
                       activeforeground=t["fg"])
        self.btn_scan.config(fg=t["blue"], activeforeground=t["blue"])

        # Trennlinie in Sidebar (Frame ohne config bg → finden via children)
        for w in self.sidebar.winfo_children():
            if isinstance(w, tk.Frame):
                w.config(bg=t["gray"])

        # Such-Entry
        self.such_entry.config(bg=t["entry_bg"], fg=t["fg"],
                                insertbackground=t["fg"])

        # Chips
        for btn, value, _ in self._chip_buttons:
            active = (self.typ_var.get() == value)
            if active:
                btn.config(bg=t["blue"], fg="white",
                           activebackground=t["blue"])
            else:
                btn.config(bg=t["btn_folder"], fg=t["btn_folder_fg"],
                           activebackground=t["btn_folder"])

        # Min-MB
        self._mb_label_prefix.config(bg=t["bg"], fg=t["textgray"])
        self.mb_slider.config(bg=t["bg"], troughcolor=t["slider_trough"],
                               fg=t["fg"])

        # Hash + Dupe-Filter
        self.btn_hash.config(bg=t["btn_folder"], fg=t["btn_folder_fg"],
                              activebackground=t["btn_folder"])

        # Stop/Pause state-abhängig
        stop_state  = str(self.btn_stop["state"])
        pause_state = str(self.btn_pause["state"])
        self.btn_stop.config(
            fg=t["red"]      if stop_state  != "disabled" else t["textgray"],
            activeforeground=t["red"])
        self.btn_pause.config(
            fg=t["darkgray"] if pause_state != "disabled" else t["textgray"],
            activeforeground=t["darkgray"])

        # Treeview
        self.liste.tag_configure("odd",           background=t["tree_odd"])
        self.liste.tag_configure("even",          background=t["tree_even"])
        self.liste.tag_configure("duplikat",      foreground=t["dupe_fg"],
                                                   background=t["dupe_bg"])
        self.liste.tag_configure("hash_duplikat", foreground=t["hash_dupe_fg"],
                                                   background=t["hash_dupe_bg"])

        self.ctx_menu.config(bg=t["tree_bg"], fg=t["fg"],
                              activebackground=t["blue"], activeforeground="white")

        # Theme-Dots: aktiver = blau, andere = grau
        for i, dot in enumerate(self._theme_dots):
            dot.config(bg=t["bg"],
                       fg=t["blue"] if i == idx else t["textgray"])

        self._refresh_dupe_btn()


    # ------------------------------------------------------------------
    # Hilfsmethoden
    # ------------------------------------------------------------------
    @staticmethod
    def _btn(parent, text, cmd, bg, fg, state=tk.NORMAL, width=None):
        kw = dict(text=text, command=cmd,
                  bg=bg or "#007AFF", fg=fg or "white",
                  font=FONT_BOLD, relief="flat",
                  padx=16, pady=5, cursor="hand2", state=state,
                  activebackground=bg or "#007AFF",
                  activeforeground=fg or "white")
        if width:
            kw["width"] = width
        return tk.Button(parent, **kw)

    def _on_mb_slider(self, _=None):
        self.min_mb_label.config(text=f"{self.min_mb_var.get()} MB")
        self.filter_tabelle()

    def _set_scan_buttons(self, scanning: bool):
        t = self._t
        if scanning:
            self.btn_scan.config(state=tk.DISABLED,  fg=t["textgray"])
            self.btn_stop.config(state=tk.NORMAL,    fg=t["red"])
            self.btn_pause.config(state=tk.NORMAL,   fg=t["darkgray"])
            self.btn_hash.config(state=tk.DISABLED,  fg=t["textgray"])
        else:
            self.btn_scan.config(state=tk.NORMAL,    fg=t["blue"])
            self.btn_stop.config(state=tk.DISABLED,  fg=t["textgray"])
            self.btn_pause.config(state=tk.DISABLED, fg=t["textgray"],
                                   text="⏸")
            self.btn_hash.config(state=tk.NORMAL,    fg=t["btn_folder_fg"])

    # ------------------------------------------------------------------
    # Klassifizierung
    # ------------------------------------------------------------------
    def _get_name_dupes(self) -> Set[str]:
        """Gibt gecachte Name-Duplikate zurück – neu berechnet nur wenn nötig."""
        if self._cache_dirty:
            self._name_dupes_cache = berechne_name_duplikate(self.alle_fundstuecke)
            self._cache_dirty = False
        return self._name_dupes_cache

    def _invalidate_cache(self):
        """Cache als veraltet markieren – aufrufen wenn neue Einträge kommen."""
        self._cache_dirty = True

    def klassifiziere_datei(self, pfad: str, dateiname: str,
                             groesse_mb: int) -> str:
        ext        = get_file_ext(dateiname)
        name_lower = dateiname.lower()
        pfad_lower = pfad.lower()

        # 1. Cross-Plattform (Extension passt nicht zum aktuellen OS)
        if ext in FOREIGN_EXT:
            base_typ = T("type_cross")

        # 2. PDF-Dokument
        elif ext == ".pdf":
            base_typ = T("type_document")

        # 3. Native Installer-Extension (.msi, .deb, .pkg ...)
        elif ext in INSTALLER_EXT:
            base_typ = T("type_installer")

        # 3. ZIP/RAR/ISO mit Installer-Muster im Dateinamen → Installer
        elif (ext in {".zip", ".rar", ".iso", ".tar.gz"} and
              any(m in name_lower for m in INSTALLER_MUSTER)):
            base_typ = T("type_installer")

        # 4. Spiele-Keyword im Pfad
        elif any(k in pfad_lower for k in SPIELE_KEYWORDS):
            base_typ = T("type_game")

        # 5. Programm-Keyword im Pfad
        elif any(k in pfad_lower for k in PROGRAMM_KEYWORDS):
            base_typ = T("type_program")

        # 6. EXE ohne klaren Kontext → "Programm" ist wahrscheinlicher
        #    als "Unbekannt" wenn der Name nicht nach Installer klingt
        elif ext == ".exe":
            base_typ = T("type_program")

        else:
            base_typ = T("type_unknown")

        # O(1) Dict-Lookup: gleicher Name schon gesehen?
        if dateiname in self._gesehene_namen:
            alt_groesse = self._gesehene_namen[dateiname]
            suffix = (T("type_copy") if groesse_mb == alt_groesse
                      else T("type_version"))
            return base_typ + suffix
        return base_typ

    # ------------------------------------------------------------------
    # Tag-Logik  (Hash-Duplikat hat höchste Priorität)
    # ------------------------------------------------------------------
    def _get_accent_tags(self, item: Tuple, name_dupes: Set) -> List[str]:
        name, _, typ, _, ordner = item
        voller_pfad = os.path.join(ordner, name)

        # 1. Hash-Duplikat → Rot (höchste Priorität)
        if voller_pfad in self._hash_dupe_pfade:
            return ["hash_duplikat"]
        # 2. Name-Duplikat → Orange
        if name in name_dupes:
            return ["duplikat"]
        # 3. Sonstige Akzente
        if   T("type_copy").strip()    in typ: return ["kopie"]
        elif T("type_version").strip() in typ: return ["version"]
        elif typ.startswith("📦"):     return ["installer"]  # Emoji stabil
        elif typ.startswith("🔀"):     return ["crossplatform"]  # Emoji stabil
        return []

    def _set_chip(self, value: str):
        self.typ_var.set(value)
        self._apply_theme(self._theme_idx.get())  # Chips neu einfärben
        self.filter_tabelle()


    # ------------------------------------------------------------------
    # Scan  (os.scandir() – schneller als os.walk())
    # ------------------------------------------------------------------
    def _scan_dir(self, pfad: str):
        """
        Rekursiver Scan mit os.scandir() – deutlich schneller als os.walk()
        da DirEntry-Objekte Metadaten (stat) ohne extra syscall liefern.
        """
        if not self.scan_aktiv:
            return
        with self.pause_condition:
            while self.pausiert:
                self.pause_condition.wait()

        try:
            entries = list(os.scandir(pfad))
        except PermissionError:
            return

        ordner_name = os.path.basename(pfad) or pfad
        self.root.after(0, self.status_label.config,
                         {"text": T("status_scanning", folder=ordner_name),
                          "fg": self._t["blue"]})

        subdirs = []
        for entry in entries:
            if not self.scan_aktiv:
                return

            if entry.is_dir(follow_symlinks=False):
                # Ignorier-Filter: Name des Ordners UND ob ein Ignore-Wort
                # irgendwo im vollen Pfad vorkommt (wichtig für externe
                # Laufwerke, z.B. /media/user/disk/Windows/System32)
                pfad_lower = entry.path.lower().replace("\\", "/")
                if (entry.name.lower() not in ORDNER_IGNORE and
                        not any(f"/{w}" in pfad_lower for w in ORDNER_IGNORE)):
                    subdirs.append(entry.path)
                continue

            if not entry.is_file(follow_symlinks=False):
                continue

            ext = get_file_ext(entry.name)
            if ext not in SCAN_EXT_UNIVERSAL and ext not in COMPOUND_EXT:
                continue
            if any(sw in entry.name.lower() for sw in STOP_WORDS):
                continue

            try:
                # DirEntry.stat() ist gecacht – kein extra syscall!
                st         = entry.stat()
                groesse_mb = int(st.st_size / (1024 * 1024))
                # PDFs: eigener niedrigerer Schwellenwert (1 MB)
                # Alle anderen: normaler MB-Slider
                schwelle = PDF_MIN_MB if ext == ".pdf" else self.min_mb_var.get()
                if groesse_mb < schwelle:
                    continue
                datum   = datetime.fromtimestamp(st.st_mtime).strftime("%d.%m.%Y")
                typ     = self.klassifiziere_datei(pfad, entry.name, groesse_mb)
                eintrag = (entry.name, groesse_mb, typ, datum, pfad)
                self._gesehene_namen[entry.name] = groesse_mb
                self._invalidate_cache()
                self.alle_fundstuecke.append(eintrag)
                self._pending_batch.append(eintrag)
                if len(self._pending_batch) >= BATCH_SIZE:
                    self._flush_batch()
            except OSError:
                continue

        # Rekursion in Unterordner
        for subdir in subdirs:
            if not self.scan_aktiv:
                return
            self._scan_dir(subdir)

    def _flush_batch(self):
        if self._pending_batch:
            snapshot = list(self._pending_batch)
            self._pending_batch.clear()
            self.root.after(0, lambda: self._append_rows(snapshot))

    def _append_rows(self, rows: List[Tuple]):
        name_dupes = self._get_name_dupes()
        for item in rows:
            if self._nur_dupes.get():
                voller_pfad = os.path.join(item[4], item[0])
                ist_dupe = (item[0] in name_dupes or
                            voller_pfad in self._hash_dupe_pfade)
                if not ist_dupe:
                    continue
            idx   = len(self.liste.get_children())
            row_t = "even" if idx % 2 == 0 else "odd"
            extra = self._get_accent_tags(item, name_dupes)
            self.liste.insert("", tk.END,
                               values=(item[0], f"{item[1]} MB",
                                       item[2], item[3], item[4]),
                               tags=(row_t, *extra))

    def start_scan(self, modus: str = "auto"):
        if not self._scan_lock.acquire(blocking=False):
            return   # bereits ein Scan aktiv – Doppelklick ignorieren
        if self.scan_aktiv:
            self._scan_lock.release()
            return
        selected_path = None
        if modus == "manual":
            selected_path = filedialog.askdirectory()
            if not selected_path:
                return

        self.scan_aktiv = True
        self.pausiert   = False
        self.alle_fundstuecke.clear()
        self._pending_batch.clear()
        self._hash_dupe_pfade.clear()
        self._gesehene_namen.clear()
        self._undo_stack.clear()
        self._invalidate_cache()
        self.liste.delete(*self.liste.get_children())
        self.lbl_dupe_count.config(text="")
        self._sort_col = None
        self._sort_rev = False
        self.root.config(cursor="watch")
        self._set_scan_buttons(True)

        def run():
            try:
                if modus == "auto":
                    for p in get_start_paths():
                        if not self.scan_aktiv:
                            break
                        self._scan_dir(p)
                else:
                    self._scan_dir(selected_path)
            except Exception as e:
                print(f"Scan-Fehler: {e}")
            finally:
                self._scan_lock.release()
            self._flush_batch()
            self.root.after(0, self._finish_scan)

        threading.Thread(target=run, daemon=True).start()

    def toggle_pause(self):
        t = self._t
        with self.pause_condition:
            self.pausiert = not self.pausiert
            if self.pausiert:
                self.btn_pause.config(text="▶", fg=t["yellow"])
                self.status_label.config(text=T("status_paused"), fg=t["yellow"])
                self.root.config(cursor="arrow")
            else:
                self.btn_pause.config(text="⏸", fg=t["darkgray"])
                self.root.config(cursor="watch")
                self.pause_condition.notify_all()

    def stop_scan(self):
        self.scan_aktiv = False
        self.root.config(cursor="arrow")
        with self.pause_condition:
            self.pausiert = False
            self.pause_condition.notify_all()
        self.status_label.config(text=T("status_stopped"), fg=self._t["red"])

    def _finish_scan(self):
        self.scan_aktiv = False
        self.root.config(cursor="arrow")
        self._set_scan_buttons(False)
        self._reapply_dupe_tags()

        if not self.alle_fundstuecke:
            min_mb = self.min_mb_var.get()
            if min_mb > 10:
                hinweis = T("status_no_files_mb", mb=min_mb)
            else:
                hinweis = T("status_no_files")
            self.status_label.config(text=hinweis, fg=self._t["textgray"])
            return

        name_dupes  = self._get_name_dupes()
        gesamt_gb   = sum(i[1] for i in self.alle_fundstuecke) / 1024
        installer_n = sum(1 for i in self.alle_fundstuecke if i[2].startswith("📦"))
        crossplat_n = sum(1 for i in self.alle_fundstuecke if i[2].startswith("🔀"))
        pdf_n       = sum(1 for i in self.alle_fundstuecke if i[2].startswith("📄"))
        dupe_n      = len(name_dupes)

        info = (T("status_done", count=len(self.alle_fundstuecke), gb=gesamt_gb)
                + (f" | 📦 {installer_n}" if installer_n else "")
                + (f" | 🔀 {crossplat_n}" if crossplat_n else "")
                + (f" | 📄 {pdf_n}" if pdf_n else ""))
        self.status_label.config(text=info, fg=self._t["green"])

        if dupe_n:
            self.lbl_dupe_count.config(
                text=f"⚠️ {dupe_n} Duplikat-Namen  →  🔬 Hash-Check empfohlen",
                fg=self._t["dupe_fg"])
        else:
            self.lbl_dupe_count.config(text="✅ Keine Duplikate",
                                        fg=self._t["green"])

    def _reapply_dupe_tags(self):
        self._invalidate_cache()
        name_dupes = self._get_name_dupes()
        for i, item_id in enumerate(self.liste.get_children()):
            vals    = self.liste.item(item_id, "values")
            row_tag = "even" if i % 2 == 0 else "odd"
            passend = next((f for f in self.alle_fundstuecke
                            if f[0] == vals[0] and f[4] == vals[4]), None)
            extra   = self._get_accent_tags(passend, name_dupes) if passend else []
            self.liste.item(item_id, tags=(row_tag, *extra))

    # ------------------------------------------------------------------
    # Tabelle
    # ------------------------------------------------------------------
    def _rebuild_tabelle(self, daten: List[Tuple]):
        self.liste.delete(*self.liste.get_children())
        name_dupes = self._get_name_dupes()
        for i, item in enumerate(daten):
            row_t = "even" if i % 2 == 0 else "odd"
            extra = self._get_accent_tags(item, name_dupes)
            self.liste.insert("", tk.END,
                               values=(item[0], f"{item[1]} MB",
                                       item[2], item[3], item[4]),
                               tags=(row_t, *extra))
        # Sortierung nach Rebuild wiederherstellen
        self._apply_sort()

    def filter_tabelle(self, _event=None):
        begriff    = self.such_entry.get().lower()
        typ_filter = self.typ_var.get()
        min_mb     = self.min_mb_var.get()
        nur_dupes  = self._nur_dupes.get()
        name_dupes = self._get_name_dupes()

        # Nach Hash-Check: nur echte Hash-Duplikate zeigen
        # Ohne Hash-Check: alle Name-Duplikate zeigen
        nur_hash_dupes = nur_dupes and bool(self._hash_dupe_pfade)

        gefiltert = []
        for f in self.alle_fundstuecke:
            if min_mb and f[1] < min_mb:
                continue
            if typ_filter != "Alle" and not f[2].startswith(typ_filter):
                continue
            if begriff and not any(
                    begriff in str(f[col]).lower() for col in (0, 2, 4)):
                continue
            if nur_hash_dupes:
                vp = os.path.join(f[4], f[0])
                if vp not in self._hash_dupe_pfade:
                    continue
            elif nur_dupes:
                vp = os.path.join(f[4], f[0])
                if f[0] not in name_dupes and vp not in self._hash_dupe_pfade:
                    continue
            gefiltert.append(f)
        self._rebuild_tabelle(gefiltert)

    def sort_column(self, col: str, reverse: bool):
        # Sortierung merken – wird nach filter_tabelle neu angewendet
        self._sort_col = col
        self._sort_rev = reverse
        self._apply_sort()
        self.liste.heading(col,
                            command=lambda: self.sort_column(col, not reverse))

    def _apply_sort(self):
        """Wendet die gespeicherte Sortierung auf den aktuellen Treeview an."""
        col     = self._sort_col
        reverse = self._sort_rev
        if not col:
            return
        rows = [(self.liste.set(k, col), k)
                for k in self.liste.get_children("")]
        if col == "Größe":
            rows.sort(key=lambda t: int(t[0].split()[0]), reverse=reverse)
        elif col == "Datum":
            rows.sort(key=lambda t: datetime.strptime(t[0], "%d.%m.%Y"),
                      reverse=reverse)
        else:
            rows.sort(reverse=reverse)
        for index, (_, k) in enumerate(rows):
            self.liste.move(k, "", index)
        for i, item in enumerate(self.liste.get_children("")):
            cur_tags = list(self.liste.item(item, "tags"))
            cur_tags = [x for x in cur_tags if x not in ("odd", "even")]
            cur_tags.insert(0, "even" if i % 2 == 0 else "odd")
            self.liste.item(item, tags=cur_tags)

    def export_liste(self):
        sichtbar = self.liste.get_children()
        if not sichtbar:
            messagebox.showinfo(T("dlg_export_title"), T("dlg_export_empty"))
            return
        # Dateiname zeigt aktiven Filter
        typ_filter = self.typ_var.get()
        filter_tag = "" if typ_filter == "Alle" else f"_{typ_filter.split()[0]}"
        datei_pfad = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV-Datei", "*.csv")],
            initialfile=f"DupeHunter{filter_tag}_{datetime.now().strftime('%d_%m_%Y')}.csv")
        if not datei_pfad:
            return
        try:
            anzahl = len(sichtbar)
            with open(datei_pfad, "w", encoding="utf-8") as f:
                f.write(T("csv_header") + "\n")
                for item_id in sichtbar:   # nur was im Treeview sichtbar ist
                    werte = list(self.liste.item(item_id)["values"])
                    tags  = self.liste.item(item_id)["tags"]
                    werte.append(T("csv_hash_yes") if "hash_duplikat" in tags else "")
                    f.write(";".join(map(str, werte)) + "\n")
            messagebox.showinfo(T("dlg_export_title"),
                                T("dlg_export_ok", count=anzahl)
                                + (f"\n" + T("dlg_export_filter", filter=typ_filter)
                                   if typ_filter != T("chip_all_lbl") else ""))
        except Exception as e:
            messagebox.showerror(T("dlg_export_etitle"), T("dlg_export_err", error=e))

    # ------------------------------------------------------------------
    # Kontext-Menü & Doppelklick
    # ------------------------------------------------------------------
    def _show_context_menu(self, event):
        row = self.liste.identify_row(event.y)
        if row:
            self.liste.selection_set(row)
            self.ctx_menu.post(event.x_root, event.y_root)

    def _selected_pfad(self) -> Optional[str]:
        sel = self.liste.selection()
        if sel:
            return self.liste.item(sel[0], "values")[4]
        return None

    def _ctx_open_folder(self):
        pfad = self._selected_pfad()
        if not pfad or not os.path.exists(pfad):
            return
        try:
            if SYSTEM == "Windows":
                os.startfile(pfad)
            elif SYSTEM == "Darwin":
                subprocess.Popen(["open", pfad])
            else:
                # Linux: xdg-open bevorzugt, Fallback auf nautilus/dolphin
                for cmd in ["xdg-open", "nautilus", "dolphin", "thunar"]:
                    try:
                        subprocess.Popen([cmd, pfad])
                        break
                    except FileNotFoundError:
                        continue
        except Exception:
            pass

    def _ctx_copy_path(self):
        pfad = self._selected_pfad()
        if pfad:
            self.root.clipboard_clear()
            self.root.clipboard_append(pfad)
            self.status_label.config(text=f"📋 Pfad kopiert: {pfad}",
                                      fg=self._t["blue"])

    def _ctx_remove(self):
        entfernt = []
        for sel in self.liste.selection():
            name = self.liste.item(sel, "values")[0]
            self.liste.delete(sel)
            for f in self.alle_fundstuecke:
                if f[0] == name:
                    entfernt.append(f)
            self.alle_fundstuecke = [f for f in self.alle_fundstuecke
                                      if f[0] != name]
        if entfernt:
            self._undo_stack.extend(entfernt)
            self.status_label.config(
                text=T("status_removed", count=len(entfernt)),
                fg=self._t["textgray"])
        self._gesehene_namen = {n: g for n, g in self._gesehene_namen.items()
                                 if any(f[0] == n for f in self.alle_fundstuecke)}
        self._invalidate_cache()

    def _ctx_undo_remove(self):
        if not self._undo_stack:
            self.status_label.config(text=T("status_undo_empty"),
                                      fg=self._t["textgray"])
            return
        # Letzten Eintrag wiederherstellen
        eintrag = self._undo_stack.pop()
        self.alle_fundstuecke.append(eintrag)
        self._gesehene_namen[eintrag[0]] = eintrag[1]
        self._invalidate_cache()
        self.filter_tabelle()
        self.status_label.config(
            text=T("status_restored", name=eintrag[0]),
            fg=self._t["green"])

    def _open_folder_event(self, event):
        self._ctx_open_folder()


# ---------------------------------------------------------------------------
# Einstiegspunkt
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app  = DupeHunterApp(root)
    root.after(500, lambda: check_pillow_and_notify(root))
    root.mainloop()
