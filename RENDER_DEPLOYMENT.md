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

---

## ✅ Schritt 4: Environment Variables (Secrets) setzen

### 4.1 Im Render Dashboard

Scrolle runter zu **"Environment Variables"**

### 4.2 Füge hinzu (Klicke "Add Environment Variable")

**Variable 1:**
```
Key:   LIVE_VOL_SHEET_ID
Value: 1EhhG5Da2kDpLMktcrSdn1DTMnr_XLEdJyNUI2ZwLuQ4
```

**Variable 2:**
```
Key:   POOL_CONFIG_SHEET_ID
Value: 14e85oqQrUjywXjNasJz7azME0t18RJEEldgRwCRFiH4
```

**Variable 3:**
```
Key:   MITARBEITER_SHEET_ID
Value: 15yfflPhE6Lqykm8aqacnZcrJj0x0Y1Yd
```

**Variable 4 (Optional für Session):**
```
Key:   SESSION_SECRET
Value: dein-geheimer-schluessel-12345
```

---

## ✅ Schritt 5: Deploy!

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
