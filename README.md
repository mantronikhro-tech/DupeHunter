<p align="center">
  <img src="dupehunter.png" width="200" alt="DupeHunter Logo">
</p>

# 🎯 DupeHunter

> Scannt Datenträger nach Installationsdateien und Dokumenten, erkennt Duplikate per Name und Hash-Prüfung – für Windows & Linux.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)
![Offline](https://img.shields.io/badge/100%25-Offline-brightgreen)
![No Tracking](https://img.shields.io/badge/Tracking-Keine-brightgreen)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-6.0-orange)

---

## 🔒 100% Offline – Keine Internetverbindung, niemals

> **DupeHunter baut zu keinem Zeitpunkt eine Netzwerkverbindung auf.**

Das ist kein Zufall – das ist eine bewusste Designentscheidung:

- ✅ **Kein Tracking** – keine Nutzungsdaten, keine Telemetrie, keine Statistiken
- ✅ **Kein "Nach-Hause-Telefonieren"** – das Tool kommuniziert mit niemandem
- ✅ **Keine automatischen Updates** – kein Code wird jemals automatisch heruntergeladen oder ausgeführt
- ✅ **Firewall-freundlich** – benötigt keinerlei Ausnahmeregeln
- ✅ **Geeignet für sensible Umgebungen** – Firmenrechner, Offline-Systeme, abgesicherte Netzwerke
- ✅ **Vollständig Open Source** – jede Zeile Code ist einsehbar und prüfbar

> Neue Versionen werden ausschließlich manuell über GitHub bezogen.
> Der **ℹ️ Info-Dialog** im Tool enthält den direkten Link.

---


## ✨ Features

### Scan & Erkennung
- **System-Scan** – scannt automatisch alle relevanten Laufwerke und Verzeichnisse
- **Ordner-Scan** – manuell einen bestimmten Ordner auswählen und scannen
- **Intelligente Dateityp-Erkennung** – klassifiziert gefundene Dateien automatisch nach Pfad, Dateiname und Extension:
  - 🔀 Cross-Plattform (z.B. `.exe` auf Linux, `.deb` auf Windows)
  - 📦 Installer (native Pakete sowie ZIPs/RARs/ISOs mit Installer-Muster im Namen)
  - 🎮 Spiel (Steam, Epic Games, GOG, Battle.net, Rockstar, Bethesda u.a.)
  - ⚙️ Programm (AppData, Program Files, JetBrains, Python, Java u.a.)
  - 📄 Dokument (PDF-Dateien ab 1 MB)
  - ❓ Unbekannt
- **Kopie & Version-Erkennung** – gleicher Dateiname in verschiedenen Ordnern wird als `📂 (Kopie)` oder `🔄 (Version)` markiert

### Duplikat-Erkennung
- **⚠️ Name-Duplikate** – findet Dateien mit gleichem Namen in verschiedenen Ordnern (schnell, orange markiert)
- **🔬 Schnell-Hash** – vergleicht Anfang + Ende jeder Datei per MD5 (inkl. Dateigröße) und findet sehr wahrscheinlich identische Dateien (rot markiert). Nach Abschluss wird die Ansicht automatisch auf die gefundenen Hash-Duplikate gefiltert
- **PDF-Duplikate** – `bericht.pdf` und `bericht(1).pdf` werden zuverlässig per Hash-Check als identisch erkannt

### Performance
- Optimiert für **500–800+ gefundene Dateien** ohne Ruckeln
- Iterativer Scan mit eigenem Stack – kein `RecursionError` bei tief verschachtelten Ordnerstrukturen (z.B. `node_modules`)
- `os.scandir()` statt `os.walk()` – gecachte Metadaten, weniger Systemaufrufe
- Gecachter Duplikat-Index – wird nur bei Änderungen neu berechnet
- O(1) Namens-Lookup statt linearer Suche bei der Klassifizierung
- Batch-Verarbeitung hält die UI während des Scans flüssig
- Thread-Lock verhindert doppelten Scan-Start bei schnellem Doppelklick

### Design & Bedienung
- **Modernes Sidebar-Layout** mit Icon-Buttons
- **🌍 Mehrsprachig** – Deutsch & Englisch, per Klick auf die Flagge wechselbar; weitere Sprachen durch eine einzige Datei erweiterbar
- **Tooltips** auf allen Buttons, Chips, Slider und Theme-Punkten
- **3 Themes** – ☀️ Light, 🌑 Dark, 🍎 macOS – per Klick auf ●●● wählbar
- **Einstellungen werden gespeichert** – Theme, Fenstergröße und -position bleiben nach Neustart erhalten (`~/.dupehunter_config.json`)
- **Typ-Filter als Chips** – schnelles Filtern per Klick (inkl. neuem 📄 Dokument-Chip)
- **Sortierung bleibt nach Filter erhalten** – nach Name sortiert, dann auf PDFs gefiltert: Sortierung bleibt
- **Freitextsuche** – nach Dateiname, Typ oder Pfad filtern
- **MB-Slider** – Mindestgröße der angezeigten Dateien einstellen (PDFs haben eigenen Schwellenwert von 1 MB)
- **Hinweis bei leerem Ergebnis** – wenn der Slider zu hoch steht und nichts gefunden wird, erscheint ein Tipp in der Statuszeile
- **CSV-Export** – exportiert immer genau was aktuell sichtbar ist; Dateiname enthält den aktiven Filter automatisch
- **Kontextmenü** – Ordner öffnen, Pfad kopieren, Eintrag entfernen
- **↩ Undo** – versehentlich entfernter Eintrag lässt sich per Rechtsklick wiederherstellen

---

## 🖥️ Systemvoraussetzungen

| | Minimum |
|---|---|
| Python | 3.8 oder neuer |
| Betriebssystem | Windows 10/11 oder Linux (z.B. Mint, Ubuntu) |
| Bibliotheken | `tkinter` (in Python enthalten) |

### Optionale Abhängigkeit

| Paket | Wozu | Installation |
|---|---|---|
| `Pillow` | App-Icon im Info-Dialog | `pip install pillow` |
| `ImageTk`| Systempaket für ImageTk | `sudo apt install python3-pil.imagetk`|

> Ohne Pillow läuft DupeHunter vollständig – nur das Icon im Info-Dialog wird nicht angezeigt.
> Beim ersten Start erscheint ein freundlicher Hinweis mit kopierbarem Installationsbefehl.

---

## 🚀 Installation & Start

```bash
# Repository klonen
git clone https://github.com/mantronikhro-tech/DupeHunter.git
cd DupeHunter

# Optional: Pillow installieren
pip install pillow

# Starten
python3 DupeHunter.py
```

Kein Setup, keine Installation, keine weiteren Abhängigkeiten – einfach starten.

---

## 🎮 Bedienung

### Sidebar-Icons

| Icon | Funktion |
|---|---|
| 🔍 | System-Scan starten |
| 📁 | Ordner manuell auswählen |
| 💾 | Sichtbare Ergebnisse als CSV exportieren |
| ⏸ | Scan pausieren / fortsetzen |
| ⏹ | Scan abbrechen |
| ℹ️ | Über DupeHunter |
| ● ● ● | Theme wechseln |

### Empfohlener Workflow

1. **🔍 System-Scan** klicken – DupeHunter durchsucht alle Laufwerke automatisch
2. Ergebnisse erscheinen laufend in der Tabelle; Statuszeile zeigt Zusammenfassung nach Abschluss
3. **Filterchips** nutzen um gezielt einen Typ anzuzeigen (z.B. nur 📄 Dokumente)
4. **⚠️ Nur Duplikate** aktivieren um verdächtige Dateien zu isolieren
5. **🔬 Hash-Check** starten – identische Dateien werden rot markiert und automatisch gefiltert angezeigt
6. **💾 Export** um die aktuell sichtbare Liste als CSV zu speichern

### Filterchips

| Chip | Bedeutung |
|---|---|
| Alle | Alle gefundenen Dateien |
| 🔀 | Cross-Plattform Dateien |
| 📦 | Native Installer & Installer-Archive |
| 🎮 | Spiele-Dateien |
| ⚙️ | Erkannte Programme |
| 📄 | PDF-Dokumente ab 1 MB |
| ❓ | Nicht klassifizierte Dateien |

### Kontextmenü (Rechtsklick auf Eintrag)

| Aktion | Beschreibung |
|---|---|
| 📂 Ordner öffnen | Öffnet den Ordner der markierten Datei im Explorer / Dateimanager |
| 📋 Pfad kopieren | Kopiert den vollständigen Pfad in die Zwischenablage |
| 🗑 Aus Liste entfernen | Entfernt den Eintrag aus der Ansicht (kein Löschen vom Datenträger) |
| ↩ Entfernen rückgängig | Stellt den zuletzt entfernten Eintrag wieder her |

---

## 🎨 Themes

| Theme | Beschreibung |
|---|---|
| ☀️ Light | Helles, modernes Layout |
| 🌑 Dark | Dunkles Layout für Augenschonung |
| 🍎 macOS | macOS-inspiriertes Design |

Theme, Fenstergröße und -position werden in `~/.dupehunter_config.json` gespeichert und beim nächsten Start automatisch wiederhergestellt.

---

## 🗂️ Ignorierte Verzeichnisse

DupeHunter überspringt automatisch System-, Cache- und temporäre Ordner um Fehlalarme und lange Pfadfehler zu vermeiden:

**Windows:** `Windows`, `System32`, `$Recycle.Bin`, `Recovery`, `WindowsApps`, `ProgramData`, `Packages`, `LocalCache`, `WinSxS`, `SoftwareDistribution`, `Temp`, `Driver` u.a.

**Linux:** `.Trash`, `x86`, `x64`, `Intel`, `GeForce`, `Temp`, `Download` u.a.

> Pfade über 250 Zeichen werden auf Windows automatisch übersprungen (Windows MAX_PATH Limit).

---

## 🔄 Updates

DupeHunter aktualisiert sich **bewusst nicht automatisch**.

Neue Versionen sind immer auf dieser GitHub-Seite verfügbar.
Der **ℹ️ Info-Button** im Tool enthält den direkten Link zu diesem Repository.

---

## 📄 Lizenz

MIT License – siehe [LICENSE](LICENSE)

---

## 👤 Autor

**Mario Schäffner**
GitHub: [@mantronikhro-tech](https://github.com/mantronikhro-tech)

---

*Gebaut mit Python & tkinter · 100% offline · Läuft auf Windows 10/11 und Linux ohne externe Abhängigkeiten.*
