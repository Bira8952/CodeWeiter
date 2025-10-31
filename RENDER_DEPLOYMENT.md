# 🚀 Render.com Deployment Anleitung

## 100% KOSTENLOS deine App hosten!

---

## ✅ Schritt 1: GitHub vorbereiten

### 1.1 Code auf GitHub hochladen

**In Replit:**
1. Links auf **🔧 Tools** klicken
2. Auf **"+"** klicken
3. **"Git"** wählen
4. **"Connect to GitHub"** klicken
5. Mit GitHub einloggen
6. Repository-Name eingeben (z.B. `einsatzplanung-nintendo`)
7. **"Stage All"** klicken
8. Commit-Message schreiben: `Initial Release - Nintendo Einsatzplanung`
9. **"Commit"** klicken
10. **"Push"** klicken

✅ **Fertig!** Code ist auf GitHub!

---

## ✅ Schritt 2: Render.com Account erstellen

1. Gehe zu: **https://render.com**
2. Klicke **"Get Started for Free"**
3. Wähle **"Sign up with GitHub"**
4. Authentifiziere deinen GitHub-Account
5. Erlaube Render Zugriff auf deine Repositories

✅ **Fertig!** Account erstellt!

---

## ✅ Schritt 3: Web Service erstellen

### 3.1 Neuen Service starten

1. Im Render Dashboard → Klicke **"New +"**
2. Wähle **"Web Service"**
3. Wähle dein GitHub-Repository: `einsatzplanung-nintendo`
4. Klicke **"Connect"**

### 3.2 Service konfigurieren

Fülle folgende Felder aus:

**Name:**
```
einsatzplanung
```

**Region:**
```
Frankfurt (EU Central) - näher zu Deutschland!
```

**Branch:**
```
main
```
(oder `master`, je nachdem was du hast)

**Runtime:**
```
Python 3
```

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
gunicorn --bind=0.0.0.0:$PORT --workers=2 server:app
```

**Instance Type:**
```
Free ✅ (ganz wichtig!)
```

### 3.3 PostgreSQL Datenbank hinzufügen

**WICHTIG: Die App benötigt eine PostgreSQL Datenbank!**

1. Klicke auf **"New +"** im Dashboard
2. Wähle **"PostgreSQL"**
3. Fülle folgende Felder aus:
   - **Name:** `einsatzplanung-db`
   - **Database:** `einsatzplanung`
   - **User:** `einsatzplanung_user`
   - **Region:** Frankfurt (EU Central)
   - **Instance Type:** Free ✅
4. Klicke **"Create Database"**
5. ⏳ Warte 1-2 Minuten bis die Datenbank erstellt ist
6. Kopiere die **Internal Database URL** (wichtig für nächsten Schritt!)

---

## ✅ Schritt 4: Environment Variables (Secrets) setzen

### 4.1 Im Render Dashboard

Scrolle runter zu **"Environment Variables"**

### 4.2 Füge hinzu (Klicke "Add Environment Variable")

**Variable 1 - Datenbank (WICHTIG!):**
```
Key:   DATABASE_URL
Value: [Kopierte Internal Database URL aus Schritt 3.3]
```
Beispiel: `postgresql://einsatzplanung_user:password@dpg-xxxxx-a.frankfurt-postgres.render.com/einsatzplanung`

**Variable 2:**
```
Key:   LIVE_VOL_SHEET_ID
Value: 1EhhG5Da2kDpLMktcrSdn1DTMnr_XLEdJyNUI2ZwLuQ4
```

**Variable 3 (Optional - falls du Pool-Daten aus Sheets lesen willst):**
```
Key:   POOL_CONFIG_SHEET_ID
Value: 14e85oqQrUjywXjNasJz7azME0t18RJEEldgRwCRFiH4
```

**Variable 4 (Optional für Session):**
```
Key:   SESSION_SECRET
Value: dein-geheimer-schluessel-12345
```

---

## ✅ Schritt 5: Datenbank initialisieren

**WICHTIG: Tabellen erstellen**

Nach dem ersten Deploy:

1. Gehe zu deiner PostgreSQL Datenbank in Render
2. Klicke auf **"Connect"** → **"External Connection"**
3. Öffne ein Terminal (z.B. in Replit)
4. Führe aus:
```bash
psql "postgresql://einsatzplanung_user:password@dpg-xxxxx-a.frankfurt-postgres.render.com/einsatzplanung"
```

5. Kopiere und führe folgendes SQL aus:
```sql
CREATE TABLE IF NOT EXISTS pools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    start_time VARCHAR(10) NOT NULL,
    deadline VARCHAR(10) NOT NULL,
    factor DECIMAL(5,2) DEFAULT 1.0,
    rate INTEGER DEFAULT 80,
    use_rotation BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mitarbeiter (
    id SERIAL PRIMARY KEY,
    date VARCHAR(10) UNIQUE NOT NULL,
    frueh INTEGER DEFAULT 0,
    spat INTEGER DEFAULT 0,
    taeti INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Standard-Pools einfügen (18 Pools)
INSERT INTO pools (name, start_time, deadline, factor, rate, use_rotation) VALUES
('FR bis 08:45', '06:00', '08:45', 1, 80, true),
('DE bis 10:00', '06:00', '10:00', 1, 80, true),
('EMS bis 13:30 und 17:00', '06:00', '13:30', 1, 80, false),
('Luftverkehr bis 16:00', '06:00', '16:00', 1, 80, false),
('Endpunkt bis 17:00', '06:00', '17:00', 1, 80, false),
('Kleinwaren MUE ab 11:00', '12:00', '17:00', 1.2, 80, false),
('NL bis 11:00', '06:00', '11:00', 1, 80, true),
('DK+NO+SE+CZ+LU+HU+IS bis 11:00', '06:00', '11:00', 1, 80, true),
('JP+AU+HK+TH+CA+US+IT', '06:00', '17:00', 1, 80, false),
('CH Retouren bis 17:00', '06:00', '17:00', 1, 80, false),
('WA Pakete bis 13:00', '06:00', '13:00', 1, 80, false),
('WA Kleinwaren MUE bis 11:00', '06:00', '11:00', 1, 80, false),
('BE+GB bis 15:00', '06:00', '15:00', 1, 80, true),
('AT bis 16:30', '06:00', '16:30', 1, 80, true),
('EMK PRA BackOffice1', '06:00', '17:00', 1, 80, false),
('AVIS PRA BackOffice1', '06:00', '17:00', 1, 80, false),
('ZB Pakete Restbestand', '06:00', '17:00', 1, 80, false),
('ZB Pakete heute', '06:00', '17:00', 1, 80, false)
ON CONFLICT (name) DO NOTHING;
```

6. Tippe `\q` um psql zu beenden
7. ✅ **Datenbank ist bereit!**

---

## ✅ Schritt 6: Deploy!

1. Scrolle nach unten
2. Klicke **"Create Web Service"**
3. ⏳ Warte 2-3 Minuten (Render installiert alles automatisch)
4. ✅ **FERTIG!**

---

## 🌐 Deine App ist jetzt LIVE!

### Du bekommst eine URL wie:
```
https://einsatzplanung.onrender.com
```

**Diese URL kannst du mit jedem teilen!**

---

## 📊 Was passiert nach dem Deployment?

### ✅ Automatisch:
- Render lädt deinen Code von GitHub
- Installiert alle Pakete aus `requirements.txt`
- Startet den Gunicorn-Server
- Gibt dir eine öffentliche HTTPS-URL

### ⚠️ Free-Plan Einschränkung:
- App **schläft nach 15 Minuten** Inaktivität
- **Erste Anfrage danach:** ~30 Sekunden (Aufwachen)
- **Danach:** Normal schnell!

---

## 🔄 Updates machen

### Wenn du Code änderst:

**In Replit:**
1. Ändere deinen Code
2. Git-Tool öffnen
3. **"Stage All"** → **"Commit"** → **"Push"**

**Auf Render:**
- Render erkennt automatisch den Push
- Deployt die neue Version automatisch! 🚀

---

## 🐛 Fehlersuche

### App startet nicht?

**Prüfe die Logs:**
1. Render Dashboard → Dein Service
2. Klicke auf **"Logs"**
3. Suche nach Fehlermeldungen

### Häufige Fehler:

**"ModuleNotFoundError"**
→ Lösung: Prüfe `requirements.txt` - fehlt ein Paket?

**"Port already in use"**
→ Lösung: Start-Command muss `$PORT` verwenden (nicht 5000!)

**"Google Sheets 400 Error"**
→ Lösung: Google Sheets müssen öffentlich sein!

---

## 💰 Kosten

**FREE Plan:**
- ✅ **$0 / Monat**
- ✅ 750 Stunden/Monat
- ✅ Automatisches HTTPS
- ✅ Automatische Deployments

**Keine Kreditkarte nötig!**

---

## 🎯 Fertig!

Deine Nintendo-Style Einsatzplanung läuft jetzt **kostenlos 24/7** auf Render.com! 🎉

**App-URL teilen und loslegen!** 🚀
