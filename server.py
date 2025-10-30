#!/usr/bin/env python3
from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS
import os
import csv
import requests
import subprocess
import json
from io import StringIO

app = Flask(__name__, static_folder='.')
CORS(app)

# Google Sheets Config
GOOGLE_SHEETS_ID = "14e85oqQrUjywXjNasJz7azME0t18RJEEldgRwCRFiH4"
LIVEVOL_SHEET_GID = "0"  # Erster Tab für Live-Vol Daten
POOLS_CONFIG_SHEET_GID = "0"  # Pool-Konfiguration Tab (NAME, START, DEADLINE, FAKTOR, RATE, ROTATION)
MITARBEITER_SHEET_ID = "15yfflPhE6Lqykm8aqacnZcrJj0x0Y1Yd"  # Mitarbeiter-Daten Google Sheet

def fetch_google_sheet_csv(sheet_id, gid="0"):
    """Lädt Google Sheet als CSV"""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Fehler beim Laden von Google Sheets: {e}")
        return None

def get_default_pools():
    """Gibt Standard-Pools zurück (Fallback wenn Google Sheets nicht erreichbar)"""
    return [
        {"name": "FR bis 08:45", "start": "06:00", "deadline": "08:45", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "DE bis 10:00", "start": "06:00", "deadline": "10:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "EMS bis 13:30 und 17:00", "start": "06:00", "deadline": "17:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "Luftverkehr bis 16:00", "start": "06:00", "deadline": "16:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "Endpunkt bis 17:00", "start": "06:00", "deadline": "17:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "Kleinwaren MUE ab 11:00", "start": "06:00", "deadline": "11:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "NL bis 11:00", "start": "06:00", "deadline": "11:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "DK+NO+SE+CZ+LU+HU+IS bis 11:00", "start": "06:00", "deadline": "11:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "JP+AU+HK+TH+CA+US+IT", "start": "06:00", "deadline": "17:00", "factor": 1, "rate": 80, "schicht": "ROTATION"},
        {"name": "CH Retouren bis 17:00", "start": "06:00", "deadline": "17:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "WA Pakete bis 13:00", "start": "06:00", "deadline": "13:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "WA Kleinwaren MUE bis 11:00", "start": "06:00", "deadline": "11:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "BE+GB bis 15:00", "start": "06:00", "deadline": "15:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "AT bis 16:30", "start": "06:00", "deadline": "16:30", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "EMK PRA BackOffice1", "start": "06:00", "deadline": "17:00", "factor": 1, "rate": 80, "schicht": "ROTATION"},
        {"name": "AVIS PRA BackOffice1", "start": "06:00", "deadline": "17:00", "factor": 1, "rate": 80, "schicht": "ROTATION"},
        {"name": "ZB Pakete Restbestand", "start": "06:00", "deadline": "17:00", "factor": 1, "rate": 80, "schicht": "ROTATION"},
        {"name": "ZB Pakete heute", "start": "06:00", "deadline": "17:00", "factor": 1, "rate": 80, "schicht": "ROTATION"},
    ]

def parse_pools_from_csv(csv_text):
    """
    Parst Pool-Konfiguration aus CSV
    
    Erwartetes Format (mit Header-Zeile):
    NAME,START,DEADLINE,FAKTOR,RATE,ROTATION
    FR bis 08:45,06:00,08:45,1,80,NEIN
    DE bis 10:00,06:00,10:00,1,80,JA
    ...
    """
    pools = []
    
    if not csv_text:
        print("⚠️ Kein CSV-Text vorhanden, verwende Standard-Pools")
        return get_default_pools()
    
    try:
        csv_file = StringIO(csv_text)
        reader = csv.reader(csv_file)
        rows = list(reader)
        
        if len(rows) < 2:
            print("⚠️ Zu wenige Zeilen in CSV, verwende Standard-Pools")
            return get_default_pools()
        
        # Erste Zeile ist Header
        header = [col.strip().upper() for col in rows[0]]
        
        # Finde Spalten-Indizes
        try:
            name_idx = header.index('NAME')
            start_idx = header.index('START')
            deadline_idx = header.index('DEADLINE')
            factor_idx = header.index('FAKTOR')
            rate_idx = header.index('RATE')
            rotation_idx = header.index('ROTATION')
        except ValueError as e:
            print(f"⚠️ Fehlende Spalte in CSV: {e}, verwende Standard-Pools")
            return get_default_pools()
        
        # Parse Pool-Daten
        for i, row in enumerate(rows[1:], start=2):
            if len(row) < max(name_idx, start_idx, deadline_idx, factor_idx, rate_idx, rotation_idx) + 1:
                print(f"⚠️ Zeile {i} hat zu wenige Spalten, überspringe")
                continue
            
            try:
                rotation_value = row[rotation_idx].strip().upper()
                use_rotation = rotation_value == 'JA'
                
                pool = {
                    "name": row[name_idx].strip(),
                    "start": row[start_idx].strip(),
                    "deadline": row[deadline_idx].strip(),
                    "factor": float(row[factor_idx].strip()) if row[factor_idx].strip() else 1,
                    "rate": int(row[rate_idx].strip()) if row[rate_idx].strip() else 80,
                    "useRotation": use_rotation
                }
                
                # Validierung
                if not pool["name"]:
                    print(f"⚠️ Zeile {i}: Name ist leer, überspringe")
                    continue
                
                pools.append(pool)
                print(f"✓ Pool geladen: {pool['name']} (START: {pool['start']}, DEADLINE: {pool['deadline']}, ROTATION: {rotation_value})")
                
            except (ValueError, IndexError) as e:
                print(f"⚠️ Fehler beim Parsen von Zeile {i}: {e}, überspringe")
                continue
        
        if pools:
            print(f"✅ {len(pools)} Pools erfolgreich aus Google Sheets geladen")
            return pools
        else:
            print("⚠️ Keine gültigen Pools gefunden, verwende Standard-Pools")
            return get_default_pools()
            
    except Exception as e:
        print(f"❌ Fehler beim Parsen des CSV: {e}, verwende Standard-Pools")
        return get_default_pools()

@app.route('/')
def index():
    response = make_response(send_from_directory('.', 'index.html'))
    # Disable caching for index.html to always get latest version
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/pools', methods=['GET'])
def get_pools():
    """Lädt Pool-Konfiguration aus Google Sheets (Tab 2)"""
    try:
        print(f"📥 Lade Pool-Konfiguration aus Google Sheets (GID={POOLS_CONFIG_SHEET_GID})...")
        
        # Lade CSV von Google Sheets (Tab 2 für Pool-Konfiguration)
        csv_text = fetch_google_sheet_csv(GOOGLE_SHEETS_ID, POOLS_CONFIG_SHEET_GID)
        
        # Parse Pools
        pools = parse_pools_from_csv(csv_text)
        
        print(f"✅ {len(pools)} Pools bereitgestellt")
        return jsonify(pools)
    except Exception as e:
        print(f"❌ Fehler beim Laden der Pools: {e}")
        # Fallback zu Standard-Pools
        return jsonify(get_default_pools())

@app.route('/api/pools/save-to-sheets', methods=['POST'])
def save_pools_to_sheets():
    """Speichert Pool-Konfiguration ins Google Sheet (Web → Google Sheet)"""
    try:
        pools = request.get_json()
        
        if not pools or not isinstance(pools, list):
            return jsonify({"error": "Ungültige Pool-Daten"}), 400
        
        print(f"📝 Speichere {len(pools)} Pools ins Google Sheet...")
        
        # Konvertiere Pools zu JSON String
        pools_json = json.dumps(pools)
        
        # Rufe Node.js Script auf
        result = subprocess.run(
            ['node', 'writeToGoogleSheets.js', pools_json],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Pools erfolgreich ins Google Sheet geschrieben")
            print(result.stdout)
            return jsonify({"success": True, "message": "Pools ins Google Sheet gespeichert"})
        else:
            print(f"❌ Fehler beim Schreiben ins Google Sheet: {result.stderr}")
            return jsonify({"error": result.stderr}), 500
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout beim Schreiben ins Google Sheet")
        return jsonify({"error": "Timeout"}), 500
    except Exception as e:
        print(f"❌ Fehler beim Speichern ins Google Sheet: {e}")
        return jsonify({"error": str(e)}), 500

# In-Memory Speicher für Mitarbeiter-Daten (Key: Datum, Value: {maFrueh, maSpat, maRotation})
mitarbeiter_cache = {}

@app.route('/api/mitarbeiter/<date>', methods=['GET'])
def get_mitarbeiter(date):
    """Lädt Mitarbeiter-Daten für ein bestimmtes Datum"""
    try:
        # Prüfe zuerst den Cache (Live-Daten aus seite3.html)
        if date in mitarbeiter_cache:
            data = mitarbeiter_cache[date]
            print(f"✅ Mitarbeiter für {date} aus Cache: FRÜH={data['maFrueh']}, SPÄT={data['maSpat']}, ROTATION={data['maRotation']}")
            return jsonify(data)
        
        # Fallback: Versuche aus Google Sheets zu laden
        print(f"📥 Lade Mitarbeiter-Daten für {date} aus Google Sheets...")
        
        csv_text = fetch_google_sheet_csv(MITARBEITER_SHEET_ID, gid="0")
        
        if not csv_text:
            print("⚠️ Mitarbeiter-Sheet nicht erreichbar, verwende 0/0/0")
            return jsonify({"maFrueh": 0, "maSpat": 0, "maRotation": 0})
        
        # Parse CSV
        csv_file = StringIO(csv_text)
        reader = csv.reader(csv_file)
        lines = list(reader)
        
        if len(lines) < 6:
            print("⚠️ Mitarbeiter-Sheet hat zu wenige Zeilen")
            return jsonify({"maFrueh": 0, "maSpat": 0, "maRotation": 0})
        
        # Finde die Spalte für das Datum
        date_parts = date.split('-')
        if len(date_parts) == 3:
            day = date_parts[2].lstrip('0')
            month = date_parts[1].lstrip('0')
            search_date = f"{day}.{month}."
        else:
            print(f"⚠️ Ungültiges Datumsformat: {date}")
            return jsonify({"maFrueh": 0, "maSpat": 0, "maRotation": 0})
        
        date_row = lines[3] if len(lines) > 3 else []
        col_index = -1
        
        for i, cell in enumerate(date_row):
            if search_date in str(cell):
                col_index = i
                break
        
        if col_index == -1:
            print(f"⚠️ Datum {search_date} nicht im Sheet gefunden")
            return jsonify({"maFrueh": 0, "maSpat": 0, "maRotation": 0})
        
        # Zähle Schichten
        count_frueh = 0
        count_spat = 0
        count_rotation = 0
        
        for row_idx in range(4, len(lines)):
            row = lines[row_idx]
            mitarbeiter = row[0].strip() if len(row) > 0 else ""
            if not mitarbeiter:
                continue
            
            if col_index >= len(row):
                continue
                
            schicht_code = row[col_index].strip().upper()
            
            if not schicht_code or schicht_code == '-' or schicht_code == '':
                continue
            
            schicht_code = ''.join([c for c in schicht_code if not c.isdigit()]).strip()
            
            if schicht_code in ['FT', 'A', 'U', 'K', 'URD', 'KA']:
                continue
            
            if 'FRÜH' in schicht_code or 'FRUEH' in schicht_code:
                count_frueh += 1
            elif 'SPÄT' in schicht_code or 'SPAT' in schicht_code:
                count_spat += 1
            elif 'ROTATION' in schicht_code or schicht_code == 'ROT':
                count_rotation += 1
        
        print(f"✅ Mitarbeiter für {date}: FRÜH={count_frueh}, SPÄT={count_spat}, ROTATION={count_rotation}")
        
        return jsonify({
            "maFrueh": count_frueh,
            "maSpat": count_spat,
            "maRotation": count_rotation
        })
        
    except Exception as e:
        print(f"❌ Fehler beim Laden der Mitarbeiter-Daten: {e}")
        return jsonify({"maFrueh": 0, "maSpat": 0, "maRotation": 0})

@app.route('/api/mitarbeiter/save', methods=['POST'])
def save_mitarbeiter():
    """Speichert Mitarbeiter-Daten (wird von index.html aufgerufen)"""
    try:
        data = request.get_json()
        
        if not data or ('date' not in data and 'datum' not in data):
            return jsonify({"error": "Ungültige Daten"}), 400
        
        date = data.get('date') or data.get('datum')
        ma_frueh = data.get('maFrueh', 0)
        ma_spat = data.get('maSpat', 0)
        ma_rotation = data.get('maRotation', 0)
        
        # Speichere im Cache (wird von /api/mitarbeiter/<date> gelesen)
        mitarbeiter_cache[date] = {
            "maFrueh": ma_frueh,
            "maSpat": ma_spat,
            "maRotation": ma_rotation
        }
        
        print(f"💾 Mitarbeiter gespeichert für {date}: FRÜH={ma_frueh}, SPÄT={ma_spat}, ROTATION={ma_rotation}")
        
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"❌ Fehler beim Speichern der Mitarbeiter-Daten: {e}")
        return jsonify({"error": str(e)}), 500

# Pool-Daten werden aus Google Sheets gelesen
# Änderungen aus dem Web werden ins Google Sheet geschrieben (Web → Google Sheet)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
