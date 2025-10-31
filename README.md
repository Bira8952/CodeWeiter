# 🎮 Nintendo-Style Einsatzplanung

Schichtplanung (Work Scheduling) App im Nintendo-Design - Bidirektionale Google Sheets Integration

---

## ✨ Features

- **Live Google Sheets Integration**: Pool-Konfiguration wird ins Google Sheet geschrieben, Live-Vol Daten werden aus Google Sheets gelesen
- **3 Schichttypen**: FRÜH (blauer Gradient), SPÄT (oranger Gradient), Täti (lila Gradient)
- **Auto/Manuell-Toggle**: Schutz manueller Eingaben vor Auto-Import
- **Echtzeit-Synchronisation**: Mitarbeiter-Daten synchronisieren zwischen seite3.html und index.html
- **Responsive Design**: Funktioniert auf Desktop und Tablet

---

## 🚀 Installation & Start (Lokal)

### Voraussetzungen
- Python 3.x
- pip (Python Package Manager)

### 1. Projekt herunterladen
```bash
# ZIP von Replit herunterladen und entpacken
# ODER via Git:
git clone https://github.com/DEIN-USERNAME/DEIN-REPO.git
cd DEIN-REPO
```

### 2. Python-Pakete installieren
```bash
pip install flask flask-cors psycopg2-binary requests
```

### 3. Google Sheets IDs konfigurieren (Optional)

Erstelle eine `.env`-Datei:
```bash
LIVE_VOL_SHEET_ID=1EhhG5Da2kDpLMktcrSdn1DTMnr_XLEdJyNUI2ZwLuQ4
POOL_CONFIG_SHEET_ID=14e85oqQrUjywXjNasJz7azME0t18RJEEldgRwCRFiH4
MITARBEITER_SHEET_ID=15yfflPhE6Lqykm8aqacnZcrJj0x0Y1Yd
```

**⚠️ WICHTIG**: Diese Datei wird **NICHT** auf GitHub hochgeladen (durch `.gitignore` geschützt)

### 4. Server starten
```bash
python3 server.py
```

### 5. App öffnen
Öffne im Browser: **http://localhost:5000**

---

## 📁 Projektstruktur

```
.
├── server.py                  # Python Flask Backend
├── index.html                 # Hauptseite - Pool-Verwaltung
├── seite3.html               # Mitarbeiter-Verwaltung
├── test-import.html          # Test-Seite für Import
├── writeToGoogleSheets.js    # Google Sheets Integration
├── .gitignore                # Git-Schutz für Secrets
└── README.md                 # Diese Anleitung
```

---

## 🔧 Google Sheets Konfiguration

### Google Sheets müssen **öffentlich** sein (Lesezugriff)!

1. **Öffne dein Google Sheet**
2. Klicke oben rechts auf **"Teilen"**
3. Klicke auf **"Allgemeiner Zugriff ändern"**
4. Wähle: **"Jeder mit dem Link"** → **"Betrachter"**
5. Fertig! ✅

### Verwendete Google Sheets:

- **Live-Vol Sheet**: Echtzeit-Daten (alle 3 Sekunden)
- **Pool-Konfiguration**: NAME, START, DEADLINE, FAKTOR, RATE, ROTATION
- **Mitarbeiter-Sheet**: Schichtdaten FRÜH/SPÄT/Täti (alle 5 Sekunden)

---

## 🎨 Schichttypen

| Schicht | Farbe | Beschreibung |
|---------|-------|--------------|
| **FRÜH** | 🔵 Blauer Gradient | Frühschicht |
| **SPÄT** | 🟠 Oranger Gradient | Spätschicht |
| **Täti** | 🟣 Lila Gradient | Täti-Schicht (vorher "ROTATION") |

---

## 🔐 Sicherheit

- **Alle Google Sheets IDs** werden in Umgebungsvariablen gespeichert
- `.gitignore` schützt Secrets vor GitHub-Upload
- `/api/config/sheets` liefert IDs sicher vom Backend

---

## 🌐 Deployment (Replit)

### Bereits konfiguriert! Einfach auf Replit:
1. Projekt öffnen
2. "Run" drücken
3. Fertig! 🚀

### Secrets in Replit setzen:
1. Links: **Secrets** (🔐)
2. Hinzufügen:
   - `LIVE_VOL_SHEET_ID`
   - `POOL_CONFIG_SHEET_ID`
   - `MITARBEITER_SHEET_ID`

---

## 📋 Features im Detail

### Auto/Manuell-Toggle (🔄 AUTO / ✏️ MANUELL)
- **AUTO**: Mitarbeiter-Daten werden alle 5 Sek. aus Google Sheets importiert
- **MANUELL**: Schützt manuelle Eingaben vor Überschreibung

### Developer-Modus
- Passwort: `123`
- Ermöglicht Bearbeitung der Mitarbeiternummern

### Live-Sync zwischen Seiten
- Änderungen auf `seite3.html` erscheinen live auf `index.html`
- Backend API mit 5-Minuten-Cache (TTL)

---

## 🐛 Häufige Probleme

### "400 Bad Request" bei Google Sheets
→ **Lösung**: Google Sheet muss öffentlich sein (siehe oben)

### Änderungen nicht sichtbar
→ **Lösung**: Server neu starten (`python3 server.py`)

### Port 5000 bereits belegt
→ **Lösung**: Port in `server.py` ändern (Zeile 380):
```python
app.run(host='0.0.0.0', port=8000, debug=False)
```

---

## 📝 Lizenz

Dieses Projekt ist privat. Alle Rechte vorbehalten.

---

## 🤝 Unterstützung

Bei Fragen oder Problemen: Kontaktiere den Entwickler

---

**Viel Erfolg mit deiner Einsatzplanung! 🎮✨**
